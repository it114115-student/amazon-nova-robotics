"""
API routes - Handles all API endpoints
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime

from flask import Blueprint, Response, jsonify, request
from middleware import require_hybrid_auth
from services.database_service import delete_robot, get_robot, list_robots, upsert_robot
from services.speech_db_service import delete_speech_message, get_pending_speech_message
from services.robot_service import robot_service
from services.strands_service_mcp import create_robot_agent as create_robot_agent_mcp
from utils.auth import validate_authentication
from utils.lambda_logger import get_lambda_logger
from utils.messages import (
    GOODBYE_MESSAGES,
    RECOMMENDED_QUESTIONS,
    WELCOME_MESSAGES,
    get_message,
)
from utils.response_utils import (
    create_response_object,
    error_response,
    parse_request_params,
)
from utils.streaming import create_sync_stream_wrapper, stream_agent_response

# Suppress OpenTelemetry context warnings (harmless in async streaming context)
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)

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
        required_params=["askText", "sessionId", "traceId", "userParams"]
    )
    if parse_error:
        return parse_error

    ask_text = params["ask_text"]
    session_id = params["session_id"]
    trace_id = params["trace_id"]
    extra = params["extra"]
    user_params = params["user_params"]

    logger.info(f"Talk stream request details - Session: {session_id}, Trace: {trace_id}, User Params: {user_params}")
    context = get_robot(user_params)
    background = ""
    if context:
        name = context.get("robot_name")
        background = context.get("context")
        background = f"""
<background>Your Name:{name}
background: {background}
</background>
            """

    # 3. Create Strands agent and stream response
    try:
        def stream_response():
            try:
                async def async_stream():
                    agent = await create_robot_agent_mcp(session_id, background)
                    async for chunk in stream_agent_response(
                        agent, ask_text, session_id, trace_id, extra
                    ):
                        yield chunk

                # Yield from the async generator wrapper
                for chunk in create_sync_stream_wrapper(async_stream()):
                    yield chunk

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
                    "timestamp": int(datetime.now().timestamp() * 1000),
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
    Returns a welcome message for the conversation system.
    For xiaoice: checks the SpeechTable for a pending speech message by presenter_id.
    If found, returns that message as the welcome text and deletes it.
    Otherwise falls back to the standard welcome message.
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

    # 3. Extract presenter_id from userParams
    user_params = params.get("user_params", {})
    presenter_id = None

    if isinstance(user_params, dict):
        presenter_id = user_params.get("presenterId")
    elif isinstance(user_params, str):
        # Handle string format like "summer-presentation" or just "summer"
        if "-" in user_params:
            parts = user_params.split("-")
            if len(parts) > 0:
                presenter_id = parts[0]
        else:
            presenter_id = user_params if user_params else None

    logger.debug(f"Extracted presenter_id: {presenter_id}")

    # 4. For xiaoice: try to get a pending speech message from the SpeechTable
    try:
        if presenter_id:
            speech_msg = get_pending_speech_message(presenter_id)
            if speech_msg:
                welcome_text = speech_msg.get("message", "")
                response = create_response_object(params, welcome_text)
                response["presenterId"] = presenter_id

                # Delete the message after reading it
                delete_speech_message(speech_msg["id"])
                logger.info(
                    f"Xiaoice welcome: delivered speech message {speech_msg['id']} "
                    f"for presenter {presenter_id}"
                )
                return jsonify(response)

        # 5. Fallback: standard welcome message
        welcome_text = get_message(WELCOME_MESSAGES, params["language_code"])
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
        goodbye_text = get_message(GOODBYE_MESSAGES, params["language_code"])
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
        questions = RECOMMENDED_QUESTIONS.get(
            params["language_code"], RECOMMENDED_QUESTIONS["zh"]
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
    非流式接口 (Non-streaming interface)
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
    
    context = get_robot("Summer")
    background = ""
    if context:
        name = context.get("robot_name")
        background = context.get("context")
        background = f"""
<background>Your Name:{name}
background: {background}
</background>
            """

    # Use Strands agent for response
    try:
        async def get_response():
            agent = await create_robot_agent_mcp(params["session_id"], background)
            return await agent.invoke_async(params["ask_text"])
        
        result = asyncio.run(get_response())

        now = datetime.now()
        response = {
            "id": now.strftime("%Y-%m-%d %H:%M:%S"),
            "traceId": params["trace_id"],
            "sessionId": params["session_id"],
            "askText": params["ask_text"],
            "replyText": str(result),
            "replyType": "Llm",
            "timestamp": now.timestamp(),
            "replyPayload": params.get("extra", {}).get("replyPayload"),
            "extra": params.get("extra", {}),
        }

        logger.info(f"Strands response generated for trace: {params['trace_id']}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error with Strands agent: {e}", exc_info=True)
        return error_response(500, f"Error processing with Strands: {e}")


@api_bp.route("/xiaoice-chat-api-strands-stream", methods=["POST"])
def chat_api_strands_stream():
    """
    Streaming Strands endpoint using SSE (Server-Sent Events)
    流式接口 (Streaming interface)
    Compatible with XiaoIce third-party chat API specification
    """
    logger.info(f"Strands streaming chat API request from {request.remote_addr}")

    # 1. Authentication check (using legacy signature method)
    auth_error = validate_authentication(use_v2=False)
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
    extra = params.get("extra", {})

    context = get_robot("Summer")

    background = ""
    if context:
        name = context.get("robot_name")
        background = context.get("context")
        background = f"""
