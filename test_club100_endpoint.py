#!/usr/bin/env python3
"""Test Club 100 endpoint"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, r'c:\Users\bigba\Desktop\New folder\sports-prediction-platform\backend')

try:
    from app.services.auth_service import AuthService
    print("✅ Backend imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Create auth token
try:
    auth = AuthService()
    test_user = {
        "sub": "test_user_123",  # JWT uses "sub" for subject (user_id)
        "email": "test@example.com",
        "subscription_tier": "elite"
    }
    token = auth.create_access_token(test_user, expires_delta=timedelta(hours=1))
    print(f"✅ Token created: {token[:20]}...")
except Exception as e:
    print(f"❌ Token creation error: {e}")
    sys.exit(1)

# Test the Club 100 endpoint
url = "http://127.0.0.1:8000/api/predictions/club-100/data"
headers = {"Authorization": f"Bearer {token}"}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("✅ Club 100 endpoint returned data!")

        for sport, players in data.items():
            print(f"\n{sport.upper()}: {len(players)} players")
            if players:
                print("Sample player:")
                print(json.dumps(players[0], indent=2))
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Connection error: {e}")