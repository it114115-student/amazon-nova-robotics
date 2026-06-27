# API Implementation Documentation

## Overview

`text_control` exposes two families of APIs:

1. **Web and operator APIs** for the chat UI, robot CRUD, direct actions, image capture, and speech helpers
2. **Xiaoice-compatible APIs** for streaming talk plus welcome/goodbye/recommended-question flows

The backend runs as a Flask app on AWS Lambda behind API Gateway and talks to the Bedrock AgentCore gateway for humanoid and digital-human tool calls.

## Endpoint summary

### Xiaoice-compatible endpoints

| Endpoint | Method | Auth mode | Notes |
|---|---|---|---|
| `/api/talk` | POST | Signature v2 | Primary SSE endpoint |
| `/api/welcome` | POST | Signature v2 | Returns pending `SpeechTable` message first, otherwise generates a greeting |
| `/api/goodbye` | POST | Signature v2 | Returns localized goodbye text |
| `/api/recquestions` | POST | Signature v2 | Returns localized recommended questions |
| `/api/xiaoice-chat-api-strands` | POST | Legacy signature | Non-streaming compatibility route |
| `/api/xiaoice-chat-api-strands-stream` | POST | Legacy signature | Streaming compatibility route |
| `/api/xiaoice-stream-machine` | POST | Signature v2 + timestamp expiry | Machine route and alias family for `/api/talk` |

### Operator and integration endpoints

| Endpoint | Method | Auth mode | Notes |
|---|---|---|---|
| `/api/chat` | POST | Hybrid auth | JSON chat endpoint |
| `/api/robots` | GET, POST | Hybrid auth | List/create robot persona entries |
| `/api/robots/<robot_id>` | GET, PUT, DELETE | Hybrid auth | Read/update/delete robot persona entries |
| `/api/run_action/<robot_id>` | GET, POST | Hybrid auth | Direct action execution |
| `/api/capture_image/<robot_id>` | POST | Hybrid auth | Capture robot image |
| `/api/speech/<robot_id>` | POST | Hybrid auth | Trigger speech output |
| `/api/image/<path:object_key>` | GET | Hybrid auth | Proxy media asset access |

## Authentication

### Hybrid auth

`@require_hybrid_auth` accepts any of the following:

- authenticated Flask session
- API Gateway authorizer claims
- Cognito bearer token
- `X-Internal-Secret` for trusted service-to-service calls

### Signature auth

Required headers:

- `X-Timestamp`
- `X-Sign`
- `X-Key`

Credential lookup order:

1. `XiaoiceProjectCredentials` in AWS Secrets Manager
2. `XIAOICE_PROJECT_CREDENTIALS` environment variable
3. local `xiaoice_credentials.json`
4. legacy global `XiaoiceChatAccessKey` and `XiaoiceChatSecretKey`

#### V2 signature

Used by:

- `/api/talk`
- `/api/welcome`
- `/api/goodbye`
- `/api/recquestions`
- `/api/xiaoice-stream-machine`

Algorithm:

```python
params = {
    "bodyString": body_string,
    "secretKey": secret_key,
    "timestamp": timestamp,
}
signature_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
signature = hashlib.sha512(signature_string.encode("utf-8")).hexdigest().upper()
```

#### Legacy signature

Used by:

- `/api/xiaoice-chat-api-strands`
- `/api/xiaoice-chat-api-strands-stream`

Algorithm:

```python
payload = body_string + secret_key + timestamp
signature = hashlib.sha512(payload.encode("utf-8")).hexdigest()
```

## Streaming response shape

The SSE endpoints stream `data:` frames containing objects shaped like:

```json
{
  "askText": "Move the robot forward",
  "extra": {},
  "id": "message-id",
  "replyPayload": null,
  "replyText": "The robot is moving forward.",
  "replyType": "Llm",
  "sessionId": "session-id",
  "timestamp": 1710000000000,
  "traceId": "trace-id",
  "isFinal": true
}
```

## Input validation

The API rejects empty or whitespace-only text inputs for the chat and streaming routes. The existing manual regression scripts in `text_control/tests/` cover these validation cases and the streaming flows.

## Robot and digital-human integration

The active cloud deployment is centered on:

- humanoid robots `robot_1` through `robot_6`
- digital human presenter `xiaoice_1`
- group control using `all` where supported by the tool schema

Robot persona data is stored in `RobotTable`. Pending digital-human speech items are stored in `SpeechTable`, with the presenter fixed to `current_presenter` for the welcome-flow handoff.

## Related UI routes

- `/login`
- `/index`
- `/robot`
- `/cleanup`
- `/cleanup/api/list`
- `/cleanup/api/delete-all`
- `/cleanup/api/delete/<message_id>`
