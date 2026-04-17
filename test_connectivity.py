#!/usr/bin/env python3
"""
Test backend connectivity and API
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Health check passed")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    return False

def test_cors_headers():
    """Test CORS headers on predictions endpoint"""
    try:
        # Send OPTIONS request for CORS preflight
        resp = requests.options(
            f"{BASE_URL}/api/predictions",
            headers={"Origin": "http://localhost:5173"},
            timeout=5
        )
        
        cors_header = resp.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            print(f"✅ CORS header present: {cors_header}")
            return True
        else:
            print("❌ CORS header missing")
            return False
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
    return False

if __name__ == "__main__":
    print(f"Testing backend at {BASE_URL}...")
    print("\nWaiting for backend to start (up to 30s)...")
    
    started = False
    for i in range(30):
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=1)
            if resp.status_code in [200, 503]:
                started = True
                print(f"✅ Backend is running after {i}s")
                break
        except:
            pass
        
        if i % 5 == 0 and i > 0:
            print(f"  Still waiting... ({i}s)")
        time.sleep(1)
    
    if not started:
        print("❌ Backend failed to start within 30 seconds")
        sys.exit(1)
    
    time.sleep(1)  # Give it a moment to settle
    
    print("\nRunning tests...")
    test_health()
    test_cors_headers()
    
    print("\n✅ Basic tests completed!")
