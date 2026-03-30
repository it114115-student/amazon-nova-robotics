"""
Configuration settings for the application
"""

import os

# AWS Bedrock settings
AWS_BEDROCK_REGION = os.getenv("AWS_BEDROCK_REGION", "us-east-1")
NOVA_MODEL_ID = "us.amazon.nova-2-lite-v1:0"

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
MCP_SERVER_URL = os.getenv("McpServerUrl", None)
ROBOT_TABLE = os.getenv("RobotTable", "")
COGNITO_USER_POOL_ID = os.getenv("CognitoUserPoolId")
COGNITO_CLIENT_ID = os.getenv("CognitoUserPoolClientId")
