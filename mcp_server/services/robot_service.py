"""
Robot service - Handles robot action execution
"""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import boto3
from botocore.config import Config

# Initialize AWS clients with retry configuration
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


def execute_robot_action(message: str, selected_robot: str) -> bool:
    """Execute a robot action by publishing to the appropriate IoT topic"""
    if selected_robot == "all":
        # If 'all' is selected, publish to all robots 1-7
        def publish_to_robot(robot_id):
            topic = f"robot_{robot_id}/topic"
            try:
                iot_client.publish(
                    topic=topic,
                    qos=0,
                    retain=False,
                    payload=bytes(f'{{ "toolName": "{message}" }}', "utf-8"),
                )
                print(f"Published to {topic}: {message}")
                return True
            except Exception as e:
                print(f"Error publishing to {topic}: {e}")
                return False

        with ThreadPoolExecutor() as executor:
            futures = list(executor.map(publish_to_robot, range(1, 10)))
            return all(futures)
    else:
        topic = f"{selected_robot}/topic"
        try:
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(f'{{ "toolName": "{message}" }}', "utf-8"),
            )
            print(f"Published to {topic}: {message}")
            return True
        except Exception as e:
            print(f"Error publishing to {topic}: {e}")
            return False


def execute_drone_action(message: Dict) -> bool:
    """Execute a robot action by publishing to the appropriate IoT topic"""

    message = json.dumps(message)

    topic = "drone_1/topic"
    try:
        iot_client.publish(
            topic=topic,
            qos=0,
            retain=False,
            payload=bytes(message, "utf-8"),
        )
        print(f"Published to {topic}: {message}")
        return True
    except Exception as e:
        print(f"Error publishing to {topic}: {e}")
        return False
