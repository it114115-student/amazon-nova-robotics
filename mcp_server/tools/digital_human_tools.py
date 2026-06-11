"""Digital Human speech tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from services.iot_service import execute_xiaoice_speech
from services.speech_service import save_speech_message

# Only one digital human device exists
DIGITAL_HUMAN_ID = "xiaoice_1"
# All presenter lookups use a single fixed key
CURRENT_PRESENTER = "current_presenter"


def execute_digital_human_speech(message: str) -> str:
    """Make the digital human speak a message aloud.
    Saves to DynamoDB and publishes to IoT Core.
    """
    if not message or not message.strip():
        return "Error: message cannot be empty."

    # Save to DynamoDB with fixed presenter key
    saved_item = save_speech_message(
        xiaoice_id=DIGITAL_HUMAN_ID,
        message=message.strip(),
        presenter_id=CURRENT_PRESENTER,
    )

    # Publish to IoT
    success = execute_xiaoice_speech(
        xiaoice_id=DIGITAL_HUMAN_ID,
        message=message.strip(),
        presenter_id=CURRENT_PRESENTER,
        metadata={"speech_record_id": saved_item.get("id", "")},
    )

    if success:
        return f'Digital Human is now speaking: "{message.strip()}"'
    else:
        return "Failed to send speech command to Digital Human."


def register_digital_human_tools(mcp: MCPLambdaHandler):
    """Register all Digital Human speech tools with the MCP handler."""

    @mcp.tool()
    def digital_human_speech(message: str) -> str:
        """Command the Digital Human to speak a message aloud.

        This tool saves the speech message to DynamoDB for retrieval,
        then publishes the message to the digital human IoT topic so the
        Digital Human can speak it.

        Args:
            message (str): The text message for the Digital Human to speak

        Returns:
            str: Confirmation that the speech command was sent.
        """
        return execute_digital_human_speech(message)
