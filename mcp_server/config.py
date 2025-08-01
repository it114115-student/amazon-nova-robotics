"""Configuration constants for the MCP server."""

# Default movement parameters
DRONE_MOVE_DISTANCE_CM = 50

# Robot action mappings
DOG_ACTION_MAPPING = {
    # Movement actions
    "move_forward": "forward",
    "move_backward": "back", 
    "move_left": "left",
    "move_right": "right",
    # Rotation actions
    "rotate_clockwise": "cw",
    "rotate_counterclockwise": "ccw",
    # Posture actions
    "stand_up": "stand_up",
    "lay_down": "lay_down",
    "hop": "hop",
    # Status actions
    "activate": "activate",
    "walk_mode": "walk_mode", 
    "dance_mode": "dance_mode",
    "stop": "stop",
    # Custom movement
    "custom_movement": "custom_movement"
}