"""
Chat service - Handles Nova chatbot integration
"""

from typing import Any, Dict, List

import boto3
import config
from botocore.config import Config
from models.actions import get_available_action_and_description, get_available_actions
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
    You are a helpful robots, dogs and drones assistant. 
    You control various robots, dogs and drones that can perform physical actions.

    <background></background>

    Available commands are: {', '.join(await get_available_action_and_description())}.

    When a user asks you to perform an action, respond in a friendly way and execute the command in order.
    If you need to execute multiple actions, separate them by commas, and don't said anything else.
    If you receive a simple command or list of commands, don't say anything else and return the commands.
    If a user asks for something that's not a valid action, politely inform them which actions are available.

    Don't reply all commands at once and first drill down to the specific type of thing such as obots, dogs and drones.
    Dont't reply more than 3 sentances at once, and if the user asks for more information, provide it in a follow-up message.
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


async def classify_response_type(
    bot_response: str, user_message: str
) -> Dict[str, Any]:
    """
    Use Bedrock tool calling to classify if the bot response is a rephrase or contains commands
    Returns: {"type": "rephrase" | "commands", "commands": List[str], "confidence": float}
    """
    available_actions = await get_available_actions()
    actions_list = ", ".join(available_actions)

    # Define the tool for classification
    classification_tool = {
        "toolSpec": {
            "name": "classify_response",
            "description": "Classify a bot response as either conversational rephrase or containing commands",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "response_type": {
                            "type": "string",
                            "enum": ["rephrase", "commands"],
                            "description": "Whether the response is conversational (rephrase) or contains action commands",
                        },
                        "commands": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of valid robot/drone commands found in the response",
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence score for the classification",
                        },
                    },
                    "required": ["response_type", "commands", "confidence"],
                }
            },
        }
    }

    # Improved conversational indicator detection in fallback
    classification_prompt = f"""
    Analyze the following bot response and classify it:
    
    Available robot/drone commands: {actions_list}
    
    User message: "{user_message}"
    Bot response: "{bot_response}"
    
    Classification rules:
    - "rephrase": conversational response, greeting, explanation, or general chat (including phrases like 'here are the available ... actions')
    - "commands": contains actual robot/drone action commands to execute
    - Only include commands that exist in the available commands list
    - Provide confidence score between 0.0 and 1.0
    
    Use the classify_response tool to provide your analysis.
    """

    try:
        response = bedrock_runtime.converse(
            modelId=config.NOVA_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": classification_prompt}]}],
            toolConfig={
                "tools": [classification_tool],
                "toolChoice": {"any": {}},
            },
            inferenceConfig={"maxTokens": 200, "temperature": 0.1, "topP": 0.9},
        )

        # Extract tool use from response
        message_content = response["output"]["message"]["content"]
        for content in message_content:
            if "toolUse" in content:
                tool_input = content["toolUse"]["input"]

                # Validate and filter commands
                valid_commands = [
                    cmd
                    for cmd in tool_input.get("commands", [])
                    if cmd in available_actions
                ]

                # If too many commands found, likely a false positive
                if len(valid_commands) > 4:
                    valid_commands = []

                return {
                    "type": tool_input["response_type"],
                    "commands": valid_commands,
                    "confidence": tool_input["confidence"],
                }

    except Exception as e:
        print(f"Error in tool-based classification: {str(e)}")

    # Default to rephrase if tool classification fails
    return {"type": "rephrase", "commands": [], "confidence": 0.5}


async def extract_actions_from_response(
    bot_response: str, user_message: str
) -> List[str]:
    """Extract action commands from bot response or user message"""
    classification = await classify_response_type(bot_response, user_message)
    return classification["commands"]
