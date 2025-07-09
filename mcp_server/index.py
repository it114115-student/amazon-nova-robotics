from enum import Enum

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from services.robot_service import execute_robot_action

mcp = MCPLambdaHandler(name="robotics-mcp-server", version="1.0.0")


class RobotID(str, Enum):
    ALL = "all"
    ROBOT_1 = "robot_1"
    ROBOT_2 = "robot_2"
    ROBOT_3 = "robot_3"
    ROBOT_4 = "robot_4"
    ROBOT_5 = "robot_5"
    ROBOT_6 = "robot_6"
    ROBOT_7 = "robot_7"
    ROBOT_8 = "robot_8"
    ROBOT_9 = "robot_9"
    ROBOT_10 = "robot_10"


class RobotExecutor:
    """Robot command executor that wraps the robot service"""

    def execute_action(self, robot_id: str, action: str) -> bool:
        """Execute a robot action"""
        return execute_robot_action(action.lower(), robot_id.lower())


executor = RobotExecutor()


@mcp.tool()
def back_fast(robot_id: RobotID) -> str:
    """Command the robot to move backward quickly.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is moving backward quickly.
    """
    executor.execute_action(robot_id, "back_fast")
    return "The robot is moving backward quickly."


@mcp.tool()
def bow(robot_id: RobotID) -> str:
    """Command the robot to bow.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is bowing.
    """
    executor.execute_action(robot_id, "bow")
    return "The robot is bowing."


@mcp.tool()
def chest(robot_id: RobotID) -> str:
    """Command the robot to perform chest exercises.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing chest exercises.
    """
    executor.execute_action(robot_id, "chest")
    return "The robot is performing chest exercises."


@mcp.tool()
def dance_eight(robot_id: RobotID) -> str:
    """Command the robot to perform dance eight.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance eight.
    """
    executor.execute_action(robot_id, "dance_eight")
    return "The robot is performing dance eight."


@mcp.tool()
def dance_five(robot_id: RobotID) -> str:
    """Command the robot to perform dance five.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance five.
    """
    executor.execute_action(robot_id, "dance_five")
    return "The robot is performing dance five."


@mcp.tool()
def dance_four(robot_id: RobotID) -> str:
    """Command the robot to perform dance four.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance four.
    """
    executor.execute_action(robot_id, "dance_four")
    return "The robot is performing dance four."


@mcp.tool()
def dance_nine(robot_id: RobotID) -> str:
    """Command the robot to perform dance nine.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance nine.
    """
    executor.execute_action(robot_id, "dance_nine")
    return "The robot is performing dance nine."


@mcp.tool()
def dance_seven(robot_id: RobotID) -> str:
    """Command the robot to perform dance seven.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance seven.
    """
    executor.execute_action(robot_id, "dance_seven")
    return "The robot is performing dance seven."


@mcp.tool()
def dance_six(robot_id: RobotID) -> str:
    """Command the robot to perform dance six.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance six.
    """
    executor.execute_action(robot_id, "dance_six")
    return "The robot is performing dance six."


@mcp.tool()
def dance_ten(robot_id: RobotID) -> str:
    """Command the robot to perform dance ten.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance ten.
    """
    executor.execute_action(robot_id, "dance_ten")
    return "The robot is performing dance ten."


@mcp.tool()
def dance_three(robot_id: RobotID) -> str:
    """Command the robot to perform dance three.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance three.
    """
    executor.execute_action(robot_id, "dance_three")
    return "The robot is performing dance three."


@mcp.tool()
def dance_two(robot_id: RobotID) -> str:
    """Command the robot to perform dance two.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance two.
    """
    executor.execute_action(robot_id, "dance_two")
    return "The robot is performing dance two."


@mcp.tool()
def go_forward(robot_id: RobotID) -> str:
    """Command the robot to move forward in the direction it is currently facing.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is moving forward.
    """
    executor.execute_action(robot_id, "go_forward")
    return "The robot is moving forward."


@mcp.tool()
def kung_fu(robot_id: RobotID) -> str:
    """Command the robot to perform kung fu moves.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing kung fu moves.
    """
    executor.execute_action(robot_id, "kung_fu")
    return "The robot is performing kung fu moves."


@mcp.tool()
def left_kick(robot_id: RobotID) -> str:
    """Command the robot to perform a left kick.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing a left kick.
    """
    executor.execute_action(robot_id, "left_kick")
    return "The robot is performing a left kick."


@mcp.tool()
def left_move_fast(robot_id: RobotID) -> str:
    """Command the robot to move left quickly.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is moving left quickly.
    """
    executor.execute_action(robot_id, "left_move_fast")
    return "The robot is moving left quickly."


@mcp.tool()
def left_shot_fast(robot_id: RobotID) -> str:
    """Command the robot to perform a fast left punch.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing a fast left punch.
    """
    executor.execute_action(robot_id, "left_shot_fast")
    return "The robot is performing a fast left punch."


