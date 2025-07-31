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
DOG_IDS = ["dog_1", "dog_2"]

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
    def publish(self, robot_id: str, message: str, parameters: Dict[str, Any] = None) -> bool:
        """Publish message to robot"""
        raise NotImplementedError("Subclasses must implement this method")


class StandardRobotPublisher(RobotPublisher):
    """Publisher for standard robots"""

    def publish(self, robot_id: str, message: str, parameters: Dict[str, Any] = None) -> bool:
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

    def publish(self, robot_id: str, message: str, parameters: Dict[str, Any] = None) -> bool:
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

    def _map_action_to_sdk(self, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
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
            logger.warning(f"No specific mapping found for action '{action}', using default")
            return {"action": action, "params": parameters}

    def _process_parameters(self, action: str, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
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

    def publish(self, robot_id: str, message: str, parameters: Dict[str, Any] = None) -> bool:
        """Publish message to dog with enhanced error handling and logging"""
        logger.info(f"DogPublisher.publish called with robot_id={robot_id}, message={message}, parameters={parameters}")
        
        try:
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
                    logger.info(f"Processed message after removing 'dog' prefix: {action}")
            
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


class RobotService:
    """Main service class for robot operations"""

    def __init__(self):
        self.robot_publisher = StandardRobotPublisher()
        self.drone_publisher = DronePublisher()
        self.dog_publisher = DogPublisher()

    def _get_robot_ids(self) -> List[str]:
        """Get list of robot IDs"""
        return [f"robot_{i}" for i in ROBOT_RANGE]

    def _execute_parallel_actions(
        self, robot_ids: List[str], message: str, publisher: RobotPublisher, parameters: Dict[str, Any] = None
    ) -> bool:
        """Execute actions in parallel for multiple robots"""
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(publisher.publish, robot_id, message, parameters): robot_id
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

    def execute_robot_action(self, message: str, selected_robot: str, parameters: Dict[str, Any] = None) -> bool:
        """Execute a robot action by publishing to the appropriate IoT topic with enhanced routing"""
        logger.info(f"execute_robot_action called with message={message}, selected_robot={selected_robot}, parameters={parameters}")
        
        try:
            # Validate inputs
            if not message or not selected_robot:
                logger.error("Invalid input: message and selected_robot are required")
                return False
            
            # Route to appropriate publisher based on robot type
            if selected_robot == "all":
                logger.info("Executing action for all standard robots")
                robot_ids = self._get_robot_ids()
                return self._execute_parallel_actions(
                    robot_ids, message, self.robot_publisher, parameters
                )

            elif selected_robot == "drone_all":
                logger.info("Executing action for all drones")
                return self._execute_parallel_actions(
                    DRONE_IDS, message, self.drone_publisher, parameters
                )

            elif selected_robot in DRONE_IDS:
                logger.info(f"Executing action for individual drone: {selected_robot}")
                return self.drone_publisher.publish(selected_robot, message, parameters)

            elif selected_robot == "dog_all":
                logger.info("Executing action for all dogs")
                return self._execute_parallel_actions(
                    DOG_IDS, message, self.dog_publisher, parameters
                )

            elif selected_robot in DOG_IDS:
                logger.info(f"Executing action for individual dog: {selected_robot}")
                return self.dog_publisher.publish(selected_robot, message, parameters)

            elif selected_robot.startswith("robot_"):
                logger.info(f"Executing action for standard robot: {selected_robot}")
                return self.robot_publisher.publish(selected_robot, message, parameters)

            else:
                logger.warning(f"Unknown robot type for {selected_robot}, trying default robot publisher")
                return self.robot_publisher.publish(selected_robot, message, parameters)

        except Exception as e:
            logger.error(f"Error executing robot action: {e}", exc_info=True)
            return False

    def execute_dog_action(self, dog_id: str, action: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Execute a specific dog action with parameters.
        
        This method provides a direct interface for dog actions, bypassing
        the general robot action routing.
        
        Args:
            dog_id: ID of the dog robot (e.g., "dog_1", "dog_2")
            action: Action name (e.g., "move_forward", "rotate_left")
            parameters: Action parameters (e.g., {"distance": 100, "speed": 0.5})
            
        Returns:
            True if action was successfully published, False otherwise
        """
        logger.info(f"execute_dog_action called with dog_id={dog_id}, action={action}, parameters={parameters}")
        
        try:
            # Validate dog ID
            if dog_id not in DOG_IDS and dog_id != "all":
                logger.error(f"Invalid dog ID: {dog_id}. Valid IDs: {DOG_IDS + ['all']}")
                return False
            
            # Handle "all" dogs
            if dog_id == "all":
                return self._execute_parallel_actions(
                    DOG_IDS, action, self.dog_publisher, parameters
                )
            
            # Execute for specific dog
            return self.dog_publisher.publish(dog_id, action, parameters)
            
        except Exception as e:
            logger.error(f"Error executing dog action: {e}", exc_info=True)
            return False

    async def process_actions(
        self, actions_to_execute: List[str], selected_robot: str, parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Process a list of actions sequentially with parameter support"""
        results = []

        try:
            available_actions = await get_available_actions()

            for action in actions_to_execute:
                if action in available_actions:
                    success = self.execute_robot_action(action, selected_robot, parameters)
                    results.append(
                        {"robot": selected_robot, "action": action, "success": success}
                    )
                    sleep(ACTION_DELAY)
                else:
                    logger.warning(f"Action '{action}' is not available")
                    results.append(
                        {
                            "robot": selected_robot,
                            "action": action,
                            "success": False,
                            "error": "Action not available",
                        }
                    )

            logger.info(f"Processed {len(results)} actions for {selected_robot}")
            return results

        except Exception as e:
            logger.error(f"Error processing actions: {e}", exc_info=True)
            return []

    def get_supported_dog_actions(self) -> List[str]:
        """Get list of supported dog actions"""
        return list(self.dog_publisher.action_mapping.keys())

    def get_robot_status(self, robot_id: str) -> Dict[str, Any]:
        """Get robot status information"""
        try:
            if robot_id in DOG_IDS:
                return {
                    "robot_id": robot_id,
                    "type": "dog",
                    "status": "active",
                    "supported_actions": self.get_supported_dog_actions()
                }
            elif robot_id in DRONE_IDS:
                return {
                    "robot_id": robot_id,
                    "type": "drone", 
                    "status": "active",
                    "supported_actions": list(self.drone_publisher.action_mapping.keys())
                }
            elif robot_id.startswith("robot_"):
                return {
                    "robot_id": robot_id,
                    "type": "standard_robot",
                    "status": "active"
                }
            else:
                return {
                    "robot_id": robot_id,
                    "type": "unknown",
                    "status": "unknown"
                }
        except Exception as e:
            logger.error(f"Error getting robot status for {robot_id}: {e}")
            return {"robot_id": robot_id, "type": "unknown", "status": "error", "error": str(e)}

    def validate_dog_action(self, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate a dog action and its parameters.
        
        Returns:
            Dictionary with validation results
        """
        try:
            # Check if action is supported
            if action not in self.dog_publisher.action_mapping:
                return {
                    "valid": False,
                    "error": f"Unsupported action: {action}",
                    "supported_actions": self.get_supported_dog_actions()
                }
            
            # Validate parameters
            mapping = self.dog_publisher.action_mapping[action]
            action_type = mapping["type"]
            
            validation_errors = []
            
            if parameters:
                if action_type == "movement":
                    if "distance" in parameters:
                        try:
                            distance = int(parameters["distance"])
                            if distance < 1 or distance > 1000:
                                validation_errors.append("Distance must be between 1 and 1000 cm")
                        except (ValueError, TypeError):
                            validation_errors.append("Distance must be a valid integer")
                    
                    if "speed" in parameters:
                        try:
                            speed = float(parameters["speed"])
                            if speed < 0.1 or speed > 1.0:
                                validation_errors.append("Speed must be between 0.1 and 1.0")
                        except (ValueError, TypeError):
                            validation_errors.append("Speed must be a valid float")
                
                elif action_type == "rotation":
                    if "angle" in parameters:
                        try:
                            angle = int(parameters["angle"])
                            if angle < 1 or angle > 360:
                                validation_errors.append("Angle must be between 1 and 360 degrees")
                        except (ValueError, TypeError):
                            validation_errors.append("Angle must be a valid integer")
            
            if validation_errors:
                return {
                    "valid": False,
                    "errors": validation_errors
                }
            
            return {
                "valid": True,
                "action_type": action_type,
                "mapped_action": mapping["action"]
            }
            
        except Exception as e:
            logger.error(f"Error validating dog action: {e}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }


# Create service instance
robot_service = RobotService()
