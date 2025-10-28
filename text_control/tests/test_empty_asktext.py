#!/usr/bin/env python3
"""
Test script to verify that empty or blank askText values are properly rejected
"""
import json
import requests

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
ENDPOINTS = [
    "/api/talk",
    "/api/xiaoice-chat-api-strands",
    "/api/xiaoice-chat-api-strands-stream"
]

def test_empty_asktext(endpoint):
    """Test that endpoint rejects empty askText"""
    print(f"\n{'='*80}")
    print(f"Testing endpoint: {endpoint}")
    print(f"{'='*80}")
    
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
        
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=10)
            
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
    
    for message, description in test_cases:
        print(f"\nTesting {description}: '{repr(message)}'")
        
        payload = {
            "message": message,
            "session_id": "test_session"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=10)
            
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
