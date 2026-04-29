"""Configuration constants for the MCP server."""

import os

# Default movement parameters
DRONE_MOVE_DISTANCE_CM = 50

# DynamoDB table for speech messages
SPEECH_TABLE = os.getenv("SpeechTable", "")

# Robot table (shared with text_control)
ROBOT_TABLE = os.getenv("RobotTable", "")
