"""Digital Human speech tools for the MCP server."""

import os
import requests
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

    # Synthesize with Amazon Polly
    polly_result = None
    try:
        from services.polly_service import synthesize_and_upload
        polly_result = synthesize_and_upload(text=message.strip(), language="en")
    except Exception as e:
        print(f"Warning: Polly synthesis failed for digital human: {e}")

    # Broadcast to simulator endpoint via REST API to trigger WebSocket speaking animation
    simulator_endpoint = os.environ.get("SIMULATOR_ENDPOINT", "").strip()
    if simulator_endpoint:
        clean_endpoint = simulator_endpoint
        if "://" in clean_endpoint:
            clean_endpoint = clean_endpoint.split("://", 1)[1]
        clean_endpoint = clean_endpoint.rstrip("/")
        
        url = f"https://{clean_endpoint}/api/digital-human/speak?session_key=mcpserver"
        try:
            payload = {
                "message": message.strip()
            }
            if polly_result and polly_result.get("url"):
                payload["audio_url"] = polly_result["url"]
                
            response = requests.post(url, json=payload, timeout=3.0)
            if response.status_code != 200:
                print(f"Warning: Failed to broadcast to simulator endpoint. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"Warning: Exception while calling simulator endpoint speech broadcast: {e}")

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
