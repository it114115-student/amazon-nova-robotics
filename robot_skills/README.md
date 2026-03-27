# Robot Skills

Self-contained, independently runnable robot control skills for AWS IoT.

## Prerequisites

- Python 3.8+
- AWS CLI configured with a named profile: `aws configure --profile <profile-name>`

## Skills

| Skill | Description |
|---|---|
| `humanoid_skill` | Publish actions to humanoid robots (robot_1 through robot_9) |
| `drone_skill` | Publish actions to drones with Tello SDK mapping |
| `dog_skill` | Publish actions to Raspberry Pi dog controllers |

## Usage

```bash
cd <skill_folder>
./run.sh --profile my-aws-profile --robot-id robot_1 --action wave
```

Each skill is fully independent — its own venv, its own deps, no shared imports.
