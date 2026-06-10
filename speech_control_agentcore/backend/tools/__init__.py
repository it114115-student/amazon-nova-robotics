"""Robot voice control tools collection."""

import logging
from tools.mcp_client import cleanup_mcp_client
from tools.robot_actions import get_dynamic_tools

logger = logging.getLogger(__name__)

_cached_tools = None


def warmup_tools() -> list:
    """Warm up IAM-backed MCP tools at process start for lower first-turn latency."""
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = get_dynamic_tools()
        logger.info(
            "MCP tool warmup complete: loaded %d tools names=%s",
            len(_cached_tools),
            [
                getattr(getattr(tool, "mcp_tool", None), "name", getattr(tool, "tool_name", str(tool)))
                for tool in _cached_tools
            ],
        )
    return _cached_tools


def get_all_tools() -> list:
    """Return IAM-authenticated MCP tools for the Strands agent.

    This project uses the native Strands MCPClient over AgentCore Gateway.
    """
    logger.info("Using native Strands MCP client over AgentCore Gateway.")
    return warmup_tools()


def cleanup_tools() -> None:
    """Release the shared MCP client and tool cache."""
    global _cached_tools
    _cached_tools = None
    cleanup_mcp_client()


__all__ = ["cleanup_tools", "get_all_tools", "warmup_tools"]
