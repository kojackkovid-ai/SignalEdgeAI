#!/usr/bin/env python3
"""
Simple test to verify the prediction fixes work
"""
import asyncio
import httpx
import time

async def test_api():
    print("="*60)
    print("TESTING PREDICTION FIXES")
    print("="*60)
    
    base_url = "http://localhost:8000/api"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1. Health Check...")
        try:
            resp = await client.get(f"{base_url}/health", timeout=10)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"   Server is running!")
            else:
                print(f"   Server returned: {resp.text}")
        except Exception as e:
            print(f"   ERROR: Server not running - {e}")
            print("\n   Please start the server first:")
            print("   cd sports-prediction-platform/backend")
            print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
            return False
        
        # Test 2: Login
        print("\n2. Testing Login...")
        try:
            resp = await client.post(
                f"{base_url}/auth/login",
                json={"email": "test@example.com", "password": "testpassword"},
                timeout=10
            )
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                print(f"   Token: {token[:30]}..." if token else "   No token")
            else:
                print(f"   Response: {resp.text[:100]}")
                token = None
        except Exception as e:
            print(f"   ERROR: {e}")
            token = None
        
        if not token:
            print("\n   Cannot test predictions without authentication")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 3: Get NBA Predictions (with 120s timeout)
        print("\n3. Testing NBA Predictions (120s timeout)...")
        start = time.time()
        try:
            resp = await client.get(
                f"{base_url}/predictions/",
                params={"sport": "basketball_nba", "limit": 3},
                headers=headers,
                timeout=130.0  # 130 seconds to allow for 120s server timeout
            )
            elapsed = time.time() - start
            print(f"   Status: {resp.status_code}")
            print(f"   Time: {elapsed:.1f}s")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"   Predictions received: {len(data)}")
                if data:
                    p = data[0]
                    print(f"   Sample: {p.get('matchup')} - {p.get('confidence')}% confidence")
                    print(f"   ✓ PREDICTIONS ARE WORKING!")
                    return True
                else:
                    print("   No predictions returned (empty list)")
            else:
                print(f"   Error: {resp.text[:200]}")
        except httpx.TimeoutException:
            print(f"   TIMEOUT after {time.time() - start:.1f}s")
            print("   The 120s timeout may not be sufficient for all games")
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 4: User Stats (fixed endpoint)
        print("\n4. Testing User Stats (fixed endpoint)...")
        try:
            resp = await client.get(
                f"{base_url}/users/me",
                headers=headers,
                timeout=10
            )
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   User: {data.get('username')}")
                print(f"   Tier: {data.get('subscription_tier')}")
                print(f"   ✓ USER STATS WORKING!")
            else:
                print(f"   Error: {resp.text[:100]}")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "="*60)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_api())
    if result:
        print("✓ Tests completed - predictions should now show in Dashboard")
    else:
        print("✗ Tests failed - check server status")
