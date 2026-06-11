#!/usr/bin/env python3
"""
Test script to verify that empty or blank askText values are properly rejected
"""
import hashlib
import json
import os
import time
import requests

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
ENDPOINTS = [
    "/api/talk",
    "/api/xiaoice-chat-api-strands",
    "/api/xiaoice-chat-api-strands-stream"
]


def calculate_signature_legacy(body_string: str, secret_key: str, timestamp: str) -> str:
    """Calculate signature for legacy authentication (used by xiaoice endpoints)"""
    string_to_checksum = body_string + secret_key + timestamp
    sha512 = hashlib.sha512()
    sha512.update(string_to_checksum.encode("utf-8"))
    hex_digest = sha512.hexdigest()
    return hex_digest.replace("-", "")


def calculate_signature_v2(secret_key: str, timestamp: str, body_string: str) -> str:
    """Calculate signature for authentication following the vendor specification (v2)"""
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


def test_empty_asktext(endpoint):
    """Test that endpoint rejects empty askText"""
    print(f"\n{'='*80}")
    print(f"Testing endpoint: {endpoint}")
    print(f"{'='*80}")
    
    # Get credentials from environment
    secret_key = os.getenv("XiaoiceChatSecretKey", "test_secret_key")
    access_key = os.getenv("XiaoiceChatAccessKey", "test_access_key")
    
    # Test cases for empty/blank askText
    test_cases = [
        ("", "empty string"),
        ("   ", "whitespace only"),
        ("\t\t", "tabs only"),
        ("\n\n", "newlines only"),
        ("  \t\n  ", "mixed whitespace")
    ]
    
    for ask_text, description in test_cases:
        print(f"\nTesting {description}: '{repr(ask_text)}'")
        
        payload = {
            "askText": ask_text,
            "sessionId": "test_session",
            "traceId": "test_trace"
        }
        if endpoint == "/api/talk":
            payload["userParams"] = "Summer"
            
        body_string = json.dumps(payload, separators=(',', ':'))
        timestamp = str(int(time.time() * 1000))
        
        if endpoint == "/api/talk":
            signature = calculate_signature_v2(secret_key, timestamp, body_string)
        else:
            signature = calculate_signature_legacy(body_string, secret_key, timestamp)
            
        headers = {
            "Content-Type": "application/json",
            "X-Timestamp": timestamp,
            "X-Sign": signature,
            "X-Key": access_key
        }
        
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", data=body_string, headers=headers, timeout=10)
            
            if response.status_code == 400:
                print(f"✅ PASS: Correctly rejected with status 400")
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data}")
                except:
                    print(f"   Raw response: {response.text}")
            else:
                print(f"❌ FAIL: Expected status 400, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed: {e}")

def test_chat_endpoint():
    """Test the /api/chat endpoint separately"""
    print(f"\n{'='*80}")
    print(f"Testing endpoint: /api/chat")
    print(f"{'='*80}")
    
    test_cases = [
        ("", "empty string"),
        ("   ", "whitespace only"),
        ("\t\t", "tabs only"),
        ("\n\n", "newlines only"),
        ("  \t\n  ", "mixed whitespace")
    ]
    
    internal_secret = os.getenv("INTERNAL_ROBOT_SECRET", "hktiit_robot_internal_bypass_2026")
    
    for message, description in test_cases:
        print(f"\nTesting {description}: '{repr(message)}'")
        
        payload = {
            "message": message,
            "session_id": "test_session"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Secret": internal_secret
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 400:
                print(f"✅ PASS: Correctly rejected with status 400")
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data}")
                except:
                    print(f"   Raw response: {response.text}")
            else:
                print(f"❌ FAIL: Expected status 400, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed: {e}")

def main():
    print("Testing Empty/Blank askText Validation")
    print("=" * 80)
    print("This script tests that all endpoints properly reject empty or blank text inputs")
    
    # Test the main endpoints
    for endpoint in ENDPOINTS:
        test_empty_asktext(endpoint)
    
    # Test the chat endpoint
    test_chat_endpoint()
    
    print(f"\n{'='*80}")
    print("Testing completed!")
    print("All endpoints should reject empty/blank text with status 400")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
