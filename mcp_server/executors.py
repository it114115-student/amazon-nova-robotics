"""Robot command executors."""

from typing import Dict

from services.iot_service import (
    execute_dog_action,
    execute_drone_action,
    execute_robot_action,
    execute_xiaoice_speech,
)


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
        """Execute a dog action."""
        if parameters is None:
            parameters = {}

        # Process parameters as provided
        sdk_params = parameters.copy()

        message = {
            "dogID": dog_id.lower(),
            "action": action,
            "parameters": sdk_params,
        }
        return execute_dog_action(message)

    def execute_action(self, robot_id: str, action: str) -> bool:
        """Execute a robot action"""
        return execute_robot_action(action, robot_id.lower())

    def execute_xiaoice_speech(self, xiaoice_id: str, message: str, presenter_id: str = None) -> bool:
        """Execute a xiaoice speech action"""
        return execute_xiaoice_speech(xiaoice_id.lower(), message, presenter_id)


# Global executor instance
robot_executor = RobotExecutor()
