import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import {
  StdioClientTransport,
  getDefaultEnvironment,
} from "@modelcontextprotocol/sdk/client/stdio.js";

import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { ToolHandler } from "./tools";
import { McpConfig, McpServerConfig, McpTool } from "../types";
import { McpConfigLoader } from "./mcp-config";
import { URL } from "url";
import { randomUUID } from "crypto";

export class McpManager {
  private clients: Map<string, Client> = new Map();
  private transports: Map<
    string,
    StdioClientTransport | StreamableHTTPClientTransport
  > = new Map();
  private tools: Map<string, McpTool[]> = new Map();
  private toolHandler: ToolHandler;
  private config: McpConfig;

  constructor(toolHandler: ToolHandler) {
    this.toolHandler = toolHandler;
    this.config = McpConfigLoader.loadConfig();
  }

  /**
   * Initialize all enabled MCP servers
   */
  async initializeServers(): Promise<void> {
    const servers = Object.entries(this.config.mcpServers);
    console.log(`Found ${servers.length} MCP server configurations`);

    await Promise.all(
      servers.map(async ([serverName, serverConfig]) => {
        if (serverConfig.disabled !== true) {
          try {
            await this.connectToServer(serverName, serverConfig);
          } catch (error) {
            console.error(
              `Failed to connect to MCP server ${serverName}: ${error}`
            );
          }
        } else {
          console.log(
            `MCP server ${serverName} is disabled, skipping connection`
          );
        }
      })
    );
  }

  /**
   * Connect to specified MCP server
   */
  async connectToServer(
    serverName: string,
    config: McpServerConfig
  ): Promise<McpTool[]> {
    console.log(`Connecting to MCP server: ${serverName}`);

    try {
      // Create client
      const client = new Client({
        name: `speech-control-mcp-client-${serverName}`,
        version: "1.0.0",
        capabilities: {
          prompts: {},
          resources: {},
          tools: {},
        },
      });

      let transport;

      // Choose different transport based on command type
      if (config.command === "restful") {
        // Use StreamableHTTPClientTransport
        if (!config.baseUrl) {
          throw new Error("baseUrl must be provided when using restful mode");
        }

        if (config.baseUrl === "McpServerUrl") {
          // Use environment variable for baseUrl
          const baseUrl = process.env.McpServerUrl;
          if (!baseUrl) {
            throw new Error("McpServerUrl environment variable is not set");
          }
          config.baseUrl = baseUrl;
        }

        const sessionId = randomUUID();
        transport = new StreamableHTTPClientTransport(new URL(config.baseUrl), {
          sessionId: sessionId,
        });
      } else {
        // Use original StdioClientTransport
        let command = config.command;
        let args = [...config.args];

        if (config.command === "node") {
          command = process.execPath;
        }

        transport = new StdioClientTransport({
          command: command,
          args: args,
          env: {
            ...getDefaultEnvironment(),
            ...config.env,
          },
          stderr: "pipe",
        });
      }

      // Store transport and client
      this.transports.set(serverName, transport);
      this.clients.set(serverName, client);

      // Connect to server
      await client.connect(transport);
      console.log(`Successfully connected to MCP server: ${serverName}`);

      // Get available tools
      const toolsResponse = await client.listTools();
      const tools = toolsResponse.tools || [];

      console.log(`Found ${tools.length} tools in server ${serverName}:`);
      tools.forEach((tool: any) => {
        console.log(
          `  - ${tool.name}: ${tool.description || "No description"}`
        );
      });

      // Convert and store tools
      const mcpTools: McpTool[] = tools.map((tool: any) => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
        serverName: serverName,
      }));

      this.tools.set(serverName, mcpTools);

