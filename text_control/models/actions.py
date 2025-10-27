"""
Robot actions module - Contains the available robot actions with metadata
"""

from typing import Set

from cache_utils import cache_result
from mcp_client import get_mcp_client


@cache_result(timeout=300, key_prefix="name_and_description")
async def get_available_action_and_description():
    """Return a list of available action names"""
    client = get_mcp_client()
    async with client:
        tools = await client.list_tools()
        name_and_description = [getattr(tool, 'tool_name', getattr(tool, 'name', 'unknown')) + " - " + getattr(tool, 'description', getattr(tool, '_tool_spec', {}).get('description', 'No description')) for tool in tools]
        return name_and_description


@cache_result(timeout=300, key_prefix="actions")
async def get_available_actions() -> Set[str]:
    """Return a list of available action names"""
    client = get_mcp_client()
    async with client:
        tools = await client.list_tools()
        actions = {getattr(tool, 'tool_name', getattr(tool, 'name', 'unknown')) for tool in tools}
        return actions
