"""
Publisher for dogs - directly uses MCP function names
"""

import json
import re
from typing import Any, Dict

import boto3
from botocore.config import Config
from utils.lambda_logger import get_lambda_logger

from ..message_transformer import MessageTransformer
from .base_publisher import RobotPublisher

logger = get_lambda_logger(__name__)

# Initialize AWS client with retry configuration
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


class DogPublisher(RobotPublisher):
    """Publisher for dogs - directly uses MCP function names"""

    def __init__(self):
        pass

    def publish(
        self, robot_id: str, message: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """Publish message to dog by removing dog_ prefix and reformatting"""
        logger.info(
            "DogPublisher.publish called with robot_id=%s, message=%s, parameters=%s",
            robot_id,
            message,
            parameters,
        )

        try:
            # Skip actions with other device prefixes
            if MessageTransformer.has_device_prefix(message, "dog"):
                logger.info(
                    "Skipping action '%s' for dog %s - wrong device type",
                    message,
                    robot_id,
                )
                return True  # Return True to indicate "handled" (by skipping)

            # Remove 'dog_' prefix if present and use the action name directly
            if message.startswith("dog"):
                action = message[3:]  # Remove 'dog_' prefix
                # Convert camelCase to snake_case for action names like 'dogMoveForward' -> 'move_forward'

                def camel_to_snake(name):
                    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
                    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

                action = camel_to_snake(action)
                logger.info("Removed 'dog_' prefix, action: %s", action)
            else:
                action = message
                logger.info("No 'dog_' prefix found, using action as-is: %s", action)

            # Create IoT message in the format expected by the dog system (same as MCP server)
            data = {
                "dogID": robot_id.lower(),
                "action": action,
                "parameters": parameters or {},
            }

            topic = f"{robot_id}/topic"
            logger.info("Publishing to topic: %s with data: %s", topic, data)

            # Publish to IoT
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(json.dumps(data), "utf-8"),
            )

            logger.info("Successfully published to %s: %s", topic, data)
            return True

        except ValueError as e:
            logger.error("Parameter validation error for dog %s: %s", robot_id, e)
            return False
        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error publishing to dog %s: %s", robot_id, e)
            return False
        except (TypeError, OSError) as e:
            logger.error("Data or system error for dog %s: %s", robot_id, e)
            return False
