import {
  BedrockRuntimeClient,
  BedrockRuntimeClientConfig,
  InvokeModelWithBidirectionalStreamCommand,
  InvokeModelWithBidirectionalStreamInput,
} from "@aws-sdk/client-bedrock-runtime";
import {
  NodeHttp2Handler,
  NodeHttp2HandlerOptions,
} from "@smithy/node-http-handler";
import { Provider } from "@smithy/types";
import { Buffer } from "node:buffer";
import { randomUUID } from "node:crypto";
import { Subject } from "rxjs";
import { take } from "rxjs/operators";
import { firstValueFrom } from "rxjs";
import {
  DefaultAudioInputConfiguration,
  DefaultAudioOutputConfiguration,
  DefaultTextConfiguration,
} from "./consts";
import { DefaultSystemPrompt } from "./prompt";
import { StreamSession } from "./streamSession";
import { InferenceConfig } from "./types";
import { ToolProcessor } from "./prompt";
import { Database } from "./database";
import { ToolHandler } from "./services/tools";

export interface NovaSonicBidirectionalStreamClientConfig {
  requestHandlerConfig?:
    | NodeHttp2HandlerOptions
    | Provider<NodeHttp2HandlerOptions | void>;
  clientConfig: Partial<BedrockRuntimeClientConfig>;
  inferenceConfig?: InferenceConfig;
  toolHandler?: ToolHandler;
}

// Types for event handling
type ResponseHandler = (data: any) => void;
type EventPayload = Record<string, any>;

// Session data type
interface SessionData {
  // Queue-related properties
  queue: Array<EventPayload>;
  queueSignal: Subject<void>;
  closeSignal: Subject<void>;
  responseSubject: Subject<any>;

  // Tool use properties
  toolUseContent: EventPayload | null;
  toolUseId: string;
  toolName: string;

  // Event handlers
  responseHandlers: Map<string, ResponseHandler>;

  // Session metadata
  promptName: string;
  inferenceConfig: InferenceConfig;
  isActive: boolean;
  isPromptStartSent: boolean;
  isAudioContentStartSent: boolean;
  audioContentId: string;
  robots: string[];
}

export class NovaSonicBidirectionalStreamClient {
  private bedrockRuntimeClient: BedrockRuntimeClient;
  private inferenceConfig: InferenceConfig;
  private activeSessions: Map<string, SessionData> = new Map();
  private sessionLastActivity: Map<string, number> = new Map();
  private sessionCleanupInProgress = new Set<string>();
  private toolProcessor: ToolProcessor;
  private database: Database;

  constructor(config: NovaSonicBidirectionalStreamClientConfig) {
    const nodeHttp2Handler = new NodeHttp2Handler({
      requestTimeout: 300000,
      sessionTimeout: 300000,
      disableConcurrentStreams: false,
      maxConcurrentStreams: 20,
      ...config.requestHandlerConfig,
    });

    if (!config.clientConfig.credentials) {
      throw new Error("No credentials provided");
    }

    this.bedrockRuntimeClient = new BedrockRuntimeClient({
      ...config.clientConfig,
      credentials: config.clientConfig.credentials,
      region: config.clientConfig.region || "us-east-1",
      requestHandler: nodeHttp2Handler,
    });

    this.inferenceConfig = config.inferenceConfig ?? {
      maxTokens: 1024,
      topP: 0.5,
      temperature: 0.3,
    };

    this.toolProcessor = new ToolProcessor(config.toolHandler);
    this.database = new Database();
  }

  public isSessionActive(sessionId: string): boolean {
    const session = this.activeSessions.get(sessionId);
    return !!session && session.isActive;
  }

  public getActiveSessions(): string[] {
    return Array.from(this.activeSessions.keys());
  }

  public getLastActivityTime(sessionId: string): number {
    return this.sessionLastActivity.get(sessionId) || 0;
  }

  private updateSessionActivity(sessionId: string): void {
    this.sessionLastActivity.set(sessionId, Date.now());
  }

