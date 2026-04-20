"""Humanoid Skill - Control humanoid robots via MCP server"""

import argparse
import json
import logging
import os
import re
import sys
import time
import uuid

import boto3
import requests
from requests_auth_aws_sigv4 import AWSSigV4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# All actions registered on the MCP server, grouped by category with durations (seconds)
ACTION_CATALOG = {
    "movement": {
        "go_forward": 3.5,
        "back_fast": 4.5,
        "turn_left": 4,
        "turn_right": 4,
        "left_move_fast": 3,
        "right_move_fast": 3,
        "stepping": 3,
    },
    "dance": {
        "dance_one": 85,
        "dance_two": 52,
        "dance_three": 70,
        "dance_four": 83,
        "dance_five": 59,
        "dance_six": 69,
        "dance_seven": 67,
        "dance_eight": 85,
        "dance_nine": 84,
        "dance_ten": 85,
    },
    "combat": {
        "kung_fu": 2,
        "wing_chun": 2,
        "left_kick": 2,
        "right_kick": 2,
        "left_uppercut": 2,
        "right_uppercut": 2,
        "left_shot_fast": 4,
        "right_shot_fast": 4,
    },
    "exercise": {
        "push_ups": 9,
        "sit_ups": 12,
        "squat": 1,
        "squat_up": 6,
        "weightlifting": 9,
        "chest": 9,
    },
    "posture": {
        "stand": 2,
        "stand_up_back": 5,
        "stand_up_front": 5,
    },
    "gesture": {
        "wave": 3.5,
        "bow": 4,
        "twist": 4,
    },
    "control": {
        "stop": 0,
    },
}

# Flat lookup: action_name -> duration
ALL_ACTIONS = {}
for _cat, _actions in ACTION_CATALOG.items():
    ALL_ACTIONS.update(_actions)

