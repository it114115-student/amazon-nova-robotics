"""
UI routes - Handles all user interface endpoints
"""

from flask import Blueprint, g, redirect, render_template, send_from_directory, url_for
from middleware import require_web_auth

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


@ui_bp.route("/login")
def login_page():
    return render_template("login.html")


@ui_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )
