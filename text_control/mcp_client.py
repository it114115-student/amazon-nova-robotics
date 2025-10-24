"""
MCP Client module - Handles MCP client initialization and management with
AWS SigV4 authentication
"""

import asyncio
import os
from typing import Any, Dict, Optional

import requests
from requests_auth_aws_sigv4 import AWSSigV4

from config import MCP_SERVER_URL

# Global MCP client instance
_mcp_client: Optional["SecureMCPClient"] = None


class SecureMCPClient:
    """MCP Client that supports both AWS SigV4 authentication and standard
    HTTP requests"""

    def __init__(self, mcp_url: str, use_aws_auth: bool = True):
        self.mcp_url = mcp_url
        self.use_aws_auth = use_aws_auth
        self.session = requests.Session()

        if self.use_aws_auth:
            # Set up AWS SigV4 authentication for Lambda function URLs
            self.aws_auth = AWSSigV4("lambda")
            self.session.auth = self.aws_auth

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any] = None
    ) -> Any:
        """Call a tool with optional AWS authentication"""
        return await self._call_tool_http(tool_name, arguments or {})

    async def _call_tool_http(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Make HTTP tool call to MCP server (with or without auth)"""
        try:
            # Prepare MCP request payload
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            # Make request (auth is handled by session if configured)
            response = self.session.post(
                self.mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Handle MCP response format
            if "error" in result:
                raise MCPError(f"MCP error: {result['error']}")

            return result.get("result")

        except requests.exceptions.RequestException as e:
            raise MCPError(f"MCP request failed: {e}") from e

    async def list_tools(self) -> list:
        """List available tools"""
        return await self._list_tools_http()

    async def _list_tools_http(self) -> list:
        """List tools via HTTP (with or without auth)"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            # Make request (auth is handled by session if configured)
            response = self.session.post(
                self.mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise MCPError(f"MCP error: {result['error']}")

            tools_data = result.get("result", {}).get("tools", [])

            # Convert dict format to object-like format for compatibility
            tools = []
            for tool in tools_data:
                if isinstance(tool, dict):
                    # Create a simple object with name and description
                    # attributes
                    tool_obj = type(
                        "Tool",
                        (),
                        {
                            "name": tool.get("name", "unknown"),
                            "description": tool.get(
                                "description", "No description"
                            ),
                        },
                    )()
                    tools.append(tool_obj)
                else:
                    tools.append(tool)

            return tools

        except requests.exceptions.RequestException as e:
            raise MCPError(f"MCP request failed: {e}") from e

    async def close(self):
        """Close the client and clean up resources"""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class MCPError(Exception):
    """Custom exception for MCP-related errors"""


def init_mcp_client() -> SecureMCPClient:
    """Initialize MCP client with optional AWS authentication"""
    global _mcp_client  # pylint: disable=global-statement
    if _mcp_client is None:
        # Check if AWS authentication should be used
        use_aws_auth = os.getenv("MCP_USE_AWS_AUTH", "true").lower() == "true"

        if not MCP_SERVER_URL:
            raise ValueError("MCP_SERVER_URL not configured")

        print(
            f"Initializing MCP client with "
            f"{'AWS SigV4' if use_aws_auth else 'standard'} authentication"
        )
        _mcp_client = SecureMCPClient(
            MCP_SERVER_URL, use_aws_auth=use_aws_auth
        )

    return _mcp_client


def get_mcp_client() -> SecureMCPClient:
    """Get MCP client instance"""
    if _mcp_client is None:
        return init_mcp_client()
    return _mcp_client


def cleanup_mcp_client():
    """Clean up MCP client"""
    global _mcp_client  # pylint: disable=global-statement
    if _mcp_client is not None:
        try:
            # Run the async close method in a new event loop
            asyncio.run(_mcp_client.close())
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error closing MCP client: {e}")
        finally:
            _mcp_client = None
