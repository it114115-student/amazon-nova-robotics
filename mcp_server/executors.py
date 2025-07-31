"""Robot command executors."""

from typing import Dict
from services.iot_service import execute_dog_action, execute_drone_action, execute_robot_action
from config import DOG_ACTION_MAPPING


class RobotExecutor:
    """Robot command executor that wraps the robot service"""

    def execute_drone_action(self, drone_id: str, action: str, parameters: Dict = None):
        """Execute a drone action with parameter mapping."""
        if parameters is None:
            parameters = {}
            
        # Map high-level actions to Tello SDK commands
        sdk_action = None
        sdk_params = None
        
        if action.startswith("move_"):
            direction = action.replace("move_", "")
            sdk_action = direction  # up, down, left, right, forward, back
            sdk_params = {"distance": parameters.get("x")}
        elif action == "rotate_clockwise":
            sdk_action = "cw"
            sdk_params = {"angle": parameters.get("x")}
        elif action == "rotate_counterclockwise":
            sdk_action = "ccw"
            sdk_params = {"angle": parameters.get("x")}
        elif action == "flip":
            sdk_action = "flip"
            sdk_params = {"direction": parameters.get("direction")}
        elif action in ["takeoff", "land"]:
            sdk_action = action
            sdk_params = {}
        else:
            sdk_action = action
            sdk_params = parameters
            
        message = {
            "droneID": drone_id.lower(),
            "action": sdk_action,
            "parameters": sdk_params,
        }
        return execute_drone_action(message)

    def execute_dog_action(self, dog_id: str, action: str, parameters: Dict = None):
        """Execute a dog action with parameter mapping."""
        if parameters is None:
            parameters = {}
        
        # Map MCP action names to action_executor action names
        sdk_action = DOG_ACTION_MAPPING.get(action, action)
        
        # Process parameters based on action type
        sdk_params = parameters.copy()
        
        # Handle legacy parameter mapping for backward compatibility
        if action.startswith("move_"):
            # Extract distance parameter consistently
            distance = parameters.get("distance") or parameters.get("x") or parameters.get("y")
            if distance:
                sdk_params["distance"] = distance
        elif action in ["rotate_clockwise", "rotate_counterclockwise"]:
            # Extract angle parameter consistently  
            angle = parameters.get("angle") or parameters.get("x")
            if angle:
                sdk_params["angle"] = angle
        
        message = {
            "dogID": dog_id.lower(),
            "action": sdk_action,
            "parameters": sdk_params,
        }
        return execute_dog_action(message)

    def execute_action(self, robot_id: str, action: str) -> bool:
        """Execute a robot action"""
        return execute_robot_action(action, robot_id.lower())


# Global executor instance
robot_executor = RobotExecutor()