"""Xiaoice Digital Human speech tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from services.iot_service import execute_xiaoice_speech
from services.speech_service import save_speech_message

# Only one xiaoice device exists
XIAOICE_ID = "xiaoice_1"
# All presenter lookups use a single fixed key
CURRENT_PRESENTER = "current_presenter"


def register_xiaoice_tools(mcp: MCPLambdaHandler):
    """Register all xiaoice Digital Human speech tools with the MCP handler."""

    @mcp.tool()
    def xiaoice_speech(message: str) -> str:
        """Command the xiaoice Digital Human to speak a message aloud.

        This tool saves the speech message to DynamoDB for retrieval,
        then publishes the message to the xiaoice IoT topic so the
        Digital Human can speak it.

        There is only one xiaoice device (xiaoice_1). The message is
        automatically saved under the presenter key "current_presenter"
        so the welcome endpoint can retrieve it.

        Args:
            message (str): The text message for xiaoice to speak

        Returns:
            str: Confirmation that the speech command was sent.
        """
        # Save to DynamoDB with fixed presenter key
        saved_item = save_speech_message(
            xiaoice_id=XIAOICE_ID,
            message=message,
            presenter_id=CURRENT_PRESENTER,
        )

        # Publish to IoT
        success = execute_xiaoice_speech(
            xiaoice_id=XIAOICE_ID,
            message=message,
            presenter_id=CURRENT_PRESENTER,
            metadata={"speech_record_id": saved_item.get("id", "")},
        )

        if success:
            return f'Xiaoice is now speaking: "{message}"'
        else:
            return f"Failed to send speech command to xiaoice."
