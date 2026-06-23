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

    Args:
        presenter_id: Optional presenter ID to filter by. Defaults to "current_presenter"

    Returns:
        The speech message item dict, or None if not found
    """
    if not SPEECH_TABLE:
        logger.debug("SpeechTable not configured, skipping speech lookup")
        return None

    try:
        table = dynamodb.Table(SPEECH_TABLE)

        target_presenter = presenter_id if presenter_id else CURRENT_PRESENTER

        # Filter by status and presenter_id
        filter_expr = Attr("status").eq("pending") & Attr("presenter_id").eq(
            target_presenter
        )

        response = table.scan(FilterExpression=filter_expr)
        items = response.get("Items", [])

        if not items:
            return None

        # Robust helper to extract timestamp safely as integer for sorting and filtering
        def get_timestamp_val(x):
            ts = x.get("timestamp", 0)
            if ts is None:
                return 0
            try:
                return int(ts)
            except (ValueError, TypeError):
                try:
                    return int(float(ts))
                except (ValueError, TypeError):
                    return 0

        # Filter out items that are older than 5 minutes (300,000 milliseconds)
        import time
        current_time_ms = int(time.time() * 1000)
        valid_items = [
            item for item in items
            if (current_time_ms - get_timestamp_val(item)) <= 300000
        ]

        if not valid_items:
            logger.info("Scanned speech messages were found, but all have expired (> 5 minutes old)")
            return None

        # Return the most recent message by timestamp from the valid ones
        valid_items.sort(key=get_timestamp_val, reverse=True)
        return valid_items[0]

    except Exception as e:
        logger.error(f"Error fetching speech message: {e}", exc_info=True)
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
