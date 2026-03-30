---
name: humanoid
description: Publish actions to humanoid robots via AWS IoT. Supports robot_1 through robot_9. Includes image capture from robot camera.
---

# Humanoid Skill

Publishes action commands to humanoid robots through AWS IoT Core.

## Prerequisites

- AWS CLI profile configured with `SkillMcpUserAccessKeyId` / `SkillMcpUserSecretAccessKey` from CDK output
- MCP server URL from CDK output (`McpServerUrl`)
- Python dependencies installed: run `pip install -r requirements.txt` (or via `run.sh`)

## Usage

```bash
# Set MCP URL (required for all actions)
export MCP_SERVER_URL=https://<McpServerUrl>

# Execute an action
./run.sh --profile skill-profile --robot-id robot_1 --action wave

# Or pass MCP URL directly
./run.sh --profile skill-profile --robot-id robot_1 --action wave --mcp-url https://<McpServerUrl>

# Capture image (downloads locally to captured_images/)
./run.sh --profile skill-profile --robot-id robot_1 --action capture_image
```

## Troubleshooting

If `run.sh` fails, ensure dependencies are installed in the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Available Actions

### Movement

go_forward, back_fast, turn_left, turn_right, left_move_fast, right_move_fast, stepping

### Dance (9 styles)

dance_two, dance_three, dance_four, dance_five, dance_six, dance_seven, dance_eight, dance_nine, dance_ten

### Combat

kung_fu, wing_chun, left_kick, right_kick, left_uppercut, right_uppercut, left_shot_fast, right_shot_fast

### Exercise

push_ups, sit_ups, squat, squat_up, weightlifting, chest

### Posture

stand, stand_up_back, stand_up_front

### Gesture

wave, bow, twist

### Image

capture_image (requires --mcp-url or MCP_SERVER_URL env var; downloads image locally)

### Control

stop
