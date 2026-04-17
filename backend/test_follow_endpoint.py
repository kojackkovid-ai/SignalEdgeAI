"""
Test script to verify the follow endpoint is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_follow_endpoint():
    """Test the follow endpoint with a player prop ID"""
    
    # First, login to get a token
    print("=" * 60)
    print("Testing Follow Endpoint")
    print("=" * 60)
    
    # Try to call the follow endpoint directly (will fail auth but should not 404)
    test_cases = [
        {
            "name": "Player prop with assists",
            "prediction_id": "401810706_assists_Ochai_Agbaji",
            "sport_key": "basketball_nba",
            "prediction_data": {
                "id": "401810706_assists_Ochai_Agbaji",
                "sport_key": "basketball_nba",
                "player": "Ochai Agbaji",
                "market_key": "assists",
                "prediction": "Ochai Agbaji Over 2.5 Assists",
                "confidence": 65.5,
                "prediction_type": "player_prop",
                "point": 2.5
            }
        },
        {
            "name": "Player prop with points",
            "prediction_id": "401810704_points_John_Doe",
            "sport_key": "basketball_nba",
            "prediction_data": {
                "id": "401810704_points_John_Doe",
                "sport_key": "basketball_nba",
                "player": "John Doe",
                "market_key": "points",
                "prediction": "John Doe Over 22.5 Points",
                "confidence": 70.2,
                "prediction_type": "player_prop",
                "point": 22.5
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n--- Testing: {test['name']} ---")
        url = f"{BASE_URL}/api/predictions/{test['prediction_id']}/follow"
        params = {"sport_key": test['sport_key']}
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        print(f"Body: {json.dumps(test['prediction_data'], indent=2)}")
        
        try:
            response = requests.post(
                url,
                params=params,
                json=test['prediction_data'],
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("✓ PASS: Endpoint exists (401 = Unauthorized, need valid token)")
            elif response.status_code == 404:
                print("✗ FAIL: Endpoint not found (404)")
            elif response.status_code == 200:
                print("✓ PASS: Request successful")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"? Response: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("✗ FAIL: Cannot connect to server. Is it running on port 8000?")
        except Exception as e:
            print(f"✗ FAIL: Error - {e}")

if __name__ == "__main__":
    test_follow_endpoint()
