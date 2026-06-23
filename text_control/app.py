"""Flask application for robot text control with AWS integration."""
import atexit
import json
import logging
import os

import awsgi2
from flask import Flask, request, jsonify
from flask_caching import Cache

from config import DEBUG
from errors import register_error_handlers
from mcp_client import cleanup_mcp_client, get_mcp_client

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


# Add global request logging hook for debugging
@app.before_request
def log_request_info():
    """Log details of every incoming request for debugging purposes."""
    try:
        # Get method, path, remote IP
        method = request.method
        path = request.path
        remote_ip = request.remote_addr or "unknown"
        
        # Get query parameters
        query_params = dict(request.args)
        
        # Get headers (convert to dict and sanitize Authorization slightly to protect secrets)
        headers = {k: v for k, v in request.headers.items()}
        if "Authorization" in headers:
            token = headers["Authorization"]
            if len(token) > 15:
                headers["Authorization"] = f"{token[:10]}...{token[-5:]} (len={len(token)})"
        
        # Get body data safely
        body_str = ""
        if request.is_json:
            try:
                body_json = request.get_json(silent=True)
                if body_json:
                    body_str = json.dumps(body_json)
            except Exception as e:
                body_str = f"[Error reading JSON body: {str(e)}]"
        else:
            if request.content_length and request.content_length < 100000:  # < 100KB
                try:
                    body_bytes = request.get_data()
                    if body_bytes:
                        body_str = body_bytes.decode('utf-8', errors='ignore')
                except Exception as e:
                    body_str = f"[Error reading raw body: {str(e)}]"
            elif request.content_length:
                body_str = f"[Body too large: {request.content_length} bytes]"
        
        # Truncate body if extremely long
        if len(body_str) > 2000:
            body_str = body_str[:2000] + "... [TRUNCATED]"
            
        log_msg = (
            f"\n=== [FLASK REQUEST START] ===\n"
            f"Method: {method}\n"
            f"Path: {path}\n"
            f"Remote IP: {remote_ip}\n"
            f"Query Args: {query_params}\n"
            f"Headers: {headers}\n"
            f"Body: {body_str}\n"
            f"============================="
        )
        # print() is guaranteed to show in AWS Lambda CloudWatch logs
        print(log_msg, flush=True)
        
    except Exception as e:
        print(f"Error in request logging hook: {str(e)}", flush=True)


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
    get_mcp_client()


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
    try:
        # Log the raw Lambda event for debugging
        print(f"--- [LAMBDA INVOCATION START] ---")
        try:
            print(f"Event: {json.dumps(event)}")
        except Exception as je:
            print(f"Event representation: {str(event)} (JSON error: {je})")
        
        # Safe extraction of request path and method
        http_method = "UNKNOWN"
        path = "UNKNOWN"
        if isinstance(event, dict):
            http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN")
            path = event.get("path") or event.get("requestContext", {}).get("http", {}).get("path", "UNKNOWN")
        print(f"Request: {http_method} {path}")
        print(f"--- [LAMBDA INVOCATION END] ---")
    except Exception as e:
        print(f"Error logging Lambda event: {e}")

    try:
        from mcp_client import notify_new_invocation
        if hasattr(context, "aws_request_id"):
            notify_new_invocation(context.aws_request_id)
    except Exception as e:
        print(f"Error notifying new invocation to MCP client: {e}")
    return awsgi2.response(app, event, context)


if __name__ == "__main__":
    print("🤖 Starting Robot Text Control with Strands Agents...")
    print("📡 Streaming endpoint: /api/talk")
    print("🔄 Non-streaming endpoint: /xiaoice-chat-api-strands")
    print("🌐 Original endpoint: /xiaoice-chat-api")
    # app.run(debug=DEBUG)
    app.run(host="0.0.0.0", debug=DEBUG)
