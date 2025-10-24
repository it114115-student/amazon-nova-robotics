"""
Strands Agents service for robot control
"""

import asyncio
from enum import Enum
from typing import List

import config
from models.actions import get_available_action_and_description, get_available_actions
from services.robot_service import robot_service
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager


# Define ID enums matching the MCP server models
class RobotID(str, Enum):
    ALL = "all"
    ROBOT_1 = "robot_1"
    ROBOT_2 = "robot_2"
    ROBOT_3 = "robot_3"
    ROBOT_4 = "robot_4"
    ROBOT_5 = "robot_5"
    ROBOT_6 = "robot_6"


class DogID(str, Enum):
    ALL = "all"
    DOG_1 = "dog_1"
    DOG_2 = "dog_2"
    DOG_3 = "dog_3"


class DroneID(str, Enum):
    ALL = "all"
    DRONE_1 = "drone_1"
    DRONE_2 = "drone_2"


# Helper functions to get ID lists
def get_robot_ids(include_all: bool = False) -> List[str]:
    """Get list of valid robot IDs"""
    ids = [robot.value for robot in RobotID if robot != RobotID.ALL]
    if include_all:
        ids.insert(0, RobotID.ALL.value)
    return ids


def get_dog_ids(include_all: bool = False) -> List[str]:
    """Get list of valid dog IDs"""
    ids = [dog.value for dog in DogID if dog != DogID.ALL]
    if include_all:
        ids.insert(0, DogID.ALL.value)
    return ids


def get_drone_ids(include_all: bool = False) -> List[str]:
    """Get list of valid drone IDs"""
    ids = [drone.value for drone in DroneID if drone != DroneID.ALL]
    if include_all:
        ids.insert(0, DroneID.ALL.value)
    return ids


def get_all_device_ids() -> List[str]:
    """Get all device IDs (robots, drones, and dogs)"""
    return get_robot_ids() + get_drone_ids() + get_dog_ids()


# Configure Nova model
nova_model = BedrockModel(
    model_id=config.NOVA_MODEL_ID,
    temperature=0.7,
    region_name=config.AWS_BEDROCK_REGION,
)


@tool
async def control_robot(robot_name: str, action: str) -> str:
    """Control a specific robot with an action"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    results = await robot_service.process_actions([action], robot_name)
    return f"Robot {robot_name} executed {action}: {results[0]['success'] if results else 'failed'}"


@tool
async def list_available_actions() -> str:
    """Get list of available robot actions with descriptions"""
    action_descriptions = await get_available_action_and_description()
    return "Available actions:\n" + "\n".join(action_descriptions)


@tool
async def control_multiple_robots(robot_names: str, action: str) -> str:
    """Control multiple robots with the same action (comma-separated names)"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    robots = [name.strip() for name in robot_names.split(",")]
    tasks = [robot_service.process_actions([action], robot) for robot in robots]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(
        1 for r in results if r and not isinstance(r, Exception) and r[0]["success"]
    )
    return (
        f"Action {action} executed on {success_count}/{len(robots)} robots successfully"
    )


@tool
async def list_available_robots() -> str:
    """Get list of all available robot IDs"""
    robots = get_robot_ids()
    return f"Available robots: {', '.join(robots)}"


@tool
async def list_available_dogs() -> str:
    """Get list of all available dog IDs"""
    dogs = get_dog_ids()
    return f"Available dogs: {', '.join(dogs)}"


@tool
async def list_available_drones() -> str:
    """Get list of all available drone IDs"""
    drones = get_drone_ids()
    return f"Available drones: {', '.join(drones)}"


@tool
async def list_all_devices() -> str:
    """Get list of all available device IDs (robots, dogs, and drones)"""
    all_ids = get_all_device_ids()
    return f"Available devices: {', '.join(all_ids)}"


@tool
async def control_robot_by_id(robot_id: RobotID, action: str) -> str:
    """Control a specific robot by its ID enum"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    results = await robot_service.process_actions([action], robot_id.value)
    return f"Robot {robot_id.value} executed {action}: {results[0]['success'] if results else 'failed'}"


@tool
async def control_dog_by_id(dog_id: DogID, action: str) -> str:
    """Control a specific dog by its ID enum"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    results = await robot_service.process_actions([action], dog_id.value)
    return f"Dog {dog_id.value} executed {action}: {results[0]['success'] if results else 'failed'}"


