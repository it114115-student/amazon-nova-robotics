"""Data models and enums for the MCP server."""

from enum import Enum


class RobotID(str, Enum):
    ALL = "all"
    ROBOT_1 = "robot_1"
    ROBOT_2 = "robot_2"
    ROBOT_3 = "robot_3"
    ROBOT_4 = "robot_4"
    ROBOT_5 = "robot_5"
    ROBOT_6 = "robot_6"


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACK = "back"
