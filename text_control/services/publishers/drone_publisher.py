"""
Publisher for drones with Tello SDK mapping
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


class DronePublisher(RobotPublisher):
    """Publisher for drones with Tello SDK mapping"""

    def __init__(self):
        self.action_mapping = {
            "rotate_clockwise": {"action": "cw", "params": {"angle": DEFAULT_ANGLE}},
            "rotate_counterclockwise": {
                "action": "ccw",
                "params": {"angle": DEFAULT_ANGLE},
            },
            "flip": {"action": "flip", "params": {"direction": "f"}},
            "takeoff": {"action": "takeoff", "params": {}},
            "land": {"action": "land", "params": {}},
        }

    def _map_action_to_sdk(self, action: str) -> Dict[str, Any]:
        """Map high-level action to Tello SDK command"""
        if action.startswith("move_"):
            direction = action.replace("move_", "")
            return {"action": direction, "params": {"distance": DEFAULT_DISTANCE}}

        return self.action_mapping.get(action, {"action": action, "params": {}})

    def publish(
        self, robot_id: str, message: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """Publish message to drone"""
        # Skip actions with other device prefixes
        if MessageTransformer.has_device_prefix(message, "drone"):
            logger.info(
                f"Skipping action '{message}' for drone {robot_id} - wrong device type"
            )
            return True  # Return True to indicate "handled" (by skipping)

        # Remove 'drone' prefix and convert to snake_case, or use generic action
        processed_message = MessageTransformer.remove_prefix(message, "drone")
        if processed_message is None:
            # No 'drone' prefix, treat as generic action
            processed_message = message
            logger.info(f"Using generic action '{message}' for drone {robot_id}")
        else:
            logger.info(f"Using drone-specific action '{message}' for drone {robot_id}")

        action = MessageTransformer.camel_to_snake_case(processed_message)
        sdk_mapping = self._map_action_to_sdk(action)

        data = {
            "droneID": robot_id.lower(),
            "action": sdk_mapping["action"],
            "parameters": sdk_mapping["params"],
        }

        topic = "drone_1/topic"  # it is a hub for all drones
        try:
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(json.dumps(data), "utf-8"),
            )
            logger.info("Published to %s: %s", topic, data)
            return True
        except (ConnectionError, TimeoutError, Exception) as e:
            logger.error("Error publishing to %s: %s", topic, e)
            return False