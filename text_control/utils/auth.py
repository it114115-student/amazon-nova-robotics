"""
Authentication utilities for API requests
"""

import hashlib
import os

from flask import request
from utils.lambda_logger import get_lambda_logger

logger = get_lambda_logger(__name__)


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


def validate_authentication(use_v2=True):
    """
    Validates authentication headers and returns error response if invalid.

    Args:
        use_v2: If True, use calculate_signature_v2, otherwise use calculate_signature

    Returns:
        None if authentication is successful, error_response tuple otherwise
    """
    from utils.response_utils import error_response
    
    try:
        # Get headers (support both X- prefixed and non-prefixed)
        timestamp = request.headers.get("X-Timestamp") or request.headers.get("timestamp")
        signature = request.headers.get("X-Sign") or request.headers.get("signature")
        access_key = request.headers.get("X-Key") or request.headers.get("key")

        stored_secret_key = os.getenv("XiaoiceChatSecretKey")
        valid_access_key = os.getenv("XiaoiceChatAccessKey")

        if not all([stored_secret_key, valid_access_key]):
            logger.error("Server configuration error: Missing environment variables")
            return error_response(500, "Server configuration error")

        if not all([timestamp, signature, access_key]):
            logger.warning("Authentication failed: Missing authentication headers")
            return error_response(401, "Missing authentication headers")

        if access_key != valid_access_key:
            logger.warning(f"Authentication failed: Invalid access key received: {access_key}")
            return error_response(401, "Invalid access key")

        body_string = request.data.decode("utf-8")

        if use_v2:
            calculated_signature = calculate_signature_v2(stored_secret_key, timestamp, body_string)
        else:
            calculated_signature = calculate_signature(stored_secret_key, timestamp, body_string)

        if calculated_signature != signature:
            logger.warning("Authentication failed: Invalid signature")
            return error_response(401, "Invalid signature")

        logger.info("Authentication successful")
        return None

    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        return error_response(401, f"Authentication failed: {e}")
