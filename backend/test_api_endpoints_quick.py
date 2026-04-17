"""
Quick test for API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_endpoints():
    print("Testing API Endpoints...")
    print("=" * 50)
    
    # Test 1: Follow endpoint (should return 401 without auth)
    print("\n1. Testing Follow Endpoint...")
    try:
        response = requests.post(
            f'{BASE_URL}/predictions/test-id/follow',
            json={'sport_key': 'basketball_nba'},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [401, 200, 400]:
            print("   PASS: Endpoint exists")
        else:
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Props endpoint
    print("\n2. Testing Props Endpoint...")
    try:
        response = requests.get(
            f'{BASE_URL}/predictions/props/basketball_nba/401810713',
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            props = response.json()
            print(f"   Props count: {len(props)}")
            if props:
                print(f"   Sample: {props[0].get('player')} - {props[0].get('prediction')}")
            print("   PASS: Props working")
        else:
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Predictions endpoint
    print("\n3. Testing Predictions Endpoint...")
    try:
        response = requests.get(
            f'{BASE_URL}/predictions?sport_key=basketball_nba',
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"   Predictions count: {len(predictions)}")
            if predictions:
                p = predictions[0]
                print(f"   Sample: {p.get('matchup')} - {p.get('prediction')}")
            print("   PASS: Predictions working")
        else:
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("API Endpoint Tests Complete")

if __name__ == "__main__":
    test_endpoints()
