/**
 * Drop-in replacement for MCP Manager with AWS authentication support
 * This extends the original MCP manager to support AWS SigV4 authentication
 */

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
import { AwsAuthTransport } from "./aws-auth-transport";

export class McpManager {
    private clients: Map<string, Client> = new Map();
    private transports: Map<
        string,
        StdioClientTransport | StreamableHTTPClientTransport | AwsAuthTransport
    > = new Map();
    private tools: Map<string, McpTool[]> = new Map();
    private toolHandler: ToolHandler;
    private config: McpConfig;
    private awsTransports: Map<string, AwsAuthTransport> = new Map();

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
     * Connect to specified MCP server with optional AWS authentication
     */
    async connectToServer(
        serverName: string,
        config: McpServerConfig
    ): Promise<McpTool[]> {
        console.log(`Connecting to MCP server: ${serverName}`);

        try {
            // Check if AWS authentication should be used
            const useAwsAuth = process.env.MCP_USE_AWS_AUTH?.toLowerCase() === 'true';

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

            // Choose different transport based on command type and auth requirements
            if (config.command === "restful") {
                // Use HTTP-based transport
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

                if (useAwsAuth) {
                    // Use AWS authenticated transport
                    console.log(`🔐 Using AWS SigV4 authentication for ${serverName}`);

                    const awsTransport = new AwsAuthTransport({
                        url: config.baseUrl,
                        region: process.env.AWS_DEFAULT_REGION || 'us-east-1',
                        service: 'lambda',
                        sessionId: randomUUID(),
                    });

                    // Connect the AWS transport
                    await awsTransport.connect();

                    // Store the AWS transport for later use
                    this.awsTransports.set(serverName, awsTransport);

                    // Use standard HTTP transport for MCP client, but we'll intercept calls
                    transport = new StreamableHTTPClientTransport(new URL(config.baseUrl), {
                        sessionId: randomUUID(),
                    });
                } else {
                    // Use standard HTTP transport
                    console.log(`🔓 Using standard HTTP transport for ${serverName}`);
                    const sessionId = randomUUID();
                    transport = new StreamableHTTPClientTransport(new URL(config.baseUrl), {
                        sessionId: sessionId,
                    });
                }
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

            // For AWS authenticated servers, we need to handle this differently
            if (useAwsAuth && config.command === "restful") {
                // Get tools directly from AWS transport instead of MCP client
                const awsTransport = this.awsTransports.get(serverName);
                if (awsTransport) {
                    const toolsResponse = await awsTransport.makeAuthenticatedRequest({
                        jsonrpc: "2.0",
                        id: 1,
                        method: "tools/list",
                        params: {}
                    });

                    const tools = toolsResponse.result?.tools || [];
                    console.log(`Found ${tools.length} tools in server ${serverName} (AWS authenticated):`);

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

                    console.log(`Successfully connected to MCP server: ${serverName} (AWS authenticated)`);
                    return mcpTools;
                }
            } else {
                // Use standard MCP client connection
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
            }

            return [];
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
        // Check if this is an AWS authenticated server
        const awsTransport = this.awsTransports.get(serverName);
        if (awsTransport) {
            // Use AWS authenticated request
            const response = await awsTransport.makeAuthenticatedRequest({
                jsonrpc: "2.0",
                id: 1,
                method: "tools/call",
                params: {
                    name: toolName,
                    arguments: arguments_
                }
            });

            if (response.error) {
                throw new Error(`MCP tool error: ${response.error.message}`);
            }

            return response.result;
        }

        // Use standard MCP client
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

    // All other methods remain the same as the original McpManager
    async disconnectFromServer(serverName: string): Promise<void> {
        try {
            console.log(`Disconnecting from MCP server: ${serverName}`);

            // Remove tools from ToolHandler
            const tools = this.tools.get(serverName) || [];
            tools.forEach((tool) => {
                this.toolHandler.unregisterMcpTool(tool.name);
            });

            // Close AWS transport if exists
            const awsTransport = this.awsTransports.get(serverName);
            if (awsTransport) {
                await awsTransport.close();
                this.awsTransports.delete(serverName);
            }

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

    private cleanup(serverName: string): void {
        this.clients.delete(serverName);
        this.transports.delete(serverName);
        this.tools.delete(serverName);
        this.awsTransports.delete(serverName);
    }

    getAllTools(): McpTool[] {
        const allTools: McpTool[] = [];
        for (const tools of this.tools.values()) {
            allTools.push(...tools);
        }
        return allTools;
    }

    getToolsForServer(serverName: string): McpTool[] {
        return this.tools.get(serverName) || [];
    }

    getConnectedServers(): string[] {
        return Array.from(this.clients.keys());
    }

    isServerConnected(serverName: string): boolean {
        return this.clients.has(serverName) || this.awsTransports.has(serverName);
    }

    async reloadConfiguration(): Promise<void> {
        console.log("Reloading MCP configuration and reconnecting...");

        // Disconnect from all current servers
        await this.disconnectFromAllServers();

        // Reload configuration
        this.config = McpConfigLoader.loadConfig();

        // Reconnect to servers
        await this.initializeServers();
    }

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