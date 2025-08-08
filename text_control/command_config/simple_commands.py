"""
Simple commands configuration for robot control.
This file contains the set of commands that don't require LLM classification.
Auto-generated from MCP server analysis.
"""

# Simple commands that don't need classification
SIMPLE_COMMANDS = {
    # Basic control commands
    "activate",
    "hop",
    "stop",
    # Movement commands
    "circle_movement",
    "head_move",
    "height_move",
    "move_back",
    "move_backward",
    "move_down",
    "move_forward",
    "move_left",
    "move_leftback",
    "move_leftfront",
    "move_right",
    "move_rightback",
    "move_rightfront",
    "move_up",
    "rotate",
    "rotate_clockwise",
    "rotate_counterclockwise",
    "walk_mode",
    # Look/Vision commands
    "look_down",
    "look_left",
    "look_leftlower",
    "look_right",
    "look_rightlower",
    "look_up",
    "look_upperleft",
    "look_upperright",
    # Advanced commands
    "backleg_lift",
    "balance",
    "body_cycle",
    "body_row",
    "foreleg_lift",
    "gait_uni",
    "head_ellipse",
    # Other commands
    "bowback",
    "dance_mode",
    "flip",
    "land",
    "lay_down",
    "stand_up",
    "takeoff",
}
