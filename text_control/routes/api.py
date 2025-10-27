"""
API routes - Handles all API endpoints
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime

from command_config.simple_commands import SIMPLE_COMMANDS
from flask import Blueprint, Response, jsonify, request
from middleware import require_hybrid_auth
from services.chat_service import extract_actions_from_response, get_chat_response
from services.database_service import delete_robot, get_robot, list_robots, upsert_robot
from services.robot_service import robot_service
from services.strands_service_mcp import create_robot_agent as create_robot_agent_mcp
from utils.command_normalization import find_matching_command

# Suppress OpenTelemetry context warnings (harmless in async streaming context)
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)
from utils.lambda_logger import get_lambda_logger

# Configure logging for AWS Lambda
logger = get_lambda_logger(__name__)

# Create a blueprint for the API routes
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/chat", methods=["POST"])
@require_hybrid_auth
def chat():
    try:
        data = request.get_json(silent=True) or request.json or {}
    except Exception:
        data = request.json or {}
    return asyncio.run(_chat(data))


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


def calculate_signature_v2(secret_key: str, timestamp: str, body_string: str) -> str:
    """
    Calculate signature for authentication following the vendor specification.

    Algorithm:
    1. Build a parameter Map with: secretKey, timestamp, bodyString
    2. Sort parameters by key name in ascending order and connect with "&"
       Format: key1=value1&key2=value2&key3=value3
    3. Calculate SHA-512 hash and convert to UPPERCASE

    Args:
        secret_key: Server-side (user) preset secret key
        timestamp: Request timestamp (milliseconds)
        body_string: JSON serialized string of request body

    Returns:
        Uppercase SHA-512 hash string
    """
    # Create parameter map
    params = {
        "bodyString": body_string,
        "secretKey": secret_key,
        "timestamp": timestamp,
    }

    # Sort by key name in ascending order and create signature string
    sorted_params = sorted(params.items())
    signature_string = "&".join([f"{k}={v}" for k, v in sorted_params])

    # Calculate SHA-512 hash
    sha512 = hashlib.sha512()
    sha512.update(signature_string.encode("utf-8"))
    hex_digest = sha512.hexdigest()

    # Convert to uppercase (SHA-512 hex digest doesn't contain "-", but keep the replace for safety)
    return hex_digest.replace("-", "").upper()


def validate_authentication(use_v2=True):
    """
    Validates authentication headers and returns error response if invalid.

    Args:
        use_v2: If True, use calculate_signature_v2, otherwise use calculate_signature

    Returns:
        None if authentication is successful, error_response tuple otherwise
    """
    try:
        # Get headers (support both X- prefixed and non-prefixed)
        timestamp = request.headers.get("X-Timestamp") or request.headers.get(
            "timestamp"
        )
        signature = request.headers.get("X-Sign") or request.headers.get("signature")
        access_key = request.headers.get("X-Key") or request.headers.get("key")

        stored_secret_key = os.getenv("XiaoiceChatSecretKey")
        valid_access_key = os.getenv("XiaoiceChatAccessKey")

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

        if use_v2:
            calculated_signature = calculate_signature_v2(
                stored_secret_key, timestamp, body_string
            )
        else:
            calculated_signature = calculate_signature(
                stored_secret_key, timestamp, body_string
            )

        if calculated_signature != signature:
            logger.warning("Authentication failed: Invalid signature")
            return error_response(401, "Invalid signature")

        logger.info("Authentication successful")
        return None

    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        return error_response(401, f"Authentication failed: {e}")


def parse_request_params(required_params=None):
    """
    Parses and validates request parameters.

    Args:
        required_params: List of required parameter names

    Returns:
        Tuple of (params_dict, error_response). If error_response is not None,
        an error occurred and should be returned.
    """
    try:
        if not request.json:
            logger.warning("Bad request: Request body must be JSON")
            return None, error_response(400, "Request body must be JSON")

        params = {}
        required = required_params or []

        # Validate required parameters
        for param in required:
            if param not in request.json:
                logger.warning(f"Bad request: Missing required parameter: {param}")
                return None, error_response(400, f"Missing required parameter: {param}")

        # Extract common parameters
        params["ask_text"] = request.json.get("askText", "")
        params["session_id"] = request.json.get("sessionId", str(uuid.uuid4()))
        params["trace_id"] = request.json.get("traceId", str(uuid.uuid4()))
        params["extra"] = request.json.get("extra", {})
        params["language_code"] = request.json.get("languageCode", "zh")
        params["device_id"] = request.json.get("deviceId", "")
        params["user_params"] = request.json.get("userParams", "")
        params["lang_by_asr"] = request.json.get("langByAsr", "")

        logger.info(
            f"Request parsed - TraceId: {params['trace_id']}, SessionId: {params['session_id']}"
        )
        return params, None

    except Exception as e:
        logger.error(f"Error parsing request: {e}", exc_info=True)
        return None, error_response(400, f"Error parsing request: {e}")


def create_response_object(params, reply_text, is_final=True):
    """
    Creates a standardized response object.

    Args:
        params: Dictionary containing request parameters (trace_id, session_id, etc.)
        reply_text: The reply text to send
        is_final: Whether this is the final response

    Returns:
        Dictionary with standardized response format
    """
    return {
        "askText": params.get("ask_text", ""),
        "extra": params.get("extra", {}),
        "id": str(uuid.uuid4()),
        "replyPayload": None,
        "replyText": reply_text,
        "replyType": "Llm",
        "sessionId": params["session_id"],
        "timestamp": int(time.time() * 1000),
        "traceId": params["trace_id"],
        "isFinal": is_final,
    }


@api_bp.route("talk", methods=["POST"])
def talk_stream():
    """
    SSE streaming endpoint using Strands Agents
    Compatible with XiaoIce API specification
    """
    logger.info(f"Talk stream request from {request.remote_addr}")

    # 1. Authentication check
    auth_error = validate_authentication(use_v2=True)
    if auth_error:
        return auth_error

    # 2. Parse request
    params, parse_error = parse_request_params(
        required_params=["askText", "sessionId", "traceId"]
    )
    if parse_error:
        return parse_error

    ask_text = params["ask_text"]
    session_id = params["session_id"]
    trace_id = params["trace_id"]
    extra = params["extra"]

    # 3. Create Strands agent and stream response
    try:
        agent = create_robot_agent_mcp(session_id)

        def stream_response():
            try:

                async def async_stream():
                    THINKING_START = "<thinking>"
                    THINKING_END = "</thinking>"

                    buffer = ""
                    inside_thinking = False
                    chunk_count = 0

                    async for event in agent.stream_async(ask_text):
                        # Extract text content from event
                        event_data = event.get("data") or event.get("result", "")
                        if not event_data:
                            continue

                        # Convert to string if needed
                        if not isinstance(event_data, str):
                            event_data = str(event_data)

                        buffer += event_data

                        # Process buffer to filter out thinking tags
                        while True:
                            if inside_thinking:
                                end_idx = buffer.find(THINKING_END)
                                if end_idx == -1:
                                    # Keep potential partial match at end
                                    buffer = buffer[-len(THINKING_END) + 1 :]
                                    break
                                buffer = buffer[end_idx + len(THINKING_END) :]
                                inside_thinking = False
                                continue

                            start_idx = buffer.find(THINKING_START)
                            if start_idx == -1:
                                # Check for partial thinking tag at end of buffer
                                for i in range(1, len(THINKING_START)):
                                    if buffer.endswith(THINKING_START[:i]):
                                        text_to_send = buffer[:-i]
                                        if text_to_send:
                                            chunk_count += 1
                                            chunk = {
                                                "askText": ask_text,
                                                "extra": extra,
                                                "id": f"{trace_id}_{chunk_count}",
                                                "replyPayload": None,
                                                "replyText": text_to_send,
                                                "replyType": "Llm",
                                                "sessionId": session_id,
                                                "timestamp": int(time.time() * 1000),
                                                "traceId": trace_id,
                                                "isFinal": False,
                                            }
                                            yield f"data: {json.dumps(chunk)}\n\n"
                                        buffer = buffer[-i:]
                                        break
                                else:
                                    # No partial match, send entire buffer
                                    if buffer:
                                        chunk_count += 1
                                        chunk = {
                                            "askText": ask_text,
                                            "extra": extra,
                                            "id": f"{trace_id}_{chunk_count}",
                                            "replyPayload": None,
                                            "replyText": buffer,
                                            "replyType": "Llm",
                                            "sessionId": session_id,
                                            "timestamp": int(time.time() * 1000),
                                            "traceId": trace_id,
                                            "isFinal": False,
                                        }
                                        yield f"data: {json.dumps(chunk)}\n\n"
                                        buffer = ""
                                break

                            # Found thinking tag start
                            text_before = buffer[:start_idx]
                            if text_before:
                                chunk_count += 1
                                chunk = {
                                    "askText": ask_text,
                                    "extra": extra,
                                    "id": f"{trace_id}_{chunk_count}",
                                    "replyPayload": None,
                                    "replyText": text_before,
                                    "replyType": "Llm",
                                    "sessionId": session_id,
                                    "timestamp": int(time.time() * 1000),
                                    "traceId": trace_id,
                                    "isFinal": False,
                                }
                                yield f"data: {json.dumps(chunk)}\n\n"

                            buffer = buffer[start_idx + len(THINKING_START) :]
                            inside_thinking = True

                    # Send final chunk with any remaining buffer
                    if buffer and not inside_thinking:
                        chunk_count += 1
                        chunk = {
                            "askText": ask_text,
                            "extra": extra,
                            "id": f"{trace_id}_{chunk_count}",
                            "replyPayload": None,
                            "replyText": buffer,
                            "replyType": "Llm",
                            "sessionId": session_id,
                            "timestamp": int(time.time() * 1000),
                            "traceId": trace_id,
                            "isFinal": False,
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Always send final marker
                    chunk_count += 1
                    final_chunk = {
                        "askText": ask_text,
                        "extra": extra,
                        "id": f"{trace_id}_{chunk_count}",
                        "replyPayload": None,
                        "replyText": "",
                        "replyType": "Llm",
                        "sessionId": session_id,
                        "timestamp": int(time.time() * 1000),
                        "traceId": trace_id,
                        "isFinal": True,
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"

                # Create a wrapper to run the async generator
                def run_async_gen():
                    """Run async generator and yield results"""
                    loop = asyncio.new_event_loop()
                    try:
                        async_gen = async_stream()
                        while True:
                            try:
                                chunk = loop.run_until_complete(async_gen.__anext__())
                                yield chunk
                            except StopAsyncIteration:
                                break
                    finally:
                        loop.close()

                # Yield from the async generator wrapper
                for chunk in run_async_gen():
                    yield chunk
                    # Force flush to prevent log truncation
                    import sys
                    sys.stdout.flush()
                    sys.stderr.flush()

            except Exception as e:
                logger.error(f"Error in stream_response: {e}", exc_info=True)
                error_chunk = {
                    "askText": ask_text,
                    "extra": extra,
                    "id": trace_id,
                    "replyPayload": None,
                    "replyText": f"Error: {str(e)}",
                    "replyType": "Error",
                    "sessionId": session_id,
                    "timestamp": int(time.time() * 1000),
                    "traceId": trace_id,
                    "isFinal": True,
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return Response(
            stream_response(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except Exception as e:
        logger.error(f"Error creating agent or streaming: {e}", exc_info=True)
        return error_response(500, f"Error processing request: {e}")


@api_bp.route("welcome", methods=["POST"])
def welcome():
    """
    Welcome message endpoint
    Returns a welcome message for the conversation system
    """
    logger.info(f"Welcome request from {request.remote_addr}")

    # 1. Authentication check
    auth_error = validate_authentication(use_v2=True)
    if auth_error:
        return auth_error

    # 2. Parse request
    params, parse_error = parse_request_params()
    if parse_error:
        return parse_error

    # 3. Generate welcome response
    try:
        welcome_messages = {
            "zh": "你好！我是智能助手，很高兴为您服务。有什么我可以帮助您的吗？",
            "en": "Hello! I'm your AI assistant. How can I help you today?",
        }

        welcome_text = welcome_messages.get(
            params["language_code"], welcome_messages["zh"]
        )
        response = create_response_object(params, welcome_text)

        logger.info(f"Welcome response generated for trace: {params['trace_id']}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error generating welcome: {e}", exc_info=True)
        return error_response(500, f"Error generating welcome: {e}")


@api_bp.route("goodbye", methods=["POST"])
def goodbye():
    """
    Goodbye message endpoint
    Returns a goodbye message for the conversation system
    """
    logger.info(f"Goodbye request from {request.remote_addr}")

    # 1. Authentication check
    auth_error = validate_authentication(use_v2=True)
    if auth_error:
        return auth_error

    # 2. Parse request
    params, parse_error = parse_request_params()
    if parse_error:
        return parse_error

    # 3. Generate goodbye response
    try:
        goodbye_messages = {
            "zh": "再见！期待下次为您服务。",
            "en": "Goodbye! Looking forward to serving you again.",
        }

        goodbye_text = goodbye_messages.get(
            params["language_code"], goodbye_messages["zh"]
        )
        response = create_response_object(params, goodbye_text)

        logger.info(f"Goodbye response generated for trace: {params['trace_id']}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error generating goodbye: {e}", exc_info=True)
        return error_response(500, f"Error generating goodbye: {e}")


@api_bp.route("recquestions", methods=["POST"])
def recquestions():
    """
    Recommended questions endpoint
    Returns a list of recommended questions for the user
    """
    logger.info(f"Recommended questions request from {request.remote_addr}")

    # 1. Authentication check
    auth_error = validate_authentication(use_v2=True)
    if auth_error:
        return auth_error

    # 2. Parse request
    params, parse_error = parse_request_params()
    if parse_error:
        return parse_error

    # 3. Generate recommended questions
    try:
        recommended_questions = {
            "zh": [
                "你能做什么？",
                "帮我控制机器人",
                "机器人向前移动",
                "停止所有动作",
                "显示机器人状态",
            ],
            "en": [
                "What can you do?",
                "Help me control the robot",
                "Move the robot forward",
                "Stop all actions",
                "Show robot status",
            ],
        }

        questions = recommended_questions.get(
            params["language_code"], recommended_questions["zh"]
        )

        response = {"data": questions, "traceId": params["trace_id"]}

        logger.info(f"Recommended questions generated for trace: {params['trace_id']}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error generating recommended questions: {e}", exc_info=True)
        return error_response(500, f"Error generating recommended questions: {e}")


@api_bp.route("/xiaoice-chat-api-strands", methods=["POST"])
def chat_api_strands():
    """
    Non-streaming Strands endpoint for backward compatibility
    """
    logger.info(f"Strands chat API request from {request.remote_addr}")

    # Authentication check (using legacy signature method)
    auth_error = validate_authentication(use_v2=False)
    if auth_error:
        return auth_error

    # Parse request
    params, parse_error = parse_request_params(
        required_params=["askText", "sessionId", "traceId"]
    )
    if parse_error:
        return parse_error

    # Use Strands agent for response
    try:
        agent = create_robot_agent_mcp(params["session_id"])
        result = asyncio.run(agent.run_async(params["ask_text"]))

        now = datetime.now()
        response = {
            "id": now.strftime("%Y-%m-%d %H:%M:%S"),
            "traceId": params["trace_id"],
            "sessionId": params["session_id"],
            "askText": params["ask_text"],
            "replyText": str(result),
            "replyType": "Llm",
            "timestamp": now.timestamp(),
        }

        logger.info(f"Strands response generated for trace: {params['trace_id']}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error with Strands agent: {e}", exc_info=True)
        return error_response(500, f"Error processing with Strands: {e}")


@api_bp.route("/xiaoice-chat-api", methods=["POST"])
def chat_api():
    """
    Direct chat API endpoint with authentication and response mapping
    Replaces the proxy functionality with direct processing
    """
    logger.info(f"Chat API request from {request.remote_addr}")

    # 1. Parse request first (for xiaoice-chat-api we need to extract extra for validation)
    params, parse_error = parse_request_params(
        required_params=["askText", "sessionId", "traceId"]
    )
    if parse_error:
        return parse_error

    # Validate 'extra' parameter if present
    extra = params.get("extra", {})
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

    # 2. Authentication check (using legacy signature method)
    auth_error = validate_authentication(use_v2=False)
    if auth_error:
        return auth_error

    # 3. Call _chat with mapped parameters
    try:
        # Map the request parameters to the internal _chat format
        chat_data = {
            "message": params["ask_text"],
            "robots": [
                "all"
            ],  # Default to all robots, can be customized based on extra params
            "session_id": params["session_id"],
        }

        # Check if streaming is requested
        is_streaming = request.args.get("stream", "false").lower() == "true"
        logger.info(f"Streaming requested: {is_streaming}")

        # Call the internal chat function
        chat_response = asyncio.run(_chat(chat_data))

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
            "traceId": params["trace_id"],
            "sessionId": params["session_id"],
            "askText": params["ask_text"],
            "replyText": response_data.get("response", ""),
            "replyType": "Llm",
            "timestamp": now.timestamp(),
        }

        logger.info(f"Chat API response generated for trace: {params['trace_id']}")
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
def run_action(robot_id):
    """Run process_actions with provided action and robot"""
    try:
        data = request.get_json(silent=True) or request.json or {}
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
        results = asyncio.run(robot_service.process_actions([action], robot))
        return jsonify({"results": results})
    if method == "StopAction":
        results = asyncio.run(robot_service.process_actions(["stop"], robot))
        return jsonify({"results": results})
    return jsonify({"error": "Invalid method"}), 400
