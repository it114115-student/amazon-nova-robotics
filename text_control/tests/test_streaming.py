#!/usr/bin/env python3
"""
Test scripts for streaming endpoints
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
    """Calculate signature for legacy authentication (used by xiaoice endpoints)"""
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


def calculate_signature_v2(secret_key: str, timestamp: str, body_string: str) -> str:
    """Calculate signature for authentication following the vendor specification (v2)"""
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


def test_xiaoice_stream():
    """Test the /api/xiaoice-chat-api-strands-stream streaming endpoint"""
    print("Testing XiaoIce streaming endpoint...")
    
    # Configuration
    base_url = "http://127.0.0.1:5000"
    endpoint = "/api/xiaoice-chat-api-strands-stream"
    
    # Get credentials from environment
    secret_key = os.getenv("ChatSecretKey", "test_secret_key")
    access_key = os.getenv("ChatAccessKey", "test_access_key")
    
    # Prepare request
    timestamp = str(int(time.time() * 1000))
    session_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    payload = {
        "askText": "Hello, can you help me control the robot?",
        "sessionId": session_id,
        "traceId": trace_id,
        "languageCode": "en",
        "deviceId": "test_device"
    }
    
    body_string = json.dumps(payload, separators=(',', ':'))
    signature = calculate_signature_legacy(body_string, secret_key, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-Sign": signature,
        "X-Key": access_key
    }
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=payload,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\nStreaming response:")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"Received: {line}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


def test_talk_stream():
    """Test the /api/talk streaming endpoint"""
    print("Testing Talk streaming endpoint...")
    
    # Configuration
    base_url = "http://127.0.0.1:5000"
    endpoint = "/api/talk"
    
    # Get credentials from environment
    secret_key = os.getenv("ChatSecretKey", "test_secret_key")
    access_key = os.getenv("ChatAccessKey", "test_access_key")
    
    # Prepare request
    timestamp = str(int(time.time() * 1000))
    session_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    payload = {
        "askText": "Move the robot forward",
        "sessionId": session_id,
        "traceId": trace_id,
        "languageCode": "en",
        "deviceId": "test_device"
    }
    
    body_string = json.dumps(payload, separators=(',', ':'))
    signature = calculate_signature_v2(secret_key, timestamp, body_string)
    
    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": timestamp,
        "X-Sign": signature,
        "X-Key": access_key
    }
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=payload,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\nStreaming response:")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"Received: {line}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


def test_conversation_continuity():
    """Test conversation continuity in the same session"""
    print("Testing conversation continuity...")
    
    # Configuration
    base_url = "http://127.0.0.1:5000"
    endpoint = "/api/xiaoice-chat-api-strands-stream"
    
    # Get credentials from environment
    secret_key = os.getenv("ChatSecretKey", "test_secret_key")
    access_key = os.getenv("ChatAccessKey", "test_access_key")
    
    session_id = str(uuid.uuid4())
    
    messages = [
        "Hello, I want to control a robot",
        "Make the robot move forward",
        "Now make it turn left",
        "Stop the robot"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i}: {message} ---")
        
        timestamp = str(int(time.time() * 1000))
        trace_id = str(uuid.uuid4())
        
        payload = {
            "askText": message,
            "sessionId": session_id,
            "traceId": trace_id,
            "languageCode": "en",
            "deviceId": "test_device"
        }
        
        body_string = json.dumps(payload, separators=(',', ':'))
        signature = calculate_signature_legacy(body_string, secret_key, timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-Timestamp": timestamp,
            "X-Sign": signature,
            "X-Key": access_key
        }
        
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json=payload,
                headers=headers,
                stream=True,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        print(f"Response: {line}")
                        break  # Just show first response chunk
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)  # Brief pause between messages


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "xiaoice":
            test_xiaoice_stream()
        elif test_type == "talk":
            test_talk_stream()
        elif test_type == "continuity":
            test_conversation_continuity()
        else:
            print("Usage: python test_streaming.py [xiaoice|talk|continuity]")
    else:
        print("Running all streaming tests...")
        test_xiaoice_stream()
        print("\n" + "="*50 + "\n")
        test_talk_stream()
        print("\n" + "="*50 + "\n")
        test_conversation_continuity()
