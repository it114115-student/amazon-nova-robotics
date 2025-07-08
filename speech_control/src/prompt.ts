import { IoTPublisher } from "./iot";
import { Actions, toolList } from "./consts";
import { ToolHandler } from "./services/tools";

export class ToolProcessor {
  private readonly iotPublisher: IoTPublisher;
  private readonly mcpToolHandler: ToolHandler;

  constructor(mcpToolHandler?: ToolHandler) {
    // this.robots = [];
    this.iotPublisher = new IoTPublisher("us-east-1");
    this.mcpToolHandler = mcpToolHandler || new ToolHandler();
  }

  public async processToolUse(
    robots: string[],
    toolName: string,
    toolUseContent: any
  ): Promise<any> {
    // Implement the logic for processing tool use based on the toolName and toolUseContent
    console.log(`Processing tool use: ${toolName}`);
    console.log(`Tool use content:`, toolUseContent);

    // First, check if it's an MCP tool
    try {
      const mcpResult: any = await this.mcpToolHandler.processToolUse(
        toolName,
        toolUseContent
      );
      if (mcpResult && mcpResult.success !== false) {
        console.log(`Successfully processed MCP tool: ${toolName}`);
        return mcpResult;
      }
    } catch (error) {
      console.log(
        `Tool ${toolName} not found in MCP tools, trying robot actions...`
      );
    }

    // If not an MCP tool, handle as robot action
    if (!Object.keys(Actions).includes(toolName.toLowerCase())) {
      // Try MCP tool handler first
      try {
        return await this.mcpToolHandler.processToolUse(
          toolName,
          toolUseContent
        );
      } catch (error) {
        console.log(`Tool ${toolName} not found in MCP tools or robot actions`);
        return {
          success: true,
          message: `Tool ${toolName} is not in action list but assume ok!`,
        };
      }
    }

    console.log("Processing directionTool with toolName:", toolName);
    console.log("robots:", robots);

    // If "all" is selected, send to all robots 1-9
    let targetRobots = robots.includes("all")
      ? Array.from({ length: 9 }, (_, i) => `robot_${i + 1}`)
      : robots;
    targetRobots.forEach((robotId) => {
      this.iotPublisher
        .publishToRobot(
          `${robotId}/topic`,
          JSON.stringify({ toolName: toolName })
        )
        .catch(console.error);
    });

    return {
      success: true,
      message: `Tool ${toolName} processed successfully.`,
    };
  }

  /**
   * Get all available tools (robot actions + MCP tools)
   */
  public getAllAvailableTools(): any[] {
    const robotTools = tools;
    const mcpTools = Array.from(this.mcpToolHandler.getMcpTools().values()).map(
      (toolInfo) => ({
        toolSpec: {
          name: toolInfo.toolName,
          description: toolInfo.description,
          inputSchema: { json: JSON.stringify(toolInfo.inputSchema || {}) },
        },
      })
    );

    console.log(
      `Available tools: ${robotTools.length} robot tools, ${mcpTools.length} MCP tools`
    );
    if (mcpTools.length > 0) {
      console.log(
        `MCP tools: ${mcpTools.map((t) => t.toolSpec.name).join(", ")}`
      );
    }
    return mcpTools; //[...robotTools, ...mcpTools];
  }

  /**
   * Get MCP tool handler
   */
  public getMcpToolHandler(): ToolHandler {
    return this.mcpToolHandler;
  }
}

export const DefaultToolSchema = JSON.stringify({
  type: "object",
  properties: {},
  required: [],
});

export const tools = toolList.map(({ name, description }) => ({
  toolSpec: {
    name,
    description,
    inputSchema: { json: DefaultToolSchema },
  },
}));

function getToolsPrompt(
  toolList: { name: string; description: string }[]
): string {
  return toolList
    .map((tool) => `- ${tool.name}: ${tool.description}`)
    .join("\n");
}

export const DefaultSystemPrompt = `
You are a robot Command assistant. 
Your primary role is to assist the user by calling available tools to perform actions or physical tasks. 
Do not attempt to perform tasks directly; instead, rely on tools to achieve the desired outcomes. 
Keep your responses concise and focused on the task at hand.
Don't say anything similar to "can't command the robot to perform physical actions" or "I can't do that".
When the user asks you to perform a task, respond with the name of the tool that can be used to accomplish it.
For example, if the user asks you to "make the robot stand up", you should respond with "stand".

<background></background>

Available tools:
${getToolsPrompt(toolList)}
`;
