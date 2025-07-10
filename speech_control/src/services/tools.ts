import axios from "axios";
import https from "https";

// Define MCP tool handler function type
export type McpToolHandler = (toolUseContent: any) => Promise<any>;

// MCP tool information
export interface McpToolInfo {
  handler: McpToolHandler;
  serverName: string;
  description: string;
  isAutoApproved: boolean;
  inputSchema?: any; // Add input schema for tool specification
  toolName: string; // Add actual tool name
}

/**
 * Tool handler class
 * Responsible for handling various tool calls and responses
 */
export class ToolHandler {
  // Store MCP tool information
  private mcpTools: Map<string, McpToolInfo> = new Map();

  /**
   * Process tool use
   * @param toolName Tool name
   * @param toolUseContent Tool use content
   */
  public async processToolUse(
    robots: string[],
    toolName: string,
    toolUseContent: object
  ): Promise<Object> {
    // Check if it's an MCP tool
    if (this.mcpTools.has(toolName)) {
      console.log(`Processing MCP tool call: ${toolName}`);
      const toolInfo = this.mcpTools.get(toolName);
      if (toolInfo) {
        try {
          let content = (toolUseContent as { content: any }).content;
          if (typeof content === "string") {
            try {
              content = JSON.parse(content);
            } catch (e) {
              throw new Error(`Failed to parse content as JSON: ${content}`);
            }
          }
          console.log(content);

          if (robots.length === 1 && robots[0] === "all") {
            // Call as usual
            // No changes needed to content
            return await toolInfo.handler(content);
          } else if (robots.length > 0) {
            // For each robot, override robot_id in content and call handler
            const results = await Promise.all(
              robots.map(async (robotId) => {
                const contentCopy =
                  "robot_id" in content
                    ? { ...content, robot_id: robotId }
                    : { ...content }; // the drone case.
                try {
                  return await toolInfo.handler(contentCopy);
                } catch (err) {
                  return {
                    success: false,
                    error: String(err),
                    robot_id: robotId,
                  };
                }
              })
            );
            return results.map((r) => JSON.stringify(r)).join("\n");
          }

          return await toolInfo.handler(content);
        } catch (error) {
          console.error(`MCP tool ${toolName} call failed:`, String(error));
          throw new Error(
            `MCP tool ${toolName} call failed: ${
              error instanceof Error ? error.message : String(error)
            }`
          );
        }
      }
    }

    return {
      success: false,
      error: `Unknown tool: ${toolName}`,
    };
  }

  /**
   * Register MCP tool
   * @param toolName Tool name
   * @param toolInfo Tool information
   */
  public registerMcpTool(toolName: string, toolInfo: McpToolInfo): void {
    console.log(
      `Registering MCP tool: ${toolName} from server: ${toolInfo.serverName}`
    );
    this.mcpTools.set(toolName, toolInfo);
  }

  /**
   * Unregister MCP tool
   * @param toolName Tool name
   */
  public unregisterMcpTool(toolName: string): void {
    console.log(`Unregistering MCP tool: ${toolName}`);
    this.mcpTools.delete(toolName);
  }

  /**
   * Get all registered MCP tools
   */
  public getMcpTools(): Map<string, McpToolInfo> {
    return new Map(this.mcpTools);
  }

  /**
   * Check if tool is auto-approved
   * @param toolName Tool name
   */
  public isToolAutoApproved(toolName: string): boolean {
    const toolInfo = this.mcpTools.get(toolName);
    return toolInfo?.isAutoApproved ?? false;
  }

  /**
   * Clear all MCP tools
   */
  public clearMcpTools(): void {
    console.log("Clearing all MCP tools");
    this.mcpTools.clear();
  }

  /**
   * Get tool count
   */
  public getToolCount(): number {
    return this.mcpTools.size;
  }

  /**
   * Get tools by server name
   */
  public getToolsByServer(serverName: string): Map<string, McpToolInfo> {
    const serverTools = new Map<string, McpToolInfo>();
    for (const [toolName, toolInfo] of this.mcpTools) {
      if (toolInfo.serverName === serverName) {
        serverTools.set(toolName, toolInfo);
      }
    }
    return serverTools;
  }
}
