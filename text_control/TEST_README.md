# Test Scripts for /api/talk Endpoint

These scripts test the `/api/talk` streaming endpoint to verify that reasoning events are properly filtered out.

## Prerequisites

1. Start the local server:

   ```bash
   cd /workspaces/amazon-nova-robotics/text_control
   source .venv/bin/activate
   python app.py
   ```

2. The server should be running on `http://localhost:5000`

## Test Scripts

### 1. Comprehensive Python Test (`test_talk_stream.py`)

Runs multiple test cases and checks for reasoning content in responses.

```bash
python test_talk_stream.py
```

**Features:**

- Tests multiple questions
- Checks each chunk for reasoning text
- Provides detailed summary
- Exit code 0 if all tests pass, 1 if any fail

**Example output:**

```
================================================================================
Testing /api/talk streaming endpoint
Checking if reasoning events are properly filtered
================================================================================

Test Case 1/3
Question: Make robot_1 wave
Streaming response:
Chunk 1: 機器人1正在揮手...
✅ TEST PASSED: Only actual content was streamed (no reasoning)
```

### 2. Simple Interactive Python Test (`test_talk_simple.py`)

Quick interactive test with a single question.

```bash
python test_talk_simple.py
```

**Features:**

- Interactive prompt for question
- Real-time streaming output
- Checks for reasoning indicators
- Simple pass/fail result

**Example:**

```bash
$ python test_talk_simple.py
Enter your question (or press Enter for default): Tell robot_1 to dance
📡 Sending: Tell robot_1 to dance
================================================================================
📥 Streaming response:
好的，我讓機器人1跳舞...
================================================================================
✅ Response does not contain reasoning text
```

### 3. Bash Script Test (`test_talk_stream.sh`)

Simple bash script for quick testing.

```bash
./test_talk_stream.sh "Make all robots wave"
```

**Features:**

- Single command test
- Custom question as argument
- Color-coded output
- Uses environment variables for credentials

## Environment Variables

The scripts use these environment variables (or defaults):

- `ChatSecretKey` - Secret key for signature (default: "your_actual_secret_key")
- `ChatAccessKey` - Access key for authentication (default: "your_actual_access_key")

Set them before running:

```bash
export ChatSecretKey="your_secret_key"
export ChatAccessKey="your_access_key"
```

## What Gets Checked

The tests verify that responses do NOT contain:

- `<thinking>` tags
- "reasoning" text
- "let me think" phrases
- Any other reasoning-related content

## Expected Behavior

✅ **PASS**: Response contains only actual robot action confirmations and results
❌ **FAIL**: Response contains reasoning/thinking process text

## Troubleshooting

### Connection Error

```
❌ ERROR: Could not connect to http://localhost:5000/api/talk
```

**Solution**: Make sure the Flask app is running:

```bash
python app.py
```

### Authentication Error

```
Error: HTTP 401
```

**Solution**: Check that `ChatSecretKey` and `ChatAccessKey` match server configuration

### No Data Received

```
⚠️  WARNING: No data content received
```

**Solution**:

- Check if MCP server is running
- Verify robot services are available
- Check server logs for errors

## Quick Start

```bash
# 1. Start the server (in one terminal)
cd /workspaces/amazon-nova-robotics/text_control
source .venv/bin/activate
python app.py

# 2. Run tests (in another terminal)
cd /workspaces/amazon-nova-robotics/text_control
source .venv/bin/activate
python test_talk_stream.py
```
