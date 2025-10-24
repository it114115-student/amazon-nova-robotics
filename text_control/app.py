"""Flask application for robot text control with AWS integration."""
import atexit
import logging
import os

import awsgi2
from flask import Flask
from flask_caching import Cache

from config import DEBUG
from errors import register_error_handlers
from mcp_client import cleanup_mcp_client, init_mcp_client

# Configure logging for development environment
if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    print("Initializing MCP client with AWS SigV4 authentication")

# Import and register blueprints after app is created to avoid circular imports
from routes.api import api_bp  # pylint: disable=wrong-import-position
from routes.auth import auth_bp  # pylint: disable=wrong-import-position
from routes.ui import ui_bp  # pylint: disable=wrong-import-position

config = {
    "DEBUG": DEBUG,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "SECRET_KEY": os.getenv(
        "FlaskSecretKey", "fallback-secret-key-for-lambda-sessions-12345"
    ),  # Required for sessions - use a consistent fallback for Lambda
}

# Initialize the Flask application
app = Flask(__name__)

app.config.from_mapping(config)
cache = Cache(app)

# Make cache available as app attribute for easy access
app.cache = cache


# Add CORS headers for API Gateway
@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
    )
    return response


# Initialize the MCP client when the app starts
with app.app_context():
    init_mcp_client()


# Register the blueprints
app.register_blueprint(api_bp)
app.register_blueprint(ui_bp)
app.register_blueprint(auth_bp)

# Register error handlers
register_error_handlers(app)

# Register cleanup function to run at exit
atexit.register(cleanup_mcp_client)


def handler(event, context):
    """AWS Lambda handler for the Flask application"""
    return awsgi2.response(app, event, context)


if __name__ == "__main__":
    print("🤖 Starting Robot Text Control with Strands Agents...")
    print("📡 Streaming endpoint: /api/talk")
    print("🔄 Non-streaming endpoint: /xiaoice-chat-api-strands")
    print("🌐 Original endpoint: /xiaoice-chat-api")
    # app.run(debug=DEBUG)
    app.run(host="0.0.0.0", debug=DEBUG)
