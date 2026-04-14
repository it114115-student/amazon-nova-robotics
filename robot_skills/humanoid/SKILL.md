---
name: humanoid
description: Control a single humanoid robot via MCP server. Supports action sequences, image capture, and JSON output for agent consumption.
---

# Humanoid Skill

Controls a single humanoid robot through the MCP server (Lambda function URL with SigV4 auth). Designed for 1 agent = 1 robot.

## Usage

```bash
# Single action
./run.sh --robot-id robot_1 --action wave

# Sequence of actions
./run.sh --robot-id robot_1 --sequence "wave,push_ups,bow"

# Sequence with auto-wait (waits for each action's duration before next)
./run.sh --robot-id robot_1 --sequence "wave,push_ups,bow" --wait

# Sequence with fixed wait between steps
./run.sh --robot-id robot_1 --sequence "wave,push_ups,bow" --wait 3

# Capture image
./run.sh --robot-id robot_1 --action capture_image

# List all available actions with durations
./run.sh --list-actions

# JSON output (for agent consumption)
./run.sh --robot-id robot_1 --action wave --json
```

## Supported Robots

robot_1, robot_2, robot_3, robot_4, robot_5, robot_6, robot_7, robot_8, robot_9

## Available Actions

### Movement

go_forward (3.5s), back_fast (4.5s), turn_left (4s), turn_right (4s), left_move_fast (3s), right_move_fast (3s), stepping (3s)

### Dance (10 styles)

dance_one (85s), dance_two (52s), dance_three (70s), dance_four (83s), dance_five (59s), dance_six (69s), dance_seven (67s), dance_eight (85s), dance_nine (84s), dance_ten (85s)

### Combat

kung_fu (2s), wing_chun (2s), left_kick (2s), right_kick (2s), left_uppercut (2s), right_uppercut (2s), left_shot_fast (4s), right_shot_fast (4s)

### Exercise

push_ups (9s), sit_ups (12s), squat (1s), squat_up (6s), weightlifting (9s), chest (9s)

### Posture

stand (2s), stand_up_back (5s), stand_up_front (5s)

### Gesture

wave (3.5s), bow (4s), twist (4s)

### Image

capture_image (~15s, downloads image locally to captured_images/)

### Control

stop

## Troubleshooting

If `run.sh` fails, ensure dependencies are installed in the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
