"""
Test API endpoints directly
"""
import asyncio
import httpx
import sys
sys.path.insert(0, '.')

BASE_URL = "http://localhost:8000/api"

async def test_props_endpoint():
    """Test the player props endpoint"""
    async with httpx.AsyncClient() as client:
        # Test NHL props
        print("Testing NHL props endpoint...")
        try:
            response = await client.get(
                f"{BASE_URL}/predictions/props/icehockey_nhl/401672633",
                timeout=30.0
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Props returned: {len(data)}")
                for prop in data[:3]:
                    print(f"    - {prop.get('player')}: {prop.get('prediction')}")
            else:
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"  Exception: {e}")

        # Test MLB props
        print("\nTesting MLB props endpoint...")
        try:
            response = await client.get(
                f"{BASE_URL}/predictions/props/baseball_mlb/401672634",
                timeout=30.0
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Props returned: {len(data)}")
                for prop in data[:3]:
                    print(f"    - {prop.get('player')}: {prop.get('prediction')}")
            else:
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"  Exception: {e}")

async def test_follow_endpoint():
    """Test the follow/unlock endpoint"""
    async with httpx.AsyncClient() as client:
        print("\nTesting follow endpoint...")
        
        # Test data for a player prop
        test_prop_id = "401672633_goals_Connor_McDavid"
        prediction_data = {
            "id": test_prop_id,
            "sport_key": "icehockey_nhl",
            "event_id": "401672633",
            "player": "Connor McDavid",
            "market_key": "goals",
            "prediction": "Over 0.8 Goals",
            "prediction_type": "player_prop",
            "confidence": 72.5,
            "odds": "-110",
            "matchup": "Oilers @ Flames"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/predictions/{test_prop_id}/follow",
                params={"sport_key": "icehockey_nhl"},
                json=prediction_data,
                timeout=10.0
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"  Exception: {e}")

async def main():
    print("=" * 60)
    print("API Endpoint Tests")
    print("=" * 60)
    print("\nNOTE: Server must be running on localhost:8000")
    print("-" * 60)
    
    await test_props_endpoint()
    await test_follow_endpoint()
    
    print("\n" + "=" * 60)
    print("Tests complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
