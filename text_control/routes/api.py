"""
API routes - Handles all API endpoints
"""

import asyncio
import hashlib
import os
import uuid
from datetime import datetime

from command_config.simple_commands import SIMPLE_COMMANDS
from flask import Blueprint, jsonify, request
from middleware import require_hybrid_auth
from services.chat_service import extract_actions_from_response, get_chat_response
from services.database_service import delete_robot, get_robot, list_robots, upsert_robot
from services.robot_service import robot_service
from utils.command_normalization import find_matching_command
from utils.lambda_logger import get_lambda_logger

# Configure logging for AWS Lambda
logger = get_lambda_logger(__name__)

# Create a blueprint for the API routes
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/chat", methods=["POST"])
@require_hybrid_auth
async def chat():
    try:
        data = await request.get_json()
    except Exception:
        data = request.json or {}
    return await _chat(data)


def error_response(status_code, message):
    """Returns a consistent JSON error response."""
    response = jsonify({"error": {"code": status_code, "message": message}})
    response.status_code = status_code
    return response


def calculate_signature(secret_key: str, timestamp: str, body_string: str) -> str:
    """Calculate signature for authentication"""
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


@api_bp.route("/xiaoice-chat-api", methods=["POST"])
async def chat_api():
    """
    Direct chat API endpoint with authentication and response mapping
    Replaces the proxy functionality with direct processing
    """
    logger.info(f"Chat API request from {request.remote_addr}")

    # 1. Extract request
    try:
        if not request.json:
            logger.warning("Bad request: Request body must be JSON")
            return error_response(400, "Request body must be JSON")

        # Required parameters
        required_params = ["askText", "sessionId", "traceId"]
        for param in required_params:
            if param not in request.json:
                logger.warning(f"Bad request: Missing required parameter: {param}")
                return error_response(400, f"Missing required parameter: {param}")

        ask_text = request.json["askText"]
        session_id = request.json["sessionId"]
        trace_id = request.json["traceId"]
        extra = request.json.get("extra", {})

        if not isinstance(extra, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in extra.items()
        ):
            logger.warning(
                "Bad request: 'extra' parameter must be a dictionary with string key-value pairs"
            )
            return error_response(
                400,
                "'extra' parameter must be a dictionary with string key-value pairs",
            )

        logger.info(f"Request parsed - TraceId: {trace_id}, SessionId: {session_id}")

    except Exception as e:
        logger.error(f"Error parsing request: {e}", exc_info=True)
        return error_response(400, f"Error parsing request: {e}")

    # 2. Authentication check
    try:
        timestamp = request.headers.get("timestamp")
        signature = request.headers.get("signature")
        access_key = request.headers.get("key")

        stored_secret_key = os.getenv("ChatSecretKey", "your_actual_secret_key")
        valid_access_key = os.getenv("ChatAccessKey", "your_actual_access_key")

        if not all([stored_secret_key, valid_access_key]):
            logger.error("Server configuration error: Missing environment variables")
            return error_response(500, "Server configuration error")

        if not all([timestamp, signature, access_key]):
            logger.warning("Authentication failed: Missing authentication headers")
            return error_response(401, "Missing authentication headers")

        if access_key != valid_access_key:
            logger.warning(
                f"Authentication failed: Invalid access key received: {access_key}"
            )
            return error_response(401, "Invalid access key")

        body_string = request.data.decode("utf-8")
        calculated_signature = calculate_signature(
            stored_secret_key, timestamp, body_string
        )

        if calculated_signature != signature:
            logger.warning("Authentication failed: Invalid signature")
            return error_response(401, "Invalid signature")

        logger.info("Authentication successful")

    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        return error_response(401, f"Authentication failed: {e}")

    # 3. Call _chat with mapped parameters
    try:
        # Map the request parameters to the internal _chat format
        chat_data = {
            "message": ask_text,
            "robots": [
                "all"
            ],  # Default to all robots, can be customized based on extra params
            "session_id": session_id,
        }

        # Check if streaming is requested
        is_streaming = request.args.get("stream", "false").lower() == "true"
        logger.info(f"Streaming requested: {is_streaming}")

        # Call the internal chat function
        chat_response = await _chat(chat_data)

        # 4. Map the output to the expected format
        if isinstance(chat_response, tuple):
            # Handle error responses
            response_data, status_code = chat_response
            if status_code != 200:
                return chat_response
            response_data = response_data.get_json()
        else:
            response_data = chat_response.get_json()

        # Map to the expected response format
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

        mapped_response = {
            "id": formatted_time,
            "traceId": trace_id,
            "sessionId": session_id,
            "askText": ask_text,
            "replyText": response_data.get("response", ""),
            "replyType": "Llm",
            "timestamp": now.timestamp(),
        }

        logger.info(f"Chat API response generated for trace: {trace_id}")
        logger.info(f"Response data: {mapped_response}")

        return jsonify(mapped_response)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return error_response(500, f"Error processing chat request: {e}")


