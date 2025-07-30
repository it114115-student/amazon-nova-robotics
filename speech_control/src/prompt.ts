import { ToolHandler } from "./services/tools";

export class ToolProcessor {
  private readonly mcpToolHandler: ToolHandler;

  constructor(mcpToolHandler?: ToolHandler) {
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

    try {
      const mcpResult: any = await this.mcpToolHandler.processToolUse(
        robots,
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
  }

  /**
   * Get all available tools (robot actions + MCP tools)
   */
  public getAllAvailableTools(): any[] {
    const mcpTools = Array.from(this.mcpToolHandler.getMcpTools().values()).map(
      (toolInfo) => ({
        toolSpec: {
          name: toolInfo.toolName,
          description: toolInfo.description,
          inputSchema: { json: JSON.stringify(toolInfo.inputSchema || {}) },
        },
      })
    );

    console.log(`Available tools: ${mcpTools.length} MCP tools`);
    if (mcpTools.length > 0) {
      console.log(
        `MCP tools: ${mcpTools.map((t) => t.toolSpec.name).join(", ")}`
      );
    }
    return mcpTools;
  }

  /**
   * Get MCP tool handler
   */
  public getMcpToolHandler(): ToolHandler {
    return this.mcpToolHandler;
  }
}

export const DefaultSystemPrompt = `
You are a robot Command assistant. 
Your primary role is to assist the user by calling available tools to perform actions or physical tasks. 
Do not attempt to perform tasks directly; instead, rely on tools to achieve the desired outcomes. 
Keep your responses concise and focused on the task at hand.
Don't say anything similar to "can't command the robot to perform physical actions" or "I can't do that".
When the user asks you to perform a task, respond with the name of the tool that can be used to accomplish it.
For example, if the user asks you to "make the robot stand up", you should respond with "stand".

The pronunciation of "drone" can be challenging, and users may sometimes say "drum," "dom,", "drome" or similar variations. 
Please make sure to clarify that the correct term is "drone."

<background></background>

Available tools:

`;
