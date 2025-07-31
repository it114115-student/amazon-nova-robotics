"""
Dog Robot API Module

This module provides a clean interface for controlling dog robots through UDP communication.
It includes movement controls, status management, and command execution capabilities.
"""

from .dog_controller import DogController
from .movement_commands import MovementCommands
from .robot_status import RobotStatus

__all__ = ['DogController', 'MovementCommands', 'RobotStatus']