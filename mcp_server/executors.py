"""Robot command executors."""

from typing import Dict

from services.iot_service import (
    execute_dog_action,
    execute_drone_action,
    execute_robot_action,
    execute_xiaoice_speech,
)
from services.polly_service import synthesize_and_upload


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

    def execute_robot_speech(self, robot_id: str, text: str, language: str = "yue") -> dict:
        """Synthesize speech with Polly, upload to S3, and publish URL to IoT.

        Returns dict with url and success status, or None on failure.
        """
        robot_id_str = robot_id.value if hasattr(robot_id, "value") else str(robot_id).lower()

        result = synthesize_and_upload(text=text.strip(), language=language)
        if result is None:
            return {"success": False, "error": "Polly synthesis failed"}

        from tools.speech_tools import _publish_speech_url
        published = _publish_speech_url(robot_id_str, result["url"], text.strip())

        return {
            "success": published,
            "url": result["url"],
            "voice_id": result["voice_id"],
            "language": language,
        }


# Global executor instance
robot_executor = RobotExecutor()
