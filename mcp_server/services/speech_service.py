"""
Speech service - Handles saving speech messages to DynamoDB
"""

import time
import uuid

import boto3
from botocore.config import Config
from config import SPEECH_TABLE

# All presenter lookups use a single fixed key
CURRENT_PRESENTER = "current_presenter"

dynamodb = boto3.resource(
    "dynamodb",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


def save_speech_message(
    xiaoice_id: str,
    message: str,
    presenter_id: str = None,
    session_id: str = None,
) -> dict:
    """
    Save a speech message to DynamoDB for retrieval by xiaoice.

    The presenter_id is always normalized to "current_presenter" regardless
    of what value is passed in, so the welcome endpoint can query with a
    single fixed key.

    Args:
        xiaoice_id: The xiaoice device ID (always "xiaoice_1")
        message: The text message to be spoken
        presenter_id: Ignored — always stored as "current_presenter"
        session_id: Optional session ID for conversation tracking

    Returns:
        The saved DynamoDB item
    """
    if not SPEECH_TABLE:
        print("Warning: SpeechTable not configured, skipping DynamoDB save")
        return {}

    table = dynamodb.Table(SPEECH_TABLE)
    item = {
        "id": str(uuid.uuid4()),
        "xiaoice_id": xiaoice_id,
        "message": message,
        "presenter_id": CURRENT_PRESENTER,
        "timestamp": int(time.time() * 1000),
        "status": "pending",
    }
    if session_id:
        item["session_id"] = session_id

    table.put_item(Item=item)
    print(f"Saved speech message to DynamoDB: {item['id']}")
    return item