@mcp.tool()
def left_uppercut(robot_id: RobotID) -> str:
    """Command the robot to perform a left uppercut.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing a left uppercut.
    """
    executor.execute_action(robot_id, "left_uppercut")
    return "The robot is performing a left uppercut."


@mcp.tool()
def push_ups(robot_id: RobotID) -> str:
    """Command the robot to perform push-ups.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing push-ups.
    """
    executor.execute_action(robot_id, "push_ups")
    return "The robot is performing push-ups."


@mcp.tool()
def right_kick(robot_id: RobotID) -> str:
    """Command the robot to perform a right kick.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing a right kick.
    """
    executor.execute_action(robot_id, "right_kick")
    return "The robot is performing a right kick."


@mcp.tool()
def right_move_fast(robot_id: RobotID) -> str:
    """Command the robot to move right quickly.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is moving right quickly.
    """
    executor.execute_action(robot_id, "right_move_fast")
    return "The robot is moving right quickly."


@mcp.tool()
def right_shot_fast(robot_id: RobotID) -> str:
    """Command the robot to perform a fast right punch.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing a fast right punch.
    """
    executor.execute_action(robot_id, "right_shot_fast")
    return "The robot is performing a fast right punch."


@mcp.tool()
def right_uppercut(robot_id: RobotID) -> str:
    """Command the robot to perform a right uppercut.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing a right uppercut.
    """
    executor.execute_action(robot_id, "right_uppercut")
    return "The robot is performing a right uppercut."


@mcp.tool()
def sit_ups(robot_id: RobotID) -> str:
    """Command the robot to perform sit-ups.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing sit-ups.
    """
    executor.execute_action(robot_id, "sit_ups")
    return "The robot is performing sit-ups."


@mcp.tool()
def squat(robot_id: RobotID) -> str:
    """Command the robot to squat down.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is squatting down.
    """
    executor.execute_action(robot_id, "squat")
    return "The robot is squatting down."


@mcp.tool()
def squat_up(robot_id: RobotID) -> str:
    """Command the robot to stand up from a squat.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is standing up from a squat.
    """
    executor.execute_action(robot_id, "squat_up")
    return "The robot is standing up from a squat."


@mcp.tool()
def stand(robot_id: RobotID) -> str:
    """Command the robot to stand up and maintain a standing position.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is standing up.
    """
    executor.execute_action(robot_id, "stand")
    return "The robot is standing up."


@mcp.tool()
def stand_up_back(robot_id: RobotID) -> str:
    """Command the robot to stand up from the back.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is standing up from the back.
    """
    executor.execute_action(robot_id, "stand_up_back")
    return "The robot is standing up from the back."


@mcp.tool()
def stand_up_front(robot_id: RobotID) -> str:
    """Command the robot to stand up from the front.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is standing up from the front.
    """
    executor.execute_action(robot_id, "stand_up_front")
    return "The robot is standing up from the front."


@mcp.tool()
def stepping(robot_id: RobotID) -> str:
    """Command the robot to perform stepping motions.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing stepping motions.
    """
    executor.execute_action(robot_id, "stepping")
    return "The robot is performing stepping motions."


@mcp.tool()
def stop(robot_id: RobotID) -> str:
    """Command the robot to perform stopping motions.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is stopping.
    """
    executor.execute_action(robot_id, "stop")
    return "The robot is stopping."


@mcp.tool()
def turn_left(robot_id: RobotID) -> str:
    """Command the robot to turn left.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is turning left.
    """
    executor.execute_action(robot_id, "turn_left")
    return "The robot is turning left."


@mcp.tool()
def turn_right(robot_id: RobotID) -> str:
    """Command the robot to turn right.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is turning right.
    """
    executor.execute_action(robot_id, "turn_right")
    return "The robot is turning right."


@mcp.tool()
def twist(robot_id: RobotID) -> str:
    """Command the robot to twist its body.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is twisting its body.
    """
    executor.execute_action(robot_id, "twist")
    return "The robot is twisting its body."


@mcp.tool()
def wave(robot_id: RobotID) -> str:
    """Command the robot to wave its hand.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is waving its hand.
    """
    executor.execute_action(robot_id, "wave")
    return "The robot is waving its hand."


@mcp.tool()
def weightlifting(robot_id: RobotID) -> str:
    """Command the robot to perform weightlifting.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing weightlifting.
    """
    executor.execute_action(robot_id, "weightlifting")
    return "The robot is performing weightlifting."


@mcp.tool()
def wing_chun(robot_id: RobotID) -> str:
    """Command the robot to perform Wing Chun moves.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing Wing Chun moves.
    """
    executor.execute_action(robot_id, "wing_chun")
    return "The robot is performing Wing Chun moves."


def handler(event, context):
    """AWS Lambda handler function."""
    return mcp.handle_request(event, context)
