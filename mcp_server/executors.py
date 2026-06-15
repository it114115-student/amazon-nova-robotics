"""Robot command executors."""

from services.iot_service import execute_robot_action
from services.polly_service import synthesize_and_upload


class RobotExecutor:
    """Robot command executor that wraps the robot service"""

    def execute_action(self, robot_id: str, action: str) -> bool:
        """Execute a robot action"""
        return execute_robot_action(action, robot_id.lower())

    def execute_robot_speech(self, robot_id: str, text: str, language: str = "yue") -> dict:
        """Synthesize speech with Polly, upload to S3, and publish URL to IoT.

        Returns dict with url and success status, or None on failure.
        """
        robot_id_str = robot_id.value if hasattr(robot_id, "value") else str(robot_id).lower()

        result = synthesize_and_upload(text=text.strip(), language=language)
        if result is None:
            return {"success": False, "error": "Polly synthesis failed"}

        # Use unified execute_robot_action which handles IoT publish and Simulator notification
        published = execute_robot_action(
            "speech",
            robot_id_str,
            {
                "audio_url": result["url"],
                "text": text.strip(),
                "duration": result["duration"],
            },
        )

        return {
            "success": published,
            "url": result["url"],
            "voice_id": result["voice_id"],
            "language": language,
            "duration": result["duration"],
        }


# Global executor instance
robot_executor = RobotExecutor()
