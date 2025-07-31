from enum import Enum
from typing import Dict

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from services.iot_service import (
    execute_dog_action,
    execute_drone_action,
    execute_robot_action,
)

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


class DogID(str, Enum):
    ALL = "all"
    DOG_1 = "dog_1"
    DOG_2 = "dog_2"


class DroneID(str, Enum):
    ALL = "all"
    DRONE_1 = "drone_1"
    DRONE_2 = "drone_2"


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACK = "back"


class RobotExecutor:
    """Robot command executor that wraps the robot service"""

    def execute_drone_action(self, drone_id: str, action: str, parameters: Dict = None):
        if parameters is None:
            parameters = {}
        # Map high-level actions to Tello SDK commands
        sdk_action = None
        sdk_params = None
        if action.startswith("move_"):
            direction = action.replace("move_", "")
            sdk_action = direction  # up, down, left, right, forward, back
            sdk_params = {"distance": parameters.get("x")}
        elif action == "rotate_clockwise":
            sdk_action = "cw"
            sdk_params = {"angle": parameters.get("x")}
        elif action == "rotate_counterclockwise":
            sdk_action = "ccw"
            sdk_params = {"angle": parameters.get("x")}
        elif action == "flip":
            sdk_action = "flip"
            sdk_params = {"direction": parameters.get("direction")}
        elif action in ["takeoff", "land"]:
            sdk_action = action
            sdk_params = {}
        else:
            sdk_action = action
            sdk_params = parameters
        message = {
            "droneID": drone_id.lower(),
            "action": sdk_action,
            "parameters": sdk_params,
        }
        return execute_drone_action(message)

    def execute_dog_action(self, dog_id: str, action: str, parameters: Dict = None):
        if parameters is None:
            parameters = {}
        # Map high-level actions to dog commands (similar to drone but no flying/flipping)
        sdk_action = None
        sdk_params = None
        if action.startswith("move_"):
            direction = action.replace("move_", "")
            sdk_action = direction  # left, right, forward, back (no up/down)
            sdk_params = {"distance": parameters.get("x")}
        elif action == "rotate_clockwise":
            sdk_action = "cw"
            sdk_params = {"angle": parameters.get("x")}
        elif action == "rotate_counterclockwise":
            sdk_action = "ccw"
            sdk_params = {"angle": parameters.get("x")}
        else:
            sdk_action = action
            sdk_params = parameters
        message = {
            "dogID": dog_id.lower(),
            "action": sdk_action,
            "parameters": sdk_params,
        }
        return execute_dog_action(message)

    def execute_action(self, robot_id: str, action: str) -> bool:
        """Execute a robot action"""
        return execute_robot_action(action, robot_id.lower())


robot_executor = RobotExecutor()


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


# Default distance for drone move commands (in cm)
DRONE_MOVE_DISTANCE_CM = 50


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


# Default distance for dog move commands (in cm)
DOG_MOVE_DISTANCE_CM = 50


@mcp.tool()
def dog_move_left(dog_id: DogID) -> str:
    """Command the dog to move left for DOG_MOVE_DISTANCE_CM cm.

    Args:
        dog_id (DogID): Dog ID

    Returns:
        str: The dog is moving left.
    """
    robot_executor.execute_dog_action(dog_id, "move_left", {"x": DOG_MOVE_DISTANCE_CM})
    return f"The dog is moving left for {DOG_MOVE_DISTANCE_CM} cm."


@mcp.tool()
def dog_move_right(dog_id: DogID) -> str:
    """Command the dog to move right for DOG_MOVE_DISTANCE_CM cm.

    Args:
        dog_id (DogID): Dog ID

    Returns:
        str: The dog is moving right.
    """
    robot_executor.execute_dog_action(dog_id, "move_right", {"x": DOG_MOVE_DISTANCE_CM})
    return f"The dog is moving right for {DOG_MOVE_DISTANCE_CM} cm."


@mcp.tool()
def dog_move_forward(dog_id: DogID) -> str:
    """Command the dog to move forward for DOG_MOVE_DISTANCE_CM cm.

    Args:
        dog_id (DogID): Dog ID

    Returns:
        str: The dog is moving forward.
    """
    robot_executor.execute_dog_action(
        dog_id, "move_forward", {"x": DOG_MOVE_DISTANCE_CM}
    )
    return f"The dog is moving forward for {DOG_MOVE_DISTANCE_CM} cm."