  public isCleanupInProgress(sessionId: string): boolean {
    return this.sessionCleanupInProgress.has(sessionId);
  }
  /**
   * Creates a new streaming session for bidirectional communication with the model
   *
   * @param sessionId - Optional unique identifier for the session, auto-generated if not provided
   * @param config - Optional configuration overrides for this specific session
   * @returns StreamSession object that provides a higher-level interface to the session
   * @throws Error if a session with the given ID already exists
   */
  public createStreamSession(
    sessionId: string = randomUUID(),
    config?: NovaSonicBidirectionalStreamClientConfig
  ): StreamSession {
    if (this.activeSessions.has(sessionId)) {
      throw new Error(`Stream session with ID ${sessionId} already exists`);
    }

    const session: SessionData = {
      queue: [],
      queueSignal: new Subject<void>(),
      closeSignal: new Subject<void>(),
      responseSubject: new Subject<any>(),
      toolUseContent: null,
      toolUseId: "",
      toolName: "",
      responseHandlers: new Map(),
      promptName: randomUUID(),
      inferenceConfig: config?.inferenceConfig ?? this.inferenceConfig,
      isActive: true,
      isPromptStartSent: false,
      isAudioContentStartSent: false,
      audioContentId: randomUUID(),
      robots: ["robot_1"],
    };

    this.activeSessions.set(sessionId, session);

    return new StreamSession(sessionId, this);
  }
  /**
   * Initiates a bidirectional streaming session with AWS Bedrock
   * Sets up initial events and establishes the connection
   *
   * @param sessionId - The ID of the session to initiate
   * @throws Error if the session is not found
   */
  public async initiateSession(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`Stream session ${sessionId} not found`);
    }

    try {
      // Set up initial events for this session
      this.setupSessionStartEvent(sessionId);

      // Create the bidirectional stream with session-specific async iterator
      const asyncIterable = this.createSessionAsyncIterable(sessionId);

      console.log(`Starting bidirectional stream for session ${sessionId}...`);

      const response = await this.bedrockRuntimeClient.send(
        new InvokeModelWithBidirectionalStreamCommand({
          modelId: "amazon.nova-sonic-v1:0",
          body: asyncIterable,
        })
      );

      console.log(
        `Stream established for session ${sessionId}, processing responses...`
      );

      // Process responses for this session
      await this.processResponseStream(sessionId, response);
    } catch (error) {
      console.error(`Error in session ${sessionId}: `, error);
      this.dispatchEventForSession(sessionId, "error", {
        source: "bidirectionalStream",
        error,
      });

      // Make sure to clean up if there's an error
      if (session.isActive) {
        this.closeSession(sessionId);
      }
    }
  }
  // Dispatch events to handlers for a specific session
  private dispatchEventForSession(
    sessionId: string,
    eventType: string,
    data: any
  ): void {
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    this._dispatchToHandlers(sessionId, session, eventType, data);
  }
  /**
   * Creates an AsyncIterable for bidirectional streaming for a specific session
   */
  private createSessionAsyncIterable(
    sessionId: string
  ): AsyncIterable<InvokeModelWithBidirectionalStreamInput> {
    // Return empty iterator if session is not active
    if (!this.isSessionActive(sessionId)) {
      console.log(
        `Cannot create async iterable: Session ${sessionId} not active`
      );
      return {
        [Symbol.asyncIterator]: () => ({
          next: async () => ({ value: undefined, done: true }),
        }),
      };
    }

    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(
        `Cannot create async iterable: Session ${sessionId} not found`
      );
    }

    let eventCount = 0;

    return {
      [Symbol.asyncIterator]: () => {
        console.log(
          `AsyncIterable iterator requested for session ${sessionId}`
        );

        return {
          next: async (): Promise<
            IteratorResult<InvokeModelWithBidirectionalStreamInput>
          > => {
            try {
              // Check if session is still active
              if (!this.isSessionStatusValid(sessionId, session)) {
                return { value: undefined, done: true };
              }

              // Wait for items in the queue or close signal if queue is empty
              if (session.queue.length === 0) {
                try {
                  await this.waitForNextQueueItemOrClose(sessionId, session);
                } catch (error) {
                  // If we catch an error here, it's likely a signal to end the iterator
                  if (error instanceof Error) {
                    if (
                      error.message === "Stream closed" ||
                      !session.isActive
                    ) {
                      // This is an expected condition when closing the session
                      if (this.activeSessions.has(sessionId)) {
                        console.log(
                          `Session \${ sessionId } closed during wait`
                        );
                      }
                      return { value: undefined, done: true };
                    }
                  } else {
                    console.error(`Error on event close`, error);
                  }
                }
              }

              // Double-check session status after waiting
              if (!this.isSessionStatusValid(sessionId, session)) {
                return { value: undefined, done: true };
              }

              // Process the next item from queue
              return this.processNextQueueItem(
                sessionId,
                session,
                eventCount++
              );
            } catch (error) {
              console.error(`Error in session ${sessionId} iterator: `, error);
              this.cleanupSessionResources(sessionId);
              return { value: undefined, done: true };
            }
          },

          return: async (): Promise<
            IteratorResult<InvokeModelWithBidirectionalStreamInput>
          > => {
            console.log(`Iterator return() called for session ${sessionId}`);
            this.cleanupSessionResources(sessionId);
            return { value: undefined, done: true };
          },

          throw: async (
            error: any
          ): Promise<
            IteratorResult<InvokeModelWithBidirectionalStreamInput>
          > => {
            console.log(
              `Iterator throw() called for session ${sessionId} with error: `,
              error
            );
            this.cleanupSessionResources(sessionId);
            throw error;
          },
        };
      },
    };
  }

  /**
   * Check if a session's status is valid for continuing iteration
   */
  private isSessionStatusValid(
    sessionId: string,
    session: SessionData
  ): boolean {
    if (!session.isActive || !this.activeSessions.has(sessionId)) {
      console.log(`Iterator closing for session ${sessionId}, done = true`);
      return false;
    }
    return true;
  }

  /**
   * Wait for the next queue item or session close signal
   */
  private async waitForNextQueueItemOrClose(
    sessionId: string,
    session: SessionData
  ): Promise<void> {
    try {
      await Promise.race([
        firstValueFrom(session.queueSignal.pipe(take(1))),
        firstValueFrom(session.closeSignal.pipe(take(1))).then(() => {
          throw new Error("Stream closed");
        }),
      ]);
    } catch (error) {
      if (error instanceof Error) {
        if (error.message === "Stream closed" || !session.isActive) {
          // This is an expected condition when closing the session
          if (this.activeSessions.has(sessionId)) {
            console.log(`Session ${sessionId} closed during wait`);
          }
          throw error; // Re-throw to signal completion
        }
      } else {
        console.error(`Error on event close`, error);
        throw error;
      }
    }
  }

  /**
   * Process the next item in the queue and return it as an iterator result
   */
  private processNextQueueItem(
    sessionId: string,
    session: SessionData,
    eventCount: number
  ): IteratorResult<InvokeModelWithBidirectionalStreamInput> {
    // If queue is empty or session is inactive, we're done
    if (session.queue.length === 0 || !session.isActive) {
      console.log(`Queue empty or session inactive: ${sessionId} `);
      return { value: undefined, done: true };
    }

    // Get next item from the session's queue
    const nextEvent = session.queue.shift();

    // For debugging, uncomment this to see events:
    // if (eventCount % 10 === 0) {
    //   console.log(`Sending event #${eventCount} for session ${sessionId}: ${JSON.stringify(nextEvent).substring(0, 100)}...`);
    // }

    return {
      value: {
        chunk: {
          bytes: new TextEncoder().encode(JSON.stringify(nextEvent)),
        },
      },
      done: false,
    };
  }
  // Process the response stream from AWS Bedrock
  private async processResponseStream(
    sessionId: string,
    response: any
  ): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    try {
      for await (const event of response.body) {
        if (!session.isActive) {
          console.log(
            `Session ${sessionId} is no longer active, stopping response processing`
          );
          break;
        }

        if (event.chunk?.bytes) {
          await this.processResponseChunk(
            sessionId,
            session,
            event.chunk.bytes
          );
        } else if (
          event.modelStreamErrorException ||
          event.internalServerException
        ) {
          this.handleStreamException(sessionId, event);
        }
      }

      console.log(
        `Response stream processing complete for session ${sessionId}`
      );
      this.dispatchEvent(sessionId, "streamComplete", {
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error(
        `Error processing response stream for session ${sessionId}: `,
        error
      );
      this.dispatchEvent(sessionId, "error", {
        source: "responseStream",
        message: "Error processing response stream",
        details: error instanceof Error ? error.message : String(error),
      });
    }
  }

  // Process individual response chunk from stream
  private async processResponseChunk(
    sessionId: string,
    session: SessionData,
    bytes: Uint8Array
  ): Promise<void> {
    try {
      this.updateSessionActivity(sessionId);
      const textResponse = new TextDecoder().decode(bytes);

      try {
        const jsonResponse = JSON.parse(textResponse);
        await this.handleJsonResponse(sessionId, session, jsonResponse);
      } catch (e) {
        console.log(
          `Raw text response for session ${sessionId}(parse error): `,
          textResponse
        );
      }
    } catch (e) {
      console.error(
        `Error processing response chunk for session ${sessionId}: `,
        e
      );
    }
  }

  // Handle response exceptions from the stream
  private handleStreamException(sessionId: string, event: any): void {
    if (event.modelStreamErrorException) {
      console.error(
        `Model stream error for session ${sessionId}: `,
        event.modelStreamErrorException
      );
      this.dispatchEvent(sessionId, "error", {
        type: "modelStreamErrorException",
        details: event.modelStreamErrorException,
      });
    } else if (event.internalServerException) {
      console.error(
        `Internal server error for session ${sessionId}: `,
        event.internalServerException
      );
      this.dispatchEvent(sessionId, "error", {
        type: "internalServerException",
        details: event.internalServerException,
      });
    }
  }

  // Process structured JSON response
  private async handleJsonResponse(
    sessionId: string,
    session: SessionData,
    jsonResponse: any
  ): Promise<void> {
    if (jsonResponse.event?.contentStart) {
      this.dispatchEvent(
        sessionId,
        "contentStart",
        jsonResponse.event.contentStart
      );
    } else if (jsonResponse.event?.textOutput) {
      this.dispatchEvent(
        sessionId,
        "textOutput",
        jsonResponse.event.textOutput
      );
    } else if (jsonResponse.event?.audioOutput) {
      this.dispatchEvent(
        sessionId,
        "audioOutput",
        jsonResponse.event.audioOutput
      );
    } else if (jsonResponse.event?.toolUse) {
      await this.handleToolUseEvent(
        sessionId,
        session,
        jsonResponse.event.toolUse
      );
    } else if (
      jsonResponse.event?.contentEnd &&
      jsonResponse.event?.contentEnd?.type === "TOOL"
    ) {
      await this.handleToolEndEvent(sessionId, session);
    } else if (jsonResponse.event?.contentEnd) {
      this.dispatchEvent(
        sessionId,
        "contentEnd",
        jsonResponse.event.contentEnd
      );
    } else {
      this.handleOtherEvents(sessionId, jsonResponse);
    }
  }

  // Handle tool use events
  private async handleToolUseEvent(
    sessionId: string,
    session: SessionData,
    toolUse: any
  ): Promise<void> {
    this.dispatchEvent(sessionId, "toolUse", toolUse);

    // Store tool use information for later
    session.toolUseContent = toolUse;
    session.toolUseId = toolUse.toolUseId;
    session.toolName = toolUse.toolName;
  }

  // Handle tool end events
  private async handleToolEndEvent(
    sessionId: string,
    session: SessionData
  ): Promise<void> {
    // Process tool use
    console.log(`Processing tool use for session ${sessionId}`);
    this.dispatchEvent(sessionId, "toolEnd", {
      toolUseContent: session.toolUseContent,
      toolUseId: session.toolUseId,
      toolName: session.toolName,
    });

    console.log("calling tooluse");
    console.log("tool use content : ", session.toolUseContent);
    const robots = session.robots || ["robot_1"];
    // function calling
    const toolResult = await this.toolProcessor.processToolUse(
      robots,
      session.toolName,
      session.toolUseContent
    );

    // Send tool result
    await this.sendToolResult(sessionId, session.toolUseId, toolResult);

    // Also dispatch event about tool result
    this.dispatchEvent(sessionId, "toolResult", {
      toolUseId: session.toolUseId,
      result: toolResult,
    });
  }

  // Handle other events not specifically handled
  private handleOtherEvents(sessionId: string, jsonResponse: any): void {
    const eventKeys = Object.keys(jsonResponse.event || {});
    console.log(`Event keys for session ${sessionId}: `, eventKeys);
    console.log(`Handling other events`);

    if (eventKeys.length > 0) {
      this.dispatchEvent(sessionId, eventKeys[0], jsonResponse.event);
    } else if (Object.keys(jsonResponse).length > 0) {
      this.dispatchEvent(sessionId, "unknown", jsonResponse);
    }
  }

  // Add an event to a session's queue
  private addEventToSessionQueue(sessionId: string, event: any): void {
    const session = this.activeSessions.get(sessionId);
    if (!session || !session.isActive) return;

    this.updateSessionActivity(sessionId);
    session.queue.push(event);
    session.queueSignal.next();
  }

  // Set up initial events for a session
  private setupSessionStartEvent(sessionId: string): void {
    console.log(`Setting up initial events for session ${sessionId}...`);
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    // Session start event
    this.addEventToSessionQueue(sessionId, {
      event: {
        sessionStart: {
          inferenceConfiguration: session.inferenceConfig,
        },
      },
    });
  }
  public setupPromptStartEvent(sessionId: string): void {
    console.log(`Setting up prompt start event for session ${sessionId}...`);
    const sessionDataPrompt = this.activeSessions.get(sessionId);
    if (!sessionDataPrompt) return;

    // Use session.robots if available, fallback to session.robot
    const robotIdPrompt =
      (sessionDataPrompt as any).robots &&
      (sessionDataPrompt as any).robots.length > 0
        ? (sessionDataPrompt as any).robots[0]
        : "robot_1";
    // Determine voiceId based on robotId
    let voiceId = "matthew";
    if (robotIdPrompt) {
      if (robotIdPrompt === "all") {
        voiceId = "tiffany";
      } else {
        const lastChar = robotIdPrompt.slice(-1);
        if (!isNaN(Number(lastChar)) && Number(lastChar) % 2 === 1) {
          voiceId = "tiffany";
        }
      }
    }
    const audioConfig = { ...DefaultAudioOutputConfiguration, voiceId };
    console.log(`${robotIdPrompt} using voice ID: ${voiceId}`);

    // Get all available tools (robot actions + MCP tools)
    const allAvailableTools = this.toolProcessor.getAllAvailableTools();
    console.log(
      `Setting up ${allAvailableTools.length} tools for session ${sessionId}:`,
      allAvailableTools.map((t) => t.toolSpec.name).join(", ")
    );

    // Prompt start event
    this.addEventToSessionQueue(sessionId, {
      event: {
        promptStart: {
          promptName: sessionDataPrompt.promptName,
          textOutputConfiguration: {
            mediaType: "text/plain",
          },
          audioOutputConfiguration: audioConfig,
          toolUseOutputConfiguration: {
            mediaType: "application/json",
          },
          toolChoice: {
            any: {},
          },
          toolConfiguration: {
            tools: allAvailableTools,
          },
        },
      },
    });
    sessionDataPrompt.isPromptStartSent = true;
  }
  /**
   * Set the robot ID(s) for a specific session
   * @param sessionId - The session to set the robot(s) for
   * @param robots - The robot ID(s) to use for tool processing
   */
  public setRobot(sessionId: string, robots: string[] | string) {
    const session = this.activeSessions.get(sessionId);
    if (!session) return;
    if (Array.isArray(robots)) {
      session.robots = robots; // Store first robot for compatibility
      (session as any).robots = robots;
    } else {
      session.robots = [robots];
    }
  }
  public async setupSystemPromptEvent(
    sessionId: string,
    textConfig: typeof DefaultTextConfiguration = DefaultTextConfiguration,
    systemPromptContent: string = DefaultSystemPrompt
  ): Promise<void> {
    console.log(`Setting up systemPrompt events for session ${sessionId}...`);

    const session = this.activeSessions.get(sessionId);
    if (!session) return;
    const robotId =
      (session as any).robots && (session as any).robots.length > 0
        ? (session as any).robots[0]
        : "robot_1";
    const context = await this.database.getRobot(robotId);
    let systemPrompt = systemPromptContent;
    if (context) {
      const name = context.robot_name;
      const background = context.context;

      systemPrompt = systemPromptContent.replace(
        "<background></background>",
        `<background>
        Your Name: ${name}
        Background: ${background}
        </background>
         `
      );
    } else {
      systemPrompt = systemPromptContent.replace(
        "<background></background>",
        ""
      );
    }

    // Generate dynamic tools list for system prompt
    const allAvailableTools = this.toolProcessor.getAllAvailableTools();
    const toolsPrompt = allAvailableTools
      .map((tool) => `- ${tool.toolSpec.name}: ${tool.toolSpec.description}`)
      .join("\n");

    // Replace the static tools list with dynamic one
    systemPrompt = systemPrompt.replace(
      /Available tools:\n.*$/s,
      `Available tools:\n${toolsPrompt}`
    );

    console.log(`Using system prompt content: ${systemPrompt}`);
    const sessionDataSys = this.activeSessions.get(sessionId);
    if (!sessionDataSys) return;
    const robotIdSys =
      (sessionDataSys as any).robots &&
      (sessionDataSys as any).robots.length > 0
        ? (sessionDataSys as any).robots[0]
        : "robot_1";
    const robotContextSys = await this.database.getRobot(robotIdSys);
    let sysPrompt = systemPromptContent;
    if (robotContextSys) {
      const name = robotContextSys.robot_name;
      const background = robotContextSys.context;
      sysPrompt = systemPromptContent.replace(
        "<background></background>",
        `<background>\n        Your Name: ${name}\n        Background: ${background}\n        </background>\n         `
      );
    } else {
      sysPrompt = systemPromptContent.replace("<background></background>", "");
    }

    // Update system prompt with dynamic tools list for the final prompt too
    sysPrompt = sysPrompt.replace(
      /Available tools:\n.*$/s,
      `Available tools:\n${toolsPrompt}`
    );

    console.log(`Using system prompt content: ${sysPrompt}`);
    // Text content start
    const textPromptID = randomUUID();
    this.addEventToSessionQueue(sessionId, {
      event: {
        contentStart: {
          promptName: sessionDataSys.promptName,
          contentName: textPromptID,
          type: "TEXT",
          interactive: true,
          role: "SYSTEM",
          textInputConfiguration: textConfig,
        },
      },
    });
    // Text input content
    this.addEventToSessionQueue(sessionId, {
      event: {
        textInput: {
          promptName: sessionDataSys.promptName,
          contentName: textPromptID,
          content: sysPrompt,
        },
      },
    });
    // Text content end
    this.addEventToSessionQueue(sessionId, {
      event: {
        contentEnd: {
          promptName: sessionDataSys.promptName,
          contentName: textPromptID,
        },
      },
    });
  }

  public setupStartAudioEvent(
    sessionId: string,
    audioConfig: typeof DefaultAudioInputConfiguration = DefaultAudioInputConfiguration
  ): void {
    console.log(
      `Setting up startAudioContent event for session ${sessionId}...`
    );
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    console.log(`Using audio content ID: ${session.audioContentId}`);
    // Audio content start
    this.addEventToSessionQueue(sessionId, {
      event: {
        contentStart: {
          promptName: session.promptName,
          contentName: session.audioContentId,
          type: "AUDIO",
          interactive: true,
          role: "USER",
          audioInputConfiguration: audioConfig,
        },
      },
    });
    session.isAudioContentStartSent = true;
    console.log(`Initial events setup complete for session ${sessionId}`);
  }

  // Stream an audio chunk for a session
  public async streamAudioChunk(
    sessionId: string,
    audioData: Buffer
  ): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session || !session.isActive || !session.audioContentId) {
      throw new Error(`Invalid session ${sessionId} for audio streaming`);
    }
    // Convert audio to base64
    const base64Data = audioData.toString("base64");

    this.addEventToSessionQueue(sessionId, {
      event: {
        audioInput: {
          promptName: session.promptName,
          contentName: session.audioContentId,
          content: base64Data,
        },
      },
    });
  }

  // Send tool result back to the model
  private async sendToolResult(
    sessionId: string,
    toolUseId: string,
    result: any
  ): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    console.log("inside tool result");
    if (!session || !session.isActive) return;

    console.log(
      `Sending tool result for session ${sessionId}, tool use ID: ${toolUseId}`
    );
    const contentId = randomUUID();

    // Tool content start
    this.addEventToSessionQueue(sessionId, {
      event: {
        contentStart: {
          promptName: session.promptName,
          contentName: contentId,
          interactive: false,
          type: "TOOL",
          role: "TOOL",
          toolResultInputConfiguration: {
            toolUseId: toolUseId,
            type: "TEXT",
            textInputConfiguration: {
              mediaType: "text/plain",
            },
          },
        },
      },
    });

    // Tool content input
    const resultContent =
      typeof result === "string" ? result : JSON.stringify(result);
    this.addEventToSessionQueue(sessionId, {
      event: {
        toolResult: {
          promptName: session.promptName,
          contentName: contentId,
          content: resultContent,
        },
      },
    });

    // Tool content end
    this.addEventToSessionQueue(sessionId, {
      event: {
        contentEnd: {
          promptName: session.promptName,
          contentName: contentId,
        },
      },
    });

    console.log(`Tool result sent for session ${sessionId}`);
  }

  public async sendContentEnd(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session || !session.isAudioContentStartSent) return;

    await this.addEventToSessionQueue(sessionId, {
      event: {
        contentEnd: {
          promptName: session.promptName,
          contentName: session.audioContentId,
        },
      },
    });

    // Wait to ensure it's processed
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  public async sendPromptEnd(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session || !session.isPromptStartSent) return;

    await this.addEventToSessionQueue(sessionId, {
      event: {
        promptEnd: {
          promptName: session.promptName,
        },
      },
    });

    // Wait to ensure it's processed
    await new Promise((resolve) => setTimeout(resolve, 300));
  }

  public async sendSessionEnd(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    await this.addEventToSessionQueue(sessionId, {
      event: {
        sessionEnd: {},
      },
    });

    // Wait to ensure it's processed
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Now it's safe to clean up
    session.isActive = false;
    session.closeSignal.next();
    session.closeSignal.complete();
    this.activeSessions.delete(sessionId);
    this.sessionLastActivity.delete(sessionId);
    console.log(`Session ${sessionId} closed and removed from active sessions`);
  }

  // Register an event handler for a session
  public registerEventHandler(
    sessionId: string,
    eventType: string,
    handler: (data: any) => void
  ): void {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }
    session.responseHandlers.set(eventType, handler);
  }
  // Helper method for dispatching events to handlers
  private _dispatchToHandlers(
    sessionId: string,
    session: SessionData,
    eventType: string,
    data: any
  ): void {
    // Dispatch to specific event handler
    const handler = session.responseHandlers.get(eventType);
    if (handler) {
      try {
        handler(data);
      } catch (e) {
        console.error(
          `Error in ${eventType} handler for session ${sessionId}:`,
          e
        );
      }
    }

    // Also dispatch to "any" handlers
    const anyHandler = session.responseHandlers.get("any");
    if (anyHandler) {
      try {
        anyHandler({ type: eventType, data });
      } catch (e) {
        console.error(`Error in 'any' handler for session ${sessionId}:`, e);
      }
    }
  }

  // Dispatch an event to registered handlers
  private dispatchEvent(sessionId: string, eventType: string, data: any): void {
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    this._dispatchToHandlers(sessionId, session, eventType, data);
  }
  /**
   * Safely close a session with proper shutdown sequence
   */
  public async closeSession(sessionId: string): Promise<void> {
    if (this.sessionCleanupInProgress.has(sessionId)) {
      console.log(
        `Cleanup already in progress for session ${sessionId}, skipping`
      );
      return;
    }

    // Mark cleanup as in progress to prevent duplicate cleanup attempts
    this.sessionCleanupInProgress.add(sessionId);

    try {
      console.log(`Starting close process for session ${sessionId}`);

      // Send proper session closure events in sequence
      await this.sendContentEnd(sessionId);
      await this.sendPromptEnd(sessionId);
      await this.sendSessionEnd(sessionId);

      console.log(`Session ${sessionId} cleanup complete`);
    } catch (error) {
      console.error(
        `Error during closing sequence for session ${sessionId}:`,
        error
      );

      // Ensure cleanup happens even if there's an error
      await this.cleanupSessionResources(sessionId);
    } finally {
      // Always clean up the tracking set
      this.sessionCleanupInProgress.delete(sessionId);
    }
  }

  /**
   * Force close a session immediately without graceful shutdown
   */
  public forceCloseSession(sessionId: string): void {
    if (
      this.sessionCleanupInProgress.has(sessionId) ||
      !this.activeSessions.has(sessionId)
    ) {
      console.log(
        `Session ${sessionId} already being cleaned up or not active`
      );
      return;
    }

    this.sessionCleanupInProgress.add(sessionId);
    try {
      console.log(`Force closing session ${sessionId}`);
      this.cleanupSessionResources(sessionId);
      console.log(`Session ${sessionId} force closed`);
    } finally {
      this.sessionCleanupInProgress.delete(sessionId);
    }
  }

  /**
   * Clean up session resources
   */
  private cleanupSessionResources(sessionId: string): void {
    const session = this.activeSessions.get(sessionId);
    if (!session) return;

    // Immediately mark as inactive and clean up resources
    session.isActive = false;

    // Signal to any waiting async iterators that the session is closed
    session.closeSignal.next();
    session.closeSignal.complete();

    // Remove from tracking maps
    this.activeSessions.delete(sessionId);
    this.sessionLastActivity.delete(sessionId);
  }
}