      // Register tools with ToolHandler
      mcpTools.forEach((tool) => {
        const isAutoApproved = config.autoApprove?.includes(tool.name) || false;

        this.toolHandler.registerMcpTool(tool.name, {
          handler: async (toolUseContent: any) => {
            return await this.callTool(serverName, tool.name, toolUseContent);
          },
          serverName: serverName,
          description: tool.description || `Tool from ${serverName}`,
          isAutoApproved: isAutoApproved,
          inputSchema: tool.inputSchema,
          toolName: tool.name,
        });
      });

      return mcpTools;
    } catch (error) {
      console.error(`Error connecting to MCP server ${serverName}:`, error);

      // Clean up on error
      this.cleanup(serverName);
      throw error;
    }
  }

  /**
   * Call tool on specified server
   */
  async callTool(
    serverName: string,
    toolName: string,
    arguments_: any
  ): Promise<any> {
    const client = this.clients.get(serverName);
    if (!client) {
      throw new Error(`No client found for server: ${serverName}`);
    }

    try {
      console.log(
        `Calling tool ${toolName} on server ${serverName} with arguments:`,
        arguments_
      );

      const response = await client.callTool({
        name: toolName,
        arguments: arguments_,
      });

      console.log(`Tool ${toolName} response:`, response);
      return response;
    } catch (error) {
      console.error(
        `Error calling tool ${toolName} on server ${serverName}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Disconnect from specified server
   */
  async disconnectFromServer(serverName: string): Promise<void> {
    try {
      console.log(`Disconnecting from MCP server: ${serverName}`);

      // Remove tools from ToolHandler
      const tools = this.tools.get(serverName) || [];
      tools.forEach((tool) => {
        this.toolHandler.unregisterMcpTool(tool.name);
      });

      // Close client connection
      const client = this.clients.get(serverName);
      if (client) {
        await client.close();
      }

      // Clean up
      this.cleanup(serverName);

      console.log(`Successfully disconnected from MCP server: ${serverName}`);
    } catch (error) {
      console.error(
        `Error disconnecting from MCP server ${serverName}:`,
        error
      );
    }
  }

  /**
   * Disconnect from all servers
   */
  async disconnectFromAllServers(): Promise<void> {
    const serverNames = Array.from(this.clients.keys());
    console.log(`Disconnecting from ${serverNames.length} MCP servers`);

    await Promise.all(
      serverNames.map(async (serverName) => {
        try {
          await this.disconnectFromServer(serverName);
        } catch (error) {
          console.error(
            `Error disconnecting from server ${serverName}:`,
            error
          );
        }
      })
    );
  }

  /**
   * Clean up server resources
   */
  private cleanup(serverName: string): void {
    this.clients.delete(serverName);
    this.transports.delete(serverName);
    this.tools.delete(serverName);
  }

  /**
   * Get all available tools
   */
  getAllTools(): McpTool[] {
    const allTools: McpTool[] = [];
    for (const tools of this.tools.values()) {
      allTools.push(...tools);
    }
    return allTools;
  }

  /**
   * Get tools for specific server
   */
  getToolsForServer(serverName: string): McpTool[] {
    return this.tools.get(serverName) || [];
  }

  /**
   * Get connected server names
   */
  getConnectedServers(): string[] {
    return Array.from(this.clients.keys());
  }

  /**
   * Check if server is connected
   */
  isServerConnected(serverName: string): boolean {
    return this.clients.has(serverName);
  }

  /**
   * Reload configuration and reconnect
   */
  async reloadConfiguration(): Promise<void> {
    console.log("Reloading MCP configuration and reconnecting...");

    // Disconnect from all current servers
    await this.disconnectFromAllServers();

    // Reload configuration
    this.config = McpConfigLoader.loadConfig();

    // Reconnect to servers
    await this.initializeServers();
  }

  /**
   * Get server status
   */
  getServerStatus(): Record<string, { connected: boolean; toolCount: number }> {
    const status: Record<string, { connected: boolean; toolCount: number }> =
      {};

    for (const [serverName, tools] of this.tools) {
      status[serverName] = {
        connected: this.isServerConnected(serverName),
        toolCount: tools.length,
      };
    }

    return status;
  }
}