@mcp.tool()
def dog_move_back(dog_id: DogID) -> str:
    """Command the dog to move back for DOG_MOVE_DISTANCE_CM cm.

    Args:
        dog_id (DogID): Dog ID

    Returns:
        str: The dog is moving back.
    """
    robot_executor.execute_dog_action(dog_id, "move_back", {"x": DOG_MOVE_DISTANCE_CM})
    return f"The dog is moving back for {DOG_MOVE_DISTANCE_CM} cm."


@mcp.tool()
def dog_turn_right(dog_id: DogID) -> str:
    """Command the dog to turn right by a 90 degree angle.

    Args:
        dog_id (DogID): Dog ID
    Returns:
        str: The dog is turning right.
    """
    robot_executor.execute_dog_action(dog_id, "rotate_clockwise", {"x": 90})
    return "The dog is turning right by 90 degrees."


@mcp.tool()
def dog_turn_left(dog_id: DogID) -> str:
    """Command the dog to turn left by a 90 degree angle.

    Args:
        dog_id (DogID): Dog ID
    Returns:
        str: The dog is turning left.
    """
    robot_executor.execute_dog_action(dog_id, "rotate_counterclockwise", {"x": 90})
    return "The dog is turning left by 90 degrees."


@mcp.tool()
def dog_turn_back(dog_id: DogID) -> str:
    """Command the dog to turn back by 180 degrees.

    Args:
        dog_id (DogID): Dog ID

    Returns:
        str: The dog is turning back.
    """
    robot_executor.execute_dog_action(dog_id, "rotate_clockwise", {"x": 180})
    return "The dog is turning back by 180 degrees."


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
def robot_bow(robot_id: RobotID) -> str:
    """Command the robot to bow.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is bowing.
    """
    robot_executor.execute_action(robot_id, "bow")
    return "The robot is bowing."


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
def robot_dance_ten(robot_id: RobotID) -> str:
    """Command the robot to perform dance ten.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing dance ten.
    """
    robot_executor.execute_action(robot_id, "dance_ten")
    return "The robot is performing dance ten."


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
def robot_right_move_fast(robot_id: RobotID) -> str:
    """Command the robot to move right quickly.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is moving right quickly.
    """
    robot_executor.execute_action(robot_id, "right_move_fast")
    return "The robot is moving right quickly."


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
def robot_stepping(robot_id: RobotID) -> str:
    """Command the robot to perform stepping motions.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is performing stepping motions.
    """
    robot_executor.execute_action(robot_id, "stepping")
    return "The robot is performing stepping motions."


@mcp.tool()
def robot_stop(robot_id: RobotID) -> str:
    """Command the robot to perform stopping motions.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is stopping.
    """
    robot_executor.execute_action(robot_id, "stop")
    return "The robot is stopping."


@mcp.tool()
def robot_turn_left(robot_id: RobotID) -> str:
    """Command the robot to turn left.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is turning left.
    """
    robot_executor.execute_action(robot_id, "turn_left")
    return "The robot is turning left."


@mcp.tool()
def robot_turn_right(robot_id: RobotID) -> str:
    """Command the robot to turn right.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is turning right.
    """
    robot_executor.execute_action(robot_id, "turn_right")
    return "The robot is turning right."


@mcp.tool()
def robot_twist(robot_id: RobotID) -> str:
    """Command the robot to twist its body.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is twisting its body.
    """
    robot_executor.execute_action(robot_id, "twist")
    return "The robot is twisting its body."


@mcp.tool()
def robot_wave(robot_id: RobotID) -> str:
    """Command the robot to wave its hand.

    Args:
        robot_id (RobotID): Robot ID

    Returns:
        str: The robot is waving its hand.
    """
    robot_executor.execute_action(robot_id, "wave")
    return "The robot is waving its hand."


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


def handler(event, context):
    """AWS Lambda handler function."""
    return mcp.handle_request(event, context)


def handler(event, context):
    """AWS Lambda handler function."""
    return mcp.handle_request(event, context)
