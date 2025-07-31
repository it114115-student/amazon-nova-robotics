"""Dog control tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import DogID
from executors import robot_executor
from config import DOG_MOVE_DISTANCE_CM, DOG_MOVE_SPEED, DOG_ROTATION_ANGLE, DOG_ROTATION_SPEED


def register_dog_tools(mcp: MCPLambdaHandler):
    """Register all dog-related tools with the MCP handler."""

    # ===== BASIC MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_move_forward(dog_id: DogID, distance: int = DOG_MOVE_DISTANCE_CM, speed: float = DOG_MOVE_SPEED) -> str:
        """Command the dog to move forward.

        Args:
            dog_id (DogID): Dog ID
            distance (int): Distance to move in cm (default: 50)
            speed (float): Movement speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is moving forward.
        """
        robot_executor.execute_dog_action(dog_id, "forward", {"distance": distance, "speed": speed})
        return f"The dog is moving forward {distance} cm at speed {speed}."

    @mcp.tool()
    def dog_move_backward(dog_id: DogID, distance: int = DOG_MOVE_DISTANCE_CM, speed: float = DOG_MOVE_SPEED) -> str:
        """Command the dog to move backward.

        Args:
            dog_id (DogID): Dog ID
            distance (int): Distance to move in cm (default: 50)
            speed (float): Movement speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is moving backward.
        """
        robot_executor.execute_dog_action(dog_id, "back", {"distance": distance, "speed": speed})
        return f"The dog is moving backward {distance} cm at speed {speed}."

    @mcp.tool()
    def dog_move_left(dog_id: DogID, distance: int = DOG_MOVE_DISTANCE_CM, speed: float = DOG_MOVE_SPEED) -> str:
        """Command the dog to move left.

        Args:
            dog_id (DogID): Dog ID
            distance (int): Distance to move in cm (default: 50)
            speed (float): Movement speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is moving left.
        """
        robot_executor.execute_dog_action(dog_id, "left", {"distance": distance, "speed": speed})
        return f"The dog is moving left {distance} cm at speed {speed}."

    @mcp.tool()
    def dog_move_right(dog_id: DogID, distance: int = DOG_MOVE_DISTANCE_CM, speed: float = DOG_MOVE_SPEED) -> str:
        """Command the dog to move right.

        Args:
            dog_id (DogID): Dog ID
            distance (int): Distance to move in cm (default: 50)
            speed (float): Movement speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is moving right.
        """
        robot_executor.execute_dog_action(dog_id, "right", {"distance": distance, "speed": speed})
        return f"The dog is moving right {distance} cm at speed {speed}."

    # ===== ROTATION COMMANDS =====

    @mcp.tool()
    def dog_rotate_left(dog_id: DogID, angle: int = DOG_ROTATION_ANGLE, speed: float = DOG_ROTATION_SPEED) -> str:
        """Command the dog to rotate left (counter-clockwise).

        Args:
            dog_id (DogID): Dog ID
            angle (int): Rotation angle in degrees (default: 90)
            speed (float): Rotation speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is rotating left.
        """
        robot_executor.execute_dog_action(dog_id, "ccw", {"angle": angle, "speed": speed})
        return f"The dog is rotating left {angle} degrees at speed {speed}."

    @mcp.tool()
    def dog_rotate_right(dog_id: DogID, angle: int = DOG_ROTATION_ANGLE, speed: float = DOG_ROTATION_SPEED) -> str:
        """Command the dog to rotate right (clockwise).

        Args:
            dog_id (DogID): Dog ID
            angle (int): Rotation angle in degrees (default: 90)
            speed (float): Rotation speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is rotating right.
        """
        robot_executor.execute_dog_action(dog_id, "cw", {"angle": angle, "speed": speed})
        return f"The dog is rotating right {angle} degrees at speed {speed}."

    @mcp.tool()
    def dog_turn_around(dog_id: DogID, speed: float = DOG_ROTATION_SPEED) -> str:
        """Command the dog to turn around 180 degrees.

        Args:
            dog_id (DogID): Dog ID
            speed (float): Rotation speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is turning around.
        """
        robot_executor.execute_dog_action(dog_id, "cw", {"angle": 180, "speed": speed})
        return f"The dog is turning around 180 degrees at speed {speed}."

    # ===== POSTURE COMMANDS =====

    @mcp.tool()
    def dog_stand_up(dog_id: DogID, speed: float = DOG_MOVE_SPEED) -> str:
        """Command the dog to stand up.

        Args:
            dog_id (DogID): Dog ID
            speed (float): Standing speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is standing up.
        """
        robot_executor.execute_dog_action(dog_id, "stand_up", {"speed": speed})
        return f"The dog is standing up at speed {speed}."

    @mcp.tool()
    def dog_lay_down(dog_id: DogID, speed: float = DOG_MOVE_SPEED) -> str:
        """Command the dog to lay down.

        Args:
            dog_id (DogID): Dog ID
            speed (float): Laying down speed 0.1-1.0 (default: 0.5)

        Returns:
            str: The dog is laying down.
        """
        robot_executor.execute_dog_action(dog_id, "lay_down", {"speed": speed})
        return f"The dog is laying down at speed {speed}."

    @mcp.tool()
    def dog_hop(dog_id: DogID, duration: float = 1.0) -> str:
        """Command the dog to hop.

        Args:
            dog_id (DogID): Dog ID
            duration (float): Hop duration in seconds (default: 1.0)

        Returns:
            str: The dog is hopping.
        """
        robot_executor.execute_dog_action(dog_id, "hop", {"duration": duration})
        return f"The dog is hopping for {duration} seconds."

    # ===== STATUS AND MODE COMMANDS =====

    @mcp.tool()
    def dog_activate(dog_id: DogID) -> str:
        """Toggle the dog's activation state.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog activation has been toggled.
        """
        robot_executor.execute_dog_action(dog_id, "activate", {})
        return "The dog activation has been toggled."

    @mcp.tool()
    def dog_enable_walking(dog_id: DogID) -> str:
        """Toggle the dog's walking mode.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog walking mode has been toggled.
        """
        robot_executor.execute_dog_action(dog_id, "walk_mode", {})
        return "The dog walking mode has been toggled."

    @mcp.tool()
    def dog_enable_dancing(dog_id: DogID) -> str:
        """Toggle the dog's dancing mode.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog dancing mode has been toggled.
        """
        robot_executor.execute_dog_action(dog_id, "dance_mode", {})
        return "The dog dancing mode has been toggled."

    @mcp.tool()
    def dog_stop(dog_id: DogID) -> str:
        """Stop all dog movement immediately.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog has stopped all movement.
        """
        robot_executor.execute_dog_action(dog_id, "stop", {})
        return "The dog has stopped all movement."

    # ===== ADVANCED MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_custom_movement(
        dog_id: DogID,
        forward_speed: float = 0.0,
        side_speed: float = 0.0,
        rotation_speed: float = 0.0,
        duration: float = 2.0
    ) -> str:
        """Execute custom movement with combined forward, side, and rotation.

        Args:
            dog_id (DogID): Dog ID
            forward_speed (float): Forward/backward speed -1.0 to 1.0 (default: 0.0)
            side_speed (float): Left/right speed -1.0 to 1.0 (default: 0.0)
            rotation_speed (float): Rotation speed -1.0 to 1.0 (default: 0.0)
            duration (float): Movement duration in seconds (default: 2.0)

        Returns:
            str: The dog is executing custom movement.
        """
        parameters = {
            "ly": forward_speed,
            "lx": side_speed,
            "dpadx": rotation_speed,
            "duration": duration
        }
        robot_executor.execute_dog_action(dog_id, "custom_movement", parameters)
        return f"The dog is executing custom movement for {duration} seconds."

    @mcp.tool()
    def dog_circle_movement(dog_id: DogID, radius: float = 1.0, clockwise: bool = True, speed: float = 0.3) -> str:
        """Make the dog move in a circle.

        Args:
            dog_id (DogID): Dog ID
            radius (float): Circle radius factor (default: 1.0)
            clockwise (bool): Direction of circle (default: True)
            speed (float): Movement speed 0.1-1.0 (default: 0.3)

        Returns:
            str: The dog is moving in a circle.
        """
        rotation_direction = -speed if clockwise else speed
        parameters = {
            "ly": speed * radius,
            "dpadx": rotation_direction,
            "duration": 5.0
        }
        robot_executor.execute_dog_action(dog_id, "custom_movement", parameters)
        direction = "clockwise" if clockwise else "counter-clockwise"
        return f"The dog is moving in a {direction} circle at speed {speed}."

    # ===== LEGACY COMPATIBILITY COMMANDS =====

    @mcp.tool()
    def dog_turn_right(dog_id: DogID) -> str:
        """Command the dog to turn right by 90 degrees (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning right.
        """
        return dog_rotate_right(dog_id, 90, DOG_ROTATION_SPEED)

    @mcp.tool()
    def dog_turn_left(dog_id: DogID) -> str:
        """Command the dog to turn left by 90 degrees (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning left.
        """
        return dog_rotate_left(dog_id, 90, DOG_ROTATION_SPEED)

    @mcp.tool()
    def dog_turn_back(dog_id: DogID) -> str:
        """Command the dog to turn back by 180 degrees (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning back.
        """
        return dog_turn_around(dog_id, DOG_ROTATION_SPEED)

    @mcp.tool()
    def dog_move_back(dog_id: DogID) -> str:
        """Command the dog to move back (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving back.
        """
        return dog_move_backward(dog_id, DOG_MOVE_DISTANCE_CM, DOG_MOVE_SPEED)