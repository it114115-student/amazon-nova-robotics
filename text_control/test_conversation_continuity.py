#!/usr/bin/env python3
"""
Test script to verify conversation continuity in the same session
Tests that the streaming endpoint responds correctly to multiple messages
"""

import hashlib
import json
import time
import uuid

import requests


def calculate_signature_legacy(body_string: str, secret_key: str, timestamp: str) -> str:
    """Calculate signature for legacy authentication"""
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


def send_message(
    url: str,
    ask_text: str,
    session_id: str,
    secret_key: str,
    access_key: str,
    verbose: bool = True
) -> tuple[bool, str]:
    """
    Send a message to the streaming endpoint and collect the response
    
    Returns:
        (success, full_reply_text)
    """
    trace_id = str(uuid.uuid4())
    
    # Prepare request
    body = {
        "askText": ask_text,
        "sessionId": session_id,
        "traceId": trace_id,
        "languageCode": "zh",
        "extra": {},
    }
    
    body_string = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    timestamp = str(int(time.time() * 1000))
    signature = calculate_signature_legacy(body_string, secret_key, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "timestamp": timestamp,
        "signature": signature,
        "key": access_key,
    }
    
    if verbose:
        print(f"\nSending: {ask_text}")
        print(f"Session: {session_id}")
        print(f"Trace: {trace_id}")
    
    try:
        response = requests.post(
            url, headers=headers, data=body_string, stream=True, timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return False, ""
        
        full_reply = []
        chunk_count = 0
        
        # Process SSE stream
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                
                if line_str.startswith("data: "):
                    chunk_count += 1
                    data_str = line_str[6:]
                    
                    try:
                        chunk = json.loads(data_str)
                        reply_text = chunk.get("replyText", "")
                        
                        if reply_text:
                            full_reply.append(reply_text)
                            if verbose and chunk_count <= 5:  # Show first 5 chunks
                                print(f"  Chunk {chunk_count}: {reply_text[:50]}...")
                        
                        if chunk.get("isFinal"):
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        return False, ""
        
        full_text = "".join(full_reply)
        
        if verbose:
            print(f"✅ Received {chunk_count} chunks, {len(full_text)} chars")
            if full_text:
                print(f"Response preview: {full_text[:100]}...")
        
        return bool(full_text), full_text
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, ""


def test_conversation_continuity():
    """Test that multiple messages in the same session work correctly"""
    import os
    
    secret_key = os.getenv("XiaoiceChatSecretKey", "your_actual_secret_key")
    access_key = os.getenv("XiaoiceChatAccessKey", "your_actual_access_key")
    
    url = "http://127.0.0.1:5000/api/xiaoice-chat-api-strands-stream"
    session_id = str(uuid.uuid4())
    
    print("=" * 80)
    print("Testing Conversation Continuity")
    print(f"Session ID: {session_id}")
    print("=" * 80)
    
    # Test conversation flow
    conversation = [
        "Hello",
        "What can you do?",
        "Can you tell me about robots?",
        "Thank you",
    ]
    
    results = []
    responses = []
    
    for i, message in enumerate(conversation, 1):
        print(f"\n--- Message {i}/{len(conversation)} ---")
        success, response = send_message(
            url, message, session_id, secret_key, access_key
        )
        results.append(success)
        responses.append(response)
        
        if not success:
            print(f"❌ FAILED: No response for message {i}")
        
        # Wait between messages
        if i < len(conversation):
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for i, (message, success, response) in enumerate(zip(conversation, results, responses), 1):
        status = "✅ PASS" if success else "❌ FAIL"
        response_preview = response[:50] + "..." if len(response) > 50 else response
        print(f"{status} Message {i}: '{message}'")
        print(f"      Response: {response_preview}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} messages received responses")
    
    if passed == total:
        print("\n🎉 All messages in the conversation received responses!")
        print("✅ Conversation continuity test PASSED")
        return True
    else:
        print(f"\n⚠️ {total - passed} message(s) failed to get responses")
        print("❌ Conversation continuity test FAILED")
        return False


if __name__ == "__main__":
    import sys
    
    success = test_conversation_continuity()
    sys.exit(0 if success else 1)
