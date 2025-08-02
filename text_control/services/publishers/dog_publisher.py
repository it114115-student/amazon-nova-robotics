"""
Publisher for dogs with comprehensive action mapping
"""

import json
import logging
from typing import Any, Dict

import boto3
from botocore.config import Config

from .base_publisher import RobotPublisher
from ..message_transformer import MessageTransformer
from ..robot_config import DEFAULT_DISTANCE, DEFAULT_ANGLE

logger = logging.getLogger(__name__)

# Initialize AWS client with retry configuration
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


class DogPublisher(RobotPublisher):
    """Publisher for dogs with comprehensive action mapping for new dog system"""

    def __init__(self):
        # Complete action mapping for new dog system
        self.action_mapping = {
            # Movement actions
            "move_forward": {"action": "forward", "type": "movement"},
            "move_backward": {"action": "back", "type": "movement"},
            "move_left": {"action": "left", "type": "movement"},
            "move_right": {"action": "right", "type": "movement"},
            # Rotation actions
            "rotate_clockwise": {"action": "cw", "type": "rotation"},
            "rotate_counterclockwise": {"action": "ccw", "type": "rotation"},
            "rotate_left": {"action": "ccw", "type": "rotation"},
            "rotate_right": {"action": "cw", "type": "rotation"},
            "turn_left": {"action": "ccw", "type": "rotation"},
            "turn_right": {"action": "cw", "type": "rotation"},
            "turn_back": {"action": "cw", "type": "rotation"},
            "turn_around": {"action": "cw", "type": "rotation"},
            # Posture actions
            "stand_up": {"action": "stand_up", "type": "posture"},
            "lay_down": {"action": "lay_down", "type": "posture"},
            "hop": {"action": "hop", "type": "special"},
            # Status actions
            "activate": {"action": "activate", "type": "status"},
            "enable_walking": {"action": "walk_mode", "type": "status"},
            "enable_dancing": {"action": "dance_mode", "type": "status"},
            "walk_mode": {"action": "walk_mode", "type": "status"},
            "dance_mode": {"action": "dance_mode", "type": "status"},
            # Control actions
            "stop": {"action": "stop", "type": "control"},
            "emergency_stop": {"action": "stop", "type": "control"},
            # Custom movement
            "custom_movement": {"action": "custom_movement", "type": "advanced"},
            "circle_movement": {"action": "custom_movement", "type": "advanced"},
        }

    def _map_action_to_sdk(
        self, action: str, parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Map high-level action to dog SDK command with comprehensive parameter handling"""
        if parameters is None:
            parameters = {}

        logger.info(f"Mapping action '{action}' with parameters: {parameters}")

        # Handle direct action mapping
        if action in self.action_mapping:
            mapping = self.action_mapping[action]
            mapped_action = mapping["action"]
            action_type = mapping["type"]

            # Process parameters based on action type
            processed_params = self._process_parameters(action, action_type, parameters)

            # Special handling for specific actions
            if action == "turn_back" or action == "turn_around":
                processed_params["angle"] = 180
            elif action == "turn_left" or action == "turn_right":
                processed_params.setdefault("angle", DEFAULT_ANGLE)

            return {"action": mapped_action, "params": processed_params}

        # Handle legacy snake_case actions
        elif action.startswith("move_"):
            direction = action.replace("move_", "")
            processed_params = self._process_parameters(action, "movement", parameters)
            return {"action": direction, "params": processed_params}

        # Handle rotation actions
        elif action in ["cw", "ccw"]:
            processed_params = self._process_parameters(action, "rotation", parameters)
            return {"action": action, "params": processed_params}

        # Default mapping
        else:
            logger.warning(
                f"No specific mapping found for action '{action}', using default"
            )
            return {"action": action, "params": parameters}

    def _process_parameters(
        self, action: str, action_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process parameters based on action type"""
        processed = parameters.copy()

        if action_type == "movement":
            # Handle distance parameter
            if "distance" not in processed:
                processed["distance"] = DEFAULT_DISTANCE

            # Handle speed parameter
            if "speed" not in processed:
                processed["speed"] = 0.5

            # Ensure valid ranges
            processed["speed"] = max(0.1, min(1.0, float(processed["speed"])))
            processed["distance"] = max(1, int(processed["distance"]))

        elif action_type == "rotation":
            # Handle angle parameter
            if "angle" not in processed:
                processed["angle"] = DEFAULT_ANGLE

            # Handle speed parameter
            if "speed" not in processed:
                processed["speed"] = 0.5

            # Ensure valid ranges
            processed["speed"] = max(0.1, min(1.0, float(processed["speed"])))
            processed["angle"] = max(1, min(360, int(processed["angle"])))

        elif action_type == "posture":
            # Handle speed parameter for posture actions
            if "speed" not in processed:
                processed["speed"] = 0.5
            processed["speed"] = max(0.1, min(1.0, float(processed["speed"])))

        elif action_type == "special":
            # Handle duration for special actions like hop
            if "duration" not in processed:
                processed["duration"] = 1.0
            processed["duration"] = max(0.1, min(5.0, float(processed["duration"])))

        elif action_type == "advanced":
            # Handle custom movement parameters
            movement_params = ["lx", "ly", "rx", "ry", "dpadx", "dpady"]
            for param in movement_params:
                if param in processed:
                    processed[param] = max(-1.0, min(1.0, float(processed[param])))

            if "duration" not in processed:
                processed["duration"] = 2.0
            processed["duration"] = max(0.1, min(10.0, float(processed["duration"])))

        return processed

    def publish(
        self, robot_id: str, message: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """Publish message to dog with enhanced error handling and logging"""
        logger.info(
            f"DogPublisher.publish called with robot_id={robot_id}, message={message}, parameters={parameters}"
        )

        try:
            # Skip actions with other device prefixes
            if MessageTransformer.has_device_prefix(message, "dog"):
                logger.info(
                    f"Skipping action '{message}' for dog {robot_id} - wrong device type"
                )
                return True  # Return True to indicate "handled" (by skipping)

            # Handle direct action names (no prefix removal needed)
            if message in self.action_mapping:
                action = message
                logger.info(f"Direct action mapping found for: {action}")
            else:
                # Remove 'dog' prefix and convert to snake_case for legacy support
                processed_message = MessageTransformer.remove_prefix(message, "dog")
                if processed_message is None:
                    # Try without prefix removal
                    action = MessageTransformer.camel_to_snake_case(message)
                    logger.info(f"No 'dog' prefix found, using message as-is: {action}")
                else:
                    action = MessageTransformer.camel_to_snake_case(processed_message)
                    logger.info(
                        f"Processed message after removing 'dog' prefix: {action}"
                    )

            # Map action to SDK format
            sdk_mapping = self._map_action_to_sdk(action, parameters or {})
            logger.info(f"SDK mapping result: {sdk_mapping}")

            # Create IoT message in the format expected by the new dog system
            data = {
                "dogID": robot_id.lower(),
                "action": sdk_mapping["action"],
                "parameters": sdk_mapping["params"],
            }

            topic = f"{robot_id}/topic"
            logger.info(f"Publishing to topic: {topic} with data: {data}")

            # Publish to IoT
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(json.dumps(data), "utf-8"),
            )

            logger.info(f"Successfully published to {topic}: {data}")
            return True

        except ValueError as e:
            logger.error(f"Parameter validation error for dog {robot_id}: {e}")
            return False
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error publishing to dog {robot_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing to dog {robot_id}: {e}")
            return False