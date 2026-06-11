"""Digital Human Skill - Control xiaoice Digital Human speech via MCP server"""

import argparse
import json
import logging
import os
import sys

import boto3
import requests
from requests_auth_aws_sigv4 import AWSSigV4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def call_mcp_tool(mcp_url, auth, tool_name, arguments, timeout=30):
    """Call an MCP tool on the Lambda server via JSON-RPC. Returns the text result or None."""
    if "bedrock-agentcore" in mcp_url and not tool_name.startswith("digital-human-mcp-lambda___"):
        tool_name = f"digital-human-mcp-lambda___{tool_name}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        resp = requests.post(
            mcp_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            auth=auth,
            timeout=timeout,
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        logger.error("MCP request failed: %s", e)
        return None

    if "error" in result:
        logger.error("MCP error: %s", result["error"])
        return None

    content = result.get("result", {}).get("content", [])
    return next((c.get("text", "") for c in content if c.get("type") == "text"), "")


def execute_speech(mcp_url, auth, message):
    """Send a speech command to the xiaoice Digital Human via MCP server.

    There is only one xiaoice device. The presenter_id is handled
    automatically by the MCP server (always "current_presenter").

    Returns (success, response_text).
    """
    arguments = {
        "message": message,
    }

    text = call_mcp_tool(mcp_url, auth, "digital_human_speech", arguments)
    if text is not None:
         logger.info("speech -> %s", text)
         return True, text
    return False, "Failed to send speech to xiaoice"


def main():
    parser = argparse.ArgumentParser(
        description="Digital Human Skill - Control xiaoice Digital Human speech via MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --message "Hello, welcome"
  %(prog)s --message "The show is starting"
  %(prog)s --message "歡迎嚟到我哋嘅展覽" --json
""",
    )
    parser.add_argument(
        "--profile", default=None, help="AWS CLI profile name"
    )
    parser.add_argument(
        "--message", required=True, help="Text message for the Digital Human to speak"
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region"
    )
    parser.add_argument(
        "--mcp-url",
        default=os.environ.get("MCP_SERVER_URL", ""),
        help="MCP server Lambda function URL (or set MCP_SERVER_URL env var)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON (useful for agent consumption)",
    )
    args = parser.parse_args()

    if not args.mcp_url:
        logger.error("--mcp-url or MCP_SERVER_URL env var is required")
        sys.exit(1)

    if not args.message.strip():
        logger.error("--message cannot be empty")
        sys.exit(1)

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    service = "bedrock-agentcore" if "bedrock-agentcore" in args.mcp_url else "lambda"
    auth = AWSSigV4(service, session=session)

    success, response_text = execute_speech(
        mcp_url=args.mcp_url,
        auth=auth,
        message=args.message,
    )

    if args.json_output:
        print(
            json.dumps(
                {
                    "success": success,
                    "message": args.message,
                    "response": response_text,
                },
                indent=2,
            )
        )
    else:
        if success:
            print(response_text)
        else:
            print(f"Error: {response_text}", file=sys.stderr)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
