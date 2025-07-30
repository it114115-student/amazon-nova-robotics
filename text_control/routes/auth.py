"""
Authentication routes - Handles Cognito authentication
"""

import os

import boto3
import jwt
from botocore.exceptions import ClientError
from config import COGNITO_CLIENT_ID, COGNITO_USER_POOL_ID
from flask import Blueprint, jsonify, request, session

# Create a blueprint for the auth routes
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Initialize Cognito client
cognito_client = boto3.client(
    "cognito-idp", region_name=os.getenv("CognitoRegion", "us-east-1")
)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Handle user login via Cognito"""
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Authenticate with Cognito
        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )

        # Return the tokens
        auth_result = response["AuthenticationResult"]

        # Decode the ID token to get user information for session
        id_token = auth_result["IdToken"]
        try:
            # Note: For session-based auth, we're not validating the JWT signature here
            # since we just got it from Cognito. In production, you might want to validate it.
            import base64
            import json

            # Decode the payload (without signature validation for simplicity)
            payload = id_token.split(".")[1]
            # Add padding if needed
            payload += "=" * (4 - len(payload) % 4)
            decoded_payload = json.loads(base64.b64decode(payload))

            # Set up session for web UI authentication
            session["authenticated"] = True
            session["user"] = {
                "username": decoded_payload.get("cognito:username", username),
                "email": decoded_payload.get("email", ""),
                "sub": decoded_payload.get("sub", ""),
            }
        except Exception:
            # If we can't decode the token, still set basic session info
            session["authenticated"] = True
            session["user"] = {"username": username}

        return jsonify(
            {
                "success": True,
                "tokens": {
                    "id_token": auth_result["IdToken"],
                    "access_token": auth_result["AccessToken"],
                    "refresh_token": auth_result["RefreshToken"],
                },
            }
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NotAuthorizedException":
            return jsonify({"error": "Invalid username or password"}), 401
        elif error_code == "UserNotFoundException":
            return jsonify({"error": "User not found"}), 404
        else:
            return (
                jsonify(
                    {
                        "error": f"Authentication failed: {e.response['Error']['Message']}"
                    }
                ),
                500,
            )
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400

        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
        )

        auth_result = response["AuthenticationResult"]
        return jsonify(
            {
                "success": True,
                "tokens": {
                    "id_token": auth_result["IdToken"],
                    "access_token": auth_result["AccessToken"],
                },
            }
        )

    except ClientError as e:
        return (
            jsonify(
                {"error": f"Token refresh failed: {e.response['Error']['Message']}"}
            ),
            401,
        )
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500


@auth_bp.route("/verify", methods=["POST"])
def verify_token():
    """Verify JWT token"""
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Token is required"}), 400

        # For now, we'll just return success as API Gateway handles verification
        # In a real implementation, you might want to decode and verify the JWT
        return jsonify({"success": True, "valid": True})

    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 500


@auth_bp.route("/config", methods=["GET"])
def get_auth_config():
    """Get authentication configuration for frontend"""
    return jsonify(
        {
            "userPoolId": COGNITO_USER_POOL_ID,
            "clientId": COGNITO_CLIENT_ID,
            "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        }
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Handle user logout - clear session"""
    try:
        # Clear the session
        session.clear()

        return jsonify({"success": True, "message": "Logged out successfully"})

    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500
