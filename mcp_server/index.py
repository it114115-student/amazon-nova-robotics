"""
Refactored MCP Server for Robotics Control

This module provides a clean, organized MCP server for controlling various robots,
drones, and robotic dogs through AWS IoT.
"""

from awslabs.mcp_lambda_handler import MCPLambdaHandler

# Import tool registration functions
from tools.drone_tools import register_drone_tools
from tools.dog_tools import register_dog_tools
from tools.robot_tools import register_robot_tools
from tools.dance_tools import register_dance_tools
from tools.image_tools import register_image_tools
from tools.xiaoice_tools import register_xiaoice_tools
from tools.speech_tools import register_speech_tools

# Initialize MCP handler
mcp = MCPLambdaHandler(name="robotics-mcp-server", version="1.0.0")

# Register all tool categories
register_drone_tools(mcp)
register_dog_tools(mcp)
register_robot_tools(mcp)
register_dance_tools(mcp)
register_image_tools(mcp)
register_xiaoice_tools(mcp)
register_speech_tools(mcp)


def handler(event, context):
    """AWS Lambda handler function."""
    return mcp.handle_request(event, context)


if __name__ == "__main__":
    # For local testing
    print("MCP Server initialized with all robot control tools")