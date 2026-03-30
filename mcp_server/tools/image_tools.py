"""Image capture tools for the MCP server."""

import json

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import RobotID
from services.image_service import (
    generate_presigned_get_url,
    generate_presigned_put_url,
    wait_for_image_upload,
)
from services.iot_service import iot_client


def register_image_tools(mcp: MCPLambdaHandler):
    """Register image-related tools with the MCP handler."""

    @mcp.tool()
    def get_image(robot_id: RobotID) -> str:
        """Capture an image from the robot's camera. The robot will take a photo
        and upload it to S3. Returns a presigned URL to view the image, or an
        error message if the robot did not upload in time.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: A presigned URL to view the captured image, or an error message.
        """
        # Handle both enum and plain string input
        rid = robot_id.value if hasattr(robot_id, "value") else str(robot_id)

        # 1. Generate a presigned PUT URL for the robot to upload to
        presigned = generate_presigned_put_url(rid)
        upload_url = presigned["upload_url"]
        object_key = presigned["object_key"]

        # 2. Publish the capture_image command with the upload URL via IoT
        topic = f"{rid}/topic"
        payload = json.dumps({
            "toolName": "capture_image",
            "upload_url": upload_url,
        })
        iot_client.publish(
            topic=topic,
            qos=0,
            retain=False,
            payload=payload.encode("utf-8"),
        )

        # 3. Poll S3 every 0.5s to check if the image was uploaded
        uploaded = wait_for_image_upload(object_key, timeout=15.0, interval=0.5)

        if uploaded:
            read_url = generate_presigned_get_url(object_key)
            return f"Image captured successfully. image_url={read_url}"
        else:
            return "Cannot read image from robot. The robot did not upload the image in time."
