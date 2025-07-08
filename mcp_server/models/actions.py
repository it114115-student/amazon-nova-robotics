"""
Robot actions module - Contains the available robot actions with metadata
"""

from typing import Any, Dict

# List of available robot actions with metadata
ACTIONS: Dict[str, Dict[str, Any]] = {
    "back_fast": {"sleep_time": 4.5, "action": ["2", "4"], "name": "back_fast"},
    "bow": {"sleep_time": 4, "action": ["10", "1"], "name": "bow"},
    "chest": {"sleep_time": 9, "action": ["12", "1"], "name": "chest"},
    "dance_eight": {"sleep_time": 85, "action": ["42", "1"], "name": "dance_eight"},
    "dance_five": {"sleep_time": 59, "action": ["39", "1"], "name": "dance_five"},
    "dance_four": {"sleep_time": 59, "action": ["38", "1"], "name": "dance_four"},
    "dance_nine": {"sleep_time": 84, "action": ["43", "1"], "name": "dance_nine"},
    "dance_seven": {"sleep_time": 67, "action": ["41", "1"], "name": "dance_seven"},
    "dance_six": {"sleep_time": 69, "action": ["40", "1"], "name": "dance_six"},
    "dance_ten": {"sleep_time": 85, "action": ["44", "1"], "name": "dance_ten"},
    "dance_three": {"sleep_time": 70, "action": ["37", "1"], "name": "dance_three"},
    "dance_two": {"sleep_time": 52, "action": ["36", "1"], "name": "dance_two"},
    "go_forward": {"sleep_time": 3.5, "action": ["1", "4"], "name": "go_forward"},
    "kung_fu": {"sleep_time": 2, "action": ["46", "2"], "name": "kung_fu"},
    "left_kick": {"sleep_time": 2, "action": ["18", "1"], "name": "left_kick"},
    "left_move_fast": {"sleep_time": 3, "action": ["3", "4"], "name": "left_move_fast"},
    "left_shot_fast": {
        "sleep_time": 4,
        "action": ["13", "1"],
        "name": "left_shot_fast",
    },
    "left_uppercut": {"sleep_time": 2, "action": ["16", "1"], "name": "left_uppercut"},
    "push_ups": {"sleep_time": 9, "action": ["5", "1"], "name": "push_ups"},
    "right_kick": {"sleep_time": 2, "action": ["19", "1"], "name": "right_kick"},
    "right_move_fast": {
        "sleep_time": 3,
        "action": ["4", "4"],
        "name": "right_move_fast",
    },
    "right_shot_fast": {
        "sleep_time": 4,
        "action": ["14", "1"],
        "name": "right_shot_fast",
    },
    "right_uppercut": {
        "sleep_time": 2,
        "action": ["17", "1"],
        "name": "right_uppercut",
    },
    "sit_ups": {"sleep_time": 12, "action": ["6", "1"], "name": "sit_ups"},
    "squat": {"sleep_time": 1, "action": ["11", "1"], "name": "squat"},
    "squat_up": {"sleep_time": 6, "action": ["45", "1"], "name": "squat_up"},
    "stand": {"sleep_time": 1, "action": ["0", "1"], "name": "站立"},
    "stand_up_back": {"sleep_time": 5, "action": ["21", "1"], "name": "stand_up_back"},
    "stand_up_front": {
        "sleep_time": 5,
        "action": ["20", "1"],
        "name": "stand_up_front",
    },
    "stepping": {"sleep_time": 3, "action": ["24", "2"], "name": "stepping"},
    "stop": {"sleep_time": 3, "action": ["24", "2"], "name": "stop"},
    "turn_left": {"sleep_time": 4, "action": ["7", "4"], "name": "turn_left"},
    "turn_right": {"sleep_time": 4, "action": ["8", "4"], "name": "turn_right"},
    "twist": {"sleep_time": 4, "action": ["22", "1"], "name": "twist"},
    "wave": {"sleep_time": 3.5, "action": ["9", "1"], "name": "wave"},
    "weightlifting": {"sleep_time": 9, "action": ["35", "1"], "name": "weightlifting"},
    "wing_chun": {"sleep_time": 2, "action": ["15", "1"], "name": "wing_chun"},
}


def get_available_actions():
    """Return a list of available action names"""
    return list(ACTIONS.keys())


def get_action_metadata(action_name: str) -> Dict[str, Any]:
    """Return metadata for a specific action"""
    return ACTIONS.get(action_name, {})
