"""
Publisher for standard robots
"""

import logging
from typing import Any, Dict

import boto3
from botocore.config import Config

from .base_publisher import RobotPublisher
from ..message_transformer import MessageTransformer

logger = logging.getLogger(__name__)

# Initialize AWS client with retry configuration
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


class StandardRobotPublisher(RobotPublisher):
    """Publisher for standard robots"""

    def publish(
        self, robot_id: str, message: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """Publish message to standard robot"""
        # Skip actions with other device prefixes
        if MessageTransformer.has_device_prefix(message, "robot"):
            logger.info(
                f"Skipping action '{message}' for robot {robot_id} - wrong device type"
            )
            return True  # Return True to indicate "handled" (by skipping)

        # Remove 'robot' prefix and convert to snake_case, or use generic action
        processed_message = MessageTransformer.remove_prefix(message, "robot")
        if processed_message is None:
            # No 'robot' prefix, treat as generic action
            processed_message = message
            logger.info(f"Using generic action '{message}' for robot {robot_id}")
        else:
            logger.info(f"Using robot-specific action '{message}' for robot {robot_id}")

        processed_message = MessageTransformer.camel_to_snake_case(processed_message)
        topic = f"{robot_id}/topic"

        try:
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(f'{{ "toolName": "{processed_message}" }}', "utf-8"),
            )
            logger.info("Published to %s: %s", topic, processed_message)
            return True
        except (ConnectionError, TimeoutError, Exception) as e:
            logger.error("Error publishing to %s: %s", topic, e)
            return False