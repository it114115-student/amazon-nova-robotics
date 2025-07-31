"""Drone control tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import DroneID
from executors import robot_executor
from config import DRONE_MOVE_DISTANCE_CM


def register_drone_tools(mcp: MCPLambdaHandler):
    """Register all drone-related tools with the MCP handler."""

    @mcp.tool()
    def drone_takeoff(drone_id: DroneID) -> str:
        """Command the drone to take off.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is taking off.
        """
        robot_executor.execute_drone_action(drone_id, "takeoff")
        return "The drone is taking off."

    @mcp.tool()
    def drone_land(drone_id: DroneID) -> str:
        """Command the drone to land.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is landing.
        """
        robot_executor.execute_drone_action(drone_id, "land")
        return "The drone is landing."

    # Movement commands
    @mcp.tool()
    def drone_move_up(drone_id: DroneID) -> str:
        """Command the drone to move up for DRONE_MOVE_DISTANCE_CM cm.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is moving up.
        """
        robot_executor.execute_drone_action(
            drone_id, "move_up", {"x": DRONE_MOVE_DISTANCE_CM}
        )
        return f"The drone is moving up for {DRONE_MOVE_DISTANCE_CM} cm."

    @mcp.tool()
    def drone_move_down(drone_id: DroneID) -> str:
        """Command the drone to move down for DRONE_MOVE_DISTANCE_CM cm.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is moving down.
        """
        robot_executor.execute_drone_action(
            drone_id, "move_down", {"x": DRONE_MOVE_DISTANCE_CM}
        )
        return f"The drone is moving down for {DRONE_MOVE_DISTANCE_CM} cm."

    @mcp.tool()
    def drone_move_left(drone_id: DroneID) -> str:
        """Command the drone to move left for DRONE_MOVE_DISTANCE_CM cm.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is moving left.
        """
        robot_executor.execute_drone_action(
            drone_id, "move_left", {"x": DRONE_MOVE_DISTANCE_CM}
        )
        return f"The drone is moving left for {DRONE_MOVE_DISTANCE_CM} cm."

    @mcp.tool()
    def drone_move_right(drone_id: DroneID) -> str:
        """Command the drone to move right for DRONE_MOVE_DISTANCE_CM cm.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is moving right.
        """
        robot_executor.execute_drone_action(
            drone_id, "move_right", {"x": DRONE_MOVE_DISTANCE_CM}
        )
        return f"The drone is moving right for {DRONE_MOVE_DISTANCE_CM} cm."

    @mcp.tool()
    def drone_move_forward(drone_id: DroneID) -> str:
        """Command the drone to move forward for DRONE_MOVE_DISTANCE_CM cm.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is moving forward.
        """
        robot_executor.execute_drone_action(
            drone_id, "move_forward", {"x": DRONE_MOVE_DISTANCE_CM}
        )
        return f"The drone is moving forward for {DRONE_MOVE_DISTANCE_CM} cm."

    @mcp.tool()
    def drone_move_back(drone_id: DroneID) -> str:
        """Command the drone to move back for DRONE_MOVE_DISTANCE_CM cm.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is moving back.
        """
        robot_executor.execute_drone_action(
            drone_id, "move_back", {"x": DRONE_MOVE_DISTANCE_CM}
        )
        return f"The drone is moving back for {DRONE_MOVE_DISTANCE_CM} cm."

    # Rotation commands
    @mcp.tool()
    def drone_turn_right(drone_id: DroneID) -> str:
        """Command the drone to turn right by a 90 degree angle.

        Args:
            drone_id (DroneID): Drone ID
        Returns:
            str: The drone is turning right.
        """
        robot_executor.execute_drone_action(drone_id, "rotate_clockwise", {"x": 90})
        return "The drone is turning right by 90 degrees."

    @mcp.tool()
    def drone_turn_left(drone_id: DroneID) -> str:
        """Command the drone to turn left by a 90 degree angle.

        Args:
            drone_id (DroneID): Drone ID
        Returns:
            str: The drone is turning left.
        """
        robot_executor.execute_drone_action(drone_id, "rotate_counterclockwise", {"x": 90})
        return "The drone is turning left by 90 degrees."

    @mcp.tool()
    def drone_turn_back(drone_id: DroneID) -> str:
        """Command the drone to turn back by 180 degrees.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is turning back.
        """
        robot_executor.execute_drone_action(drone_id, "rotate_clockwise", {"x": 180})
        return "The drone is turning back by 180 degrees."

    # Flip commands
    @mcp.tool()
    def drone_flip_left(drone_id: DroneID) -> str:
        """Command the drone to flip to the left.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is flipping to the left.
        """
        robot_executor.execute_drone_action(drone_id, "flip", {"direction": "l"})
        return "The drone is flipping to the left."

    @mcp.tool()
    def drone_flip_right(drone_id: DroneID) -> str:
        """Command the drone to flip to the right.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is flipping to the right.
        """
        robot_executor.execute_drone_action(drone_id, "flip", {"direction": "r"})
        return "The drone is flipping to the right."

    @mcp.tool()
    def drone_flip_forward(drone_id: DroneID) -> str:
        """Command the drone to flip forward.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is flipping forward.
        """
        robot_executor.execute_drone_action(drone_id, "flip", {"direction": "f"})
        return "The drone is flipping forward."

    @mcp.tool()
    def drone_flip_back(drone_id: DroneID) -> str:
        """Command the drone to flip backward.

        Args:
            drone_id (DroneID): Drone ID

        Returns:
            str: The drone is flipping backward.
        """
        robot_executor.execute_drone_action(drone_id, "flip", {"direction": "b"})
        return "The drone is flipping backward."