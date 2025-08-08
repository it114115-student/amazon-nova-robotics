"""
Command normalization utilities for processing user input variations.
Handles camelCase, spaces, underscores, and synonym mapping.
"""

import re


def normalize_command(command):
    """
    Normalize command variations to match SIMPLE_COMMANDS format.
    Handles camelCase, spaces, underscores, and other variations.

    Examples:
    - "moveForward" -> "move_forward"
    - "move forward" -> "move_forward"
    - "pushUps" -> "push_ups"
    - "standUp" -> "stand_up"
    - "rotateClockwise" -> "rotate_clockwise"

    Args:
        command (str): The input command to normalize

    Returns:
        str: The normalized command string
    """
    if not command:
        return ""

    # Strip whitespace first
    normalized = command.strip()

    # Handle camelCase: insert underscore before uppercase letters BEFORE converting to lowercase
    # This regex finds lowercase letter followed by uppercase letter
    normalized = re.sub(r"([a-z])([A-Z])", r"\1_\2", normalized)

    # Convert to lowercase after camelCase processing
    normalized = normalized.lower()

    # Handle space-separated words: convert spaces to underscores
    normalized = re.sub(r"\s+", "_", normalized)

    # Remove any duplicate underscores
    normalized = re.sub(r"_+", "_", normalized)

    # Remove leading/trailing underscores
    normalized = normalized.strip("_")

    return normalized


def get_command_synonyms():
    """
    Get dictionary of command synonyms and variations.

    Returns:
        dict: Dictionary mapping synonym commands to standard commands
    """
    return {
        # Movement synonyms
        "forward": "move_forward",
        "backward": "move_backward",
        "back": "move_backward",
        "left": "move_left",
        "right": "move_right",
        "up": "move_up",
        "down": "move_down",
        # Action synonyms
        "exercise": "push_ups",
        "workout": "push_ups",
        "pushup": "push_ups",
        "situp": "sit_ups",
        "kick": "left_kick",
        "punch": "left_shot_fast",
        "takeoff": "takeoff",
        "landing": "land",
        # State synonyms
        "standup": "stand_up",
        "laydown": "lay_down",
        "sitdown": "sit",
    }


def find_matching_command(user_input, simple_commands):
    """
    Find a matching command in SIMPLE_COMMANDS using normalization.
    Returns the normalized command if found in SIMPLE_COMMANDS, None otherwise.

    Args:
        user_input (str): The user's input command
        simple_commands (set): Set of valid simple commands

    Returns:
        str or None: The matched command if found, None otherwise
    """
    # First try direct match
    user_input_lower = user_input.lower().strip()
    if user_input_lower in simple_commands:
        return user_input_lower

    # Try normalized version
    normalized = normalize_command(user_input)
    if normalized in simple_commands:
        return normalized

    # Try common variations and synonyms
    command_synonyms = get_command_synonyms()

    if normalized in command_synonyms:
        return command_synonyms[normalized]

    return None
