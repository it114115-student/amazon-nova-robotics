"""Robot speech tools for the MCP server.

Uses Amazon Polly to synthesize speech, uploads the audio to S3,
generates a presigned URL, and publishes the URL to the robot's IoT topic
so the client can play it.
"""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import RobotID
from services.polly_service import synthesize_and_upload, VOICE_MAP

import json


def _publish_speech_url(robot_id_str: str, audio_url: str, text: str, duration: float = 0.0) -> bool:
    """Publish a speech audio URL to the robot's IoT topic and simulator."""
    from services.iot_service import execute_robot_action

    return execute_robot_action(
        "speech",
        robot_id_str,
        {"audio_url": audio_url, "text": text, "duration": duration},
    )


def register_speech_tools(mcp: MCPLambdaHandler):
    """Register speech tools with the MCP handler."""

    @mcp.tool()
    def robot_speak(robot_id: RobotID, text: str, language: str = "yue") -> str:
        """Make the robot speak a message aloud using Amazon Polly text-to-speech.

        The audio is synthesized via Amazon Polly, uploaded to S3, and the
        presigned URL is published to the robot's IoT topic for playback.

        Supported languages:
          - yue: Cantonese (default, voice: Hiujin)
          - cmn: Mandarin Chinese (voice: Zhiyu)
          - en:  English (voice: Joanna)
          - ja:  Japanese (voice: Kazuha)
          - ko:  Korean (voice: Seoyeon)

        Args:
            robot_id (RobotID): Target robot ID (e.g. robot_1 or all)
            text (str): The text message for the robot to speak
            language (str): Language code — yue, cmn, en, ja, ko (default: yue)

        Returns:
            str: Confirmation with the audio URL, or an error message.
        """
        if not text or not text.strip():
            return "Error: text cannot be empty."

        if language not in VOICE_MAP:
            supported = ", ".join(VOICE_MAP.keys())
            return f"Error: unsupported language '{language}'. Supported: {supported}"

        # Resolve enum value
        robot_id_str = robot_id.value if hasattr(robot_id, "value") else str(robot_id)

        # 1. Synthesize with Polly and upload to S3
        result = synthesize_and_upload(text=text.strip(), language=language)
        if result is None:
            return f"Failed to synthesize speech for robot ({robot_id_str})."

        audio_url = result["url"]
        duration = result["duration"]

        # 2. Publish the presigned URL to IoT
        published = _publish_speech_url(robot_id_str, audio_url, text.strip(), duration)

        if published:
            return (
                f'Robot ({robot_id_str}) is speaking: "{text.strip()}" '
                f'[lang={language}, voice={result["voice_id"]}, duration={duration:.2f}s] '
                f"audio_url={audio_url}"
            )
        else:
            return (
                f"Speech synthesized but failed to publish to IoT for robot ({robot_id_str}). "
                f"audio_url={audio_url}, duration={duration:.2f}s"
            )
