"""
Strands Agents service for robot control
"""

import asyncio
import os

import config
from models.actions import get_available_actions
from services.robot_service import robot_service
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager

# Configure Nova model
nova_model = BedrockModel(
    model_id=config.NOVA_MODEL_ID,
    temperature=0.7,
    region_name=config.AWS_BEDROCK_REGION,
)


@tool
async def control_robot(robot_name: str, action: str) -> str:
    """Control a specific robot with an action"""
    results = await robot_service.process_actions([action], robot_name)
    return f"Robot {robot_name} executed {action}: {results[0]['success'] if results else 'failed'}"


@tool
async def list_available_actions() -> str:
    """Get list of available robot actions"""
    actions = await get_available_actions()
    return f"Available actions: {', '.join(actions)}"


@tool
async def control_multiple_robots(robot_names: str, action: str) -> str:
    """Control multiple robots with the same action (comma-separated names)"""
    robots = [name.strip() for name in robot_names.split(",")]
    tasks = [robot_service.process_actions([action], robot) for robot in robots]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(
        1 for r in results if r and not isinstance(r, Exception) and r[0]["success"]
    )
    return (
        f"Action {action} executed on {success_count}/{len(robots)} robots successfully"
    )


def create_robot_agent(session_id: str):
    """Create a robot control agent with session management"""
    session_manager = FileSessionManager(
        session_id=session_id, base_dir="./agent_sessions"
    )

    return Agent(
        model=nova_model,
        system_prompt="""You control robots, drones, and dogs through voice commands.
        
Available robots: robot_1 to robot_9, drone_1, dog_1 to dog_3
Use "all" to control all robots at once.

Execute user commands using available actions. Be concise and action-oriented.
Always confirm what action was performed on which robots.
Response in Traditional Chinese.
""",
        tools=[control_robot, list_available_actions, control_multiple_robots],
        session_manager=session_manager,
    )
