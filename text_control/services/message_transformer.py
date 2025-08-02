"""
Message transformation utilities for robot service
"""

import re
from typing import Optional


class MessageTransformer:
    """Handles message transformation between different formats"""

    @staticmethod
    def camel_to_snake_case(text: str) -> str:
        """Convert camelCase to snake_case"""
        text = text.lstrip("_")
        return re.sub(r"([A-Z])", r"_\1", text).lower().lstrip("_")

    @staticmethod
    def remove_prefix(text: str, prefix: str) -> Optional[str]:
        """Remove prefix from text if present"""
        if text.startswith(prefix):
            return text[len(prefix) :]
        return None
    
    @staticmethod
    def has_device_prefix(message: str, target_device: str) -> bool:
        """Check if message has a specific device prefix (robot, drone, dog)"""
        device_prefixes = ["robot", "drone", "dog"]
        
        for prefix in device_prefixes:
            if prefix != target_device and message.lower().startswith(prefix.lower()):
                # Check if it's a real prefix (followed by uppercase letter or end of string)
                if len(message) == len(prefix) or (len(message) > len(prefix) and message[len(prefix)].isupper()):
                    return True
        return False