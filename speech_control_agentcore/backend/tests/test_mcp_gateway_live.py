#!/usr/bin/env python3
"""Optional live smoke tests for a deployed AgentCore Gateway MCP endpoint."""

import json
import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))


RUN_LIVE_MCP_GATEWAY_TEST = os.getenv("RUN_LIVE_MCP_GATEWAY_TEST") == "true"


@unittest.skipUnless(
    RUN_LIVE_MCP_GATEWAY_TEST,
    "Set RUN_LIVE_MCP_GATEWAY_TEST=true to run live AgentCore Gateway smoke tests.",
)
class TestLiveMcpGateway(unittest.TestCase):
    def test_gateway_lists_tools(self):
        from tools import cleanup_tools
        from tools.robot_actions import get_dynamic_tools

        try:
            tools = get_dynamic_tools()
            self.assertGreater(len(tools), 0, "Expected at least one MCP tool from the deployed gateway.")
        finally:
            cleanup_tools()

    @unittest.skipUnless(
        os.getenv("MCP_SMOKE_TOOL_NAME"),
        "Set MCP_SMOKE_TOOL_NAME to run a real MCP tool smoke call.",
    )
    def test_gateway_calls_a_real_tool(self):
        from tools import cleanup_tools
        from tools.mcp_client import get_mcp_client

        tool_name = os.environ["MCP_SMOKE_TOOL_NAME"]
        tool_args = json.loads(os.getenv("MCP_SMOKE_TOOL_ARGS", "{}"))

        try:
            client = get_mcp_client()
            result = client.call_tool_sync(
                tool_use_id="smoke-test",
                name=tool_name,
                arguments=tool_args,
            )

            self.assertIsNotNone(result)
            if hasattr(result, "status"):
                self.assertNotEqual(str(result.status).lower(), "error")
        finally:
            cleanup_tools()


if __name__ == "__main__":
    unittest.main()
