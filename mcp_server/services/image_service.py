"""Image service - Handles S3 presigned URL generation and image upload verification."""

import os
import time
import uuid
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

s3_client = boto3.client(
    "s3",
    config=Config(
        retries={"max_attempts": 3, "mode": "standard"},
        signature_version="s3v4"
    ),
)

MEDIA_BUCKET_NAME = os.environ.get("MEDIA_BUCKET_NAME", "")
PRESIGNED_URL_EXPIRY = 300  # 5 minutes


def generate_presigned_put_url(robot_id: str) -> dict:
    """Generate a presigned PUT URL for the robot to upload a captured image.

    Returns dict with 'upload_url' and 'object_key'.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    object_key = f"robot-images/{robot_id}/{robot_id}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
    upload_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": MEDIA_BUCKET_NAME,
            "Key": object_key,
            "ContentType": "image/jpeg",
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )
    return {"upload_url": upload_url, "object_key": object_key}


def generate_presigned_get_url(object_key: str) -> str:
    """Generate a presigned GET URL to read an uploaded image."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": MEDIA_BUCKET_NAME, "Key": object_key},
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )


def wait_for_image_upload(
    object_key: str, timeout: float = 15.0, interval: float = 0.5
) -> bool:
    """Poll S3 to check if the image has been uploaded.

    Args:
        object_key: The S3 object key to check.
        timeout: Maximum seconds to wait.
        interval: Seconds between each poll.

    Returns:
        True if the object exists within the timeout, False otherwise.
    """
    elapsed = 0.0
    while elapsed < timeout:
        try:
            s3_client.head_object(Bucket=MEDIA_BUCKET_NAME, Key=object_key)
            return True
        except ClientError as e:
            # 404 means not uploaded yet, anything else is a real error
            if e.response["Error"]["Code"] == "404":
                time.sleep(interval)
                elapsed += interval
            else:
                raise
    return False

def copy_to_latest(object_key: str, robot_id: str) -> None:
    """Copy the newly uploaded image to a 'latest.jpg' key for easier querying."""
    latest_key = f"robot-images/{robot_id}/latest.jpg"
    try:
        s3_client.copy_object(
            Bucket=MEDIA_BUCKET_NAME,
            CopySource={"Bucket": MEDIA_BUCKET_NAME, "Key": object_key},
            Key=latest_key,
        )
    except ClientError as e:
        print(f"Failed to copy image to latest: {e}")
