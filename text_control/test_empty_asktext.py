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
    
    test_cases = [
        {"name": "Empty string", "askText": ""},
        {"name": "Whitespace only", "askText": "   "},
        {"name": "Tabs only", "askText": "\t\t"},
        {"name": "Newlines only", "askText": "\n\n"},
        {"name": "Mixed whitespace", "askText": "  \t\n  "},
    ]
    
    for test in test_cases:
        print(f"\n📝 Test case: {test['name']}")
        print(f"   Value: {repr(test['askText'])}")
        
        payload = {
            "askText": test["askText"],
            "sessionId": "test-session-123",
            "traceId": "test-trace-123",
            "userParams": "test-user"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 400:
                print(f"   ✅ PASS - Correctly rejected with 400")
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data.get('error', {}).get('message', 'N/A')}")
                except:
                    print(f"   Response: {response.text[:200]}")
            else:
                print(f"   ❌ FAIL - Should return 400, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Server not running")
            return False
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    return True

def test_valid_asktext(endpoint):
    """Test that endpoint accepts valid askText"""
    print(f"\n{'='*80}")
    print(f"Testing valid askText on: {endpoint}")
    print(f"{'='*80}")
    
    payload = {
        "askText": "Hello, this is a valid question",
        "sessionId": "test-session-123",
        "traceId": "test-trace-123",
        "userParams": "test-user"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        # For streaming endpoints, 200 is expected, for non-streaming we might get various codes
        if response.status_code in [200, 401, 403]:  # 401/403 if auth is enabled
            print(f"✅ PASS - Valid askText accepted (or auth required)")
        else:
            print(f"⚠️  Got status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("="*80)
    print("EMPTY/BLANK askText VALIDATION TEST")
    print("="*80)
    print("\nThis test verifies that API endpoints properly reject empty or blank askText values")
    print("\nNote: Tests will show '⚠️ Server not running' if the server is not started")
    print("      Start server with: python app.py")
    
    for endpoint in ENDPOINTS:
        test_empty_asktext(endpoint)
    
    # Test one valid case to ensure we didn't break normal functionality
    test_valid_asktext("/api/talk")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("="*80)
