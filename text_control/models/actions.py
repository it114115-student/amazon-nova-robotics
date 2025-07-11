"""
Robot actions module - Contains the available robot actions with metadata
"""

from typing import Set
from mcp_client import get_mcp_client


async def get_available_action_and_description():
    """Return a list of available action names"""
    client = get_mcp_client()
    async with client:
        tools = await client.list_tools()
        name_and_description = [tool.name + " - " + tool.description for tool in tools]
        return name_and_description


async def get_available_actions() -> Set[str]:
    """Return a list of available action names"""
    client = get_mcp_client()
    async with client:
        tools = await client.list_tools()
        actions = {tool.name for tool in tools}
        return actions
