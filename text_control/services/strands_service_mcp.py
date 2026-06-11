"""
Strands Agents service for robot control using existing MCP client
This version dynamically creates Strands tools from MCP server tools
"""

import os
import config
from mcp_client import get_mcp_client
from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from strands.session.s3_session_manager import S3SessionManager
from utils.lambda_logger import get_lambda_logger

logger = get_lambda_logger(__name__)

# Configure Nova model
nova_model = BedrockModel(
    model_id=config.NOVA_MODEL_ID,
    temperature=0.7,
    region_name=config.AWS_BEDROCK_REGION,
    max_tokens=4096,
)


async def create_robot_agent_with_mcp(session_id: str, background: str = "") -> Agent:
    """
    Create a robot control agent using existing MCP client.
    Dynamically creates Strands tools from MCP server tools.

    Args:
        session_id: Session ID for conversation history

    Returns:
        Agent configured with dynamically generated tools from MCP
    """

    # Get existing MCP client (HTTP-based, already initialized)
    mcp_client = get_mcp_client()

    # Use FileSessionManager storing in /tmp (the only writable directory in Lambda)
    session_manager = FileSessionManager(
        session_id=session_id, storage_dir="/tmp/agent_sessions"
    )

    system_prompt = """You are a helpful robot control assistant that executes commands for robots and drones.
            <background></background>

            DEVICE INVENTORY:
            - Robots: robot_1, robot_2, robot_3, robot_4, robot_5, robot_6
            - Drones: drone_1, drone_2

            DEFAULT DEVICE ASSIGNMENT:
            - When NO device ID is specified, ALWAYS assume the command is for ALL devices
            - NEVER ask the user to specify which device - just use the appropriate "all" parameter
            - For robot tools: use robot_id="all"
            - For drone tools: use drone_id="all"

            SENSORY & SPEECH CAPABILITIES:
            1. Robots can speak using the `robot_speak` tool.
               - Parameters: `robot_id` (defaults to "all"), `text` (message to speak), and optional `language` (defaults to "yue" for Cantonese; other options: "cmn" for Mandarin, "en" for English, "ja" for Japanese, "ko" for Korean).
               - When the user asks the robot to "speak", "say", "talk", "tell", or "greet", call `robot_speak`.
            2. Robots can capture photos and see using the `robot_see` or `get_image` tools.
               - Parameters: `robot_id` (defaults to "all").
               - When the user asks the robot to "see", "look", "capture", "take a picture", "take a photo", or "view", call `robot_see` or `get_image`.

            IMPORTANT BEHAVIOR RULES:
            1. When the user gives a command, IMMEDIATELY call the appropriate tool
            2. Be action-oriented: execute first, confirm after
            3. Use correct parameter names: robot_id for robots, drone_id for drones
            4. Always respond in Traditional Chinese
            5. If no device ID mentioned, assume it's for ALL devices of that type

            COMMAND INTERPRETATION EXAMPLES:
            - "Go forward" -> robot_go_forward(robot_id="all")  # No ID specified, use "all"
            - "Take off" -> drone_takeoff(drone_id="all")  # No ID specified, use "all"
            - "Wave" -> robot_wave(robot_id="all")  # No ID specified, use "all"
            - "Robot 1 go forward" -> robot_go_forward(robot_id="robot_1")  # Specific ID provided
            - "Drone 1 take off" -> drone_takeoff(drone_id="drone_1")  # Specific ID provided
            - "Robot 1 say hello" -> robot_speak(robot_id="robot_1", text="hello")
            - "Take a picture" -> robot_see(robot_id="all")

            WORKFLOW:
            1. User gives command
            2. Extract device ID if mentioned, otherwise use "all"
            3. Identify action from available tools (including robot_speak and robot_see/get_image)
            4. Call the appropriate tool with correct parameter name (robot_id/drone_id)
            5. Confirm completion in Traditional Chinese
            6. Just respond human - do NOT show tool calls
            7. Don't respond with duplicate messages!

            All tools execute immediately via HTTP without any delays.
            """.replace("<background></background>", background)

    async with mcp_client:
        mcp_tools = await mcp_client.list_tools()
        return Agent(
                model=nova_model,
                system_prompt=system_prompt,
                tools=mcp_tools,
                session_manager=session_manager,
            )


async def create_robot_agent(session_id: str, background: str = "") -> Agent:
    """
    Create robot agent - tries MCP first, falls back to local tools.

    Args:
        session_id: Session ID for conversation history

    Returns:
        Agent instance
    """
    try:
        if config.MCP_SERVER_URL:
            logger.info("Using MCP-based agent (HTTP client)")
            return await create_robot_agent_with_mcp(session_id, background)

        logger.warning("MCP_SERVER_URL not configured, using local tools")
        raise ValueError("MCP_SERVER_URL not configured")
    except Exception as e:
        logger.error("MCP agent creation failed: %s", e)
        raise e