@tool
async def control_drone_by_id(drone_id: DroneID, action: str) -> str:
    """Control a specific drone by its ID enum"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    results = await robot_service.process_actions([action], drone_id.value)
    return f"Drone {drone_id.value} executed {action}: {results[0]['success'] if results else 'failed'}"


@tool
async def control_all_robots(action: str) -> str:
    """Control all robots with the same action"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    robot_ids = get_robot_ids()
    tasks = [
        robot_service.process_actions([action], robot_id) for robot_id in robot_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(
        1 for r in results if r and not isinstance(r, Exception) and r[0]["success"]
    )
    return f"Action {action} executed on {success_count}/{len(robot_ids)} robots successfully"


@tool
async def control_all_dogs(action: str) -> str:
    """Control all dogs with the same action"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    dog_ids = get_dog_ids()
    tasks = [robot_service.process_actions([action], dog_id) for dog_id in dog_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(
        1 for r in results if r and not isinstance(r, Exception) and r[0]["success"]
    )
    return (
        f"Action {action} executed on {success_count}/{len(dog_ids)} dogs successfully"
    )


@tool
async def control_all_drones(action: str) -> str:
    """Control all drones with the same action"""
    # Validate action is available
    available_actions = await get_available_actions()
    if action not in available_actions:
        return f"Error: Action '{action}' is not available. Use list_available_actions to see valid actions."

    drone_ids = get_drone_ids()
    tasks = [
        robot_service.process_actions([action], drone_id) for drone_id in drone_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(
        1 for r in results if r and not isinstance(r, Exception) and r[0]["success"]
    )
    return f"Action {action} executed on {success_count}/{len(drone_ids)} drones successfully"


def create_robot_agent(session_id: str):
    """Create a robot control agent with session management"""
    session_manager = FileSessionManager(
        session_id=session_id, base_dir="./agent_sessions"
    )

    return Agent(
        model=nova_model,
        system_prompt="""You are a helpful robot control assistant that executes commands for robots, drones, and dogs.

DEVICE INVENTORY:
- Robots: robot_1, robot_2, robot_3, robot_4, robot_5, robot_6
- Drones: drone_1, drone_2
- Dogs: dog_1, dog_2, dog_3

IMPORTANT BEHAVIOR RULES:
1. When the user gives a command, IMMEDIATELY use the appropriate control tool to execute it
2. Be action-oriented: execute first, confirm after
3. Use list_available_actions tool FIRST if you don't know what actions are available
4. If unsure which action to use, ask the user or check available actions
5. Always respond in Traditional Chinese

COMMAND INTERPRETATION EXAMPLES:
- "Robot 1 go forward" → control_robot(robot_id="robot_1", action="robot_move_forward")
- "All dogs sit" → control_all_dogs(action="dog_sit")
- "Move drone 2 up" → control_drone_by_id(drone_id=DRONE_2, action="drone_move_up")
- "Make all robots wave" → control_all_robots(action="robot_wave")

ACTION NAMING PATTERN:
- Robot actions typically start with "robot_" (e.g., robot_move_forward, robot_wave)
- Dog actions typically start with "dog_" (e.g., dog_move_forward, dog_sit)
- Drone actions typically start with "drone_" (e.g., drone_move_up, drone_rotate_clockwise)

WORKFLOW:
1. User gives command
2. Identify device(s) and action
3. Execute using appropriate tool
4. Confirm completion in Traditional Chinese

Be concise and action-focused. Execute commands immediately without excessive explanation.
""",
        tools=[
            control_robot,
            list_available_actions,
            control_multiple_robots,
            list_available_robots,
            list_available_dogs,
            list_available_drones,
            list_all_devices,
            control_robot_by_id,
            control_dog_by_id,
            control_drone_by_id,
            control_all_robots,
            control_all_dogs,
            control_all_drones,
        ],
        session_manager=session_manager,
    )
