# Text Control

Flask-based control plane for the web chat UI, robot knowledge-base editor, Xiaoice-compatible webhook endpoints, and direct AgentCore gateway tool execution.

## What this service does

- Serves the Cognito-protected web UI at `/index`, `/robot`, and `/cleanup`
- Exposes Xiaoice-compatible API endpoints for `talk`, `welcome`, `goodbye`, and `recquestions`
- Routes humanoid and digital-human actions through the Bedrock AgentCore gateway
- Stores robot persona/context data in `RobotTable`
- Stores pending digital-human speech messages in `SpeechTable`
- Optimizes simple robot commands by bypassing the full LLM pipeline when possible

## Main files

| File | Purpose |
|---|---|
| `app.py` | Flask app entry point and Lambda handler |
| `routes/api.py` | API endpoints for chat, Xiaoice compatibility, robot CRUD, actions, image capture, and speech |
| `routes/ui.py` | Web UI routes, including the new SpeechTable cleanup console |
| `middleware.py` | Hybrid auth decorators for session, bearer token, API Gateway context, and internal secret flows |
| `utils/auth.py` | Signature validation and Xiaoice credential resolution |
| `services/speech_db_service.py` | SpeechTable read/delete helpers |
| `scripts/backup_restore.py` | RobotTable backup and restore utility |
| `scripts/sync_postures.py` | Syncs available Xiaoice postures into RobotTable |

## Authentication model

### Web and internal APIs

`@require_hybrid_auth` supports:

- Cognito-backed web session auth
- Bearer token auth for direct API callers
- API Gateway authorizer claims
- `X-Internal-Secret` for trusted service-to-service calls such as simulator-triggered robot actions

### Xiaoice-compatible endpoints

The service resolves project credentials in this order:

1. AWS Secrets Manager secret `XiaoiceProjectCredentials`
2. `XIAOICE_PROJECT_CREDENTIALS` environment variable
3. Local `xiaoice_credentials.json` for offline/local testing
4. Legacy global fallback keys from `XiaoiceChatAccessKey` and `XiaoiceChatSecretKey`

Signature modes:

- **V2 signature**: `/api/talk`, `/api/welcome`, `/api/goodbye`, `/api/recquestions`, `/api/xiaoice-stream-machine`
- **Legacy signature**: `/api/xiaoice-chat-api-strands`, `/api/xiaoice-chat-api-strands-stream`

## Web UI routes

- `/login` — login page
- `/index` — main chat UI
- `/robot` — robot knowledge-base editor
- `/cleanup` — SpeechTable cleanup console
- `/cleanup/api/list` — list pending speech rows
- `/cleanup/api/delete-all` — bulk delete SpeechTable rows
- `/cleanup/api/delete/<message_id>` — delete a single SpeechTable row

## Key API routes

- `/api/chat` — hybrid-auth JSON chat endpoint
- `/api/talk` — Xiaoice-compatible SSE endpoint using signature v2
- `/api/welcome`, `/api/goodbye`, `/api/recquestions` — companion Xiaoice endpoints
- `/api/xiaoice-chat-api-strands` — legacy non-streaming endpoint
- `/api/xiaoice-chat-api-strands-stream` — legacy streaming endpoint
- `/api/xiaoice-stream-machine` — machine route with signature v2 and timestamp-expiry enforcement
- `/api/robots` and `/api/robots/<robot_id>` — robot persona CRUD
- `/api/run_action/<robot_id>` — direct robot action execution
- `/api/capture_image/<robot_id>` — camera capture helper
- `/api/speech/<robot_id>` — speech trigger helper
- `/api/image/<path:object_key>` — media proxy endpoint

## Command optimization

The service still keeps the simple-command fast path:

- command metadata is generated into `command_config/simple_commands.py`
- `update_simple_commands.py` refreshes the command set from the current MCP/AgentCore tool surfaces
- `pre_deploy_update_commands.sh` runs before bundling in the CDK text-control Lambda

This keeps short robot commands on the low-latency path while preserving the LLM flow for complex requests.

## Xiaoice credentials workflow

Generate per-project keys with:

```bash
cd text_control
python3 generate_keys.py [optional_seed] <project_name>
```

Store the generated JSON mapping in `text_control/xiaoice_credentials.json`. During CDK deployment, `TextControlWebConstruct` seeds the `XiaoiceProjectCredentials` secret from that file and grants the Lambda read access to it.

## Operations scripts

### Backup and restore RobotTable

```bash
cd text_control
python3 scripts/backup_restore.py backup --table <table_name> --file robot_table_backup.json
python3 scripts/backup_restore.py restore --table <table_name> --file robot_table_backup.json
```

### Sync available Xiaoice postures

```bash
cd text_control
python3 scripts/sync_postures.py
```

## Local development

```bash
cd text_control
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Tests

Existing manual test scripts live in `text_control/tests/`:

- `tests/test_empty_asktext.py`
- `tests/test_streaming.py`
