---
name: humanoid
description: Publish actions to humanoid robots via AWS IoT. Supports robot_1 through robot_9.
---

# Humanoid Skill

Publishes action commands to humanoid robots through AWS IoT Core.

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- IoT Core permissions for `iot:Publish` on `robot_*/topic`

## Usage

```bash
# With named profile
./run.sh --profile my-robot-profile --robot-id robot_1 --action wave

# Uses 'default' profile if --profile is omitted
./run.sh --robot-id robot_1 --action wave
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

### Control

stop
