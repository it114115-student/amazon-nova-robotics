"""Xiaoice Digital Human speech tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import XiaoiceID
from services.iot_service import execute_xiaoice_speech
from services.speech_service import save_speech_message


def register_xiaoice_tools(mcp: MCPLambdaHandler):
    """Register all xiaoice Digital Human speech tools with the MCP handler."""

    @mcp.tool()
    def xiaoice_speech(xiaoice_id: XiaoiceID, message: str, presenter_id: str = None) -> str:
        """Command the xiaoice Digital Human to speak a message aloud.

        This tool saves the speech message to DynamoDB for auditing and retrieval,
        then publishes the message to the xiaoice IoT topic so the Digital Human
        can speak it.

        Args:
            xiaoice_id (XiaoiceID): The xiaoice device ID (e.g. xiaoice_1 or all)
            message (str): The text message for xiaoice to speak
            presenter_id (str): Optional presenter ID for context lookup

        Returns:
            str: Confirmation that the speech command was sent.
        """
        # Save to DynamoDB
        saved_item = save_speech_message(
            xiaoice_id=xiaoice_id,
            message=message,
            presenter_id=presenter_id,
        )

        # Publish to IoT
        success = execute_xiaoice_speech(
            xiaoice_id=xiaoice_id,
            message=message,
            presenter_id=presenter_id,
            metadata={"speech_record_id": saved_item.get("id", "")},
        )

        if success:
            return f"Xiaoice ({xiaoice_id}) is now speaking: \"{message}\""
        else:
            return f"Failed to send speech command to xiaoice ({xiaoice_id})."