def call_mcp_tool(mcp_url, auth, tool_name, arguments, timeout=30):
    """Call an MCP tool on the Lambda server via JSON-RPC. Returns the text result or None."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        resp = requests.post(
            mcp_url, json=payload,
            headers={"Content-Type": "application/json"},
            auth=auth, timeout=timeout,
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        logger.error("MCP request failed: %s", e)
        return None

    if "error" in result:
        logger.error("MCP error: %s", result["error"])
        return None

    content = result.get("result", {}).get("content", [])
    return next((c.get("text", "") for c in content if c.get("type") == "text"), "")


def execute_action(mcp_url, auth, robot_id, action):
    """Execute a single robot action via MCP server. Returns (success, message)."""
    tool_name = f"robot_{action}"
    text = call_mcp_tool(mcp_url, auth, tool_name, {"robot_id": robot_id})
    if text is not None:
        logger.info("[%s] %s -> %s", robot_id, action, text)
        return True, text
    return False, f"Failed to execute {action}"


def capture_image(mcp_url, auth, robot_id):
    """Capture an image via MCP get_image tool. Downloads locally and returns the file path."""
    text = call_mcp_tool(mcp_url, auth, "get_image", {"robot_id": robot_id}, timeout=30)
    if text is None:
        return None

    if "Cannot read image" in text:
        logger.error("Robot did not upload image: %s", text)
        return None

    url_match = re.search(r"image_url=(\S+)", text)
    if not url_match:
        logger.error("No image_url found in MCP response: %s", text)
        return None

    try:
        img_resp = requests.get(url_match.group(1), timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to download image: %s", e)
        return None

    local_dir = os.path.join(os.getcwd(), "captured_images")
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, f"{robot_id}_{uuid.uuid4().hex[:8]}.jpg")

    with open(local_path, "wb") as f:
        f.write(img_resp.content)

    logger.info("Image saved to %s (%d bytes)", local_path, len(img_resp.content))
    return local_path


def validate_action(action):
    """Validate that an action exists. Returns (valid, suggestion)."""
    if action in ALL_ACTIONS or action == "capture_image":
        return True, None
    # Fuzzy match for typos
    from difflib import get_close_matches
    matches = get_close_matches(action, list(ALL_ACTIONS.keys()), n=3, cutoff=0.6)
    return False, matches


def list_actions():
    """Print all available actions grouped by category."""
    output = {"categories": {}, "total_actions": len(ALL_ACTIONS) + 1}
    for category, actions in ACTION_CATALOG.items():
        output["categories"][category] = {
            name: f"{dur}s" for name, dur in actions.items()
        }
    output["categories"]["image"] = {"capture_image": "~15s"}
    print(json.dumps(output, indent=2))


def run_sequence(mcp_url, auth, robot_id, actions, wait):
    """Execute a sequence of actions on a single robot."""
    results = []
    for action in actions:
        action = action.strip()
        if not action:
            continue

        valid, suggestions = validate_action(action)
        if not valid:
            msg = f"Unknown action: {action}"
            if suggestions:
                msg += f" (did you mean: {', '.join(suggestions)}?)"
            logger.error(msg)
            results.append({"action": action, "success": False, "error": msg})
            continue

        if action == "capture_image":
            path = capture_image(mcp_url, auth, robot_id)
            results.append({
                "action": action, "robot_id": robot_id,
                "success": path is not None,
                "file": path,
            })
        else:
            ok, text = execute_action(mcp_url, auth, robot_id, action)
            results.append({
                "action": action, "robot_id": robot_id,
                "success": ok, "response": text,
            })

        # Wait between actions in a sequence if requested
        if wait and action in ALL_ACTIONS:
            duration = ALL_ACTIONS[action]
            if duration > 0:
                wait_time = min(duration, wait) if wait != -1 else duration
                logger.info("Waiting %.1fs for '%s' to complete...", wait_time, action)
                time.sleep(wait_time)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Humanoid Skill - Control a single humanoid robot via MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --robot-id robot_1 --action wave
  %(prog)s --robot-id robot_1 --sequence "wave,bow,dance_one"
  %(prog)s --robot-id robot_1 --sequence "wave,push_ups,bow" --wait
  %(prog)s --list-actions
""",
    )
    parser.add_argument("--profile", default="skill-profile", help="AWS CLI profile name")
    parser.add_argument("--robot-id", help="Robot ID (e.g. robot_1)")
    parser.add_argument("--action", help="Single action to execute")
    parser.add_argument("--sequence", help="Comma-separated list of actions to execute in order")
    parser.add_argument("--wait", nargs="?", const=-1, type=float, default=0,
                        help="Wait for action duration between sequence steps. "
                             "Use --wait for auto-duration or --wait 5 for fixed seconds.")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--mcp-url", default=os.environ.get("MCP_SERVER_URL", ""),
                        help="MCP server Lambda function URL (or set MCP_SERVER_URL env var)")
    parser.add_argument("--list-actions", action="store_true", help="List all available actions and exit")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON (useful for agent consumption)")
    args = parser.parse_args()

    # List actions mode
    if args.list_actions:
        list_actions()
        sys.exit(0)

    # Validate required args for execution
    if not args.robot_id:
        parser.error("--robot-id is required (unless using --list-actions)")
    if not args.action and not args.sequence:
        parser.error("--action or --sequence is required")

    if not args.mcp_url:
        logger.error("--mcp-url or MCP_SERVER_URL env var is required")
        sys.exit(1)

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    auth = AWSSigV4("lambda", session=session)

    robot_id = args.robot_id

    # Build action list from either --action or --sequence
    if args.sequence:
        actions = [a.strip() for a in args.sequence.split(",")]
    else:
        actions = [args.action]

    results = run_sequence(args.mcp_url, auth, robot_id, actions, args.wait)

    # Output
    success = all(r.get("success") for r in results)

    if args.json_output:
        print(json.dumps({"success": success, "results": results}, indent=2))
    else:
        # For single capture_image, print the file path for backward compat
        if len(actions) == 1 and actions[0] == "capture_image":
            path = results[0].get("file") if results else None
            if path:
                print(path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
