import atexit

try:
    import awsgi2
    from config import DEBUG
    from flask import Flask
    from mcp_client import cleanup_mcp_client, init_mcp_client

    # Initialize the Flask application
    app = Flask(__name__)

    # Initialize the MCP client when the app starts
    with app.app_context():
        init_mcp_client()
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print(
        "Please install all required dependencies with: pip install -r requirements.txt"
    )
    import sys

    sys.exit(1)

from errors import register_error_handlers

# Import and register blueprints after app is created to avoid circular imports
from routes.api import api_bp
from routes.ui import ui_bp

# Register the blueprints
app.register_blueprint(api_bp)
app.register_blueprint(ui_bp)

# Register error handlers
register_error_handlers(app)

# Register cleanup function to run at exit
atexit.register(cleanup_mcp_client)


def handler(event, context):
    """AWS Lambda handler for the Flask application"""
    return awsgi2.response(app, event, context)


if __name__ == "__main__":
    # app.run(debug=DEBUG)
    app.run(host="0.0.0.0", debug=DEBUG)
