# AWS Secure MCP Implementation

This implementation provides AWS IAM authentication for MCP (Model Context Protocol) servers, specifically designed for Lambda Function URLs protected with AWS IAM authorization.

## Overview

Based on the approach from [Securing Lambda Function URLs](https://pgrzesik.com/posts/securing-lambda-furls/), this implementation adds AWS SigV4 authentication to the existing MCP manager, allowing secure communication with IAM-protected Lambda Function URLs.

### Key Features

- ✅ **Drop-in replacement** for existing MCP manager
- ✅ **AWS SigV4 authentication** for Lambda Function URLs
- ✅ **Automatic credential resolution** using AWS SDK credential chain
- ✅ **Backward compatibility** with non-authenticated servers
- ✅ **Environment-based configuration** for easy setup

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │───▶│  AwsAuthTransport│───▶│  Lambda Function│
│   (@mcp/sdk)    │    │  (AWS SigV4)     │    │  URL (IAM Auth) │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Files Structure

```
speech_control/
├── src/
│   ├── services/
│   │   ├── aws-auth-transport.ts      # AWS SigV4 authentication transport
│   │   └── mcp-manager-secure.ts      # Enhanced MCP manager with AWS auth
│   └── test-aws-connection.ts         # AWS connection test utility
├── package.json                       # Updated dependencies
└── AWS_SECURE_MCP.md                 # This documentation
```

## Quick Setup

### 1. Environment Variables

```bash
# Enable AWS authentication
export MCP_USE_AWS_AUTH=true

# MCP Server URL (your Lambda Function URL)
export McpServerUrl=https://your-lambda-url.lambda-url.region.on.aws/

# AWS Configuration
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 2. Update Server Code

The implementation is already integrated. The server uses:

```typescript
// In src/server.ts
import { McpManager } from "./services/mcp-manager-secure";

// Enable AWS authentication
process.env.MCP_USE_AWS_AUTH = 'true';

// Initialize as usual - authentication is handled automatically
const mcpManager = new McpManager(toolHandler);
await mcpManager.initializeServers();
```

### 3. Test the Setup

```bash
# Load environment variables
source ../load_cdkstack_env.sh

# Test AWS authentication
npm run test-aws-auth

# Run the server
npm run dev
```

## Dependencies

The following dependencies were added to `package.json`:

```json
{
  "@aws-sdk/client-sts": "^3.840.0",
  "@aws-crypto/sha256-js": "^5.2.0",
  "@smithy/protocol-http": "^4.1.4",
  "@smithy/signature-v4": "^4.2.0"
}
```

## How It Works

### 1. AWS Authentication Transport

The `AwsAuthTransport` class handles AWS SigV4 signing:

```typescript
// Automatically resolves AWS credentials
const credentialProvider = fromNodeProviderChain();
const credentials = await credentialProvider();

// Signs requests with AWS SigV4
const signer = new SignatureV4({
  service: 'lambda',
  region: this.region,
  credentials: credentials,
  sha256: Sha256,
});
```

### 2. Enhanced MCP Manager

The `McpManager` (from `mcp-manager-secure.ts`) automatically:

- Detects when AWS authentication is enabled via `MCP_USE_AWS_AUTH`
- Creates AWS authenticated transport for HTTP-based MCP servers
- Falls back to standard transport for non-authenticated servers
- Handles tool registration and execution with proper authentication

### 3. Automatic Mode Detection

```typescript
// Checks environment variable
const useAwsAuth = process.env.MCP_USE_AWS_AUTH?.toLowerCase() === 'true';

if (useAwsAuth && config.command === "restful") {
  // Use AWS authenticated transport
  console.log(`🔐 Using AWS SigV4 authentication for ${serverName}`);
  const awsTransport = new AwsAuthTransport({...});
} else {
  // Use standard transport
  console.log(`🔓 Using standard HTTP transport for ${serverName}`);
}
```

## Security Requirements

### Lambda Function Configuration

Your Lambda Function URL must be configured with AWS IAM authorization:

```yaml
# In your serverless.yml or CDK
functions:
  your-function:
    handler: handler.your_handler
    url:
      authorizer: aws_iam  # This enables IAM authentication
```

### Required AWS Permissions

Your AWS credentials must have the `lambda:InvokeFunctionUrl` permission:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunctionUrl",
            "Resource": "arn:aws:lambda:region:account:function:your-function"
        }
    ]
}
```

### Credential Resolution

The implementation uses AWS SDK's standard credential resolution chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM roles (when running on EC2/Lambda/ECS)
4. AWS SSO
5. Container credentials

## Testing

### Test AWS Authentication

```bash
npm run test-aws-auth
```

Expected output:
```
🔐 Testing AWS authenticated connection to Lambda Function URL
✅ AWS credentials found: Access Key ID: AKIARUEM...
✅ Connection test successful, found 52 tools
🎉 AWS authentication test PASSED!
```

### Test Full Server

```bash
# Load environment
source ../load_cdkstack_env.sh

# Start server
npm run dev
```

Expected output:
```
🔐 Using AWS SigV4 authentication for robot-mcpServers
✅ Connection test successful, found 52 tools
✅ Successfully connected to AWS authenticated MCP server
Found 52 tools in server robot-mcpServers (AWS authenticated)
```

## Troubleshooting

### Common Issues

1. **"McpServerUrl environment variable is not set"**
   - Run `source ../load_cdkstack_env.sh` before starting the server
   - Verify the CDK stack has been deployed

2. **"No AWS credentials found"**
   - Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - Or configure `~/.aws/credentials`
   - Or use IAM roles if running on AWS

3. **"HTTP 403: Forbidden"**
   - Verify Lambda Function URL has `authorizer: aws_iam`
   - Check that credentials have `lambda:InvokeFunctionUrl` permission
   - Ensure the function URL is correct

4. **"Connection test failed"**
   - Verify the Lambda function is deployed and running
   - Check AWS region configuration
   - Test with AWS CLI: `aws lambda invoke-url --function-url <url>`

### Debug Mode

Enable detailed logging by setting:

```bash
export DEBUG=mcp:*
```

### Manual Testing

Test your Lambda Function URL directly:

```bash
# Without auth (should fail with 403)
curl https://your-lambda-url.lambda-url.region.on.aws/

# With AWS CLI (should work)
aws lambda invoke-url \
  --function-url https://your-lambda-url.lambda-url.region.on.aws/ \
  --request-payload '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  response.json
```

## Implementation Details

### Tool Execution Flow

1. **Standard Mode** (`MCP_USE_AWS_AUTH=false`):
   ```
   Client → MCP SDK → HTTP Transport → Lambda URL (fails with 403)
   ```

2. **Secure Mode** (`MCP_USE_AWS_AUTH=true`):
   ```
   Client → AWS Auth Transport → SigV4 Signing → Lambda URL (succeeds)
   ```

### Performance Considerations

- **Connection Pooling**: Reuses HTTP connections where possible
- **Credential Caching**: AWS credentials are cached by the SDK
- **Signature Computation**: SigV4 signatures are computed per request (as required by AWS)
- **Async Operations**: Fully asynchronous implementation

## Migration from Standard MCP

If you have an existing MCP setup, migration is simple:

1. **No code changes needed** - the secure manager is already integrated
2. **Set environment variable**: `MCP_USE_AWS_AUTH=true`
3. **Configure AWS credentials** as described above
4. **Update Lambda Function URL** to use IAM authorization

The implementation maintains full backward compatibility with non-authenticated servers.

## Success Indicators

When working correctly, you should see:

```bash
# Server startup
🔐 Using AWS SigV4 authentication for robot-mcpServers
✅ Connection test successful, found 52 tools
✅ Successfully connected to AWS authenticated MCP server

# Tool execution
Tool use detected: robotWave
Processing MCP tool call: robotWave
Successfully processed MCP tool: robotWave
```

## References

- [AWS Lambda Function URLs Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html)
- [AWS Signature Version 4 Documentation](https://docs.aws.amazon.com/general/latest/gr/signing-aws-api-requests.html)
- [Securing Lambda Function URLs Blog Post](https://pgrzesik.com/posts/securing-lambda-furls/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/typescript-sdk)

---

## Summary

This implementation successfully adds AWS IAM authentication to your MCP setup while maintaining full compatibility with existing functionality. The Lambda Function URL is now properly secured, and your TypeScript application can authenticate and access it using AWS SigV4 signatures.

**Status: ✅ Fully Implemented and Tested**