<background>Your Name:{name}
background: {background}
</background>
            """
    # 3. Create Strands agent and stream response
    try:
        def stream_response():
            try:
                async def async_stream():
                    agent = await create_robot_agent_mcp(session_id, background)
                    async for chunk in stream_agent_response(
                        agent, ask_text, session_id, trace_id, extra
                    ):
                        yield chunk

                # Yield from the async generator wrapper
                for chunk in create_sync_stream_wrapper(async_stream()):
                    yield chunk

            except Exception as e:
                logger.error(f"Error in stream_response: {e}", exc_info=True)
                error_chunk = {
                    "id": str(uuid.uuid4()),
                    "askText": ask_text,
                    "extra": extra,
                    "traceId": trace_id,
                    "replyPayload": None,
                    "replyText": f"Error: {str(e)}",
                    "replyType": "Error",
                    "sessionId": session_id,
                    "timestamp": int(datetime.now().timestamp() * 1000),
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


async def _chat(data):
    """Handle chat requests with Strands MCP agent"""
    user_message = data.get("message")
    session_id = str(data.get("session_id", str(uuid.uuid4())))
    
    # Validate that message is not empty or blank
    if not user_message or not user_message.strip():
        logger.warning("Bad request: Parameter 'message' cannot be empty or blank")
        return jsonify({
            "error": "Parameter 'message' cannot be empty or blank",
            "session_id": session_id,
        }), 400

    selected_robots = data.get("robots")
    context_robot = selected_robots[0] if selected_robots else None
    context = get_robot(context_robot)
    background = ""
    if context:
        name = context.get("robot_name")
        background = context.get("context")
        background = f"""
<background>Your Name:{name}
background: {background}
</background>
            """

    # Use Strands MCP agent instead of old chat service
    try:
        agent = await create_robot_agent_mcp(session_id, background)
        response = await agent.invoke_async(user_message)

        return jsonify({
            "response": str(response),
            "session_id": session_id,
        })

    except Exception as e:
        logger.error(f"Error with Strands MCP agent: {e}", exc_info=True)
        return jsonify({
            "response": f"I'm sorry, I encountered an error: {str(e)}",
            "session_id": session_id,
            "error": str(e),
        }), 500


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


@api_bp.route("/capture_image/<robot_id>", methods=["POST"])
@require_hybrid_auth
def capture_image(robot_id):
    """Capture an image from a robot's camera and return a presigned URL to view it."""
    if not robot_id:
        return jsonify({"error": "Missing robot_id"}), 400

    result = robot_service.capture_image(robot_id)
    status_code = 200 if result.get("success") else 504
    return jsonify(result), status_code


@api_bp.route("/speech/<robot_id>", methods=["POST"])
@require_hybrid_auth
def robot_speech(robot_id):
    """Make a robot speak using Amazon Polly TTS via the MCP server.

    Request body:
        {
            "text": "你好，歡迎",
            "language": "yue"       // optional, default "yue"
        }

    Supported languages: yue (Cantonese), cmn (Mandarin), en (English),
                         ja (Japanese), ko (Korean)

    The MCP server synthesizes speech with Polly, uploads to S3, and
    publishes the presigned audio URL to the robot's IoT topic.
    """
    if not robot_id:
        return jsonify({"error": "Missing robot_id"}), 400

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    language = data.get("language", "yue")

    if not text:
        return jsonify({"error": "Missing or empty 'text' parameter"}), 400

    try:
        from mcp_client import get_mcp_client

        mcp_client = get_mcp_client()
        result = asyncio.run(
            mcp_client.call_tool(
                "robot_speak",
                {"robot_id": robot_id, "text": text, "language": language},
            )
        )

        # Extract text from MCP response
        content = result.get("content", []) if isinstance(result, dict) else []
        response_text = next(
            (c.get("text", "") for c in content if c.get("type") == "text"),
            str(result),
        )

        success = "Failed" not in response_text and "Error" not in response_text
        status_code = 200 if success else 500

        return jsonify({
            "success": success,
            "robot_id": robot_id,
            "text": text,
            "language": language,
            "response": response_text,
        }), status_code

    except Exception as e:
        logger.error("Error in robot_speech for %s: %s", robot_id, e, exc_info=True)
        return jsonify({"error": f"Speech failed: {e}"}), 500


@api_bp.route("/image/<path:object_key>", methods=["GET"])
@require_hybrid_auth
def get_image_url(object_key):
    """Generate a short-lived presigned GET URL for a robot-captured image."""
    import os
    import boto3
    from botocore.config import Config

    bucket = os.environ.get("IMAGE_BUCKET_NAME", "")
    if not bucket:
        return jsonify({"error": "Image bucket not configured"}), 500

    s3_client = boto3.client(
        "s3", config=Config(retries={"max_attempts": 3, "mode": "standard"})
    )
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=300,
    )
    return jsonify({"image_url": url})
