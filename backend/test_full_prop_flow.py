"""
Test the complete player prop flow including authentication
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_full_flow():
    print("=" * 60)
    print("Testing Full Player Prop Flow")
    print("=" * 60)
    
    # Step 1: Login to get token
    print("\n1. Logging in...")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print(f"   ✓ Got access token")
        else:
            print(f"   ✗ Login failed: {response.text}")
            print("   Trying to register first...")
            
            # Try to register
            reg_data = {
                "email": "test@example.com",
                "password": "password123",
                "username": "testuser"
            }
            reg_response = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
            print(f"   Register status: {reg_response.status_code}")
            
            if reg_response.status_code == 200:
                token_data = reg_response.json()
                access_token = token_data.get('access_token')
                print(f"   ✓ Registered and got token")
            else:
                print(f"   ✗ Register failed: {reg_response.text}")
                return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Get predictions to find a game
    print("\n2. Getting predictions...")
    try:
        response = requests.get(f"{BASE_URL}/predictions/?sport=basketball_nba&limit=5", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', []) if isinstance(data, dict) else data
            print(f"   ✓ Got {len(predictions)} predictions")
            
            if not predictions:
                print("   ✗ No predictions available")
                return False
            
            # Get first prediction
            game = predictions[0]
            event_id = game.get('event_id')
            sport_key = game.get('sport_key', 'basketball_nba')
            print(f"   Using game: {game.get('matchup')} (ID: {event_id})")
        else:
            print(f"   ✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Step 3: Get player props for the game
    print(f"\n3. Getting player props for {sport_key}/{event_id}...")
    try:
        response = requests.get(f"{BASE_URL}/predictions/props/{sport_key}/{event_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            props = response.json()
            print(f"   ✓ Got {len(props)} player props")
            
            if not props:
                print("   ✗ No props available")
                return False
            
            # Show first few props
            for i, prop in enumerate(props[:3]):
                print(f"   Prop {i+1}: {prop.get('player')} - {prop.get('market_key')} - {prop.get('confidence')}%")
            
            # Get first player prop
            player_prop = next((p for p in props if p.get('prediction_type') == 'player_prop'), None)
            if not player_prop:
                print("   ✗ No player props found")
                return False
            
            prop_id = player_prop.get('id')
            print(f"   Selected prop: {prop_id}")
        else:
            print(f"   ✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Step 4: Try to unlock (follow) the player prop
    print(f"\n4. Unlocking player prop {prop_id}...")
    try:
        # Prepare the prediction data
        prediction_data = {
            "id": prop_id,
            "sport_key": sport_key,
            "event_id": event_id,
            "player": player_prop.get('player'),
            "market_key": player_prop.get('market_key'),
            "point": player_prop.get('point'),
            "prediction": player_prop.get('prediction'),
            "prediction_type": player_prop.get('prediction_type', 'player_prop'),
            "confidence": player_prop.get('confidence'),
            "odds": player_prop.get('odds'),
            "matchup": player_prop.get('matchup'),
            "reasoning": player_prop.get('reasoning'),
            "models": player_prop.get('models')
        }
        
        print(f"   Request body: {json.dumps(prediction_data, indent=2)[:200]}...")
        
        response = requests.post(
            f"{BASE_URL}/predictions/{prop_id}/follow",
            params={"sport_key": sport_key},
            json=prediction_data,
            headers=headers
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Successfully unlocked!")
            print(f"   Response: {json.dumps(result, indent=2)[:300]}...")
            return True
        elif response.status_code == 404:
            print(f"   ✗ 404 Not Found - Endpoint issue")
            print(f"   Response: {response.text}")
            return False
        elif response.status_code == 400:
            print(f"   ✗ 400 Bad Request")
            print(f"   Response: {response.text}")
            return False
        elif response.status_code == 403:
            print(f"   ⚠ 403 Forbidden - Daily limit reached")
            print(f"   Response: {response.text}")
            return True  # This is expected behavior
        else:
            print(f"   ✗ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_flow()
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ TESTS FAILED")
    print("=" * 60)
