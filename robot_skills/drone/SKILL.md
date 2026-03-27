---
name: drone
description: Publish actions to drones via AWS IoT with Tello SDK command mapping.
---

# Drone Skill

Publishes action commands to drones through AWS IoT Core, mapping high-level actions to Tello SDK commands.

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- IoT Core permissions for `iot:Publish` on `drone_*/topic`
- Python dependencies installed: run `pip install -r requirements.txt` (or via `run.sh`)

## Usage

```bash
# With named profile
./run.sh --profile my-robot-profile --robot-id drone_1 --action takeoff

# Uses 'default' profile if --profile is omitted
./run.sh --robot-id drone_1 --action takeoff
```

## Troubleshooting

If `run.sh` fails, ensure dependencies are installed in the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Available Actions

### Flight Control

takeoff, land

### Movement

move_up, move_down, move_left, move_right, move_forward, move_back

### Rotation

rotate_clockwise, rotate_counterclockwise

### Flip

flip
