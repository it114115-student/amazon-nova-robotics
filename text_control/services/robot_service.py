"""
Robot service - Handles robot action execution

This module provides a refactored robot service with improved structure,
better error handling, and separation of concerns.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from models.actions import get_available_actions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DISTANCE = 50  # cm
DEFAULT_ANGLE = 90  # degrees
ACTION_DELAY = 0.1  # seconds
ROBOT_RANGE = range(1, 10)
DRONE_IDS = ["drone_1", "drone_2"]

# Initialize AWS clients with retry configuration
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


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


class RobotPublisher(ABC):
    """Abstract base class for robot publishers"""

    @abstractmethod
    def publish(self, robot_id: str, message: str) -> bool:
        """Publish message to robot"""
        raise NotImplementedError("Subclasses must implement this method")


class StandardRobotPublisher(RobotPublisher):
    """Publisher for standard robots"""

    def publish(self, robot_id: str, message: str) -> bool:
        """Publish message to standard robot"""
        # Remove 'robot' prefix and convert to snake_case
        processed_message = MessageTransformer.remove_prefix(message, "robot")
        if processed_message is None:
            logger.error("Invalid message format for robot %s: %s", robot_id, message)
            return False

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

    def publish(self, robot_id: str, message: str) -> bool:
        """Publish message to drone"""
        # Remove 'drone' prefix and convert to snake_case
        processed_message = MessageTransformer.remove_prefix(message, "drone")
        if processed_message is None:
            logger.error("Invalid message format for drone %s: %s", robot_id, message)
            return False

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


class RobotService:
    """Main service class for robot operations"""

    def __init__(self):
        self.robot_publisher = StandardRobotPublisher()
        self.drone_publisher = DronePublisher()

    def _get_robot_ids(self) -> List[str]:
        """Get list of robot IDs"""
        return [f"robot_{i}" for i in ROBOT_RANGE]

    def _execute_parallel_actions(
        self, robot_ids: List[str], message: str, publisher: RobotPublisher
    ) -> bool:
        """Execute actions in parallel for multiple robots"""
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(publisher.publish, robot_id, message): robot_id
                for robot_id in robot_ids
            }
            results = []

            for future in as_completed(futures):
                robot_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error("Error executing action for %s: %s", robot_id, e)
                    results.append(False)

            return all(results)

    def execute_robot_action(self, message: str, selected_robot: str) -> bool:
        """Execute a robot action by publishing to the appropriate IoT topic"""
        try:
            if selected_robot == "all":
                robot_ids = self._get_robot_ids()
                return self._execute_parallel_actions(
                    robot_ids, message, self.robot_publisher
                )

            elif selected_robot == "drone_all":
                return self.drone_publisher.publish("all", message)

            elif selected_robot in DRONE_IDS:
                return self.drone_publisher.publish(selected_robot, message)

            else:
                return self.robot_publisher.publish(selected_robot, message)

        except Exception as e:
            logger.error("Error executing robot action: %s", e)
            return False

    async def process_actions(
        self, actions_to_execute: List[str], selected_robot: str
    ) -> List[Dict[str, Any]]:
        """Process a list of actions sequentially"""
        results = []

        try:
            available_actions = await get_available_actions()

            for action in actions_to_execute:
                if action in available_actions:
                    success = self.execute_robot_action(action, selected_robot)
                    results.append(
                        {"robot": selected_robot, "action": action, "success": success}
                    )
                    sleep(ACTION_DELAY)
                else:
                    logger.warning("Action '%s' is not available", action)
                    results.append(
                        {
                            "robot": selected_robot,
                            "action": action,
                            "success": False,
                            "error": "Action not available",
                        }
                    )

            logger.info("Processed %d actions for %s", len(results), selected_robot)
            return results

        except Exception as e:
            logger.error("Error processing actions: %s", e)
            return []


# Create service instance
robot_service = RobotService()
