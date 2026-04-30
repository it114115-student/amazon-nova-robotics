"""
Speech database service - Fetches and deletes pending speech messages from DynamoDB
"""

import logging

import boto3
from boto3.dynamodb.conditions import Attr
from config import SPEECH_TABLE

logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")

# Fixed presenter key — matches what the MCP server saves
CURRENT_PRESENTER = "current_presenter"


def get_pending_speech_message(presenter_id: str = None):
    """
    Get the latest pending speech message from the SpeechTable.

    The presenter_id parameter is accepted for interface compatibility but
    the query always uses "current_presenter" as the lookup key, since all
    speech messages are saved under that fixed key.

    Args:
        presenter_id: Ignored — always queries "current_presenter"

    Returns:
        The speech message item dict, or None if not found
    """
    if not SPEECH_TABLE:
        logger.debug("SpeechTable not configured, skipping speech lookup")
        return None

    try:
        table = dynamodb.Table(SPEECH_TABLE)

        # Always query with the fixed presenter key
        filter_expr = Attr("status").eq("pending") & Attr("presenter_id").eq(
            CURRENT_PRESENTER
        )

        response = table.scan(FilterExpression=filter_expr)
        items = response.get("Items", [])

        if not items:
            return None

        # Return the most recent message by timestamp
        items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return items[0]

    except Exception as e:
        logger.error(f"Error fetching speech message: {e}")
        return None


def delete_speech_message(message_id: str):
    """
    Delete a speech message from the SpeechTable by its id.

    Args:
        message_id: The partition key (id) of the message to delete
    """
    if not SPEECH_TABLE or not message_id:
        return

    try:
        table = dynamodb.Table(SPEECH_TABLE)
        table.delete_item(Key={"id": message_id})
        logger.info(f"Deleted speech message: {message_id}")
    except Exception as e:
        logger.error(f"Error deleting speech message {message_id}: {e}")
