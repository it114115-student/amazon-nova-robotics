# Strands Agents Integration

This implementation adds **Strands Agents 1.0** support to the Amazon Nova Robotics text control system, providing production-ready multi-agent orchestration with streaming capabilities.

## Features

- ✅ **SSE Streaming**: Real-time Server-Sent Events compatible with XiaoIce API
- ✅ **Session Persistence**: Automatic conversation state management
- ✅ **Amazon Nova Integration**: Native Bedrock model support
- ✅ **Robot Control Tools**: Direct integration with robot actions
- ✅ **Multi-Robot Support**: Control individual robots or groups
- ✅ **Backward Compatibility**: Maintains existing API endpoints

## Endpoints

### 1. Streaming SSE Endpoint
```
POST /api/talk
Content-Type: application/json
X-Timestamp: <timestamp>
X-Sign: <signature>
X-Key: <access_key>

{
  "askText": "Make robot_1 dance",
  "sessionId": "session_123",
  "traceId": "trace_456",
  "extra": {},
  "languageCode": "en",
  "deviceId": "device_789"
}
```

**Response**: Server-Sent Events stream
```
data: {"askText":"Make robot_1 dance","replyText":"Executing dance action...","isFinal":false}

data: {"askText":"Make robot_1 dance","replyText":"Robot robot_1 executed dance: true","isFinal":true}
```

### 2. Non-Streaming Endpoint
```
POST /xiaoice-chat-api-strands
```
Same request format, returns single JSON response.

## Installation

```bash
# Install dependencies
./install_strands.sh

# Or manually:
pip install strands-agents
mkdir -p agent_sessions
```

## Usage

### Start the Server
```bash
python app.py
```

### Test the Integration
```bash
python test_strands.py
```

## Robot Control Commands

The Strands agent supports natural language commands:

- `"Make robot_1 dance"` - Control specific robot
- `"List available actions"` - Get available commands
- `"Make all robots wave"` - Control all robots
- `"Control robot_2 and robot_3 to do push_ups"` - Multi-robot control

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   XiaoIce API   │───▶│  Strands Agent   │───▶│  Robot Service  │
│   (SSE Stream)  │    │  (Nova Model)    │    │   (AWS IoT)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Session Manager  │
                       │ (File/S3 Store)  │
                       └──────────────────┘
```

## Configuration

Environment variables:
- `AWS_BEDROCK_REGION`: AWS region for Nova model (default: us-east-1)
- `ChatSecretKey`: Secret key for authentication
- `ChatAccessKey`: Access key for authentication

## Session Management

Sessions are automatically persisted to `./agent_sessions/` directory. Each conversation maintains full context across requests.

## Error Handling

- Authentication failures return 401
- Missing parameters return 400
- Server errors return 500
- All errors include descriptive messages

## Performance

- **Async Support**: Full async/await throughout
- **Streaming**: Real-time response chunks
- **Session Persistence**: Automatic state management
- **Concurrent Execution**: Multiple robot actions in parallel

## Compatibility

- ✅ XiaoIce API specification compliant
- ✅ Maintains existing `/xiaoice-chat-api` endpoint
- ✅ Backward compatible with current clients
- ✅ Production-ready with error handling
