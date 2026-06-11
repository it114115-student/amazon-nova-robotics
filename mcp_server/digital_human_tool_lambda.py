"""Plain Lambda tool target for digital human AgentCore Gateway access."""

import json
import logging
from typing import Any

from tools.digital_human_tools import execute_digital_human_speech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _response(status_code: int, body: Any) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"},
    }


def _normalize_tool_name(tool_name: str) -> str:
    if "___" in tool_name:
        return tool_name.split("___", 1)[1]
    return tool_name


def _mapping_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _candidate_tool_names(context: Any, event: Any) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []

    client_context = getattr(context, "client_context", None)
    custom = getattr(client_context, "custom", None)
    value = _mapping_value(custom, "bedrockAgentCoreToolName")
    if isinstance(value, str) and value.strip():
        candidates.append(("context.client_context.custom.bedrockAgentCoreToolName", value.strip()))

    value = _mapping_value(context, "bedrockAgentCoreToolName")
    if isinstance(value, str) and value.strip():
        candidates.append(("context.bedrockAgentCoreToolName", value.strip()))

    return candidates


_ALLOWED_TOOLS = {"digital_human_speech"}


def _extract_tool_name(context: Any, event: Any) -> str:
    candidates = _candidate_tool_names(context, event)
    first_candidate: tuple[str, str] | None = None
    for source, tool_name in candidates:
        normalized_tool_name = _normalize_tool_name(tool_name)
        if first_candidate is None:
            first_candidate = (source, normalized_tool_name)
        if normalized_tool_name in _ALLOWED_TOOLS:
            logger.info(
                "Resolved digital human tool name from %s. raw_tool_name=%s normalized_tool_name=%s",
                source,
                tool_name,
                normalized_tool_name,
            )
            return normalized_tool_name

    if first_candidate is not None:
        source, normalized_tool_name = first_candidate
        logger.warning(
            "Resolved unsupported digital human tool name from %s. normalized_tool_name=%s",
            source,
            normalized_tool_name,
        )
        return normalized_tool_name

    raise ValueError(
        "Gateway request is missing a supported tool name. "
        f"candidate_locations={[(source, value) for source, value in candidates]}"
    )


def _extract_payload(event: Any) -> dict[str, Any]:
    if event is None:
        return {}

    if isinstance(event, dict):
        body = event.get("body")
        if isinstance(body, str):
            parsed_body = json.loads(body)
            if not isinstance(parsed_body, dict):
                raise ValueError("Tool input event body must be a JSON object.")
            return parsed_body
        if isinstance(body, dict):
            return body
        return event

    raise ValueError("Tool input event must be a JSON object.")


def _summarize_event(event: Any) -> dict[str, Any]:
    if isinstance(event, dict):
        body = event.get("body")
        return {
            "event_keys": sorted(event.keys()),
            "body_type": type(body).__name__ if body is not None else "missing",
            "request_context_keys": sorted(event.get("requestContext", {}).keys())
            if isinstance(event.get("requestContext"), dict)
            else [],
            "client_context_keys": sorted(event.get("clientContext", {}).keys())
            if isinstance(event.get("clientContext"), dict)
            else [],
        }
    return {"event_type": type(event).__name__}


def lambda_handler(event: Any, context: Any) -> dict[str, Any]:
    """Dispatch the digital human tool requested by AgentCore Gateway."""
    try:
        tool_name = _extract_tool_name(context, event)
        logger.info(
            "Digital human tool Lambda invoked. tool_name=%s summary=%s",
            tool_name,
            _summarize_event(event),
        )

        payload = _extract_payload(event)

        if tool_name == "digital_human_speech":
            message = payload.get("message", "")
            logger.info("Dispatching digital_human_speech tool. message=%s", message)
            result_str = execute_digital_human_speech(message)
            return _response(200, result_str)

        return _response(400, {"error": f"Unknown digital human tool: {tool_name}"})
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.exception("Digital human tool Lambda request failed.")
        return _response(400, {"error": str(exc)})
