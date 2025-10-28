#!/usr/bin/env python3
"""
Quick manual test for empty askText validation
Run this after starting the server with: python app.py
"""
import json

import requests

BASE_URL = "http://127.0.0.1:5000"

def test_empty():
    print("\n" + "="*60)
    print("Testing EMPTY askText (should be rejected with 400)")
    print("="*60)
    
    payload = {
        "askText": "",
        "sessionId": "test-123",
        "traceId": "trace-123",
        "userParams": "test"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/talk",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 400:
        print("✅ PASS - Empty askText correctly rejected")
    else:
        print("❌ FAIL - Should return 400")

def test_whitespace():
    print("\n" + "="*60)
    print("Testing WHITESPACE-ONLY askText (should be rejected)")
    print("="*60)
    
    payload = {
        "askText": "   \t\n   ",
        "sessionId": "test-123",
        "traceId": "trace-123",
        "userParams": "test"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/talk",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 400:
        print("✅ PASS - Whitespace-only askText correctly rejected")
    else:
        print("❌ FAIL - Should return 400")

def test_valid():
    print("\n" + "="*60)
    print("Testing VALID askText (should be accepted)")
    print("="*60)
    
    payload = {
        "askText": "Hello robot",
        "sessionId": "test-123",
        "traceId": "trace-123",
        "userParams": "test"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/talk",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code in [200, 401, 403]:
        print("✅ PASS - Valid askText accepted (or auth required)")
    else:
        print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    print("Quick Empty/Blank askText Validation Test")
    print("Make sure server is running: python app.py")
    
    try:
        test_empty()
        test_whitespace()
        test_valid()
        
        print("\n" + "="*60)
        print("Tests complete!")
        print("="*60)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure the server is running: python app.py")
        print("Make sure the server is running: python app.py")