async def _chat(data):
    """Handle chat requests with Nova Chatbot integration"""
    user_message = data.get("message")
    selected_robots = data.get("robots")
    session_id = data.get("session_id", str(uuid.uuid4()))

    # For backward compatibility, if robots is not a list, make it a list
    if not isinstance(selected_robots, list):
        selected_robots = [selected_robots] if selected_robots else []

    # Get response from Nova chatbot (use first robot for context, or None)
    context_robot = selected_robots[0] if selected_robots else None
    response_data = await get_chat_response(user_message, context_robot, session_id)

    if "error" in response_data:
        return jsonify(response_data), 500

    # Optimize classification - check for simple commands first with normalization
    user_message_lower = user_message.lower().strip()
    bot_response = response_data["response"]

    # Check if user message is a simple command (with normalization)
    matched_command = find_matching_command(user_message, SIMPLE_COMMANDS)
    if matched_command:
        logger.info(f"Simple command detected: '{user_message}' -> '{matched_command}'")
        actions_to_execute = [matched_command]
    else:
        # Check if any word in the message is a simple command (with normalization)
        words = user_message_lower.split()
        simple_action_found = None

        for word in words:
            matched_word_command = find_matching_command(word, SIMPLE_COMMANDS)
            if matched_word_command:
                simple_action_found = matched_word_command
                logger.info(
                    f"Simple action found in message: '{word}' -> '{matched_word_command}'"
                )
                break

        if simple_action_found:
            actions_to_execute = [simple_action_found]
        else:
            # Fall back to full classification for complex requests
            logger.info("Complex request detected, using full classification")
            actions_to_execute = await extract_actions_from_response(
                bot_response, user_message
            )

    logger.debug(f"Actions to execute: {actions_to_execute}")

    # Handle special robot selections
    actions_executed = []
    robots_to_use = []

    if "all" in selected_robots:
        # If 'all' is selected, send to all individual robots, drones, and dogs
        individual_robots = [f"robot_{i}" for i in range(1, 10)]  # robot_1 to robot_9
        individual_drones = ["drone_1", "drone_2"]
        individual_dogs = ["dog_1", "dog_2", "dog_3"]
        robots_to_use = individual_robots + individual_drones + individual_dogs
    else:
        # Handle other selections (individual robots, groups, or combinations)
        robots_to_use = selected_robots

    # Optimization: Process robot actions in parallel instead of sequentially
    if actions_to_execute and robots_to_use:
        logger.info(f"Processing actions for {len(robots_to_use)} robots in parallel")

        # Create tasks for parallel execution
        tasks = []
        for robot in robots_to_use:
            task = asyncio.create_task(
                robot_service.process_actions(actions_to_execute, robot)
            )
            tasks.append((robot, task))

        # Execute all tasks concurrently
        for robot, task in tasks:
            try:
                execution_results = await task
                actions_executed.append({"robot": robot, "results": execution_results})
            except Exception as e:
                logger.error(f"Error executing actions for robot {robot}: {e}")
                actions_executed.append(
                    {
                        "robot": robot,
                        "results": [
                            {"action": "error", "success": False, "error": str(e)}
                        ],
                    }
                )

    if actions_executed:
        response_data["actions_executed"] = actions_executed

    return jsonify(response_data)


@api_bp.route("/robots", methods=["GET"])
@require_hybrid_auth
def get_robots():
    robots = list_robots()
    return jsonify(robots)


@api_bp.route("/robots/<robot_id>", methods=["GET"])
@require_hybrid_auth
def get_robot_by_id(robot_id):
    robot = get_robot(robot_id)
    if robot:
        return jsonify(robot)
    return jsonify({"error": "Not found"}), 404


@api_bp.route("/robots", methods=["POST"])
@require_hybrid_auth
def create_robot():
    data = request.json
    robot_id = data.get("id")
    if not robot_id:
        return jsonify({"error": "Missing id"}), 400
    robot = upsert_robot(robot_id, data)
    return jsonify(robot), 201


@api_bp.route("/robots/<robot_id>", methods=["PUT"])
@require_hybrid_auth
def robot_update(robot_id):
    data = request.json
    robot = upsert_robot(robot_id, data)
    return jsonify(robot)


@api_bp.route("/robots/<robot_id>", methods=["DELETE"])
@require_hybrid_auth
def robot_delete(robot_id):
    delete_robot(robot_id)
    return jsonify({"deleted": True})


@api_bp.route("/run_action/<robot_id>", methods=["GET", "POST"])
@require_hybrid_auth
async def run_action(robot_id):
    """Run process_actions with provided action and robot"""
    try:
        data = await request.get_json()
    except Exception:
        # Fallback to synchronous request.json if async fails
        data = request.json or {}

    robot = robot_id or data.get("robot")
    method = data.get("method")
    action = data.get("action")

    logger.info(
        f"Running action for robot: {robot}, method: {method}, action: {action}"
    )

    if not method or not action or not robot:
        return jsonify({"error": "Missing robot or method or params."}), 400

    if method == "RunAction":
        results = await robot_service.process_actions([action], robot)
        return jsonify({"results": results})
    if method == "StopAction":
        results = await robot_service.process_actions(["stop"], robot)
        return jsonify({"results": results})
    return jsonify({"error": "Invalid method"}), 400
