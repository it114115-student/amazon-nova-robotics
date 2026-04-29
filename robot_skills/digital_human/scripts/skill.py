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

VALID_XIAOICE_IDS = ["all", "xiaoice_1"]


def call_mcp_tool(mcp_url, auth, tool_name, arguments, timeout=30):
    """Call an MCP tool on the Lambda server via JSON-RPC. Returns the text result or None."""
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


def execute_speech(mcp_url, auth, xiaoice_id, message, presenter_id=None):
    """Send a speech command to the xiaoice Digital Human via MCP server.

    Returns (success, response_text).
    """
    arguments = {
        "xiaoice_id": xiaoice_id,
        "message": message,
    }
    if presenter_id:
        arguments["presenter_id"] = presenter_id

    text = call_mcp_tool(mcp_url, auth, "xiaoice_speech", arguments)
    if text is not None:
        logger.info("[%s] speech -> %s", xiaoice_id, text)
        return True, text
    return False, f"Failed to send speech to {xiaoice_id}"


def main():
    parser = argparse.ArgumentParser(
        description="Digital Human Skill - Control xiaoice Digital Human speech via MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --xiaoice-id xiaoice_1 --message "Hello, welcome"
  %(prog)s --xiaoice-id xiaoice_1 --message "Welcome" --presenter-id Summer
  %(prog)s --xiaoice-id all --message "The show is starting"
""",
    )
    parser.add_argument(
        "--profile", default="skill-profile", help="AWS CLI profile name"
    )
    parser.add_argument(
        "--xiaoice-id",
        required=True,
        choices=VALID_XIAOICE_IDS,
        help="Xiaoice device ID (e.g. xiaoice_1 or all)",
    )
    parser.add_argument(
        "--message", required=True, help="Text message for the Digital Human to speak"
    )
    parser.add_argument(
        "--presenter-id",
        default=None,
        help="Optional presenter ID for context lookup",
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
    auth = AWSSigV4("lambda", session=session)

    success, response_text = execute_speech(
        mcp_url=args.mcp_url,
        auth=auth,
        xiaoice_id=args.xiaoice_id,
        message=args.message,
        presenter_id=args.presenter_id,
    )

    if args.json_output:
        print(
            json.dumps(
                {
                    "success": success,
                    "xiaoice_id": args.xiaoice_id,
                    "message": args.message,
                    "presenter_id": args.presenter_id,
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
