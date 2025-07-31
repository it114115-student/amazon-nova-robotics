"""
Movement Commands for Dog Robot

This module provides movement command implementations for the dog robot,
including directional movement, rotation, and posture controls.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import (
    BASE_COMMAND_TEMPLATE,
    DEFAULT_MESSAGE_RATE,
    ERROR_MESSAGES,
    validate_duration,
    validate_speed,
)

from .UDPComms import Publisher

logger = logging.getLogger(__name__)


class MovementCommands:
    """Handles all movement-related commands for the dog robot."""

    def __init__(self, publisher: Publisher):
        """
        Initialize movement commands.

        Args:
            publisher: UDP publisher instance for sending commands
        """
        self.publisher = publisher
        self._base_command = BASE_COMMAND_TEMPLATE.copy()

    def _send_movement_command(self, **kwargs) -> None:
        """
        Send a movement command with specified parameters.

        Args:
            **kwargs: Command parameters to override in base command
        """
        command = self._base_command.copy()
        command.update(kwargs)

        try:
            self.publisher.send(command)
            logger.debug(f"Movement command sent: {kwargs}")
        except Exception as e:
            logger.error(f"{ERROR_MESSAGES['udp_send_failed']}: {e}")
            raise

    def _execute_timed_movement(
        self, command_params: Dict[str, Any], duration: Optional[float] = None
    ) -> None:
        """
        Execute a movement command for a specified duration.

        Args:
            command_params: Command parameters to send
            duration: Optional duration in seconds
        """
        if duration is None:
            self._send_movement_command(**command_params)
            return

        duration = validate_duration(duration)
        start_time = time.time()
        sleep_interval = 1.0 / DEFAULT_MESSAGE_RATE

        while time.time() - start_time < duration:
            self._send_movement_command(**command_params)
            time.sleep(sleep_interval)

        self.stop()

    def move_forward(
        self, speed: float = 0.5, duration: Optional[float] = None
    ) -> None:
        """
        Move robot forward.

        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"ly": speed}, duration)
        logger.info(f"Moving forward at speed {speed}")

    def move_backward(
        self, speed: float = 0.5, duration: Optional[float] = None
    ) -> None:
        """
        Move robot backward.

        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"ly": -speed}, duration)
        logger.info(f"Moving backward at speed {speed}")

    def move_left(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Move robot left.

        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"lx": -speed}, duration)
        logger.info(f"Moving left at speed {speed}")

    def move_right(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Move robot right.

        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"lx": speed}, duration)
        logger.info(f"Moving right at speed {speed}")

    def rotate_left(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Rotate robot left (counter-clockwise).

        Args:
            speed: Rotation speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"dpadx": speed}, duration)
        logger.info(f"Rotating left at speed {speed}")

    def rotate_right(
        self, speed: float = 0.5, duration: Optional[float] = None
    ) -> None:
        """
        Rotate robot right (clockwise).

        Args:
            speed: Rotation speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"dpadx": -speed}, duration)
        logger.info(f"Rotating right at speed {speed}")

    def stand_up(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Make robot stand up.

        Args:
            speed: Standing speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"dpady": speed}, duration)
        logger.info("Standing up")

    def lay_down(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Make robot lay down.

        Args:
            speed: Laying down speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = validate_speed(speed)
        self._execute_timed_movement({"dpady": -speed}, duration)
        logger.info("Laying down")

    def hop(self, duration: float = 1.0) -> None:
        """
        Make robot hop.

        Args:
            duration: Hop duration in seconds
        """
        duration = validate_duration(duration)
        self._execute_timed_movement({"x": 1}, duration)
        logger.info("Hopping")

    def stop(self) -> None:
        """Stop all movement."""
        self._send_movement_command()  # Send base command (all zeros)
        logger.info("Movement stopped")

    def custom_movement(
        self,
        lx: float = 0.0,
        ly: float = 0.0,
        rx: float = 0.0,
        ry: float = 0.0,
        dpadx: float = 0.0,
        dpady: float = 0.0,
        duration: Optional[float] = None,
    ) -> None:
        """
        Execute custom movement with specified parameters.

        Args:
            lx: Left stick X axis (-1.0 to 1.0)
            ly: Left stick Y axis (-1.0 to 1.0)
            rx: Right stick X axis (-1.0 to 1.0)
            ry: Right stick Y axis (-1.0 to 1.0)
            dpadx: D-pad X axis (-1.0 to 1.0)
            dpady: D-pad Y axis (-1.0 to 1.0)
            duration: Optional duration in seconds
        """
        from config import clamp_value

        # Clamp all values to valid range
        params = {
            "lx": clamp_value(lx, -1.0, 1.0),
            "ly": clamp_value(ly, -1.0, 1.0),
            "rx": clamp_value(rx, -1.0, 1.0),
            "ry": clamp_value(ry, -1.0, 1.0),
            "dpadx": clamp_value(dpadx, -1.0, 1.0),
            "dpady": clamp_value(dpady, -1.0, 1.0),
        }

        self._execute_timed_movement(params, duration)
        logger.info(f"Custom movement executed: {params}")
        logger.info(f"Custom movement executed: {params}")
