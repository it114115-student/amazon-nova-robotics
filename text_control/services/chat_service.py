"""
Chat service - Handles Nova chatbot integration using Strands
"""

from typing import Any, Dict, List

import config
from models.actions import get_available_action_and_description, get_available_actions
from services.database_service import get_robot
import os
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from strands.session.s3_session_manager import S3SessionManager

# Configure Nova model
nova_model = BedrockModel(
    model_id=config.NOVA_MODEL_ID,
    temperature=0.7,
    region_name=config.AWS_BEDROCK_REGION,
)


@tool(name="classify_response", description="Classify a bot response as either conversational rephrase or containing commands")
async def classify_response_tool(
    response_type: str,  # "rephrase" or "commands"
    commands: List[str],  # List of valid robot/drone commands found
    confidence: float  # Confidence score 0.0-1.0
) -> Dict[str, Any]:
    """Tool for classifying bot responses"""
    return {
        "response_type": response_type,
        "commands": commands,
        "confidence": confidence
    }


async def get_chat_response(
    user_message: str, selected_robot: str, session_id: str
) -> Dict[str, Any]:
    """Get a response from the Nova chatbot using Strands"""

    # Nova Chatbot system prompt
    SYSTEM_PROMPT = f"""
    You are a helpful robots, dogs and drones assistant.
    You control various robots, dogs and drones that can perform physical actions.

    <background></background>

    Available commands are: {', '.join(await get_available_action_and_description())}.

    When a user asks you to perform an action, respond in a friendly way and execute the command in order.
    If you need to execute multiple actions, separate them by commas, and don't said anything else.
    If you receive a simple command or list of commands, don't say anything else and return the commands.
    If a user asks for something that's not a valid action, politely inform them which actions are available.

    Don't reply all commands at once and first drill down to the specific type of thing such as obots, dogs and drones.
    Don't reply more than 3 sentences at once, and if the user asks for more information, provide it in a follow-up message.

    Commands is in format dogMoveForward, droneRotateClockwise, robotMoveBackward, etc., and
    you need to rephrase it like "dog move forward", "drone rotate clockwise", "robot move backward" etc for user.
    """

    context = get_robot(selected_robot)
    if context:
        name = context.get("robot_name")
        background = context.get("context")
        system_prompt = SYSTEM_PROMPT.replace(
            "<background></background>",
            f"""
<background>Your Name:{name}
background: {background}
</background>
            """,
        )
    else:
        system_prompt = SYSTEM_PROMPT.replace("<background></background>", "")

    # Use FileSessionManager storing in /tmp (the only writable directory in Lambda)
    session_manager = FileSessionManager(
        session_id=str(session_id), storage_dir="/tmp/chat_sessions"
    )

    agent = Agent(
        model=nova_model,
        system_prompt=system_prompt,
        session_manager=session_manager,
    )

    try:
        # Get response from agent
        response = await agent.invoke_async(user_message)

        return {
            "response": str(response),
            "session_id": session_id,
        }

    except Exception as e:
        print(f"Error calling Nova via Strands: {str(e)}")
        return {
            "response": f"I'm sorry, I encountered an error: {str(e)}",
            "session_id": session_id,
            "error": str(e),
        }


async def classify_response_type(
    bot_response: str, user_message: str
) -> Dict[str, Any]:
    """
    Use Strands agent to classify if the bot response is a rephrase or contains commands
    """
    available_actions = await get_available_actions()
    actions_list = ", ".join(available_actions)

    classification_prompt = f"""
    Analyze the following bot response and classify it:

    Available robot/drone commands: {actions_list}

    User message: "{user_message}"
    Bot response: "{bot_response}"

    Classification rules:
    - "rephrase": conversational response, greeting, explanation, or general chat
    - "commands": contains actual robot/drone action commands to execute
    - Only include commands that exist in the available commands list
    - Provide confidence score between 0.0 and 1.0

    Use the classify_response tool to provide your analysis.
    """

    # Create classification agent
    classifier_agent = Agent(
        model=nova_model,
        system_prompt="You are a response classifier. Use the classify_response tool to analyze responses.",
        tools=[classify_response_tool],
    )

    try:
        result = await classifier_agent.invoke_async(classification_prompt)

        # Parse result if it's a tool call result
        if hasattr(result, 'get') and 'response_type' in result:
            return result

        # Fallback parsing
        return {"type": "rephrase", "commands": [], "confidence": 0.5}

    except Exception as e:
        print(f"Error in Strands classification: {str(e)}")
        return {"type": "rephrase", "commands": [], "confidence": 0.5}


async def extract_actions_from_response(
    bot_response: str, user_message: str
) -> List[str]:
    """Extract action commands from bot response or user message"""
    classification = await classify_response_type(bot_response, user_message)
    return classification.get("commands", [])
