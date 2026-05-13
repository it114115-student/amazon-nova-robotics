"""
Robot service - Handles robot action execution
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import requests
import boto3
from botocore.config import Config

# Initialize AWS clients with retry configuration
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)

# Get simulator endpoint from environment variable
SIMULATOR_ENDPOINT = os.getenv("SIMULATOR_ENDPOINT", "")


def _send_to_simulator(
    robot_name: str,
    action_name: str = None,
    audio_url: str = None,
    text: str = None,
    duration: float = 0.0,
) -> bool:
    """Send an action or speech command to the 3D simulator for browser playback."""
    if not SIMULATOR_ENDPOINT:
        print("SIMULATOR_ENDPOINT not configured, skipping simulator call")
        return False

    try:
        if action_name is not None:
            # Robot action: POST /run_action/{robot_name}
            url = f"https://{SIMULATOR_ENDPOINT}/run_action/{robot_name}?session_key=mcpserver"
            payload = {"action": action_name}
        else:
            # Speech: POST /speech/{robot_name}
            url = f"https://{SIMULATOR_ENDPOINT}/speech/{robot_name}?session_key=mcpserver"
            payload = {
                "audio_url": audio_url or "",
                "text": text or "",
                "duration": duration,
            }

        resp = requests.post(
            url,
            json=payload,
            timeout=3.0,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        print(f"Simulator call successful [{robot_name}]: {resp.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to send to simulator [{robot_name}]: {e}")
        return False


def execute_robot_action(message: str, selected_robot: str, parameters: Dict = None) -> bool:
    """Execute a robot action by publishing to the appropriate IoT topic.

    Also sends the action to the 3D simulator if SIMULATOR_ENDPOINT is configured.
    """
    # Resolve enum to its raw string value if needed
    selected_robot = (
        selected_robot.value
        if hasattr(selected_robot, "value")
        else str(selected_robot)
    )

    # Determine payload and simulator arguments
    if message == "speech" and parameters:
        payload = {
            "action": "speech",
            "audio_url": parameters.get("audio_url"),
            "text": parameters.get("text"),
            "duration": parameters.get("duration", 0.0),
        }
        audio_url = parameters.get("audio_url")
        text = parameters.get("text")
        duration = parameters.get("duration", 0.0)
        sim_action = None
    else:
        payload = {"toolName": message}
        audio_url = None
        text = None
        duration = 0.0
        sim_action = message

    payload_json = json.dumps(payload)

    if selected_robot == "all":
        # If 'all' is selected, publish to all robots 1-7
        def publish_to_robot(robot_id):
            robot_name = f"robot_{robot_id}"
            topic = f"{robot_name}/topic"
            try:
                iot_client.publish(
                    topic=topic,
                    qos=0,
                    retain=False,
                    payload=payload_json.encode("utf-8"),
                )
                print(f"Published to {topic}: {payload_json}")

                # Send to simulator if endpoint is configured
                _send_to_simulator(
                    robot_name,
                    action_name=sim_action,
                    audio_url=audio_url,
                    text=text,
                    duration=duration,
                )

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
                payload=payload_json.encode("utf-8"),
            )
            print(f"Published to {topic}: {payload_json}")

            # Send to simulator if endpoint is configured
            _send_to_simulator(
                selected_robot,
                action_name=sim_action,
                audio_url=audio_url,
                text=text,
                duration=duration,
            )

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


def execute_xiaoice_speech(
    xiaoice_id: str,
    message: str,
    presenter_id: str = None,
    metadata: Dict = None,
) -> bool:
    """Execute a xiaoice speech action by publishing to the appropriate IoT topic.

    The xiaoice Digital Human will receive the message and speak it aloud.
    """
    # Resolve enum to its raw string value so the IoT topic is correct
    # (e.g. "xiaoice_1" instead of "XiaoiceID.XIAOICE_1")
    xiaoice_id_str = (
        xiaoice_id.value if hasattr(xiaoice_id, "value") else str(xiaoice_id)
    )

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
