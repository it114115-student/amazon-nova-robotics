import atexit

import awsgi2
from config import DEBUG
from errors import register_error_handlers
from flask import Flask
from flask_caching import Cache
from mcp_client import cleanup_mcp_client, init_mcp_client

# Import and register blueprints after app is created to avoid circular imports
from routes.api import api_bp
from routes.ui import ui_bp

config = {
    "DEBUG": DEBUG,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# Initialize the Flask application
app = Flask(__name__)

app.config.from_mapping(config)
cache = Cache(app)

# Make cache available as app attribute for easy access
app.cache = cache

# Initialize the MCP client when the app starts
with app.app_context():
    init_mcp_client()


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
