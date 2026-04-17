import httpx
import asyncio
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

async def test_auth_flow():
    timestamp = int(datetime.now().timestamp())
    test_email = f"testuser{timestamp}@test.com"
    test_password = "TestPassword123!"
    test_username = f"testuser{timestamp}"
    
    print("=" * 60)
    print("TESTING AUTHENTICATION FLOW")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Registration
        print("\n[1] Testing Registration...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": test_email,
                    "password": test_password,
                    "username": test_username
                }
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Registration successful")
                print(f"  - access_token: {data.get('access_token')[:50]}...")
                print(f"  - user_id: {data.get('user_id')}")
                print(f"  - subscription_tier: {data.get('subscription_tier')}")
                token = data.get('access_token')
            else:
                print(f"[FAIL] Registration failed: {response.text}")
                return
        except Exception as e:
            print(f"[ERROR] Registration error: {e}")
            return
        
        # Test 2: Login
        print("\n[2] Testing Login...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                }
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Login successful")
                print(f"  - access_token: {data.get('access_token')[:50]}...")
                print(f"  - user_id: {data.get('user_id')}")
                print(f"  - subscription_tier: {data.get('subscription_tier')}")
                token = data.get('access_token')
            else:
                print(f"[FAIL] Login failed: {response.text}")
                return
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            return
        
        # Test 3: Get user profile
        print("\n[3] Testing Get User Profile...")
        try:
            response = await client.get(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Profile retrieved")
                print(f"  - username: {data.get('username')}")
                print(f"  - email: {data.get('email')}")
                print(f"  - subscription_tier: {data.get('subscription_tier')}")
            else:
                print(f"[FAIL] Get profile failed: {response.text}")
        except Exception as e:
            print(f"[ERROR] Get profile error: {e}")
        
        # Test 4: Get real predictions
        print("\n[4] Testing Get Real Predictions...")
        try:
            response = await client.get(
                f"{BASE_URL}/predictions/",
                headers={"Authorization": f"Bearer {token}"},
                params={"limit": 3}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                predictions = response.json()
                print(f"[OK] Retrieved {len(predictions)} predictions")
                if predictions:
                    for i, pred in enumerate(predictions, 1):
                        print(f"\n  Prediction {i}:")
                        print(f"    - Sport: {pred.get('sport')}")
                        print(f"    - Matchup: {pred.get('matchup')}")
                        print(f"    - Prediction: {pred.get('prediction')}")
                        print(f"    - Confidence: {pred.get('confidence')}%")
                else:
                    print("  (No predictions available from OddsAPI)")
            else:
                print(f"[FAIL] Get predictions failed: {response.text}")
        except Exception as e:
            print(f"[ERROR] Get predictions error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
