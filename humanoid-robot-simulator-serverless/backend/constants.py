#!/usr/bin/env python3
"""Constants and configuration for the Serverless Robot Simulator"""

from enum import Enum


class HumanoidAction(Enum):
    # Basic actions
    IDLE = "idle"
    DANCE = "dance"
    WAVE = "wave"
    BOW = "bow"
    KUNG_FU = "kung_fu"
    KICK = "kick"
    PUNCH = "punch"
    JUMP = "jump"
    PUSH_UPS = "push_ups"
    SIT_UPS = "sit_ups"
    JUMPING_JACKS = "jumping_jacks"
    CELEBRATE = "celebrate"
    THINK = "think"

    # Movement actions
    GO_FORWARD = "go_forward"
    GO_BACKWARD = "go_backward"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    STEPPING = "stepping"
    TWIST = "twist"
    RIGHT_MOVE_FAST = "right_move_fast"
    LEFT_MOVE_FAST = "left_move_fast"
    BACK_FAST = "back_fast"

    # Dance variations
    DANCE_TWO = "dance_two"
    DANCE_THREE = "dance_three"
    DANCE_FOUR = "dance_four"
    DANCE_FIVE = "dance_five"
    DANCE_SIX = "dance_six"
    DANCE_SEVEN = "dance_seven"
    DANCE_EIGHT = "dance_eight"
    DANCE_NINE = "dance_nine"
    DANCE_TEN = "dance_ten"

    # Standing, combat, and exercise actions
    STAND_UP_BACK = "stand_up_back"
    STAND_UP_FRONT = "stand_up_front"
    RIGHT_KICK = "right_kick"
    LEFT_KICK = "left_kick"
    RIGHT_UPPERCUT = "right_uppercut"
    LEFT_UPPERCUT = "left_uppercut"
    WING_CHUN = "wing_chun"
    RIGHT_SHOT_FAST = "right_shot_fast"
    LEFT_SHOT_FAST = "left_shot_fast"
    CHEST = "chest"
    SQUAT_UP = "squat_up"
    SQUAT = "squat"
    WEIGHTLIFTING = "weightlifting"


# Configuration constants
DEFAULT_ROBOTS = [
    {'id': 'robot_1', 'position': [-50, 0, 50], 'color': '#4A90E2'},
    {'id': 'robot_2', 'position': [0, 0, 50], 'color': '#E24A90'},
    {'id': 'robot_3', 'position': [50, 0, 50], 'color': '#90E24A'},
    {'id': 'robot_4', 'position': [-50, 0, -50], 'color': '#E2904A'},
    {'id': 'robot_5', 'position': [0, 0, -50], 'color': '#904AE2'},
    {'id': 'robot_6', 'position': [50, 0, -50], 'color': '#4AE290'},
]

ACTION_DURATIONS = {
    # Dance actions (long durations)
    'dance_two': 52, 'dance_three': 70, 'dance_four': 83, 'dance_five': 59,
    'dance_six': 69, 'dance_seven': 67, 'dance_eight': 85, 'dance_nine': 84, 'dance_ten': 85,

    # Movement actions
    'stepping': 3, 'twist': 4, 'right_move_fast': 3, 'left_move_fast': 3,
    'back_fast': 4.5, 'go_forward': 3.5, 'turn_right': 4, 'turn_left': 4,

    # Standing actions
    'stand_up_back': 5, 'stand_up_front': 5,

    # Combat actions
    'right_kick': 2, 'left_kick': 2, 'right_uppercut': 2, 'left_uppercut': 2,
    'wing_chun': 2, 'right_shot_fast': 4, 'left_shot_fast': 4, 'kung_fu': 2,

    # Exercise actions
    'chest': 9, 'squat_up': 6, 'squat': 1, 'push_ups': 9, 'sit_ups': 12, 'weightlifting': 9,

    # Other actions
    'bow': 4, 'wave': 3.5, 'default': 2
}

MOVEMENT_ACTIONS = {
    HumanoidAction.GO_FORWARD, HumanoidAction.GO_BACKWARD,
    HumanoidAction.TURN_LEFT, HumanoidAction.TURN_RIGHT,
    HumanoidAction.RIGHT_MOVE_FAST, HumanoidAction.LEFT_MOVE_FAST,
    HumanoidAction.BACK_FAST
}
