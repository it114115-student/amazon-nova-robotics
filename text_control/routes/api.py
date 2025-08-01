"""
API routes - Handles all API endpoints
"""

import uuid

from flask import Blueprint, jsonify, request
from middleware import require_hybrid_auth
from services.chat_service import extract_actions_from_response, get_chat_response
from services.database_service import delete_robot, get_robot, list_robots, upsert_robot
from services.robot_service import robot_service

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


@api_bp.route("/chat-api", methods=["POST"])
async def chat_api():
    try:
        data = await request.get_json()
    except Exception:
        data = request.json or {}
    return await _chat(data)


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

    # Extract actions to execute
    bot_response = response_data["response"]
    actions_to_execute = await extract_actions_from_response(bot_response, user_message)

    print(f"Actions to execute: {actions_to_execute}")

    # Handle 'all' as mutually exclusive in backend as well
    actions_executed = []
    robots_to_use = selected_robots
    if "all" in selected_robots:
        # If 'all' is selected, ignore other selections and send to all robots 1-7
        robots_to_use = ["all"]

    for robot in robots_to_use:
        if actions_to_execute:
            execution_results = await robot_service.process_actions(
                actions_to_execute, robot
            )
            actions_executed.append({"robot": robot, "results": execution_results})

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

    print(f"Running action for robot: {robot}, method: {method}, action: {action}")
    print(f"Data received: {data}")

    if not method or not action or not robot:
        return jsonify({"error": "Missing robot or method or params."}), 400

    if method == "RunAction":
        results = await robot_service.process_actions([action], robot)
        return jsonify({"results": results})
    if method == "StopAction":
        results = await robot_service.process_actions(["stop"], robot)
        return jsonify({"results": results})
    return jsonify({"error": "Invalid method"}), 400
