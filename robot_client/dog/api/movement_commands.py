"""
Movement Commands for Dog Robot

This module provides movement command implementations for the dog robot,
including directional movement, rotation, and posture controls.
"""

import time
import logging
from typing import Dict, Any, Optional
from .UDPComms import Publisher

logger = logging.getLogger(__name__)


class MovementCommands:
    """Handles all movement-related commands for the dog robot."""
    
    # Base command template with all parameters
    BASE_COMMAND = {
        'lx': 0.0, 'ly': 0.0, 'rx': 0.0, 'ry': 0.0,
        'x': 0, 'square': 0, 'circle': 0, 'triangle': 0,
        'dpadx': 0, 'dpady': 0, 'L1': 0, 'R1': 0, 'L2': 0, 'R2': 0,
        'message_rate': 20
    }
    
    def __init__(self, publisher: Publisher):
        """
        Initialize movement commands.
        
        Args:
            publisher: UDP publisher instance for sending commands
        """
        self.publisher = publisher
    
    def _send_movement_command(self, **kwargs) -> None:
        """
        Send a movement command with specified parameters.
        
        Args:
            **kwargs: Command parameters to override in base command
        """
        command = self.BASE_COMMAND.copy()
        command.update(kwargs)
        
        try:
            self.publisher.send(command)
            logger.info(f"Movement command sent: {kwargs}")
        except Exception as e:
            logger.error(f"Failed to send movement command: {e}")
            raise
    
    def move_forward(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Move robot forward.
        
        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        self._send_movement_command(ly=speed)
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(ly=speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Moving forward at speed {speed}")
    
    def move_backward(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Move robot backward.
        
        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        self._send_movement_command(ly=-speed)
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(ly=-speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Moving backward at speed {speed}")
    
    def move_left(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Move robot left.
        
        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        self._send_movement_command(lx=-speed)
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(lx=-speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Moving left at speed {speed}")
    
    def move_right(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Move robot right.
        
        Args:
            speed: Movement speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        self._send_movement_command(lx=speed)
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(lx=speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Moving right at speed {speed}")
    
    def rotate_left(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Rotate robot left (counter-clockwise).
        
        Args:
            speed: Rotation speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        self._send_movement_command(dpadx=speed)
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(dpadx=speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Rotating left at speed {speed}")
    
    def rotate_right(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Rotate robot right (clockwise).
        
        Args:
            speed: Rotation speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        self._send_movement_command(dpadx=-speed)
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(dpadx=-speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Rotating right at speed {speed}")
    
    def stand_up(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Make robot stand up.
        
        Args:
            speed: Standing speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(dpady=speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
            
        logger.info("Standing up")
    
    def lay_down(self, speed: float = 0.5, duration: Optional[float] = None) -> None:
        """
        Make robot lay down.
        
        Args:
            speed: Laying down speed (0.0 to 1.0)
            duration: Optional duration in seconds
        """
        speed = max(0.0, min(1.0, speed))  # Clamp speed
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(dpady=-speed)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
            
        logger.info("Laying down")
    
    def hop(self, duration: float = 1.0) -> None:
        """
        Make robot hop.
        
        Args:
            duration: Hop duration in seconds
        """
        start_time = time.time()
        while time.time() - start_time < duration:
            self._send_movement_command(x=1)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        self.stop()
        logger.info("Hopping")
    
    def stop(self) -> None:
        """Stop all movement."""
        self._send_movement_command()  # Send base command (all zeros)
        logger.info("Movement stopped")
    
    def custom_movement(self, lx: float = 0.0, ly: float = 0.0, 
                       rx: float = 0.0, ry: float = 0.0,
                       dpadx: float = 0.0, dpady: float = 0.0,
                       duration: Optional[float] = None) -> None:
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
        # Clamp all values to valid range
        params = {
            'lx': max(-1.0, min(1.0, lx)),
            'ly': max(-1.0, min(1.0, ly)),
            'rx': max(-1.0, min(1.0, rx)),
            'ry': max(-1.0, min(1.0, ry)),
            'dpadx': max(-1.0, min(1.0, dpadx)),
            'dpady': max(-1.0, min(1.0, dpady))
        }
        
        start_time = time.time()
        while not duration or (time.time() - start_time < duration):
            self._send_movement_command(**params)
            time.sleep(1.0 / self.BASE_COMMAND['message_rate'])
        
        if duration:
            self.stop()
        
        logger.info(f"Custom movement executed: {params}")