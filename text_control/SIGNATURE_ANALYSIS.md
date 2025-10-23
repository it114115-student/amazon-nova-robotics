# Signature Calculation Analysis

## Current Implementation vs. Vendor Specification

### Vendor Specification (Chinese Documentation)

**Authentication Requirements:**
All interfaces require signature verification to ensure request legitimacy and security.

**Authentication Parameters:**

- `X-Timestamp` (Header, String, Required): Request timestamp in milliseconds
- `X-Sign` (Header, String, Required): Request signature
- `X-Key` (Header, String, Required): Access key

**Signature Algorithm:**

1. Build a signature parameter Map containing:

   - `secretKey`: Server-side (user) preset secret key
   - `timestamp`: Request timestamp
   - `bodyString`: JSON serialized string of request body

2. Sort parameters by key name in ascending order and connect with "&" in format:

   ```
   key1=value1&key2=value2&key3=value3
   ```

3. Calculate SHA-512 hash and convert to **UPPERCASE**

4. Use the calculated hash value as the `X-Sign` value in request header

**Authentication Verification Flow:**

1. Verify request headers contain necessary signature parameters (X-Timestamp, X-Sign, X-Key)
2. Verify X-Key is included in system preset accessKey
3. Verify request is within validity period (currently set to 5 minutes)
4. Calculate signature using same algorithm and compare with X-Sign in request header
5. If verification passes, process request; otherwise return 401 error

---

## Implementation Analysis

### ❌ Existing Implementation: `calculate_signature()`

**Location:** `text_control/routes/api.py` lines 50-57

```python
def calculate_signature(secret_key: str, timestamp: str, body_string: str) -> str:
    """Calculate signature for authentication"""
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")
```

**Issues:**

1. ❌ **Incorrect concatenation format**: Concatenates values directly without key names

   - Current: `body_string + secret_key + timestamp`
   - Should be: `bodyString=<value>&secretKey=<value>&timestamp=<value>`

2. ❌ **Missing uppercase conversion**: Returns lowercase hex digest

   - Current: `hex_digest.replace("-", "")`
   - Should be: `hex_digest.replace("-", "").upper()`

3. ❌ **No parameter sorting**: The vendor spec requires sorting by key name
   - Required order: `bodyString`, `secretKey`, `timestamp` (alphabetically sorted)

---

### ✅ New Implementation: `calculate_signature_v2()`

**Location:** `text_control/routes/api.py` lines 60-95

```python
def calculate_signature_v2(secret_key: str, timestamp: str, body_string: str) -> str:
    """
    Calculate signature for authentication following the vendor specification.

    Algorithm:
    1. Build a parameter Map with: secretKey, timestamp, bodyString
    2. Sort parameters by key name in ascending order and connect with "&"
       Format: key1=value1&key2=value2&key3=value3
    3. Calculate SHA-512 hash and convert to UPPERCASE
    """
    # Create parameter map
    params = {
        "bodyString": body_string,
        "secretKey": secret_key,
        "timestamp": timestamp
    }

    # Sort by key name in ascending order and create signature string
    sorted_params = sorted(params.items())
    signature_string = "&".join([f"{k}={v}" for k, v in sorted_params])

    # Calculate SHA-512 hash
    sha512 = hashlib.sha512()
    sha512.update(signature_string.encode("utf-8"))
    hex_digest = sha512.hexdigest()

    # Convert to uppercase
    return hex_digest.replace("-", "").upper()
```

**Correct Implementation:**

1. ✅ **Proper key-value format**: Creates parameter map with key names
2. ✅ **Alphabetical sorting**: Sorts parameters before concatenation
3. ✅ **Uppercase conversion**: Converts hash to uppercase as required
4. ✅ **Correct format**: `bodyString=<value>&secretKey=<value>&timestamp=<value>`

---

## Example Comparison

Given:

- `secret_key` = "my_secret"
- `timestamp` = "1234567890"
- `body_string` = '{"message":"hello"}'

### Old Implementation Output:

```
String to hash: {"message":"hello"}my_secret1234567890
Hash: lowercase_hex_string
```

### New Implementation Output:

```
String to hash: bodyString={"message":"hello"}&secretKey=my_secret&timestamp=1234567890
Hash: UPPERCASE_HEX_STRING
```

---

## Current Usage in Code

The existing `calculate_signature()` function is currently used but **the signature verification is commented out** in multiple endpoints:

1. **`talk_stream()` endpoint** (line 130):

   ```python
   calculated_signature = calculate_signature(stored_secret_key, timestamp, body_string)
   # if calculated_signature != signature:
   #     logger.warning("Authentication failed: Invalid signature")
   #     return error_response(401, "Invalid signature")
   ```

2. **`welcome()` endpoint** (line 371)
3. **`goodbye()` endpoint** (line 462)
4. **`recquestions()` endpoint** (line 553)

---

## Recommendation

### To Use Vendor-Compatible Signature:

Replace all occurrences of:

```python
calculated_signature = calculate_signature(stored_secret_key, timestamp, body_string)
```

With:

```python
calculated_signature = calculate_signature_v2(stored_secret_key, timestamp, body_string)
```

Then uncomment the signature verification blocks to enable proper authentication.

---

## Verification Checklist

- ✅ `calculate_signature_v2()` follows vendor specification exactly
- ✅ Parameters are sorted alphabetically
- ✅ Format is `key=value&key=value`
- ✅ Hash is converted to uppercase
- ✅ Old function preserved for backward compatibility
- ⚠️ Signature verification currently commented out (needs to be enabled)
- ⚠️ Need to update all endpoints to use `calculate_signature_v2()`

---

## Summary

**Answer to your question: "Does the api.py follow the rule in description?"**

**NO**, the current `calculate_signature()` function does **NOT** follow the vendor specification. However, I have added a new `calculate_signature_v2()` function that correctly implements the specification.

The old function has been preserved unchanged as requested. To use the correct implementation, you need to:

1. Replace `calculate_signature()` calls with `calculate_signature_v2()` in all endpoints
2. Uncomment the signature verification blocks
3. Ensure timestamp validation (5-minute window) is implemented
