"""Dog control tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import DogID
from executors import robot_executor



def register_dog_tools(mcp: MCPLambdaHandler):
    """Register all dog-related tools with the MCP handler."""

    # ===== BASIC MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_move_forward(dog_id: DogID) -> str:
        """Command the dog to move forward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving forward.
        """
        robot_executor.execute_dog_action(dog_id, "forward", {})
        return "The dog is moving forward."

    @mcp.tool()
    def dog_move_backward(dog_id: DogID) -> str:
        """Command the dog to move backward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving backward.
        """
        robot_executor.execute_dog_action(dog_id, "back", {})
        return "The dog is moving backward."

    @mcp.tool()
    def dog_move_left(dog_id: DogID) -> str:
        """Command the dog to move left.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving left.
        """
        robot_executor.execute_dog_action(dog_id, "left", {})
        return "The dog is moving left."

    @mcp.tool()
    def dog_move_right(dog_id: DogID) -> str:
        """Command the dog to move right.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving right.
        """
        robot_executor.execute_dog_action(dog_id, "right", {})
        return "The dog is moving right."

    # ===== ROTATION COMMANDS =====

    @mcp.tool()
    def dog_rotate_left(dog_id: DogID) -> str:
        """Command the dog to rotate left (counter-clockwise).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is rotating left.
        """
        robot_executor.execute_dog_action(dog_id, "ccw", {})
        return "The dog is rotating left."

    @mcp.tool()
    def dog_rotate_right(dog_id: DogID) -> str:
        """Command the dog to rotate right (clockwise).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is rotating right.
        """
        robot_executor.execute_dog_action(dog_id, "cw", {})
        return "The dog is rotating right."

    @mcp.tool()
    def dog_turn_around(dog_id: DogID) -> str:
        """Command the dog to turn around 180 degrees.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning around.
        """
        robot_executor.execute_dog_action(dog_id, "cw", {})
        return "The dog is turning around."

    # ===== POSTURE COMMANDS =====

    @mcp.tool()
    def dog_stand_up(dog_id: DogID) -> str:
        """Command the dog to stand up.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is standing up.
        """
        robot_executor.execute_dog_action(dog_id, "stand_up", {})
        return "The dog is standing up."

    @mcp.tool()
    def dog_lay_down(dog_id: DogID) -> str:
        """Command the dog to lay down.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is laying down.
        """
        robot_executor.execute_dog_action(dog_id, "lay_down", {})
        return "The dog is laying down."

    @mcp.tool()
    def dog_hop(dog_id: DogID) -> str:
        """Command the dog to hop.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is hopping.
        """
        robot_executor.execute_dog_action(dog_id, "hop", {})
        return "The dog is hopping."

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
    def dog_circle_movement(dog_id: DogID, radius: float = 1.0, clockwise: bool = True) -> str:
        """Make the dog move in a circle.

        Args:
            dog_id (DogID): Dog ID
            radius (float): Circle radius factor (default: 1.0)
            clockwise (bool): Direction of circle (default: True)

        Returns:
            str: The dog is moving in a circle.
        """
        speed = 0.3
        rotation_direction = -speed if clockwise else speed
        parameters = {
            "ly": speed * radius,
            "dpadx": rotation_direction,
            "duration": 5.0
        }
        robot_executor.execute_dog_action(dog_id, "custom_movement", parameters)
        direction = "clockwise" if clockwise else "counter-clockwise"
        return f"The dog is moving in a {direction} circle."

    # ===== LEGACY COMPATIBILITY COMMANDS =====

    @mcp.tool()
    def dog_turn_right(dog_id: DogID) -> str:
        """Command the dog to turn right by 90 degrees (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning right.
        """
        return dog_rotate_right(dog_id)

    @mcp.tool()
    def dog_turn_left(dog_id: DogID) -> str:
        """Command the dog to turn left by 90 degrees (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning left.
        """
        return dog_rotate_left(dog_id)

    @mcp.tool()
    def dog_turn_back(dog_id: DogID) -> str:
        """Command the dog to turn back by 180 degrees (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is turning back.
        """
        return dog_turn_around(dog_id)

    @mcp.tool()
    def dog_move_back(dog_id: DogID) -> str:
        """Command the dog to move back (legacy compatibility).

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving back.
        """
        return dog_move_backward(dog_id)