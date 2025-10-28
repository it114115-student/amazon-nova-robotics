"""
Response utilities for API endpoints
"""

import time
import uuid

from flask import jsonify, request
from utils.lambda_logger import get_lambda_logger

logger = get_lambda_logger(__name__)


def error_response(status_code, message):
    """
    Returns a consistent JSON error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        Flask response with error details
    """
    response = jsonify({"error": {"code": status_code, "message": message}})
    response.status_code = status_code
    return response


def parse_request_params(required_params=None):
    """
    Parses and validates request parameters.

    Args:
        required_params: List of required parameter names

    Returns:
        Tuple of (params_dict, error_response). If error_response is not None,
        an error occurred and should be returned.
    """
    try:
        if not request.json:
            logger.warning("Bad request: Request body must be JSON")
            return None, error_response(400, "Request body must be JSON")

        params = {}
        required = required_params or []

        # Validate required parameters
        for param in required:
            if param not in request.json:
                logger.warning(f"Bad request: Missing required parameter: {param}")
                return None, error_response(400, f"Missing required parameter: {param}")
            
            # Validate that askText is not empty or blank if it's required
            if param == "askText":
                ask_text_value = request.json.get("askText", "")
                if not ask_text_value or not ask_text_value.strip():
                    logger.warning(f"Bad request: Parameter 'askText' cannot be empty or blank")
                    return None, error_response(400, "Parameter 'askText' cannot be empty or blank")

        # Extract common parameters
        params["ask_text"] = request.json.get("askText", "")
        params["session_id"] = request.json.get("sessionId", str(uuid.uuid4()))
        params["trace_id"] = request.json.get("traceId", str(uuid.uuid4()))
        params["extra"] = request.json.get("extra", {})
        params["language_code"] = request.json.get("languageCode", "zh")
        params["device_id"] = request.json.get("deviceId", "")
        params["user_params"] = request.json.get("userParams", "")
        params["lang_by_asr"] = request.json.get("langByAsr", "")

        logger.info(
            f"Request parsed - TraceId: {params['trace_id']}, SessionId: {params['session_id']}"
        )
        return params, None

    except Exception as e:
        logger.error(f"Error parsing request: {e}", exc_info=True)
        return None, error_response(400, f"Error parsing request: {e}")


def create_response_object(params, reply_text, is_final=True):
    """
    Creates a standardized response object.

    Args:
        params: Dictionary containing request parameters (trace_id, session_id, etc.)
        reply_text: The reply text to send
        is_final: Whether this is the final response

    Returns:
        Dictionary with standardized response format
    """
    return {
        "askText": params.get("ask_text", ""),
        "extra": params.get("extra", {}),
        "id": str(uuid.uuid4()),
        "replyPayload": None,
        "replyText": reply_text,
        "replyType": "Llm",
        "sessionId": params["session_id"],
        "timestamp": int(time.time() * 1000),
        "traceId": params["trace_id"],
        "isFinal": is_final,
    }


def create_stream_chunk(ask_text, extra, trace_id, session_id, reply_text, is_final, chunk_id=None):
    """
    Creates a standardized streaming chunk object.

    Args:
        ask_text: Original question text
        extra: Extra parameters from request
        trace_id: Request trace ID
        session_id: Session ID
        reply_text: Text content for this chunk
        is_final: Whether this is the final chunk
        chunk_id: Optional custom chunk ID

    Returns:
        Dictionary with standardized streaming chunk format
    """
    return {
        "askText": ask_text,
        "extra": extra,
        "id": chunk_id if chunk_id else str(uuid.uuid4()),
        "replyPayload": None,
        "replyText": reply_text,
        "replyType": "Llm",
        "sessionId": session_id,
        "timestamp": int(time.time() * 1000),
        "traceId": trace_id,
        "isFinal": is_final,
    }
