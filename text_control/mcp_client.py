"""
MCP Client module - Handles MCP client initialization and management
"""

import asyncio
from typing import Optional

from config import MCP_SERVER_URL
from fastmcp import Client

# Global MCP client instance
_mcp_client: Optional[Client] = None


def init_mcp_client() -> Client:
    """Initialize MCP client"""
    global _mcp_client
    if _mcp_client is None:
        config = {"mcpServers": {"my_server": {"url": MCP_SERVER_URL}}}
        _mcp_client = Client(config)
    return _mcp_client


def get_mcp_client() -> Client:
    """Get MCP client instance"""
    if _mcp_client is None:
        return init_mcp_client()
    return _mcp_client


def cleanup_mcp_client():
    """Clean up MCP client"""
    global _mcp_client
    if _mcp_client is not None:
        try:
            # Run the async close method in a new event loop
            asyncio.run(_mcp_client.close())
        except Exception as e:
            print(f"Error closing MCP client: {e}")
        finally:
            _mcp_client = None
