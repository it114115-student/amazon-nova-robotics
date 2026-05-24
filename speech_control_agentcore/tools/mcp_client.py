import os
import json
import logging
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

logger = logging.getLogger(__name__)

# Load MCP Server URL from environment
MCP_SERVER_URL = os.environ.get("McpServerUrl")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Send a signed JSON-RPC tools/call request to the Lambda MCP Server Function URL.

    Args:
        tool_name: The name of the MCP tool to call.
        arguments: The arguments dictionary to pass to the tool.

    Returns:
        The response dictionary from the MCP server.
    """
    if not MCP_SERVER_URL:
        logger.error("McpServerUrl environment variable is not configured.")
        return {"success": False, "error": "McpServerUrl is not configured."}

    # Format standard MCP JSON-RPC payload
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }
    
    payload_str = json.dumps(payload)
    logger.info(f"Calling MCP Tool: {tool_name} with arguments: {arguments}")

    try:
        # Create AWS credentials session
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        
        # Prepare AWSRequest for signing
        request = AWSRequest(
            method="POST",
            url=MCP_SERVER_URL,
            data=payload_str,
            headers={"Content-Type": "application/json"}
        )
        
        # Sign with Lambda service auth and region
        SigV4Auth(credentials, "lambda", AWS_REGION).add_auth(request)
        
        # Dispatch the HTTP POST request with signed headers
        response = requests.post(
            url=request.url,
            headers=dict(request.headers),
            data=request.data,
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"MCP server returned HTTP {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": f"MCP server error (HTTP {response.status_code})",
                "details": response.text
            }
            
        response_json = response.json()
        logger.info(f"MCP Tool {tool_name} call succeeded.")
        
        # Parse MCP JSON-RPC success response format
        if "result" in response_json:
            result = response_json["result"]
            # Extract content from MCP format if present
            if isinstance(result, dict) and "content" in result:
                content_list = result["content"]
                if isinstance(content_list, list) and len(content_list) > 0:
                    text_content = content_list[0].get("text", "")
                    try:
                        # Attempt to parse nested JSON string
                        return json.loads(text_content)
                    except Exception:
                        return {"success": True, "result": text_content}
            return result
        elif "error" in response_json:
            return {"success": False, "error": response_json["error"]}
            
        return response_json
        
    except Exception as e:
        logger.exception(f"Exception raised while calling MCP tool {tool_name}")
        return {"success": False, "error": f"Local invocation exception: {str(e)}"}
