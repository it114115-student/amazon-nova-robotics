# Secure MCP Client with AWS SigV4 Authentication

This implementation provides a secure MCP (Model Context Protocol) client that uses AWS Signature Version 4 (SigV4) authentication to connect to Lambda Function URLs protected with AWS IAM authorization.

## Overview

Based on the approach described in [Securing Lambda Function URLs](https://pgrzesik.com/posts/securing-lambda-furls/), this implementation:

1. Uses `requests-auth-aws-sigv4` library for AWS SigV4 authentication
2. Integrates with FastMCP Client for MCP protocol communication
3. Supports both secure (AWS IAM) and standard authentication modes
4. Provides testing and setup utilities

## Prerequisites

1. **AWS Lambda Function URL** configured with IAM authorization:
   ```yaml
   functions:
     your-function:
       handler: handler.your_handler
       url:
         authorizer: aws_iam
   ```

2. **AWS Credentials** with `lambda:InvokeFunctionUrl` permission

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### 1. Install Dependencies

The required dependency `requests-auth-aws-sigv4` has been added to `requirements.txt`.

### 2. Configure Environment Variables

```bash
# Enable AWS authentication
export MCP_USE_AWS_AUTH=true

# Your Lambda Function URL
export McpServerUrl=https://your-lambda-url.lambda-url.region.on.aws/

# AWS Configuration
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 3. Run Setup Script

```bash
python setup_secure_mcp.py
```

### 4. Test Configuration

```bash
python test_secure_mcp.py
```

## Usage

### Basic Usage

```python
import os
from mcp_client import get_mcp_client, cleanup_mcp_client

# Enable AWS authentication
os.environ['MCP_USE_AWS_AUTH'] = 'true'

try:
    # Get secure MCP client
    client = get_mcp_client()
    
    # Use the client
    tools = await client.list_tools()
    result = await client.call_tool("tool_name", {"param": "value"})
    
finally:
    cleanup_mcp_client()
```

### Environment-Based Configuration

The client automatically detects the authentication mode based on the `MCP_USE_AWS_AUTH` environment variable:

- `MCP_USE_AWS_AUTH=true`: Uses AWS SigV4 authentication
- `MCP_USE_AWS_AUTH=false` or unset: Uses standard authentication

## Security Features

### AWS SigV4 Authentication

- Automatically signs requests with AWS credentials
- Uses the `lambda` service for signature calculation
- Supports all AWS credential resolution methods (environment variables, IAM roles, profiles, etc.)

### Credential Resolution

The client uses the same credential resolution chain as boto3:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM roles (when running on EC2/Lambda/ECS)
4. AWS SSO

### Required Permissions

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

## Testing

### Test Scripts

1. **setup_secure_mcp.py**: Configure environment and check AWS setup
2. **test_secure_mcp.py**: Test credentials, connection, and client initialization
3. **example_secure_usage.py**: Example usage patterns

### Manual Testing

Test your Lambda Function URL directly:

```bash
# Without authentication (should fail)
curl https://your-lambda-url.lambda-url.region.on.aws/

# With AWS CLI (should work if credentials are correct)
aws lambda invoke-url \
  --function-url https://your-lambda-url.lambda-url.region.on.aws/ \
  --request-payload '{}' \
  response.json
```

## Troubleshooting

### Common Issues

1. **"Forbidden" Error**:
   - Check that `MCP_USE_AWS_AUTH=true` is set
   - Verify AWS credentials are configured
   - Ensure credentials have `lambda:InvokeFunctionUrl` permission

2. **"No AWS credentials found"**:
   - Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - Or configure AWS credentials file
   - Or use IAM roles if running on AWS

3. **"Connection failed"**:
   - Verify the Lambda Function URL is correct
   - Check that the Lambda function is deployed
   - Ensure the function URL has IAM authorization enabled

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │───▶│  SecureMCP       │───▶│  Lambda Function│
│   (FastMCP)     │    │  Transport       │    │  URL (IAM Auth) │
│                 │    │  (AWS SigV4)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

The `SecureMCPTransport` class handles:
- AWS SigV4 request signing
- HTTP request/response handling
- Error handling and retries

## Integration with Existing Code

The secure client is a drop-in replacement for the standard MCP client. Existing code will continue to work, with security enabled via environment variables.

## References

- [AWS Lambda Function URLs Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html)
- [AWS Signature Version 4 Documentation](https://docs.aws.amazon.com/general/latest/gr/signing-aws-api-requests.html)
- [Securing Lambda Function URLs Blog Post](https://pgrzesik.com/posts/securing-lambda-furls/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)