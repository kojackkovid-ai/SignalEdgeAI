"""
End-to-end test for player props API flow.
Tests the complete flow from API endpoint to ESPN data.
"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_player_props_api():
    """Test the player props API endpoint"""
    print("=" * 80)
    print("TESTING PLAYER PROPS API ENDPOINT")
    print("=" * 80)
    
    # First, login to get a token
    print("\n1. Testing login...")
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    
    if login_response.status_code != 200:
        print(f"   Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        print("   Skipping authenticated tests...")
        token = None
    else:
        token = login_response.json().get("access_token")
        print(f"   ✓ Login successful, got token")
    
    if not token:
        print("\n⚠ No authentication token - cannot test protected endpoints")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test the path parameter endpoint
    print("\n2. Testing /api/predictions/props/{sport}/{event_id}...")
    sport = "basketball_nba"
    event_id = "401810657"  # Valid NBA game
    
    response = client.get(
        f"/api/predictions/props/{sport}/{event_id}",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"   ✓ Got {len(data)} props")
            if data:
                print(f"   ✓ First prop: {data[0].get('player', 'N/A')} - {data[0].get('market_key', 'N/A')}")
        else:
            print(f"   ⚠ Unexpected response format: {type(data)}")
            print(f"   Response: {data}")
    else:
        print(f"   ✗ Error: {response.text}")
    
    # Test the query parameter endpoint (frontend compatibility)
    print("\n3. Testing /api/predictions/player-props?event_id=...&sport=...")
    
    response = client.get(
        f"/api/predictions/player-props?event_id={event_id}&sport={sport}",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        props = data.get("props", [])
        print(f"   ✓ Got {len(props)} props")
        if props:
            print(f"   ✓ First prop: {props[0].get('player', 'N/A')} - {props[0].get('market_key', 'N/A')}")
    else:
        print(f"   ✗ Error: {response.text}")
    
    # Test with NHL
    print("\n4. Testing with NHL...")
    sport = "icehockey_nhl"
    event_id = "401803261"  # Valid NHL game
    
    response = client.get(
        f"/api/predictions/props/{sport}/{event_id}",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"   ✓ Got {len(data)} props")
            player_props = [p for p in data if p.get('prediction_type') == 'player_prop']
            print(f"   ✓ Player props: {len(player_props)}")
            if data:
                print(f"   ✓ First prop: {data[0].get('player', 'N/A')} - {data[0].get('market_key', 'N/A')}")
        else:
            print(f"   ⚠ Unexpected response format: {type(data)}")
    else:
        print(f"   ✗ Error: {response.text}")
    
    # Test with invalid event ID
    print("\n5. Testing with invalid event ID...")
    response = client.get(
        "/api/predictions/props/basketball_nba/invalid_id",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) == 0:
            print("   ✓ Correctly returned empty list for invalid ID")
        else:
            print(f"   ⚠ Response: {data}")
    
    print("\n" + "=" * 80)
    print("API ENDPOINT TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_player_props_api()
