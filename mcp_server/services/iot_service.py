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
    # Resolve enum to its raw string value if needed
    selected_robot = selected_robot.value if hasattr(selected_robot, "value") else str(selected_robot)

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
    """Execute a drone action by publishing to the appropriate IoT topic"""

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


def execute_xiaoice_speech(xiaoice_id: str, message: str, presenter_id: str = None, metadata: Dict = None) -> bool:
    """Execute a xiaoice speech action by publishing to the appropriate IoT topic.
    
    The xiaoice Digital Human will receive the message and speak it aloud.
    """
    # Resolve enum to its raw string value so the IoT topic is correct
    # (e.g. "xiaoice_1" instead of "XiaoiceID.XIAOICE_1")
    xiaoice_id_str = xiaoice_id.value if hasattr(xiaoice_id, "value") else str(xiaoice_id)

    payload = {
        "action": "speech",
        "message": message,
    }
    if presenter_id:
        payload["presenterId"] = presenter_id
    if metadata:
        payload["metadata"] = metadata

    payload_json = json.dumps(payload)

    if xiaoice_id_str == "all":
        def publish_to_xiaoice(num):
            topic = f"xiaoice_{num}/topic"
            try:
                iot_client.publish(
                    topic=topic,
                    qos=0,
                    retain=False,
                    payload=bytes(payload_json, "utf-8"),
                )
                print(f"Published to {topic}: {payload_json}")
                return True
            except Exception as e:
                print(f"Error publishing to {topic}: {e}")
                return False

        with ThreadPoolExecutor() as executor:
            futures = list(executor.map(publish_to_xiaoice, range(1, 2)))
            return all(futures)
    else:
        topic = f"{xiaoice_id_str}/topic"
        try:
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(payload_json, "utf-8"),
            )
            print(f"Published to {topic}: {payload_json}")
            return True
        except Exception as e:
            print(f"Error publishing to {topic}: {e}")
            return False


def execute_dog_action(message: Dict) -> bool:
    """Execute a dog action by publishing to the appropriate IoT topic"""

    dog_id = message.get("dogID", "dog_1")
    # Resolve enum to its raw string value if needed
    dog_id = dog_id.value if hasattr(dog_id, "value") else str(dog_id)
    message_json = json.dumps(message)

    if dog_id == "all":
        # If 'all' is selected, publish to all dogs
        def publish_to_dog(dog_num):
            topic = f"dog_{dog_num}/topic"
            try:
                iot_client.publish(
                    topic=topic,
                    qos=0,
                    retain=False,
                    payload=bytes(message_json, "utf-8"),
                )
                print(f"Published to {topic}: {message_json}")
                return True
            except Exception as e:
                print(f"Error publishing to {topic}: {e}")
                return False

        with ThreadPoolExecutor() as executor:
            futures = list(executor.map(publish_to_dog, range(1, 3)))  # dog_1, dog_2
            return all(futures)
    else:
        topic = f"{dog_id}/topic"
        try:
            iot_client.publish(
                topic=topic,
                qos=0,
                retain=False,
                payload=bytes(message_json, "utf-8"),
            )
            print(f"Published to {topic}: {message_json}")
            return True
        except Exception as e:
            print(f"Error publishing to {topic}: {e}")
            return False
