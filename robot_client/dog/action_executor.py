"""
Dog Robot Action Executor

Enhanced action executor for dog robots using the new API structure.
Provides queued action execution, parameter handling, and comprehensive
robot control capabilities.
"""

import logging
import queue
import threading
import time
from typing import Any, Dict, Optional, Union
from uuid import uuid4

import requests
from api import DogController
from config import (
    DEFAULT_ACTION_SLEEP_TIME,
    DEFAULT_SPEED,
    HOP_ACTION_SLEEP_TIME,
    STATUS_ACTION_SLEEP_TIME,
    STOP_ACTION_SLEEP_TIME,
    ActionType,
)

logger = logging.getLogger(__name__)

# Dog-specific action configuration dictionary with enhanced parameters
actions: Dict[str, Dict[str, Any]] = {
    # Basic movement actions
    "left": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "left",
        "type": ActionType.MOVEMENT,
        "default_speed": DEFAULT_SPEED,
        "description": "Move robot left",
    },
    "right": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "right",
        "type": ActionType.MOVEMENT,
        "default_speed": DEFAULT_SPEED,
        "description": "Move robot right",
    },
    "forward": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "forward",
        "type": ActionType.MOVEMENT,
        "default_speed": DEFAULT_SPEED,
        "description": "Move robot forward",
    },
    "back": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "back",
        "type": ActionType.MOVEMENT,
        "default_speed": DEFAULT_SPEED,
        "description": "Move robot backward",
    },
    # Rotation actions
    "cw": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "cw",
        "type": ActionType.ROTATION,
        "default_speed": DEFAULT_SPEED,
        "description": "Rotate robot clockwise",
    },
    "ccw": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "ccw",
        "type": ActionType.ROTATION,
        "default_speed": DEFAULT_SPEED,
        "description": "Rotate robot counter-clockwise",
    },
    # Posture actions
    "stand_up": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "stand_up",
        "type": ActionType.POSTURE,
        "default_speed": DEFAULT_SPEED,
        "description": "Make robot stand up",
    },
    "lay_down": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "lay_down",
        "type": ActionType.POSTURE,
        "default_speed": DEFAULT_SPEED,
        "description": "Make robot lay down",
    },
    "hop": {
        "sleep_time": HOP_ACTION_SLEEP_TIME,
        "name": "hop",
        "type": ActionType.SPECIAL,
        "description": "Make robot hop",
    },
    # Status actions
    "activate": {
        "sleep_time": STATUS_ACTION_SLEEP_TIME,
        "name": "activate",
        "type": ActionType.STATUS,
        "description": "Toggle robot activation",
    },
    "walk_mode": {
        "sleep_time": STATUS_ACTION_SLEEP_TIME,
        "name": "walk_mode",
        "type": ActionType.STATUS,
        "description": "Toggle walking mode",
    },
    "dance_mode": {
        "sleep_time": STATUS_ACTION_SLEEP_TIME,
        "name": "dance_mode",
        "type": ActionType.STATUS,
        "description": "Toggle dancing mode",
    },
    "stop": {
        "sleep_time": STOP_ACTION_SLEEP_TIME,
        "name": "stop",
        "type": ActionType.CONTROL,
        "description": "Stop all movement",
    },
    # Advanced actions
    "custom_movement": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "custom_movement",
        "type": ActionType.MOVEMENT,
        "description": "Execute custom movement pattern",
    },
}

# Idle action state
idle_action: Dict[str, Any] = {"name": None, "sleep_time": 0, "type": ActionType.IDLE}


