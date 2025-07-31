"""
Robot Status Management

This module handles robot status controls including activation,
walking mode, and dancing mode toggles.
"""

import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import BASE_COMMAND_TEMPLATE, ERROR_MESSAGES

from .UDPComms import Publisher

logger = logging.getLogger(__name__)


class RobotStatus:
    """Handles robot status and mode controls."""

    def __init__(self, publisher: Publisher):
        """
        Initialize robot status controller.

        Args:
            publisher: UDP publisher instance for sending commands
        """
        self.publisher = publisher
        self._base_command = BASE_COMMAND_TEMPLATE.copy()

    def _send_status_command(self, **kwargs) -> None:
        """
        Send a status command with specified parameters.

        Args:
            **kwargs: Command parameters to override in base command
        """
        command = self._base_command.copy()
        command.update(kwargs)

        try:
            self.publisher.send(command)
            logger.debug(f"Status command sent: {kwargs}")
        except Exception as e:
            logger.error(f"{ERROR_MESSAGES['udp_send_failed']}: {e}")
            raise

    def toggle_activation(self) -> None:
        """
        Toggle robot activation state.

        The L1 button controls robot activation. Run once to activate,
        run again to deactivate.
        """
        self._send_status_command(L1=1)
        logger.info("Robot activation toggled")

    def toggle_walk(self) -> None:
        """
        Toggle walking mode.

        The R1 button controls walking mode. Run once to start walking motion,
        run again to stop walking motion.
        """
        self._send_status_command(R1=1)
        logger.info("Walking mode toggled")

    def toggle_dance(self) -> None:
        """
        Toggle dancing mode.

        The circle button controls dancing mode. Run once to start dancing,
        run again to stop dancing.
        """
        self._send_status_command(circle=1)
        logger.info("Dancing mode toggled")

    def trigger_special_action(self) -> None:
        """
        Trigger special action using X button.

        This can be used for custom actions or specific robot behaviors.
        """
        self._send_status_command(x=1)
        logger.info("Special action triggered")

    def trigger_square_action(self) -> None:
        """
        Trigger square button action.

        This can be used for additional custom behaviors.
        """
        self._send_status_command(square=1)
        logger.info("Square action triggered")

    def trigger_triangle_action(self) -> None:
        """
        Trigger triangle button action.

        This can be used for additional custom behaviors.
        """
        self._send_status_command(triangle=1)
        logger.info("Triangle action triggered")

    def trigger_l2_action(self) -> None:
        """
        Trigger L2 button action.

        This can be used for additional custom behaviors.
        """
        self._send_status_command(L2=1)
        logger.info("L2 action triggered")

    def trigger_r2_action(self) -> None:
        """
        Trigger R2 button action.

        This can be used for additional custom behaviors.
        """
        self._send_status_command(R2=1)
        logger.info("R2 action triggered")
        logger.info("R2 action triggered")
