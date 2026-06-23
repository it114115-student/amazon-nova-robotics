"""
UI routes - Handles all user interface endpoints
"""

from flask import Blueprint, g, redirect, render_template, send_from_directory, url_for, jsonify, request
from middleware import require_web_auth
from services.speech_db_service import (
    get_all_speech_messages,
    delete_all_speech_messages,
    delete_speech_message,
)

# Create a blueprint for the UI routes
ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
def root():
    return redirect(url_for("ui.home"))


@ui_bp.route("/index")
@require_web_auth
def home():
    # Pass user context to template if needed
    user_context = getattr(g, "current_user", None)
    return render_template("index.html", user=user_context)


@ui_bp.route("/robot")
@require_web_auth
def robot_page():
    # Pass user context to template if needed
    user_context = getattr(g, "current_user", None)
    return render_template("robot.html", user=user_context)


@ui_bp.route("/cleanup")
@require_web_auth
def cleanup_page():
    user_context = getattr(g, "current_user", None)
    return render_template("cleanup.html", user=user_context)


@ui_bp.route("/cleanup/api/list")
@require_web_auth
def cleanup_list_api():
    messages = get_all_speech_messages()
    return jsonify({"success": True, "messages": messages})


@ui_bp.route("/cleanup/api/delete-all", methods=["POST"])
@require_web_auth
def cleanup_delete_all_api():
    count = delete_all_speech_messages()
    return jsonify({"success": True, "deleted_count": count})


@ui_bp.route("/cleanup/api/delete/<message_id>", methods=["POST"])
@require_web_auth
def cleanup_delete_single_api(message_id):
    delete_speech_message(message_id)
    return jsonify({"success": True, "message_id": message_id})


@ui_bp.route("/login")
def login_page():
    return render_template("login.html")


@ui_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )

