import requests
import json

url = "http://127.0.0.1:8000/api/auth/register"
data = {
    "email": "test123@test.com",
    "password": "TestPass123",
    "username": "testuser123"
}

print("Testing registration...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n[SUCCESS] Registration worked!")
        print(f"Token: {result.get('access_token')[:50]}...")
        print(f"User ID: {result.get('user_id')}")
        print(f"Tier: {result.get('subscription_tier')}")
    else:
        print(f"\n[FAIL] Registration failed")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
