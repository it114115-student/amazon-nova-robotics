"""
Chat service - Handles Nova chatbot integration
"""

from typing import Any, Dict, List

import boto3
import config
from botocore.config import Config
from models.actions import get_available_actions, get_available_action_and_description
from services.database_service import get_robot


# Session storage for Nova conversation tracking
active_sessions = {}

# Initialize the Bedrock runtime client
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    config=Config(
        region_name=config.AWS_BEDROCK_REGION,
        retries={"max_attempts": 3, "mode": "standard"},
    ),
)


async def get_chat_response(
    user_message: str, selected_robot: str, session_id: str
) -> Dict[str, Any]:
    """Get a response from the Nova chatbot"""

    # Nova Chatbot system prompt
    SYSTEM_PROMPT = f"""
    You are a helpful robot and drone assistant. You control various robots and drones that can perform physical actions.

    <background></background>

    Available commands are: {', '.join(await get_available_action_and_description())}.

    When a user asks you to perform an action, respond in a friendly way and execute the command in order.
    If you need to execute multiple actions, separate them by commas, and don't said anything else.
    If you receive a simple command or list of commands, don't say anything else and return the commands.
    If a user asks for something that's not a valid action, politely inform them which actions are available.
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

    # Create or retrieve session history
    if session_id not in active_sessions:
        active_sessions[session_id] = []

    # Add user message to history
    active_sessions[session_id].append({"role": "user", "content": user_message})

    # Convert message history to the format expected by converse API
    messages = []
    for msg in active_sessions[session_id]:
        messages.append({"role": msg["role"], "content": [{"text": msg["content"]}]})

    system = [{"text": system_prompt}]

    # Call Nova via Bedrock API using converse method
    try:
        response = bedrock_runtime.converse(
            modelId=config.NOVA_MODEL_ID,
            messages=messages,
            system=system,
            inferenceConfig={"maxTokens": 1024, "temperature": 0.7, "topP": 0.9},
            additionalModelRequestFields={"inferenceConfig": {"topK": 20}},
        )

        bot_response = response["output"]["message"]["content"][0]["text"]

        # Add assistant response to history
        active_sessions[session_id].append(
            {"role": "assistant", "content": bot_response}
        )

        return {
            "response": bot_response,
            "session_id": session_id,
        }

    except Exception as e:
        print(f"Error calling Nova: {str(e)}")
        return {
            "response": f"I'm sorry, I encountered an error: {str(e)}",
            "session_id": session_id,
            "error": str(e),
        }


async def extract_actions_from_response(
    bot_response: str, user_message: str
) -> List[str]:
    """Extract action commands from bot response or user message"""
    # Check if Nova's response contains any of our robot commands
    potential_actions = []
    available_actions = await get_available_actions()

    for word in bot_response.split():
        word = "".join(char for char in word if char.isalnum() or char == "_")
        if word in available_actions:
            potential_actions.append(word)

    # If comma-separated commands are detected in the user input, prioritize those
    if "," in user_message:
        direct_commands = [item.strip() for item in user_message.split(",")]
        valid_commands = [cmd for cmd in direct_commands if cmd in available_actions]

        if valid_commands:
            return valid_commands

    return potential_actions
