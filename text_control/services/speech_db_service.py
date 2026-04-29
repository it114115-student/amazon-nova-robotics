"""
Speech database service - Fetches and deletes pending speech messages from DynamoDB
"""

import logging

import boto3
from boto3.dynamodb.conditions import Attr
from config import SPEECH_TABLE

logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")


def get_pending_speech_message(presenter_id: str = None):
    """
    Get the latest pending speech message for a presenter from the SpeechTable.

    Scans for items with status='pending' matching the presenter_id,
    returns the most recent one by timestamp.

    Args:
        presenter_id: The presenter ID to look up

    Returns:
        The speech message item dict, or None if not found
    """
    if not SPEECH_TABLE:
        logger.debug("SpeechTable not configured, skipping speech lookup")
        return None

    if not presenter_id:
        return None

    try:
        table = dynamodb.Table(SPEECH_TABLE)

        # Scan with filter for pending messages matching this presenter
        filter_expr = Attr("status").eq("pending") & Attr("presenter_id").eq(
            presenter_id
        )

        response = table.scan(FilterExpression=filter_expr)
        items = response.get("Items", [])

        if not items:
            return None

        # Return the most recent message by timestamp
        items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return items[0]

    except Exception as e:
        logger.error(f"Error fetching speech message for {presenter_id}: {e}")
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
