"""Digital Human Skill - Control xiaoice Digital Human speech via MCP server and direct ADB"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time

import boto3
import requests
import yaml
from requests_auth_aws_sigv4 import AWSSigV4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_settings(settings_path: str) -> dict:
    try:
        with open(settings_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error("Failed to load settings: %s", e)
        return {}


class AdbExecutor:
    """Executes speech actions on the xiaoice Digital Human device via adb."""

    def __init__(self, settings: dict):
        self.settings = settings
        self.adb_ip = self.settings.get("adb_ip")
        self.adb_path = self.settings.get("adb_path", "adb")
        self.wait_duration = self.settings.get("wait_duration", 2)

    def _resolve_adb_executable(self) -> str:
        """Return a usable adb executable path."""
        return self.adb_path if os.path.exists(self.adb_path) else "adb"

    def _is_device_connected(self) -> bool:
        """Check whether the configured adb target appears in adb devices output."""
        if not self.adb_ip:
            return False

        cmd = [self._resolve_adb_executable(), "devices"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return False

            for line in result.stdout.splitlines():
                if line.startswith(f"{self.adb_ip}\t") and line.rstrip().endswith("device"):
                    return True
            return False
        except Exception:
            return False

    def _ensure_adb_connection(self) -> bool:
        """Ensure adb is connected to the configured target."""
        if not self.adb_ip:
            return False

        if self._is_device_connected():
            return True

        logger.info("ADB device %s is not connected, attempting reconnect...", self.adb_ip)
        cmd = [self._resolve_adb_executable(), "connect", self.adb_ip]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return self._is_device_connected()
        except Exception:
            return False

    def _run_adb_command(self, args: list, description: str) -> bool:
        """Run an adb command and return True on success."""
        cmd = [self._resolve_adb_executable()] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info("%s succeeded", description)
                return True
            else:
                logger.error("%s failed: %s", description, result.stderr.strip())
                return False
        except Exception as e:
            logger.error("%s error: %s", description, e)
            return False

    def open_chat(self) -> bool:
        """Open the chat UI by tapping at (1900, 775)."""
        return self._run_adb_command(
            ["shell", "input", "swipe", "1900", "775", "1900", "775", "100"],
            "Open chat",
        )

    def close_chat(self) -> bool:
        """Close the chat UI by tapping at (1650, 2275)."""
        return self._run_adb_command(
            ["shell", "input", "swipe", "1650", "2275", "1650", "2275", "100"],
            "Close chat",
        )

    def execute_flow(self):
        """Execute the full UI flow: Open -> Close -> Wait -> Open."""
        if not self._ensure_adb_connection():
            logger.error("ADB connection unavailable, skipping direct control")
            return

        self.open_chat()
        self.close_chat()
        logger.info("Waiting %s seconds...", self.wait_duration)
        time.sleep(self.wait_duration)
        self.open_chat()


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


def execute_speech(mcp_url, auth, message, adb_executor=None):
    """Send a speech command to the xiaoice Digital Human via MCP server and direct ADB.

    Returns (success, response_text).
    """
    # 1. Direct ADB control
    if adb_executor:
        logger.info("Executing direct ADB control flow...")
        adb_executor.execute_flow()

    # 2. Call MCP tool (sends to IoT and DynamoDB)
    arguments = {
        "message": message,
    }

    text = call_mcp_tool(mcp_url, auth, "xiaoice_speech", arguments)
    if text is not None:
        logger.info("speech -> %s", text)
        return True, text
    return False, "Failed to send speech to xiaoice"


def main():
    parser = argparse.ArgumentParser(
        description="Digital Human Skill - Control xiaoice Digital Human via MCP and direct ADB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --message "Hello, welcome"
  %(prog)s --message "The show is starting"
  %(prog)s --message "歡迎嚟到我哋嘅展覽" --json
""",
    )
    parser.add_argument(
        "--profile", default="skill-profile", help="AWS CLI profile name"
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
    parser.add_argument(
        "--settings",
        default=os.path.join(os.path.dirname(__file__), "..", "settings.yaml"),
        help="Path to settings.yaml",
    )
    args = parser.parse_args()

    if not args.mcp_url:
        logger.error("--mcp-url or MCP_SERVER_URL env var is required")
        sys.exit(1)

    if not args.message.strip():
        logger.error("--message cannot be empty")
        sys.exit(1)

    # Load ADB settings
    settings = load_settings(args.settings)
    adb_executor = AdbExecutor(settings) if settings else None

    service = "bedrock-agentcore" if "bedrock-agentcore" in args.mcp_url else "lambda"
    auth = AWSSigV4(service, session=session)

    success, response_text = execute_speech(
        mcp_url=args.mcp_url,
        auth=auth,
        message=args.message,
        adb_executor=adb_executor,
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
