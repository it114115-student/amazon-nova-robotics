#!/usr/bin/env python3
"""
Test script for the /api/talk streaming endpoint
Tests that reasoning events are properly filtered out
"""

import hashlib
import json
import os
import sys
import time
import traceback
import uuid

import requests


def calculate_signature_v2(secret_key: str, timestamp: str, body_string: str) -> str:
    """
    Calculate signature for authentication following the vendor specification (v2).

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
        "timestamp": timestamp,
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


def test_talk_stream(
    url="http://127.0.0.1:5000/api/talk",
    ask_text="dog_move_forward",
    session_id=None,
):
    """Test the talk streaming endpoint"""

    # Get credentials from environment
    secret_key = os.getenv("XiaoiceChatSecretKey", "your_actual_secret_key")
    access_key = os.getenv("XiaoiceChatAccessKey", "your_actual_access_key")

    if not session_id:
        session_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    # Prepare request body
    body = {
        "askText": ask_text,
        "sessionId": session_id,
        "traceId": trace_id,
        "extra": {},
        "languageCode": "zh",
        "deviceId": "test-device",
        "userParams": "",
        "langByAsr": "",
    }

    body_string = json.dumps(body)
    timestamp = str(int(time.time()))

    # Calculate signature using v2 algorithm (matches server's /api/talk endpoint)
    signature = calculate_signature_v2(secret_key, timestamp, body_string)

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-Sign": signature,
        "X-Key": access_key,
    }

    print(f"Testing endpoint: {url}")
    print(f"Question: {ask_text}")
    print(f"Session ID: {session_id}")
    print(f"Trace ID: {trace_id}")
    print("-" * 80)
    print("Debug - Headers:")
    print(f"  X-Timestamp: {timestamp}")
    print(f"  X-Sign: {signature}")
    print(f"  X-Key: {access_key}")
    print("Debug - Body:")
    print(f"  {body_string[:200]}...")
    print("-" * 80)

    # Send request with streaming
    try:
        response = requests.post(
            url, headers=headers, json=body, stream=True, timeout=60
        )

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return False

        print("Streaming response:")
        print("-" * 80)

        chunk_count = 0
        has_reasoning = False
        has_data = False

        # Process SSE stream
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")

                # SSE format: "data: {...}"
                if line_str.startswith("data: "):
                    chunk_count += 1
                    data_str = line_str[6:]  # Remove "data: " prefix

                    try:
                        chunk = json.loads(data_str)

                        # Check for reasoning content
                        reply_text = chunk.get("replyText", "")
                        if any(
                            keyword in reply_text.lower()
                            for keyword in ["<thinking>", "reasoning", "let me think"]
                        ):
                            has_reasoning = True
                            print(
                                f"\n⚠️  WARNING: Chunk {chunk_count} contains reasoning text!"
                            )

                        if reply_text:
                            has_data = True
                            print(f"\nChunk {chunk_count}:")
                            print(f"  Reply: {reply_text[:100]}...")
                            print(f"  isFinal: {chunk.get('isFinal', False)}")

                        # Check if final
                        if chunk.get("isFinal"):
                            print("\n✅ Final chunk received")
                            break

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                        print(f"Raw data: {data_str}")

        print("-" * 80)
        print(f"\nTotal chunks received: {chunk_count}")
        print(f"Has data content: {has_data}")
        print(f"Has reasoning content: {has_reasoning}")

        if has_reasoning:
            print("\n❌ TEST FAILED: Reasoning content was not filtered out!")
            return False
        if has_data:
            print("\n✅ TEST PASSED: Only actual content was streamed (no reasoning)")
            return True
        print("\n⚠️  WARNING: No data content received")
        return False

    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to {url}")
        print("Make sure the server is running with: python app.py")
        return False
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("=" * 80)
    print("Testing /api/talk streaming endpoint")
    print("Checking if reasoning events are properly filtered")
    print("=" * 80)
    print()

    # Test different scenarios
    test_cases = [
        "dog_move_forward",
        # "Tell all robots to dance",
        # "What actions can the robots perform?",
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Case {i}/{len(test_cases)}")
        print(f"{'=' * 80}\n")

        result = test_talk_stream(ask_text=test_case)
        results.append((test_case, result))

        if i < len(test_cases):
            print("\nWaiting 2 seconds before next test...")
            time.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_case, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_case}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
