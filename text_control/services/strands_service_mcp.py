"""
Strands Agents service for robot control using existing MCP client
This version dynamically creates Strands tools from MCP server tools
"""

import asyncio

import config
from mcp_client import get_mcp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from utils.lambda_logger import get_lambda_logger

logger = get_lambda_logger(__name__)

# Configure Nova model
nova_model = BedrockModel(
    model_id=config.NOVA_MODEL_ID,
    temperature=0.7,
    region_name=config.AWS_BEDROCK_REGION,
)


def create_robot_agent_with_mcp(session_id: str):
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

    # Fetch available tools from MCP server synchronously
    async def get_tools():
        async with mcp_client:
            return await mcp_client.list_tools()

    mcp_tools = asyncio.run(get_tools())
    logger.info(f"Loaded {len(mcp_tools)} tools from MCP server")

    # Dynamically create Strands tools that wrap each MCP tool
    strands_tools = []

    for mcp_tool in mcp_tools:
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description

        # Determine the correct parameter name based on tool prefix
        # Handle both snake_case (dog_) and camelCase (dog, drone) prefixes
        param_name = "robot_id"  # default
        tool_name_lower = tool_name.lower()
        if tool_name_lower.startswith("dog"):
            param_name = "dog_id"
        elif tool_name_lower.startswith("drone"):
            param_name = "drone_id"

        # Create a closure to capture the tool_name and param_name
        def make_tool_function(name, description, parameter_name):
            # Create the function FIRST with correct name
            async def tool_func(robot_id: str) -> str:
                """
                Dynamically generated tool from MCP server.

                Args:
                    robot_id: ID of the robot/dog/drone (e.g., robot_1, dog_1, drone_1)

                Returns:
                    Result from MCP tool execution
                """
                try:
                    logger.info(
                        f"Calling MCP tool: {name} for {robot_id} using parameter '{parameter_name}'"
                    )
                    result = await mcp_client.call_tool(
                        name, {parameter_name: robot_id}
                    )
                    return str(result) if result else f"{name} executed successfully"
                except Exception as e:
                    logger.error(f"MCP tool {name} failed: {e}")
                    return f"Error: {str(e)}"

            # Set proper name and docstring BEFORE applying @tool decorator
            tool_func.__name__ = name
            tool_func.__doc__ = description or f"Execute {name} command"

            # Now apply the @tool decorator
            return tool(tool_func)

        strands_tools.append(
            make_tool_function(tool_name, tool_description, param_name)
        )

    logger.info(f"Created {len(strands_tools)} Strands tools from MCP")

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

DEFAULT DEVICE ASSIGNMENT:
- When NO device ID is specified, ALWAYS assume the command is for ALL devices
- NEVER ask the user to specify which device - just use robot_id="all"
- The "all" option will execute the command on all available devices of that type

IMPORTANT BEHAVIOR RULES:
1. When the user gives a command, IMMEDIATELY call the appropriate tool
2. Be action-oriented: execute first, confirm after
3. All tools accept robot_id parameter: "all", "robot_1", "robot_2", etc.
4. Always respond in Traditional Chinese
5. If no device ID mentioned, assume it's for ALL devices (robot_id="all")

COMMAND INTERPRETATION EXAMPLES:
- "Go forward" -> robot_go_forward(robot_id="all")  # No ID specified, use "all"
- "Sit" -> dog_sit(robot_id="all")  # No ID specified, use "all"
- "Take off" -> drone_takeoff(robot_id="all")  # No ID specified, use "all"
- "Wave" -> robot_wave(robot_id="all")  # No ID specified, use "all"
- "Robot 1 go forward" -> robot_go_forward(robot_id="robot_1")  # Specific ID provided
- "Dog 2 sit" -> dog_sit(robot_id="dog_2")  # Specific ID provided
- "Drone 1 take off" -> drone_takeoff(robot_id="drone_1")  # Specific ID provided

WORKFLOW:
1. User gives command
2. Extract device ID if mentioned, otherwise use "all"
3. Identify action from available tools
4. Call the appropriate tool with robot_id
5. Confirm completion in Traditional Chinese

All tools execute immediately via HTTP without any delays.
""",
        tools=strands_tools,
        session_manager=session_manager,
    )


def create_robot_agent(session_id: str):
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
            return create_robot_agent_with_mcp(session_id)
        else:
            logger.warning("MCP_SERVER_URL not configured, using local tools")
    except Exception as e:
        logger.warning(f"MCP agent creation failed: {e}, falling back to local tools")
