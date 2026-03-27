---
name: dog-skill
description: Publish actions to Raspberry Pi dog controllers via AWS IoT.
---

# Dog Skill

Publishes action commands to dog robots through AWS IoT Core.

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- IoT Core permissions for `iot:Publish` on `dog_*/topic`

## Usage

```bash
./run.sh --profile <aws-profile> --robot-id dog_1 --action move_forward
```

## Supported Devices

dog_1, dog_2, dog_3

## Available Actions

### Basic Movement
move_forward, move_backward, move_left, move_right, move_leftfront, move_rightfront, move_leftback, move_rightback

### Posture
stand_up, lay_down, hop

### Head Movement
look_up, look_down, look_left, look_right, look_upperleft, look_upperright, look_rightlower, look_leftlower

### Head (Parameterized)
head_move (pitch_deg, yaw_deg, time_uni, time_acc)

### Body Posture
body_row (roll_deg, time_uni, time_acc), balance (roll_deg, pitch_deg, time_uni, time_acc)

### Gait
gait_uni (v_x, v_y, time_uni, time_acc)

### Height
height_move (height, time_uni, time_acc)

### Leg Control
foreleg_lift (leg_side, height, time_uni, time_acc), backleg_lift (leg_side, height, time_uni, time_acc)

### Rotation
rotate (angle)

### Special Movements
bowback (angle), body_cycle, head_ellipse, circle_movement (radius, clockwise)

### Mode & Control
activate, walk_mode, dance_mode, stop, stop (with time parameter)
