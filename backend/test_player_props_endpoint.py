"""
Test script to verify player props endpoint is working correctly.
Tests the full flow from API call to ESPN data retrieval.
"""
import asyncio
import httpx
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_player_props_endpoint():
    """Test the player props endpoint with real ESPN data"""
    print("=" * 80)
    print("TESTING PLAYER PROPS ENDPOINT")
    print("=" * 80)
    
    service = ESPNPredictionService()
    
    # Test with a valid NHL game (from previous successful tests)
    test_cases = [
        {
            "sport_key": "icehockey_nhl",
            "event_id": "401672719",  # Valid NHL game ID
            "description": "NHL Game - Should return props"
        },
        {
            "sport_key": "basketball_nba",
            "event_id": "401672720",  # Test NBA game
            "description": "NBA Game - Should return props or empty if no data"
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['description']}")
        print(f"Sport: {test['sport_key']}, Event ID: {test['event_id']}")
        print(f"{'='*60}")
        
        try:
            # Call the service directly
            props = await service.get_player_props(test['sport_key'], test['event_id'])
            
            print(f"\n✓ Service call completed successfully")
            print(f"✓ Returned {len(props)} player props")
            
            if props:
                print(f"\n--- Sample Props ---")
                for i, prop in enumerate(props[:3]):  # Show first 3
                    print(f"  {i+1}. {prop.get('player', 'N/A')} - {prop.get('market_key', 'N/A')}")
                    print(f"     Prediction: {prop.get('prediction', 'N/A')}")
                    print(f"     Confidence: {prop.get('confidence', 'N/A')}%")
                    print(f"     Type: {prop.get('prediction_type', 'N/A')}")
            else:
                print(f"\n⚠ No props returned - this is expected if no real ESPN data available")
                
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    await service.close()
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

async def test_api_endpoint_directly():
    """Test the API endpoint directly with HTTP request"""
    print("\n" + "=" * 80)
    print("TESTING API ENDPOINT DIRECTLY")
    print("=" * 80)
    
    # First, we need to get a valid token
    # For now, just test if the endpoint is accessible
    
    base_url = "http://localhost:8000/api"
    
    async with httpx.AsyncClient() as client:
        # Test the player-props endpoint (without auth to see error)
        try:
            response = await client.get(
                f"{base_url}/predictions/player-props",
                params={"event_id": "401672719", "sport": "icehockey_nhl"},
                timeout=30.0
            )
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
        except Exception as e:
            print(f"\n✗ Error calling API: {e}")

if __name__ == "__main__":
    print("Starting Player Props Tests...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run the service test
    asyncio.run(test_player_props_endpoint())
    
    # Run the API test
    # asyncio.run(test_api_endpoint_directly())
