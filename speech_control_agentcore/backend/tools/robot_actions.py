import logging
from typing import Optional
from strands import tool
from tools.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)

# ==========================================
# Humanoid Robot Tools
# ==========================================

@tool
def robot_stand(robot_id: str) -> dict:
    """Command the humanoid robot to stand up and maintain a standing position.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_stand({robot_id})")
    return call_mcp_tool("robot_stand", {"robot_id": robot_id})


@tool
def robot_squat(robot_id: str) -> dict:
    """Command the humanoid robot to squat down.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_squat({robot_id})")
    return call_mcp_tool("robot_squat", {"robot_id": robot_id})


@tool
def robot_squat_up(robot_id: str) -> dict:
    """Command the humanoid robot to stand up from a squat position.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_squat_up({robot_id})")
    return call_mcp_tool("robot_squat_up", {"robot_id": robot_id})


@tool
def robot_go_forward(robot_id: str) -> dict:
    """Command the humanoid robot to walk forward.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_go_forward({robot_id})")
    return call_mcp_tool("robot_go_forward", {"robot_id": robot_id})


@tool
def robot_back_fast(robot_id: str) -> dict:
    """Command the humanoid robot to walk backward quickly.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_back_fast({robot_id})")
    return call_mcp_tool("robot_back_fast", {"robot_id": robot_id})


@tool
def robot_left_move_fast(robot_id: str) -> dict:
    """Command the humanoid robot to slide left quickly.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_left_move_fast({robot_id})")
    return call_mcp_tool("robot_left_move_fast", {"robot_id": robot_id})


@tool
def robot_right_move_fast(robot_id: str) -> dict:
    """Command the humanoid robot to slide right quickly.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_right_move_fast({robot_id})")
    return call_mcp_tool("robot_right_move_fast", {"robot_id": robot_id})


@tool
def robot_dance_one(robot_id: str) -> dict:
    """Command the humanoid robot to perform dance sequence number one.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_dance_one({robot_id})")
    return call_mcp_tool("robot_dance_one", {"robot_id": robot_id})


@tool
def robot_dance_two(robot_id: str) -> dict:
    """Command the humanoid robot to perform dance sequence number two.

    Args:
        robot_id: The ID of the humanoid robot to control (e.g. 'robot_1').
    """
    logger.info(f"Tool invoked: robot_dance_two({robot_id})")
    return call_mcp_tool("robot_dance_two", {"robot_id": robot_id})


# ==========================================
# Drone Tools
# ==========================================

@tool
def drone_takeoff(drone_id: str) -> dict:
    """Command the drone to take off and hover in the air.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_takeoff({drone_id})")
    return call_mcp_tool("drone_takeoff", {"drone_id": drone_id})


@tool
def drone_land(drone_id: str) -> dict:
    """Command the drone to descend and land on the ground.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_land({drone_id})")
    return call_mcp_tool("drone_land", {"drone_id": drone_id})


@tool
def drone_move_up(drone_id: str) -> dict:
    """Command the drone to fly straight upwards.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_move_up({drone_id})")
    return call_mcp_tool("drone_move_up", {"drone_id": drone_id})


@tool
def drone_move_down(drone_id: str) -> dict:
    """Command the drone to fly straight downwards.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_move_down({drone_id})")
    return call_mcp_tool("drone_move_down", {"drone_id": drone_id})


@tool
def drone_move_left(drone_id: str) -> dict:
    """Command the drone to slide or fly to the left.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_move_left({drone_id})")
    return call_mcp_tool("drone_move_left", {"drone_id": drone_id})


@tool
def drone_move_right(drone_id: str) -> dict:
    """Command the drone to slide or fly to the right.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_move_right({drone_id})")
    return call_mcp_tool("drone_move_right", {"drone_id": drone_id})


@tool
def drone_move_forward(drone_id: str) -> dict:
    """Command the drone to fly forward.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_move_forward({drone_id})")
    return call_mcp_tool("drone_move_forward", {"drone_id": drone_id})


@tool
def drone_move_back(drone_id: str) -> dict:
    """Command the drone to fly backward.

    Args:
        drone_id: The ID of the drone to control (e.g. 'drone_1').
    """
    logger.info(f"Tool invoked: drone_move_back({drone_id})")
    return call_mcp_tool("drone_move_back", {"drone_id": drone_id})