class DogActionExecutor:
    """
    Enhanced action executor for dog robots with improved API integration.

    This class manages a queue of actions to be executed on the dog robot,
    using the new DogController API for better control and error handling.
    """

    def __init__(
        self,
        robot_name: str,
        simulator_endpoint: str = "",
        session_key: str = "",
        robot_ip: str = "127.0.0.1",
        robot_port: int = 8830,
    ) -> None:
        """
        Initialize the DogActionExecutor.

        Args:
            robot_name: Name/ID of the robot
            simulator_endpoint: Optional simulator endpoint for dual control
            session_key: Optional session key for simulator
            robot_ip: IP address of the physical robot
            robot_port: UDP port for robot communication
        """
        self.robot_name = robot_name
        self.simulator_endpoint = simulator_endpoint
        self.session_key = session_key
        self.logger = logging.getLogger(__name__)
        self._walking_mode_enabled = False  # Track walking mode state

        # Initialize dog controller
        try:
            self.dog_controller = DogController(ip=robot_ip, port=robot_port)
            self.logger.info(f"Dog controller initialized for {robot_ip}:{robot_port}")
        except Exception as e:
            self.logger.error(f"Failed to initialize dog controller: {e}")
            self.dog_controller = None

        # Queue and threading setup
        self.action_queue: queue.Queue = queue.Queue()
        self.current_action: Dict[str, Any] = idle_action.copy()
        self.is_running: bool = False
        self._immediate_stop_event = threading.Event()
        self.queue_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Action execution statistics
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "last_action_time": None,
        }

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self.consumer_thread.start()

        self.logger.info(f"DogActionExecutor initialized for robot: {robot_name}")

    def _execute_dog_action(
        self, action_name: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """
        Execute an action using the DogController API.

        Args:
            action_name: Name of the action to execute
            parameters: Optional parameters for the action

        Returns:
            True if action executed successfully, False otherwise
        """
        if not self.dog_controller:
            self.logger.error("Dog controller not available")
            return False

        try:
            from config import (
                DEFAULT_SPEED,
                angle_to_duration,
                distance_to_duration,
                validate_duration,
                validate_speed,
            )

            # Extract and validate parameters
            speed = (
                validate_speed(parameters.get("speed", DEFAULT_SPEED))
                if parameters
                else DEFAULT_SPEED
            )
            duration = parameters.get("duration") if parameters else None
            distance = parameters.get("distance") if parameters else None
            angle = parameters.get("angle") if parameters else None

            # Convert distance/angle to duration if not specified
            if distance and not duration:
                duration = distance_to_duration(distance)
            elif angle and not duration:
                duration = angle_to_duration(angle)

            if duration:
                duration = validate_duration(duration)

            # Handle walking mode for movement actions
            if action_name in ["forward", "back", "left", "right", "cw", "ccw"]:
                if not self._walking_mode_enabled:
                    self.logger.info(
                        "Walking mode is not enabled, enabling it permanently..."
                    )
                    self.dog_controller.enable_walking()
                    time.sleep(2)  # Allow time for walking mode to activate
                    self._walking_mode_enabled = True
                    self.logger.info(
                        "Walking mode enabled permanently for movement actions"
                    )

            self.logger.info(
                f"Executing dog action: {action_name} with speed={speed}, duration={duration}, parameters={parameters}"
            )
            # Execute action based on type
            if action_name == "forward":
                self.dog_controller.movement.move_forward(
                    speed=speed, duration=duration
                )
            elif action_name == "back":
                self.dog_controller.movement.move_backward(
                    speed=speed, duration=duration
                )
            elif action_name == "left":
                self.dog_controller.movement.move_left(speed=speed, duration=duration)
            elif action_name == "right":
                self.dog_controller.movement.move_right(speed=speed, duration=duration)
            elif action_name == "cw":
                self.dog_controller.movement.rotate_right(
                    speed=speed, duration=duration
                )
            elif action_name == "ccw":
                self.dog_controller.movement.rotate_left(speed=speed, duration=duration)
            elif action_name == "stand_up":
                self.dog_controller.movement.stand_up(speed=speed)
            elif action_name == "lay_down":
                self.dog_controller.movement.lay_down(speed=speed)
            elif action_name == "hop":
                hop_duration = duration if duration else 1.0
                self.dog_controller.movement.hop(duration=hop_duration)
            elif action_name == "activate":
                self.dog_controller.activate()
            elif action_name == "walk_mode":
                self._walking_mode_enabled = not self._walking_mode_enabled
                self.dog_controller.enable_walking()
            elif action_name == "dance_mode":
                self.dog_controller.enable_dancing()
            elif action_name == "stop":
                self.dog_controller.stop_all()
                if self._walking_mode_enabled:
                    self.dog_controller.enable_walking()
                self._walking_mode_enabled = False
            elif action_name == "custom_movement":
                # Handle custom movement with multiple parameters
                lx = parameters.get("lx", 0.0)
                ly = parameters.get("ly", 0.0)
                rx = parameters.get("rx", 0.0)
                ry = parameters.get("ry", 0.0)
                dpadx = parameters.get("dpadx", 0.0)
                dpady = parameters.get("dpady", 0.0)
                self.dog_controller.movement.custom_movement(
                    lx=lx,
                    ly=ly,
                    rx=rx,
                    ry=ry,
                    dpadx=dpadx,
                    dpady=dpady,
                    duration=duration,
                )
            else:
                self.logger.error(f"Unknown action: {action_name}")
                return False

            self.logger.info(f"Dog action '{action_name}' executed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error executing dog action '{action_name}': {e}")
            return False

    def _stop_dog_action(self) -> bool:
        """
        Stop current dog action.

        Returns:
            True if stop was successful, False otherwise
        """
        if not self.dog_controller:
            return False

        try:
            self.dog_controller.stop_all()
            self.logger.info("Dog action stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping dog action: {e}")
            return False

    def _execute_action(self, action_item: Dict[str, Any]) -> None:
        """
        Execute a single action from the queue.

        Args:
            action_item: Dictionary containing action details and parameters
        """
        action_name = action_item["name"]
        action_config = actions[action_name]

        # Update current action status
        self.current_action = {
            "name": action_config["name"],
            "sleep_time": action_config["sleep_time"],
            "type": action_config["type"],
            "start_time": time.time(),
        }

        success = False
        try:
            # Update statistics
            self.execution_stats["total_actions"] += 1
            self.execution_stats["last_action_time"] = time.time()

            # Get parameters from action item
            parameters = action_item.get("parameters", {})

            # Execute the action using dog controller
            success = self._execute_dog_action(action_name, parameters)

            # Also send to simulator if configured
            if self.simulator_endpoint and success:
                self._send_to_simulator(action_name)

            if success:
                self.execution_stats["successful_actions"] += 1
            else:
                self.execution_stats["failed_actions"] += 1

            # Wait for action completion with interrupt capability
            sleep_time = action_config["sleep_time"]

            # Override sleep time if duration is specified in parameters
            if "duration" in parameters:
                sleep_time = parameters["duration"]

            elapsed = 0.0
            while elapsed < sleep_time:
                if self._immediate_stop_event.is_set():
                    self.logger.info(f"Stopping action execution for {action_name}")
                    self._immediate_stop_event.clear()
                    self._stop_dog_action()
                    break
                time.sleep(0.1)
                elapsed += 0.1

        except Exception as e:
            self.logger.error(f"Error executing action {action_name}: {e}")
            self.execution_stats["failed_actions"] += 1
        finally:
            # Clean up
            self._remove_action_by_id(action_item["id"])
            self.current_action = idle_action.copy()

            # Log execution result
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"Action {action_name} completed: {status}")

    def _remove_action_by_id(self, action_id: str) -> None:
        """Remove an action from the queue by its ID."""
        with self.queue_lock:
            temp_list = list(self.action_queue.queue)
            filtered = [item for item in temp_list if item["id"] != action_id]
            self._replace_queue(filtered)

    def _replace_queue(self, items: list) -> None:
        """Replace the current queue with a new list of items."""
        self.action_queue.queue.clear()
        for item in items:
            self.action_queue.put(item)

    def _consumer(self) -> None:
        """
        Continuously consume actions from the queue and execute them.

        This method runs in a separate thread and processes actions sequentially.
        """
        self.logger.info("Action consumer thread started")

        # Align to 5-second boundary for consistent timing
        time.sleep(5 - time.time() % 5)

        while not self._stop_event.is_set():
            try:
                # Check for immediate stop
                if self._immediate_stop_event.is_set():
                    self.logger.info(
                        "Immediate stop triggered, clearing queue and setting to idle"
                    )
                    self.clear_action_queue()
                    self.current_action = idle_action.copy()
                    self.is_running = False
                    self._immediate_stop_event.clear()
                    time.sleep(0.5)
                    continue

                # Align to 1-second boundary for consistent timing
                time.sleep(1 - time.time() % 1)

                # Try to get an action from the queue
                try:
                    action_item = self.action_queue.get(timeout=1)
                    self.is_running = True
                    self._execute_action(action_item)
                    time.sleep(0.5)  # Brief pause between actions
                except queue.Empty:
                    self.is_running = False
                    time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Error in consumer thread: {e}")
                self.is_running = False
                time.sleep(1)

        self.logger.info("Action consumer thread stopped")

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns:
            Dictionary containing execution statistics
        """
        stats = self.execution_stats.copy()
        if stats["total_actions"] > 0:
            stats["success_rate"] = (
                stats["successful_actions"] / stats["total_actions"]
            ) * 100
        else:
            stats["success_rate"] = 0.0
        return stats

    def get_available_actions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available actions with their configurations.

        Returns:
            Dictionary of available actions and their configurations
        """
        return actions.copy()

    def add_action_to_queue(
        self, action_name: str, parameters: Dict[str, Any] = None
    ) -> str:
        """
        Add a new action to the queue.

        Args:
            action_name: Name of the action to execute
            parameters: Optional parameters for the action

        Returns:
            Action ID for tracking purposes
        """
        action_id = str(uuid4())

        # Handle special stop action
        if action_name == "stop":
            self.stop()
            return action_id

        # Validate action name
        if action_name not in actions:
            available_actions = list(actions.keys())
            self.logger.error(
                f"Action '{action_name}' not found. Available actions: {available_actions}"
            )
            raise ValueError(f"Unknown action: {action_name}")

        # Validate and process parameters
        processed_parameters = self._process_parameters(action_name, parameters or {})

        with self.queue_lock:
            action_item = {
                "id": action_id,
                "name": action_name,
                "parameters": processed_parameters,
                "timestamp": time.time(),
                "type": actions[action_name]["type"],
            }

            self.action_queue.put(action_item)

        self.logger.info(f"Action '{action_name}' added to queue with ID: {action_id}")
        return action_id

    def _process_parameters(
        self, action_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and validate parameters for an action.

        Args:
            action_name: Name of the action
            parameters: Raw parameters

        Returns:
            Processed and validated parameters
        """
        processed = parameters.copy()
        action_config = actions[action_name]

        # Set default speed if not provided
        if "speed" not in processed and "default_speed" in action_config:
            processed["speed"] = action_config["default_speed"]

        # Validate speed parameter
        if "speed" in processed:
            processed["speed"] = max(0.1, min(1.0, float(processed["speed"])))

        # Validate duration parameter
        if "duration" in processed:
            processed["duration"] = max(0.1, float(processed["duration"]))

        # Handle distance parameter for movement actions
        if "distance" in processed and action_config["type"] == "movement":
            distance = abs(float(processed["distance"]))
            processed["distance"] = distance
            # Convert distance to duration if not specified
            if "duration" not in processed:
                processed["duration"] = min(5.0, max(0.5, distance / 50.0))

        # Handle angle parameter for rotation actions
        if "angle" in processed and action_config["type"] == "rotation":
            angle = abs(float(processed["angle"]))
            processed["angle"] = angle
            # Convert angle to duration if not specified
            if "duration" not in processed:
                processed["duration"] = min(5.0, max(0.5, angle / 90.0))

        return processed

    def remove_action_from_queue(self, action_id: str) -> None:
        """Remove an action from the queue by its ID."""
        self._remove_action_by_id(action_id)

    def clear_action_queue(self) -> None:
        """Clear all actions from the queue."""
        with self.queue_lock:
            self.action_queue.queue.clear()

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the action queue.

        Returns:
            Dictionary containing queue status information
        """
        with self.queue_lock:
            queue_items = list(self.action_queue.queue)

        return {
            "queue": queue_items,
            "queue_size": len(queue_items),
            "current_action": self.current_action,
            "is_running": self.is_running,
            "robot_status": (
                self.dog_controller.get_status() if self.dog_controller else None
            ),
            "execution_stats": self.get_execution_stats(),
        }

    def stop(self) -> None:
        """
        Stop all actions immediately and clear the queue.

        This method triggers an immediate stop of the current action
        and clears all pending actions from the queue while preserving walking mode.
        """
        self.logger.info(
            "Immediate stop requested: clearing queue and interrupting current action"
        )
        self._immediate_stop_event.set()
        self.clear_action_queue()

        # Also stop the dog controller if available
        if self.dog_controller:
            try:
                # Remember walking mode state
                was_walking = self._walking_mode_enabled
                self.dog_controller.emergency_stop()
                # Restore walking mode if it was enabled
                if was_walking:
                    self.dog_controller.enable_walking()
                    self._walking_mode_enabled = True
            except Exception as e:
                self.logger.error(f"Error during emergency stop: {e}")

    def shutdown(self) -> None:
        """
        Gracefully shutdown the action executor.

        This method stops the consumer thread and cleans up resources.
        """
        self.logger.info("Shutting down action executor...")

        # Stop the consumer thread
        self._stop_event.set()

        # Clear any remaining actions
        self.clear_action_queue()

        # Stop current action
        self.stop()

        # Wait for consumer thread to finish
        if self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
            if self.consumer_thread.is_alive():
                self.logger.warning("Consumer thread did not shut down gracefully")

        self.logger.info("Action executor shutdown complete")

    def pause_execution(self) -> None:
        """Pause action execution without clearing the queue."""
        self._immediate_stop_event.set()
        self.logger.info("Action execution paused")

    def resume_execution(self) -> None:
        """Resume action execution."""
        self._immediate_stop_event.clear()
        self.logger.info("Action execution resumed")

    def _send_to_simulator(
        self,
        action_name: str,
        parameters: Dict[str, Any] = None,
        log_success_msg: str = None,
        log_error_msg: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send an action command to the robot simulator (optional dual control).

        Args:
            action_name: The name of the action to execute
            parameters: Optional action parameters
            log_success_msg: Message to log on successful API call
            log_error_msg: Message to log on failed API call

        Returns:
            Optional response data from the simulator API call
        """
        if not self.simulator_endpoint:
            return None

        if log_success_msg is None:
            log_success_msg = (
                f"Simulator action {action_name} for robot {self.robot_name} successful"
            )
        if log_error_msg is None:
            log_error_msg = f"Error sending action {action_name} to simulator for robot {self.robot_name}"

        # Construct the URL
        url = f"{self.simulator_endpoint}/run_action/{self.robot_name}"
        if self.session_key:
            url += f"?session_key={self.session_key}"

        # Prepare the payload
        payload = {"action": action_name}
        if parameters:
            payload["parameters"] = parameters

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=3.0,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            resp_json = response.json()
            self.logger.info(
                f"{self.robot_name} - {log_success_msg}. Response: {resp_json}"
            )
            return resp_json
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{log_error_msg}: {e}")
            return None


# Legacy compatibility - alias for backward compatibility
ActionExecutor = DogActionExecutor
