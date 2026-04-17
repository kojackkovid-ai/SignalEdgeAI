import httpx
import asyncio
import json
from datetime import datetime
import sys

# BASE_URL = "http://127.0.0.1:8000/api"
BASE_URL = "http://localhost:8000/api"

async def verify_predictions():
    timestamp = int(datetime.now().timestamp())
    test_email = f"debug_{timestamp}@test.com"
    test_password = "Password123!"
    test_username = f"debug_{timestamp}"
    
    print(f"Creating temporary user: {test_email}")
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        try:
            resp = await client.post(
                f"{BASE_URL}/auth/register",
                json={"email": test_email, "password": test_password, "username": test_username},
                timeout=10.0
            )
            if resp.status_code != 200:
                print(f"Registration failed: {resp.text}")
                return
            
            data = resp.json()
            token = data['access_token']
            print(f"Got token: {token[:20]}...")
            
        except Exception as e:
            print(f"Error during auth: {e}")
            return

        # 2. Fetch Predictions
        print("\nFetching predictions...")
        try:
            resp = await client.get(
                f"{BASE_URL}/predictions/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
            
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                predictions = resp.json()
                print(f"Count: {len(predictions)}")
                if len(predictions) > 0:
                    print("Sample Prediction 0:")
                    print(json.dumps(predictions[0], indent=2))
                else:
                    print("RECEIVED EMPTY LIST []")
            else:
                print(f"Error response: {resp.text}")
                
        except Exception as e:
            print(f"Error fetching predictions: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_predictions())
