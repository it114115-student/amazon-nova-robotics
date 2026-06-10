# CDK Infrastructure

This CDK app provisions the AWS infrastructure for the Amazon Nova Robotics project, including the **speech AgentCore runtime**, the **robot-only AgentCore MCP gateway**, the legacy/shared MCP surfaces, static websites, Cognito, and supporting data stores.

## Useful commands

- `npm run build` — compile TypeScript
- `npm run test` — run unit tests
- `npx cdk synth` — synthesize CloudFormation
- `npx cdk diff` — compare local changes with the deployed stack
- `npx cdk deploy` — deploy the stack

## Current speech + MCP deployment shape

The voice cockpit no longer points at the shared mixed MCP surface.

It now deploys and uses a **separate robot-only AgentCore gateway path**:

- `cdk/lib/construct/robot-tool-gateway.ts`
  - creates a dedicated Lambda target for robot-only tools
  - publishes a robot-only tool schema asset
  - sets the AgentCore gateway target name to `robot-only-mcp-lambda`
- `cdk/lib/construct/speech-web-agentcore.ts`
  - points the speech runtime at that robot-only gateway
  - grants the speech runtime permission to invoke that gateway
  - injects the exact gateway-visible tool names into runtime environment variables

## Important AgentCore tool naming rule

For AgentCore Lambda targets, the MCP-visible tool name is:

`{gatewayTargetName}___{toolName}`

In this stack that means tools are exposed as names such as:

- `robot-only-mcp-lambda___robot_wave`
- `robot-only-mcp-lambda___robot_stop`

Important implications:

1. The speech runtime/model must use the **exact prefixed names** from the gateway.
2. The Lambda target must strip the `robot-only-mcp-lambda___` prefix before dispatching to the internal robot action map.
3. If the Lambda cannot read the AgentCore-provided tool name from the invocation context, the gateway call fails before any robot action is executed.

## Important implementation findings

- The clean solution is **not** to rename tools for the model. The current code keeps the exact AgentCore gateway names end-to-end on the speech side.
- The robot Lambda now relies on the documented AgentCore context contract for tool-name resolution instead of broad fallback parsing.
- For tool-call debugging, the most useful log stream is often the **BedrockAgentCoreGateway application log**, not only the speech runtime log stream.
- `cdk.out/` can grow very large after repeated synth/deploy cycles and is safe to remove when cleaning local workspace disk usage.

## OpenClaw MCP callers

The MCP Lambda URL is granted to the current AWS account by default. That makes both OpenClaw `dev` and `prod` execution roles work in the same account, while the actual caller is still constrained by the identity-based policy attached on the OpenClaw side.

You can override the allowed caller accounts with CDK context:

- `openclawCallerAccountIds`: comma-separated string or array of AWS account IDs that should be allowed to invoke the MCP Lambda URL
