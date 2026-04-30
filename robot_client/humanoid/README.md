# Humanoid Robot Client

MQTT client that runs on the Raspberry Pi inside each humanoid robot. It subscribes to the robot's AWS IoT topic, receives commands, and executes them on the physical hardware.

## What It Does

```
AWS IoT (robot_X/topic)
  │
  ▼
pubsub.py  ─── receives MQTT messages
  │
  ├── {"toolName": "wave"}          → ActionExecutor  → sends to servo controller (localhost:9030)
  │                                                    → sends to 3D simulator
  │
  ├── {"toolName": "capture_image"} → captures from camera (localhost:8080) → uploads to S3
  │
  └── {"action": "speech",          → SpeechPlayer    → plays audio on speakers
       "audio_url": "https://..."}                       (streams directly via mpv/ffplay)
                                     → forwards to 3D simulator (POST /speech/<robot_id>)
                                       so the browser plays the same audio
```

## Files

| File | Purpose |
|---|---|
| `pubsub.py` | Main entry point. Connects to AWS IoT via MQTT, dispatches incoming messages. |
| `action_executor.py` | Queues and executes robot actions (servo movements). Sends actions to both the physical servo controller and the 3D simulator. |
| `speech_player.py` | Singleton audio player. Receives presigned S3 URLs (Amazon Polly TTS) and plays them through the robot's speakers. |
| `tools.py` | Action catalog and tool definitions (reference data). |
| `settings.yaml` | Configuration — robot name, IoT endpoint, certificates, simulator URL. |
| `requirements.txt` | Python dependencies. |
| `AmazonRootCA1.pem` | AWS IoT root CA certificate. |

## Setup

### 1. Prerequisites

- Python 3.8+
- Audio player for speech (install one):
  ```bash
  sudo apt install mpv        # recommended — lightweight, streams URLs directly
  # OR
  sudo apt install ffmpeg      # provides ffplay, also streams directly
  ```
- Robot servo controller running on `localhost:9030`
- Camera service on `localhost:8080` (for image capture)

### 2. Install Dependencies

```bash
./create_virtual_env.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

Edit `settings.yaml`:

```yaml
robot_name: "robot_1"              # Your robot ID (robot_1 through robot_9)
input_topic: "{robot_name}/topic"
base_path: "../certificates"
input_cert: "{base_path}/{robot_name}/{robot_name}.cert.pem"
input_key: "{base_path}/{robot_name}/{robot_name}.private.key"
input_ca: "AmazonRootCA1.pem"
input_endpoint: "a1qlex7vqi1791-ats.iot.us-east-1.amazonaws.com"
input_clientId: "arn:aws:iot:us-east-1:111964674713:thing/{robot_name}"
session_key: "hkiitshow"           # Simulator session key
simulator_endpoint: "https://..."  # 3D simulator URL
```

Make sure the IoT certificates for your robot exist at `../certificates/robot_X/`.

### 4. Run

```bash
source venv/bin/activate
python pubsub.py
```

Type `s` and press Enter to stop gracefully.

## IoT Message Formats

The client handles three types of messages on the `robot_X/topic`:

### Robot Action

```json
{"toolName": "wave"}
```

Executes a physical action. See the full list of 38 actions in `action_executor.py`.

### Image Capture

```json
{"toolName": "capture_image", "upload_url": "https://s3-presigned-url..."}
```

Captures a JPEG from the camera and uploads it to S3 via the presigned URL.

### Speech (Amazon Polly TTS)

```json
{"action": "speech", "audio_url": "https://s3-presigned-url...", "text": "你好"}
```

Plays the audio through the robot's speakers. The audio file is an MP3 synthesized by Amazon Polly and stored in S3. Supported languages: Cantonese, Mandarin, English, Japanese, Korean.

The speech event is also forwarded to the 3D simulator (`POST /speech/<robot_id>`) so the browser plays the same audio in sync.

Speech behavior:
- If a new speech message arrives while the previous one is still playing, the old one is **interrupted** and the new one starts immediately.
- Only **one audio instance** plays at any time (singleton pattern).
- `mpv` and `ffplay` stream the URL directly — no download needed.
- Falls back to download + `aplay` if neither is available.

## Connection

The client tries MQTT with mTLS (certificates) first. If that fails, it falls back to WebSocket with AWS IAM credentials. Credentials are loaded from (in order):

1. `settings.yaml` (`aws_access_key_id` / `aws_secret_access_key`)
2. Environment variables (`IoTRobotAccessKeyId` / `IoTRobotSecretAccessKey`)
3. Standard AWS env vars (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)
4. `~/.aws/credentials` file

## Action Queue

The `ActionExecutor` processes actions sequentially:

- Actions are queued and executed one at a time.
- Each action has a configured duration (sleep time) to wait for the servo to finish.
- `stop` clears the queue, interrupts the current action, and returns to `stand`.
- Actions are also forwarded to the 3D simulator for visual feedback.

## Deployment

To deploy to a new robot:

```bash
./create_deploy_package.sh    # creates deploy_package.zip
# Transfer to robot, then:
unzip deploy_package.zip
./create_virtual_env.sh
# Edit settings.yaml with the correct robot_name
source venv/bin/activate
python pubsub.py
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `No audio player available` | Install `mpv` or `ffmpeg`: `sudo apt install mpv` |
| MQTT connection fails | Check certificates exist at `../certificates/robot_X/` and endpoint is correct |
| Actions not executing | Verify servo controller is running on `localhost:9030` |
| Speech not playing | Check speakers are connected; run `aplay -l` to list audio devices |
| Image capture fails | Verify camera service on `localhost:8080` |
