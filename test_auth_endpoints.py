#!/usr/bin/env python3
"""Test auth endpoints to verify they're working"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test the register endpoint"""
    print("\n🧪 Testing POST /api/auth/register/...")
    url = f"{BASE_URL}/api/auth/register/"
    payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "username": "testuser123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"✅ Register successful!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"❌ Register failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login():
    """Test the login endpoint"""
    print("\n🧪 Testing POST /api/auth/login/...")
    url = f"{BASE_URL}/api/auth/login/"
    payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"✅ Login successful!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_health():
    """Test the health endpoint"""
    print("\n🧪 Testing GET /health...")
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Auth Endpoints Test Suite")
    print("=" * 60)
    
    # Test health check first
    test_health()
    
    # Test register
    register_result = test_register()
    
    # Test login (if register succeeded)
    if register_result:
        test_login()
    else:
        print("\n⚠️  Skipping login test since register failed")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
