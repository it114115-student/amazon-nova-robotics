"""Humanoid Skill - Control humanoid robots via MCP server"""

import argparse
import logging
import os
import re
import sys
import uuid

import boto3
import requests
from requests_auth_aws_sigv4 import AWSSigV4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def call_mcp_tool(mcp_url, auth, tool_name, arguments):
    """Call an MCP tool on the Lambda server via JSON-RPC. Returns the text result or None."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        resp = requests.post(
            mcp_url, json=payload,
            headers={"Content-Type": "application/json"},
            auth=auth, timeout=30,
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


def publish(mcp_url, auth, robot_id, action):
    """Execute a robot action via MCP server."""
    tool_name = f"robot_{action}"
    text = call_mcp_tool(mcp_url, auth, tool_name, {"robot_id": robot_id})
    if text is not None:
        logger.info("MCP response: %s", text)
        return True
    return False


def capture_image(mcp_url, auth, robot_id):
    """Capture an image via MCP get_image tool. Downloads locally and returns the file path."""
    text = call_mcp_tool(mcp_url, auth, "get_image", {"robot_id": robot_id})
    if text is None:
        return None

    if "Cannot read image" in text:
        logger.error("Robot did not upload image: %s", text)
        return None

    url_match = re.search(r"image_url=(\S+)", text)
    if not url_match:
        logger.error("No image_url found in MCP response: %s", text)
        return None

    try:
        img_resp = requests.get(url_match.group(1), timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to download image: %s", e)
        return None

    local_dir = os.path.join(os.getcwd(), "captured_images")
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, f"{robot_id}_{uuid.uuid4().hex[:8]}.jpg")

    with open(local_path, "wb") as f:
        f.write(img_resp.content)

    logger.info("Image saved to %s (%d bytes)", local_path, len(img_resp.content))
    return local_path


def main():
    parser = argparse.ArgumentParser(description="Humanoid Skill")
    parser.add_argument("--profile", default="default", help="AWS CLI profile name")
    parser.add_argument("--robot-id", required=True, help="Robot ID (e.g. robot_1)")
    parser.add_argument("--action", required=True, help="Action to execute (e.g. wave, capture_image)")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--mcp-url", default=os.environ.get("MCP_SERVER_URL", ""),
                        help="MCP server Lambda function URL (or set MCP_SERVER_URL env var)")
    args = parser.parse_args()

    if not args.mcp_url:
        logger.error("--mcp-url or MCP_SERVER_URL env var is required")
        sys.exit(1)

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    auth = AWSSigV4("lambda", session=session)

    if args.action == "capture_image":
        result = capture_image(args.mcp_url, auth, args.robot_id)
        if result:
            print(result)
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        success = publish(args.mcp_url, auth, args.robot_id, args.action)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
