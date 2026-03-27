"""Dog Skill - Publish actions to Raspberry Pi dog controllers via AWS IoT"""

import argparse
import json
import logging
import re
import sys

import boto3
from botocore.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEVICE_PREFIXES = ["robot", "drone", "dog"]


def camel_to_snake(text):
    text = text.lstrip("_")
    return re.sub(r"([A-Z])", r"_\1", text).lower().lstrip("_")


def has_other_device_prefix(message, target):
    for prefix in DEVICE_PREFIXES:
        if prefix != target and message.lower().startswith(prefix.lower()):
            if len(message) == len(prefix) or (
                len(message) > len(prefix) and message[len(prefix)].isupper()
            ):
                return True
    return False


def remove_prefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else None


def publish(profile, robot_id, action, parameters=None, region="us-east-1"):
    if has_other_device_prefix(action, "dog"):
        logger.info("Skipping action '%s' for %s - wrong device type", action, robot_id)
        return True

    processed = remove_prefix(action, "dog")
    processed = camel_to_snake(processed if processed is not None else action)

    data = {"dogID": robot_id.lower(), "action": processed, "parameters": parameters or {}}

    session = boto3.Session(profile_name=profile, region_name=region)
    client = session.client("iot-data", config=Config(retries={"max_attempts": 3, "mode": "standard"}))

    topic = f"{robot_id}/topic"
    try:
        client.publish(topic=topic, qos=0, retain=False, payload=bytes(json.dumps(data), "utf-8"))
        logger.info("Published to %s: %s", topic, data)
        return True
    except Exception as e:
        logger.error("Error publishing to %s: %s", topic, e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Dog Skill")
    parser.add_argument("--profile", default="default", help="AWS CLI profile name (default: 'default')")
    parser.add_argument("--robot-id", required=True, help="Dog ID (e.g. dog_1)")
    parser.add_argument("--action", required=True, help="Action to execute")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    success = publish(args.profile, args.robot_id, args.action, region=args.region)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
