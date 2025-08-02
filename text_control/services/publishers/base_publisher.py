"""
Abstract base class for robot publishers
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class RobotPublisher(ABC):
    """Abstract base class for robot publishers"""

    @abstractmethod
    def publish(
        self, robot_id: str, message: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """Publish message to robot"""
        raise NotImplementedError("Subclasses must implement this method")