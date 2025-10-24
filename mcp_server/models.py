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


class DogID(str, Enum):
    ALL = "all"
    DOG_1 = "dog_1"
    DOG_2 = "dog_2"
    DOG_3 = "dog_3"


class DroneID(str, Enum):
    ALL = "all"
    DRONE_1 = "drone_1"
    DRONE_2 = "drone_2"


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACK = "back"
