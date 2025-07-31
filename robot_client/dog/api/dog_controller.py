"""
Dog Robot Controller

Main controller class for managing dog robot operations including movement,
status control, and command execution.
"""

import logging
import time
from typing import Any, Dict, Optional

from .movement_commands import MovementCommands
from .robot_status import RobotStatus
from .UDPComms import Publisher

logger = logging.getLogger(__name__)


class DogController:
    """Main controller for dog robot operations."""

    def __init__(self, ip: str = "127.255.255.255", port: int = 8830):
        """
        Initialize the dog controller.

        Args:
            ip: Robot IP address
            port: UDP communication port
        """
        self.ip = ip
        self.port = port
        print(f"Initializing DogController with IP: {ip}, Port: {port}")
        self.publisher = Publisher(port, ip)
        self.movement = MovementCommands(self.publisher)
        self.status = RobotStatus(self.publisher)
        self._is_activated = False
        self._is_walking = False
        self._is_dancing = False

        logger.info(f"Dog controller initialized for {ip}:{port}")

    def send_command(self, command: Dict[str, Any]) -> None:
        """
        Send a raw command to the robot.

        Args:
            command: Command dictionary to send
        """
        try:
            self.publisher.send(command)
            logger.debug(f"Command sent: {command}")
        except Exception as e:
            logger.error(f"Failed to send command {command}: {e}")
            raise

    def activate(self) -> None:
        """Activate the robot controller."""
        self.status.toggle_activation()
        self._is_activated = not self._is_activated
        logger.info(f"Robot {'activated' if self._is_activated else 'deactivated'}")

    def enable_walking(self) -> None:
        """Enable walking mode."""
        self.status.toggle_walk()
        self._is_walking = not self._is_walking
        logger.info(f"Walking mode {'enabled' if self._is_walking else 'disabled'}")

    def enable_dancing(self) -> None:
        """Enable dancing mode."""
        self.status.toggle_dance()
        self._is_dancing = not self._is_dancing
        logger.info(f"Dancing mode {'enabled' if self._is_dancing else 'disabled'}")

    def stop_all(self) -> None:
        """Stop all robot movement and return to neutral state."""
        self.movement.stop()
        logger.info("All movement stopped")

    def emergency_stop(self) -> None:
        """Emergency stop - immediately halt all operations."""
        self.stop_all()
        if self._is_walking:
            self.enable_walking()
        if self._is_dancing:
            self.enable_dancing()
        logger.warning("Emergency stop executed")

    @property
    def is_activated(self) -> bool:
        """Check if robot is activated."""
        return self._is_activated

    @property
    def is_walking_enabled(self) -> bool:
        """Check if walking mode is enabled."""
        return self._is_walking

    @property
    def is_dancing_enabled(self) -> bool:
        """Check if dancing mode is enabled."""
        return self._is_dancing

    def get_status(self) -> Dict[str, bool]:
        """
        Get current robot status.

        Returns:
            Dictionary containing current status flags
        """
        return {
            "activated": self._is_activated,
            "walking_enabled": self._is_walking,
            "dancing_enabled": self._is_dancing,
        }
