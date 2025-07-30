"""
Middleware for JWT token validation and API Gateway authentication context
"""

import inspect
import os
from functools import wraps

import jwt
import requests
from config import COGNITO_CLIENT_ID, COGNITO_USER_POOL_ID
from flask import g, jsonify, redirect, request, session, url_for
from jwt.exceptions import InvalidTokenError

# Configuration settings
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# Cache for JWKS
_jwks_cache = None


def get_jwks():
    """Get JSON Web Key Set from Cognito"""
    global _jwks_cache
    if _jwks_cache is None:
        jwks_url = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def validate_jwt_token(token):
    """Validate JWT token from Cognito"""
    try:
        # Get JWKS
        jwks = get_jwks()

        # Decode header to get kid
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Find the key
        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] == kid:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                break

        if not key:
            return None

        # Verify and decode the token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}",
        )

        return payload

    except InvalidTokenError:
        return None
    except Exception:
        return None


def extract_api_gateway_auth_context():
    """Extract authentication context from API Gateway event"""
    # API Gateway stores the event context in the WSGI environ
    # When using awsgi2, the Lambda event is available
    if hasattr(request, "environ") and "lambda.event" in request.environ:
        event = request.environ["lambda.event"]
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})

        # API Gateway Cognito authorizer provides claims in the authorizer context
        claims = authorizer.get("claims", {})
        if claims:
            return claims

    return None


def require_hybrid_auth(f):
    """Decorator that supports both session-based (web) and token-based (API) authentication"""

    if inspect.iscoroutinefunction(f):

        @wraps(f)
        async def async_decorated_function(*args, **kwargs):
            # Try session-based authentication first (for web UI)
            if "user" in session and session.get("authenticated"):
                g.current_user = session["user"]
                return await f(*args, **kwargs)

            # Try API Gateway auth context
            auth_context = extract_api_gateway_auth_context()
            if auth_context:
                g.current_user = auth_context
                return await f(*args, **kwargs)

            # Try JWT token validation for direct API requests
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = validate_jwt_token(token)
                if payload:
                    g.current_user = payload
                    return await f(*args, **kwargs)

            # No valid authentication found
            return jsonify({"error": "Authentication required"}), 401

        return async_decorated_function
    else:

        @wraps(f)
        def sync_decorated_function(*args, **kwargs):
            # Try session-based authentication first (for web UI)
            if "user" in session and session.get("authenticated"):
                g.current_user = session["user"]
                return f(*args, **kwargs)

            # Try API Gateway auth context
            auth_context = extract_api_gateway_auth_context()
            if auth_context:
                g.current_user = auth_context
                return f(*args, **kwargs)

            # Try JWT token validation for direct API requests
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = validate_jwt_token(token)
                if payload:
                    g.current_user = payload
                    return f(*args, **kwargs)

            # No valid authentication found
            return jsonify({"error": "Authentication required"}), 401

        return sync_decorated_function


def require_auth(f):
    """Decorator to require authentication for routes (handles both sync and async functions)"""

    if inspect.iscoroutinefunction(f):

        @wraps(f)
        async def async_decorated_function(*args, **kwargs):
            # First, try to get auth context from API Gateway
            auth_context = extract_api_gateway_auth_context()
            if auth_context:
                g.current_user = auth_context
                return await f(*args, **kwargs)

            # Fallback to JWT token validation for direct requests
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return (
                    jsonify({"error": "Missing or invalid authorization header"}),
                    401,
                )

            # Extract token
            token = auth_header.split(" ")[1]

            # Validate token
            payload = validate_jwt_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Store user info in g for use in the route
            g.current_user = payload

            return await f(*args, **kwargs)

        return async_decorated_function
    else:

        @wraps(f)
        def sync_decorated_function(*args, **kwargs):
            # First, try to get auth context from API Gateway
            auth_context = extract_api_gateway_auth_context()
            if auth_context:
                g.current_user = auth_context
                return f(*args, **kwargs)

            # Fallback to JWT token validation for direct requests
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return (
                    jsonify({"error": "Missing or invalid authorization header"}),
                    401,
                )

            # Extract token
            token = auth_header.split(" ")[1]

            # Validate token
            payload = validate_jwt_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Store user info in g for use in the route
            g.current_user = payload

            return f(*args, **kwargs)

        return sync_decorated_function


def require_web_auth(f):
    """Decorator to require authentication for web UI routes using session"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Debug session info
        print(f"DEBUG: Session contents: {dict(session)}")
        print(f"DEBUG: 'user' in session: {'user' in session}")
        print(f"DEBUG: session.get('authenticated'): {session.get('authenticated')}")

        # Check if user is authenticated via session
        if "user" not in session or not session.get("authenticated"):
            # For web routes, redirect to login page
            # Check if we're running behind API Gateway with a stage
            if hasattr(request, "environ") and "lambda.event" in request.environ:
                event = request.environ["lambda.event"]
                request_context = event.get("requestContext", {})
                stage = request_context.get("stage", "")

                # Debug logging
                print(f"DEBUG: Lambda event detected. Stage: '{stage}'")
                print(f"DEBUG: Request path: {request.path}")
                print(f"DEBUG: Request context keys: {list(request_context.keys())}")

                if stage and stage != "$default":
                    # Construct proper redirect URL with stage prefix
                    host = request.headers.get("Host", "")
                    scheme = request.headers.get("X-Forwarded-Proto", "https")
                    login_url = f"{scheme}://{host}/{stage}/login"
                    print(f"DEBUG: Redirecting to: {login_url}")
                    return redirect(login_url)

            # Fallback to standard Flask url_for
            print("DEBUG: Using Flask url_for fallback")
            return redirect(url_for("ui.login_page"))

        # Store user info in g for use in the route
        g.current_user = session["user"]

        return f(*args, **kwargs)

    return decorated_function
