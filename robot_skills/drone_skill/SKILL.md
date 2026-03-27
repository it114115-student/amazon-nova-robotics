---
name: drone-skill
description: Publish actions to drones via AWS IoT with Tello SDK command mapping.
---

# Drone Skill

Publishes action commands to drones through AWS IoT Core, mapping high-level actions to Tello SDK commands.

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- IoT Core permissions for `iot:Publish` on `drone_1/topic`

## Usage

```bash
./run.sh --profile <aws-profile> --robot-id drone_1 --action takeoff
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
