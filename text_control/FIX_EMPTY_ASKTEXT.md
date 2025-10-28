# Fix for Empty/Blank askText Error

## Problem

The API endpoints were not properly validating that the `askText` (or `message` for `/api/chat`) parameter contains actual content. Empty strings or whitespace-only strings would pass validation but could cause errors downstream in the agent processing logic.

## Root Cause

The `parse_request_params()` function in `utils/response_utils.py` only checked if required parameters existed in the request JSON, but did not validate that string values were non-empty and non-blank.

Similarly, the `/api/chat` endpoint's `_chat()` function did not validate the `message` parameter.

## Solution

### 1. Enhanced Parameter Validation

**File: `text_control/utils/response_utils.py`**

Added validation to check that when `askText` is a required parameter, it must:

- Not be an empty string (`""`)
- Not be whitespace-only (e.g., `"   "`, `"\t\t"`, `"\n"`)

```python
# Validate that askText is not empty or blank if it's required
if param == "askText":
    ask_text_value = request.json.get("askText", "")
    if not ask_text_value or not ask_text_value.strip():
        logger.warning(f"Bad request: Parameter 'askText' cannot be empty or blank")
        return None, error_response(400, "Parameter 'askText' cannot be empty or blank")
```

This fix automatically applies to all endpoints using `parse_request_params()` with `askText` in `required_params`:

- `/api/talk`
- `/api/xiaoice-chat-api-strands`
- `/api/xiaoice-chat-api-strands-stream`

### 2. Chat Endpoint Validation

**File: `text_control/routes/api.py`**

Added validation to the `_chat()` function to check the `message` parameter:

```python
# Validate that message is not empty or blank
if not user_message or not user_message.strip():
    logger.warning("Bad request: Parameter 'message' cannot be empty or blank")
    return jsonify({
        "error": "Parameter 'message' cannot be empty or blank",
        "session_id": session_id,
    }), 400
```

This protects the `/api/chat` endpoint.

## Affected Endpoints

| Endpoint                               | Parameter | Status   |
| -------------------------------------- | --------- | -------- |
| `/api/chat`                            | `message` | ✅ Fixed |
| `/api/talk`                            | `askText` | ✅ Fixed |
| `/api/xiaoice-chat-api-strands`        | `askText` | ✅ Fixed |
| `/api/xiaoice-chat-api-strands-stream` | `askText` | ✅ Fixed |

## Error Response

When an empty or blank text parameter is provided, the API now returns:

**Status Code:** `400 Bad Request`

**Response Body:**

```json
{
  "error": {
    "code": 400,
    "message": "Parameter 'askText' cannot be empty or blank"
  }
}
```

For the `/api/chat` endpoint:

```json
{
  "error": "Parameter 'message' cannot be empty or blank",
  "session_id": "..."
}
```

## Testing

A test script has been created at `text_control/test_empty_asktext.py` to verify the fix.

### Running the Tests

1. Start the application server:

   ```bash
   cd /workspaces/amazon-nova-robotics/text_control
   python app.py
   ```

2. In another terminal, run the test:
   ```bash
   cd /workspaces/amazon-nova-robotics/text_control
   python test_empty_asktext.py
   ```

### Test Cases

The test script validates that the following invalid inputs are rejected:

- Empty string: `""`
- Whitespace only: `"   "`
- Tabs only: `"\t\t"`
- Newlines only: `"\n\n"`
- Mixed whitespace: `"  \t\n  "`

## Benefits

1. **Early Error Detection**: Invalid requests fail fast at the validation layer
2. **Better Error Messages**: Clear, actionable error messages for API consumers
3. **Prevents Downstream Errors**: Avoids passing empty strings to the agent/LLM which could cause unexpected behavior
4. **Consistent Validation**: Single implementation applies to multiple endpoints
5. **Logging**: All validation failures are logged for debugging

## Backward Compatibility

This change is backward compatible for all valid use cases. Only requests that were already problematic (empty/blank text) will now receive proper error responses instead of potentially failing silently or with unclear error messages.
