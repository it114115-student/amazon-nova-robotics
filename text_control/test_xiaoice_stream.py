#!/usr/bin/env python3
"""
Test script for the /api/xiaoice-chat-api-strands-stream streaming endpoint
Tests the third-party chat API streaming interface with legacy signature authentication
"""

import hashlib
import json
import os
import sys
import time
import traceback
import uuid

import requests


def calculate_signature_legacy(body_string: str, secret_key: str, timestamp: str) -> str:
    """
    Calculate signature for legacy authentication (used by xiaoice endpoints).
    
    Algorithm: SHA512Hash(RequestBody + SecretKey + TimeStamp)
    Note: Keep body as string without changing parameter order
    """
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


def test_xiaoice_stream(
    url="http://127.0.0.1:5000/api/xiaoice-chat-api-strands-stream",
    ask_text="dog_move_forward",
    session_id=None,
    verbose=True,
):
    """Test the xiaoice streaming endpoint with legacy signature authentication"""

    # Get credentials from environment
    secret_key = os.getenv("XiaoiceChatSecretKey", "your_actual_secret_key")
    access_key = os.getenv("XiaoiceChatAccessKey", "your_actual_access_key")

    if not session_id:
        session_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    # Prepare request body (must maintain order for signature calculation)
    body = {
        "askText": ask_text,
        "sessionId": session_id,
        "traceId": trace_id,
        "languageCode": "zh",
        "extra": {"testMode": "true"},
    }

    body_string = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    timestamp = str(int(time.time() * 1000))  # Unix timestamp in milliseconds

    # Calculate signature using legacy algorithm
    signature = calculate_signature_legacy(body_string, secret_key, timestamp)

    # Prepare headers (legacy format)
    headers = {
        "Content-Type": "application/json",
        "timestamp": timestamp,
        "signature": signature,
        "key": access_key,
    }

    if verbose:
        print(f"Testing endpoint: {url}")
        print(f"Question: {ask_text}")
        print(f"Session ID: {session_id}")
        print(f"Trace ID: {trace_id}")
        print("-" * 80)
        print("Debug - Headers:")
        print(f"  timestamp: {timestamp}")
        print(f"  signature: {signature[:32]}...")
        print(f"  key: {access_key}")
        print("Debug - Body:")
        print(f"  {body_string[:150]}...")
        print("-" * 80)

    # Send request with streaming
    try:
        response = requests.post(
            url, headers=headers, data=body_string, stream=True, timeout=60
        )

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return False

        if verbose:
            print("Streaming response:")
            print("-" * 80)

        chunk_count = 0
        has_data = False
        full_reply = []
        last_chunk = None

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
                        last_chunk = chunk

                        # Validate required fields
                        required_fields = [
                            "id",
                            "traceId",
                            "sessionId",
                            "askText",
                            "replyText",
                            "replyType",
                            "timestamp",
                        ]
                        missing_fields = [
                            field for field in required_fields if field not in chunk
                        ]
                        if missing_fields:
                            print(
                                f"\n⚠️  WARNING: Chunk {chunk_count} missing fields: {missing_fields}"
                            )

                        reply_text = chunk.get("replyText", "")
                        if reply_text:
                            has_data = True
                            full_reply.append(reply_text)
                            if verbose:
                                print(f"\nChunk {chunk_count}:")
                                print(f"  ID: {chunk.get('id', 'N/A')}")
                                print(f"  Reply: {reply_text[:100]}...")
                                print(f"  ReplyType: {chunk.get('replyType', 'N/A')}")
                                print(f"  isFinal: {chunk.get('isFinal', False)}")

                        # Check if final
                        if chunk.get("isFinal"):
                            if verbose:
                                print("\n✅ Final chunk received")
                            break

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                        print(f"Raw data: {data_str}")

        if verbose:
            print("-" * 80)
            print(f"\nTotal chunks received: {chunk_count}")
            print(f"Has data content: {has_data}")

        # Validate response format
        if last_chunk:
            print("\nResponse validation:")
            print(f"  ✓ ID present: {bool(last_chunk.get('id'))}")
            print(f"  ✓ TraceId matches: {last_chunk.get('traceId') == trace_id}")
            print(
                f"  ✓ SessionId matches: {last_chunk.get('sessionId') == session_id}"
            )
            print(f"  ✓ AskText matches: {last_chunk.get('askText') == ask_text}")
            print(f"  ✓ ReplyType present: {bool(last_chunk.get('replyType'))}")
            print(f"  ✓ Timestamp present: {bool(last_chunk.get('timestamp'))}")
            print(
                f"  ✓ Extra field present: {'extra' in last_chunk} (optional, value: {last_chunk.get('extra', 'N/A')})"
            )
            print(
                f"  ✓ ReplyPayload field present: {'replyPayload' in last_chunk} (optional)"
            )

        if has_data:
            full_text = "".join(full_reply)
            print(f"\nFull reply ({len(full_text)} chars):")
            print(f"  {full_text[:200]}...")
            print("\n✅ TEST PASSED: Streaming endpoint working correctly")
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


def test_xiaoice_non_stream(
    url="http://127.0.0.1:5000/api/xiaoice-chat-api-strands",
    ask_text="dog_move_forward",
    session_id=None,
):
    """Test the non-streaming endpoint for comparison"""

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
        "languageCode": "zh",
        "extra": {"testMode": "true"},
    }

    body_string = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    timestamp = str(int(time.time() * 1000))

    # Calculate signature
    signature = calculate_signature_legacy(body_string, secret_key, timestamp)

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "timestamp": timestamp,
        "signature": signature,
        "key": access_key,
    }

    print(f"Testing non-streaming endpoint: {url}")
    print(f"Question: {ask_text}")
    print("-" * 80)

    try:
        response = requests.post(url, headers=headers, data=body_string, timeout=60)

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return False

        result = response.json()

        print("Response:")
        print("-" * 80)
        print(f"  ID: {result.get('id', 'N/A')}")
        print(f"  TraceId: {result.get('traceId', 'N/A')}")
        print(f"  ReplyText: {result.get('replyText', '')[:200]}...")
        print(f"  ReplyType: {result.get('replyType', 'N/A')}")
        print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
        print("-" * 80)

        if result.get("replyText"):
            print("\n✅ TEST PASSED: Non-streaming endpoint working correctly")
            return True

        print("\n⚠️  WARNING: No reply text received")
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
    print("Testing XiaoIce Chat API Endpoints (Legacy Signature)")
    print("=" * 80)
    print()

    # Test cases
    test_cases = [
        "dog_move_forward",
        "What can you do?",
    ]

    results = []

    # Test streaming endpoint
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"STREAMING Test Case {i}/{len(test_cases)}")
        print(f"{'=' * 80}\n")

        result = test_xiaoice_stream(ask_text=test_case)
        results.append(("STREAM: " + test_case, result))

        if i < len(test_cases):
            print("\nWaiting 2 seconds before next test...")
            time.sleep(2)

    # Test non-streaming endpoint for comparison
    print(f"\n{'=' * 80}")
    print("NON-STREAMING Test (for comparison)")
    print(f"{'=' * 80}\n")
    result = test_xiaoice_non_stream(ask_text=test_cases[0])
    results.append(("NON-STREAM: " + test_cases[0], result))

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
