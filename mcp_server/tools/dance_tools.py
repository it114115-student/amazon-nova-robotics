"""Dance control tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import RobotID
from executors import robot_executor


def register_dance_tools(mcp: MCPLambdaHandler):
    """Register all dance-related tools with the MCP handler."""

    @mcp.tool()
    def robot_dance_two(robot_id: RobotID) -> str:
        """Command the robot to perform dance two.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance two.
        """
        robot_executor.execute_action(robot_id, "dance_two")
        return "The robot is performing dance two."

    @mcp.tool()
    def robot_dance_three(robot_id: RobotID) -> str:
        """Command the robot to perform dance three.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance three.
        """
        robot_executor.execute_action(robot_id, "dance_three")
        return "The robot is performing dance three."

    @mcp.tool()
    def robot_dance_four(robot_id: RobotID) -> str:
        """Command the robot to perform dance four.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance four.
        """
        robot_executor.execute_action(robot_id, "dance_four")
        return "The robot is performing dance four."

    @mcp.tool()
    def robot_dance_five(robot_id: RobotID) -> str:
        """Command the robot to perform dance five.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance five.
        """
        robot_executor.execute_action(robot_id, "dance_five")
        return "The robot is performing dance five."

    @mcp.tool()
    def robot_dance_six(robot_id: RobotID) -> str:
        """Command the robot to perform dance six.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance six.
        """
        robot_executor.execute_action(robot_id, "dance_six")
        return "The robot is performing dance six."

    @mcp.tool()
    def robot_dance_seven(robot_id: RobotID) -> str:
        """Command the robot to perform dance seven.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance seven.
        """
        robot_executor.execute_action(robot_id, "dance_seven")
        return "The robot is performing dance seven."

    @mcp.tool()
    def robot_dance_eight(robot_id: RobotID) -> str:
        """Command the robot to perform dance eight.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance eight.
        """
        robot_executor.execute_action(robot_id, "dance_eight")
        return "The robot is performing dance eight."

    @mcp.tool()
    def robot_dance_nine(robot_id: RobotID) -> str:
        """Command the robot to perform dance nine.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance nine.
        """
        robot_executor.execute_action(robot_id, "dance_nine")
        return "The robot is performing dance nine."

    @mcp.tool()
    def robot_dance_ten(robot_id: RobotID) -> str:
        """Command the robot to perform dance ten.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing dance ten.
        """
        robot_executor.execute_action(robot_id, "dance_ten")
        return "The robot is performing dance ten."