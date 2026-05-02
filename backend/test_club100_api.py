#!/usr/bin/env python3
"""
Test script for Club 100 API endpoint
"""
import asyncio
import httpx
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_club_100_api():
    """Test the Club 100 API endpoint"""
    print("Testing Club 100 API endpoint...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://127.0.0.1:8000/api/predictions/club-100/data",
                headers={
                    "Authorization": "Bearer test-token",
                    "Content-Type": "application/json"
                }
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ API call successful")
                print(f"   Response type: {type(data)}")

                if isinstance(data, list):
                    print(f"   Returned {len(data)} streak records")
                    if data:
                        sample = data[0]
                        print(f"   Sample record keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                        if isinstance(sample, dict):
                            print(f"   Sample player: {sample.get('player_name', 'N/A')}")
                            print(f"   Sample streak: {sample.get('streak_length', 'N/A')} games")
                else:
                    print(f"   Response: {data}")

            else:
                print(f"❌ API call failed with status {response.status_code}")
                print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    asyncio.run(test_club_100_api())