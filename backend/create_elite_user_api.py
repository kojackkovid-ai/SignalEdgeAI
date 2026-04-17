#!/usr/bin/env python3
"""
Create Elite User via API
Creates an elite user by calling the registration endpoint, then updates the tier
"""

import requests
import json
import time

# API endpoint
BASE_URL = "http://localhost:8000"
REGISTER_ENDPOINT = f"{BASE_URL}/api/auth/register/"

def register_user_via_api(email: str, password: str, username: str):
    """Register user via API endpoint"""
    
    payload = {
        "email": email,
        "password": password,
        "username": username
    }
    
    print(f"Registering user via API...")
    print(f"Endpoint: {REGISTER_ENDPOINT}")
    print(f"Payload: {json.dumps({**payload, 'password': '***'}, indent=2)}")
    print()
    
    try:
        response = requests.post(REGISTER_ENDPOINT, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ User registered successfully!")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            print(f"   Access Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"   User ID: {result.get('user_id', 'N/A')}")
            print(f"   Tier: {result.get('subscription_tier', 'N/A')}")
            
            return result
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API at http://localhost:8000")
        print("   Please make sure the backend server is running:")
        print("   - Start the server with: python -m uvicorn app.main:app --reload")
        print("   - Or use the task: 'Start Backend Server'")
        return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    email = "sportsai@gmail.com"
    password = "bonustester11"
    username = "sportsai_elite"
    
    print("Creating Elite User via API")
    print("=" * 50)
    print()
    
    result = register_user_via_api(email, password, username)
    
    if result:
        print()
        print("✅ User created successfully!")
        print()
        print("📝 Next steps:")
        print(f"   1. Login with email: {email}")
        print(f"   2. Password: {password}")
        print()
        print("📌 Note: This user was registered with the default 'free' tier")
        print("   To upgrade to 'elite', contact an administrator")
    else:
        print()
        print("❌ Failed to create user")
