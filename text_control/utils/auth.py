"""
Authentication utilities for API requests
"""

import hashlib
import os

from flask import request
from utils.lambda_logger import get_lambda_logger
import boto3
from botocore.exceptions import ClientError
import json

logger = get_lambda_logger(__name__)

def get_secret(secret_name: str, region_name: str = None) -> dict:
    """Fetch secret from AWS Secrets Manager"""
    if not region_name:
        region_name = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        return None

    secret = get_secret_value_response.get('SecretString')
    if secret:
        try:
            return json.loads(secret)
        except json.JSONDecodeError:
            logger.error(f"Secret {secret_name} is not valid JSON")
            return None
    return None


def calculate_signature(secret_key: str, timestamp: str, body_string: str) -> str:
    """
    Calculate signature for authentication (legacy method)
    
    Args:
        secret_key: Server-side secret key
        timestamp: Request timestamp
        body_string: Request body as string
        
    Returns:
        SHA-512 hash string
    """
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


def calculate_signature_v2(secret_key: str, timestamp: str, body_string: str) -> str:
    """
    Calculate signature for authentication following the vendor specification.

    Algorithm:
    1. Build a parameter Map with: secretKey, timestamp, bodyString
    2. Sort parameters by key name in ascending order and connect with "&"
       Format: key1=value1&key2=value2&key3=value3
    3. Calculate SHA-512 hash and convert to UPPERCASE

    Args:
        secret_key: Server-side (user) preset secret key
        timestamp: Request timestamp (milliseconds)
        body_string: JSON serialized string of request body

    Returns:
        Uppercase SHA-512 hash string
    """
    # Create parameter map
    params = {
        "bodyString": body_string,
        "secretKey": secret_key,
        "timestamp": timestamp,
    }

    # Sort by key name in ascending order and create signature string
    sorted_params = sorted(params.items())
    signature_string = "&".join([f"{k}={v}" for k, v in sorted_params])

    # Calculate SHA-512 hash
    sha512 = hashlib.sha512()
    sha512.update(signature_string.encode("utf-8"))
    hex_digest = sha512.hexdigest()

    # Convert to uppercase (SHA-512 hex digest doesn't contain "-", but keep the replace for safety)
    return hex_digest.replace("-", "").upper()


def validate_authentication(use_v2=True, enforce_expiry=False):
    """
    Validates authentication headers and returns error response if invalid.

    Args:
        use_v2: If True, use calculate_signature_v2, otherwise use calculate_signature
        enforce_expiry: If True, check that request timestamp is within 5 minutes of current server time

    Returns:
        Tuple of (project_id, error_response). If authentication is successful, error_response is None.
    """
    from utils.response_utils import error_response
    import time
    
    try:
        # Get headers (support both X- prefixed and non-prefixed)
        timestamp = request.headers.get("X-Timestamp") or request.headers.get("timestamp")
        signature = request.headers.get("X-Sign") or request.headers.get("signature")
        access_key = request.headers.get("X-Key") or request.headers.get("key")

        stored_secret_key = os.getenv("XiaoiceChatSecretKey")
        valid_access_key = os.getenv("XiaoiceChatAccessKey")

        if not all([timestamp, signature, access_key]):
            logger.warning("Authentication failed: Missing authentication headers")
            return None, error_response(401, "Missing authentication headers")

        is_machine_route = "/xiaoice-stream-machine" in request.path
        should_enforce = enforce_expiry or is_machine_route

        if should_enforce and timestamp:
            try:
                # Convert timestamp from milliseconds to seconds
                request_ts = float(timestamp) / 1000.0
                current_ts = time.time()
                # 5 minutes = 300 seconds
                if abs(current_ts - request_ts) > 300:
                    logger.warning(f"Authentication failed: Request timestamp expired. Request: {request_ts}, Current: {current_ts}")
                    return None, error_response(401, "Request timestamp expired")
            except (ValueError, TypeError) as e:
                logger.warning(f"Authentication failed: Invalid timestamp format: {timestamp}")
                return None, error_response(401, f"Invalid timestamp format: {e}")

        project_id = None
        stored_secret_key = None
        
        # 1. Try to load from AWS Secrets Manager first
        secret_name = os.getenv("XIAOICE_SECRET_NAME", "XiaoiceProjectCredentials")
        credentials_map = get_secret(secret_name)
        
        # 2. Fallback to Environment Variable mapping if Secret Manager fails
        if not credentials_map:
            creds_json = os.getenv("XIAOICE_PROJECT_CREDENTIALS")
            if creds_json:
                try:
                    credentials_map = json.loads(creds_json)
                except Exception as e:
                    logger.error(f"Failed to parse XIAOICE_PROJECT_CREDENTIALS env var: {e}")
                    
        # 2.5. Fallback to local file if Secret Manager and Env Var mapping fail (e.g., for local/offline testing)
        if not credentials_map:
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                local_path = os.path.join(base_dir, "xiaoice_credentials.json")
                if os.path.exists(local_path):
                    with open(local_path, "r") as f:
                        credentials_map = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load local xiaoice_credentials.json: {e}")

        # Extract keys from mapping
        if credentials_map:
            project_config = credentials_map.get(access_key)
            if project_config:
                stored_secret_key = project_config.get("secret_key")
                project_id = project_config.get("project_id")
                
        # 3. Fallback to old global keys
        if not stored_secret_key:
            global_secret_key = os.getenv("XiaoiceChatSecretKey")
            global_access_key = os.getenv("XiaoiceChatAccessKey")
            
            if access_key == global_access_key:
                stored_secret_key = global_secret_key
                # Default fallback project_id
                project_id = "Summer"

        if not stored_secret_key:
            logger.warning(f"Authentication failed: Invalid access key received: {access_key}")
            return None, error_response(401, "Invalid access key or missing configuration")

        body_string = request.data.decode("utf-8")

        if use_v2:
            calculated_signature = calculate_signature_v2(stored_secret_key, timestamp, body_string)
        else:
            calculated_signature = calculate_signature(stored_secret_key, timestamp, body_string)

        if calculated_signature != signature:
            logger.warning("Authentication failed: Invalid signature")
            return None, error_response(401, "Invalid signature")

        logger.info("Authentication successful: " + project_id)
        return project_id, None

    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        return None, error_response(401, f"Authentication failed: {e}")
