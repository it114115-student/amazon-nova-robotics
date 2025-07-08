"""
Robot service - Handles robot action execution
"""

from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import Any, Dict, List

import boto3
from botocore.config import Config
from models.actions import ACTIONS

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


def process_actions(
    actions_to_execute: List[str], selected_robot: str
) -> List[Dict[str, Any]]:
    """Process a list of actions sequentially"""
    results = []

    for action in actions_to_execute:
        if action in ACTIONS:
            success = execute_robot_action(action, selected_robot)
            results.append(
                {"action": action, "success": success, "name": ACTIONS[action]["name"]}
            )
            sleep(0.1)
        # else:
        #     results.append(
        #         {"action": action, "success": False, "error": "Invalid action"}
        #     )
    print(f"results: {results}")
    return results
