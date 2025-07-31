import logging
import queue
import threading
import time
from typing import Any, Dict, Optional
from uuid import uuid4

import requests

logger = logging.getLogger(__name__)

# Dog-specific action configuration dictionary - only movement and rotation actions
actions: Dict[str, Dict[str, Any]] = {
    # Movement actions for dogs (matching MCP server actions)
    "left": {"sleep_time": 2.0, "action": ["0", "50"], "name": "left"},
    "right": {"sleep_time": 2.0, "action": ["0", "-50"], "name": "right"},
    "forward": {"sleep_time": 2.0, "action": ["50", "0"], "name": "forward"},
    "back": {"sleep_time": 2.0, "action": ["-50", "0"], "name": "back"},
    
    # Rotation actions for dogs (matching MCP server actions)
    "cw": {"sleep_time": 2.0, "action": ["0", "90"], "name": "cw"},
    "ccw": {"sleep_time": 2.0, "action": ["0", "-90"], "name": "ccw"},
}

# 空閒動作 (Idle action)
idle_action: Dict[str, Any] = {"name": None, "sleep_time": 0}


class ActionExecutor:

    def __init__(
        self, robot_name: str, simulator_endpoint: str, session_key: str
    ) -> None:
        """Initialize the ActionExecutor with a queue and a consumer thread."""
        self.robot_name = robot_name
        self.simulator_endpoint = simulator_endpoint
        self.session_key = session_key
        self.logger = logging.getLogger(__name__)
        self.action_queue: queue.Queue = queue.Queue()
        self.current_action: Dict[str, Any] = idle_action.copy()
        self.is_running: bool = False
        self._immediate_stop_event = threading.Event()
        self.queue_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.movement_parameters: Dict[str, Any] = {}  # Store dynamic parameters
        self.consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self.consumer_thread.start()

    def _run_action(
        self, action_name: str, p1: str, p2: str
    ) -> Optional[Dict[str, Any]]:
        """Send a request to execute an action."""

        self._send_to_simulator(
            action_name=action_name,
            log_success_msg=f"Action {action_name} sent to simulator.",
            log_error_msg=f"Error sending action {action_name} to simulator:",
        )

        return self._send_request(
            method="RunAction",
            params=[p1, p2],
            log_success_msg=f"Action run_action({p1}, {p2}) successful.",
            log_error_msg=f"Error running action run_action({p1}, {p2}):",
        )

    def _run_stop_action(self) -> Optional[Dict[str, Any]]:
        """Send a request to stop the current action group."""
        return self._send_request(
            method="StopBusServo",
            params=["stopAction"],
            log_success_msg="Action run_stop_action() successful.",
            log_error_msg="Error running action run_stop_action():",
        )

    def _send_request(
        self,
        method: str,
        params: Optional[list],
        log_success_msg: str,
        log_error_msg: str,
    ) -> Optional[Dict[str, Any]]:
        if not params:
            self.logger.error("No parameters provided for dog action")
            return None
            
        try:
            # Format parameters: add "x/" or "y/" prefix unless value is "0"
            p0 = params[0] if params[0] == "0" else f"x/{params[0]}"
            p1 = params[1] if params[1] == "0" else f"y/{params[1]}"
            
            # Execute walk API sequence
            requests.get("http://localhost:8080/walk/status/toggle")
            
            if p0 != "0":
                requests.get(f"http://localhost:8080/walk/vel_{p0}")
            if p1 != "0":
                requests.get(f"http://localhost:8080/walk/vel_{p1}")
                
            time.sleep(2)
            requests.get("http://localhost:8080/walk/vel_x=1")
            requests.get("http://localhost:8080/walk/vel_y=1")
            requests.get("http://localhost:8080/walk/status/toggle")
            
            self.logger.info(log_success_msg)
            return {"status": "success", "params": params}
            
        except requests.exceptions.RequestException as e:
            self.logger.error("%s %s", log_error_msg, e)
            return None

    def _execute_action(self, action_item: Dict[str, Any]) -> None:
        """Execute a single action from the queue."""
        action_name = action_item["name"]
        action = actions[action_name]
        self.current_action = {
            "name": action["name"],
            "sleep_time": action["sleep_time"],
        }
        try:
            # Get base parameters from action config
            param1 = action["action"][0]
            param2 = action["action"][1]
            
            # Override with dynamic parameter if available (from MCP server)
            if "parameter" in action_item:
                dynamic_param = str(action_item["parameter"])
                # For movement actions, the dynamic parameter replaces the distance/angle
                if action_name in ["left", "right"]:
                    # For left/right movement, dynamic param goes to y (param2)
                    param2 = dynamic_param if action_name == "left" else f"-{dynamic_param}"
                elif action_name in ["forward", "back"]:
                    # For forward/back movement, dynamic param goes to x (param1)
                    param1 = dynamic_param if action_name == "forward" else f"-{dynamic_param}"
                elif action_name in ["cw", "ccw"]:
                    # For rotation, dynamic param goes to y (param2)
                    param2 = dynamic_param if action_name == "cw" else f"-{dynamic_param}"
            
            self._run_action(action_name, param1, param2)
            elapsed = 0.0
            while elapsed < action["sleep_time"]:
                if self._immediate_stop_event.is_set():
                    self.logger.info("Stopping action execution for %s", action_name)
                    self._immediate_stop_event.clear()
                    self._run_stop_action()
                    break
                time.sleep(0.1)
                elapsed += 0.1
        except Exception as e:
            self.logger.error("Error executing action %s: %s", action_name, e)
        finally:
            self._remove_action_by_id(action_item["id"])
            self.current_action = idle_action.copy()

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
        """Continuously consume actions from the queue and execute them."""
        time.sleep(5 - time.time() % 5)
        while not self._stop_event.is_set():
            try:
                if self._immediate_stop_event.is_set():
                    self.logger.info(
                        "Immediate stop triggered, clearing queue and setting to idle."
                    )
                    self.clear_action_queue()
                    self.current_action = idle_action.copy()
                    self.is_running = False
                    self._immediate_stop_event.clear()
                    time.sleep(0.5)
                    continue
                time.sleep(1 - time.time() % 1)
                action_item = self.action_queue.get(timeout=1)
                self.is_running = True
                self._execute_action(action_item)
                time.sleep(0.5)
            except queue.Empty:
                self.is_running = False
                time.sleep(0.5)

    def set_movement_parameter(self, action_name: str, value: Any) -> None:
        """Set a dynamic parameter for a movement action."""
        self.movement_parameters[action_name] = value

    def add_action_to_queue(self, action_name: str) -> None:
        """Add a new action to the queue."""
        action_id = str(uuid4())

        # Handle special stop action
        if action_name == "stop":
            self.stop()
            return

        if action_name not in actions:
            self.logger.error(
                "Action '%s' not found in actions dictionary. Available actions: %s", 
                action_name, list(actions.keys())
            )
            return

        with self.queue_lock:
            # Include any dynamic parameters with the action
            action_item = {"id": action_id, "name": action_name}
            if action_name in self.movement_parameters:
                action_item["parameter"] = self.movement_parameters[action_name]
                # Clear the parameter after use
                del self.movement_parameters[action_name]
            self.action_queue.put(action_item)

    def remove_action_from_queue(self, action_id: str) -> None:
        """Remove an action from the queue by its ID."""
        self._remove_action_by_id(action_id)

    def clear_action_queue(self) -> None:
        """Clear all actions from the queue."""
        with self.queue_lock:
            self.action_queue.queue.clear()

    def get_queue_status(self) -> Dict[str, Any]:
        """Get the current status of the action queue."""
        with self.queue_lock:
            queue_items = list(self.action_queue.queue)
        return {
            "queue": queue_items,
            "current_action": self.current_action,
            "is_running": self.is_running,
        }

    def stop(self) -> None:
        """Stop all actions immediately and clear the queue."""
        self.logger.info(
            "Immediate stop requested: clearing queue and interrupting current action."
        )
        self._immediate_stop_event.set()
        self.clear_action_queue()

    def shutdown(self) -> None:
        """Gracefully shutdown the consumer thread."""
        self._stop_event.set()
        self.consumer_thread.join()

    def _send_to_simulator(
        self,
        action_name: str,
        log_success_msg: str = None,
        log_error_msg: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send an action command to the robot simulator.

        Args:
            action_name: The name of the action to execute
            robot_id: The ID of the robot to control
            session_key: The session key for authentication
            simulator_base_url: The base URL of the simulator (default: http://localhost:5000)
            log_success_msg: Message to log on successful API call
            log_error_msg: Message to log on failed API call

        Returns:
            Optional response data from the simulator API call
        """

        if log_success_msg is None:
            log_success_msg = f"Simulator action {action_name} for robot {self.robot_name} successful."
        if log_error_msg is None:
            log_error_msg = f"Error sending action {action_name} to simulator for robot {self.robot_name}:"

        # Construct the URL in the format:
        url = f"{self.simulator_endpoint}/run_action/{self.robot_name}?session_key={self.session_key}"

        # Prepare the payload in the expected format: {"action": "bow"}
        payload = {"action": action_name}

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
                "%s - %s Response: %s", self.robot_name, log_success_msg, resp_json
            )
            return resp_json
        except requests.exceptions.RequestException as e:
            self.logger.error("%s %s", log_error_msg, e)
            return None
