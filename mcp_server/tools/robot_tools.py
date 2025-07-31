"""Robot control tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from models import RobotID
from executors import robot_executor


def register_robot_tools(mcp: MCPLambdaHandler):
    """Register all robot-related tools with the MCP handler."""

    # Movement commands
    @mcp.tool()
    def robot_go_forward(robot_id: RobotID) -> str:
        """Command the robot to move forward in the direction it is currently facing.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is moving forward.
        """
        robot_executor.execute_action(robot_id, "go_forward")
        return "The robot is moving forward."

    @mcp.tool()
    def robot_back_fast(robot_id: RobotID) -> str:
        """Command the robot to move backward quickly.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is moving backward quickly.
        """
        robot_executor.execute_action(robot_id, "back_fast")
        return "The robot is moving backward quickly."

    @mcp.tool()
    def robot_left_move_fast(robot_id: RobotID) -> str:
        """Command the robot to move left quickly.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is moving left quickly.
        """
        robot_executor.execute_action(robot_id, "left_move_fast")
        return "The robot is moving left quickly."

    @mcp.tool()
    def robot_right_move_fast(robot_id: RobotID) -> str:
        """Command the robot to move right quickly.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is moving right quickly.
        """
        robot_executor.execute_action(robot_id, "right_move_fast")
        return "The robot is moving right quickly."

    # Posture commands
    @mcp.tool()
    def robot_stand(robot_id: RobotID) -> str:
        """Command the robot to stand up and maintain a standing position.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is standing up.
        """
        robot_executor.execute_action(robot_id, "stand")
        return "The robot is standing up."

    @mcp.tool()
    def robot_squat(robot_id: RobotID) -> str:
        """Command the robot to squat down.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is squatting down.
        """
        robot_executor.execute_action(robot_id, "squat")
        return "The robot is squatting down."

    @mcp.tool()
    def robot_squat_up(robot_id: RobotID) -> str:
        """Command the robot to stand up from a squat.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is standing up from a squat.
        """
        robot_executor.execute_action(robot_id, "squat_up")
        return "The robot is standing up from a squat."

    @mcp.tool()
    def robot_stand_up_back(robot_id: RobotID) -> str:
        """Command the robot to stand up from the back.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is standing up from the back.
        """
        robot_executor.execute_action(robot_id, "stand_up_back")
        return "The robot is standing up from the back."

    @mcp.tool()
    def robot_stand_up_front(robot_id: RobotID) -> str:
        """Command the robot to stand up from the front.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is standing up from the front.
        """
        robot_executor.execute_action(robot_id, "stand_up_front")
        return "The robot is standing up from the front."

    @mcp.tool()
    def robot_bow(robot_id: RobotID) -> str:
        """Command the robot to bow.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is bowing.
        """
        robot_executor.execute_action(robot_id, "bow")
        return "The robot is bowing."

    # Exercise commands
    @mcp.tool()
    def robot_push_ups(robot_id: RobotID) -> str:
        """Command the robot to perform push-ups.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing push-ups.
        """
        robot_executor.execute_action(robot_id, "push_ups")
        return "The robot is performing push-ups."

    @mcp.tool()
    def robot_sit_ups(robot_id: RobotID) -> str:
        """Command the robot to perform sit-ups.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing sit-ups.
        """
        robot_executor.execute_action(robot_id, "sit_ups")
        return "The robot is performing sit-ups."

    @mcp.tool()
    def robot_chest(robot_id: RobotID) -> str:
        """Command the robot to perform chest exercises.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing chest exercises.
        """
        robot_executor.execute_action(robot_id, "chest")
        return "The robot is performing chest exercises."

    @mcp.tool()
    def robot_stepping(robot_id: RobotID) -> str:
        """Command the robot to perform stepping motions.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing stepping motions.
        """
        robot_executor.execute_action(robot_id, "stepping")
        return "The robot is performing stepping motions."

    # Combat/martial arts commands
    @mcp.tool()
    def robot_left_kick(robot_id: RobotID) -> str:
        """Command the robot to perform a left kick.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing a left kick.
        """
        robot_executor.execute_action(robot_id, "left_kick")
        return "The robot is performing a left kick."

    @mcp.tool()
    def robot_right_kick(robot_id: RobotID) -> str:
        """Command the robot to perform a right kick.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing a right kick.
        """
        robot_executor.execute_action(robot_id, "right_kick")
        return "The robot is performing a right kick."

    @mcp.tool()
    def robot_left_shot_fast(robot_id: RobotID) -> str:
        """Command the robot to perform a fast left punch.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing a fast left punch.
        """
        robot_executor.execute_action(robot_id, "left_shot_fast")
        return "The robot is performing a fast left punch."

    @mcp.tool()
    def robot_right_shot_fast(robot_id: RobotID) -> str:
        """Command the robot to perform a fast right punch.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing a fast right punch.
        """
        robot_executor.execute_action(robot_id, "right_shot_fast")
        return "The robot is performing a fast right punch."

    @mcp.tool()
    def robot_left_uppercut(robot_id: RobotID) -> str:
        """Command the robot to perform a left uppercut.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing a left uppercut.
        """
        robot_executor.execute_action(robot_id, "left_uppercut")
        return "The robot is performing a left uppercut."

    @mcp.tool()
    def robot_right_uppercut(robot_id: RobotID) -> str:
        """Command the robot to perform a right uppercut.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing a right uppercut.
        """
        robot_executor.execute_action(robot_id, "right_uppercut")
        return "The robot is performing a right uppercut."

    @mcp.tool()
    def robot_kung_fu(robot_id: RobotID) -> str:
        """Command the robot to perform kung fu moves.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing kung fu moves.
        """
        robot_executor.execute_action(robot_id, "kung_fu")
        return "The robot is performing kung fu moves."

    @mcp.tool()
    def robot_wing_chun(robot_id: RobotID) -> str:
        """Command the robot to perform Wing Chun moves.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing Wing Chun moves.
        """
        robot_executor.execute_action(robot_id, "wing_chun")
        return "The robot is performing Wing Chun moves."

    # Additional exercise commands
    @mcp.tool()
    def robot_weightlifting(robot_id: RobotID) -> str:
        """Command the robot to perform weightlifting.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot is performing weightlifting.
        """
        robot_executor.execute_action(robot_id, "weightlifting")
        return "The robot is performing weightlifting."

    # Control commands
    @mcp.tool()
    def robot_stop(robot_id: RobotID) -> str:
        """Command the robot to stop all movement.

        Args:
            robot_id (RobotID): Robot ID

        Returns:
            str: The robot has stopped.
        """
        robot_executor.execute_action(robot_id, "stop")
        return "The robot has stopped."