"""
Test player props with valid ESPN game IDs.
"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_props_with_valid_games():
    """Test player props with valid game IDs"""
    service = ESPNPredictionService()
    
    print("=" * 80)
    print("TESTING PLAYER PROPS WITH VALID GAME IDs")
    print("=" * 80)
    
    # Valid game IDs from the previous search
    test_cases = [
        {
            "sport_key": "basketball_nba",
            "event_id": "401810657",
            "description": "NBA: Cleveland Cavaliers @ Charlotte Hornets"
        },
        {
            "sport_key": "icehockey_nhl", 
            "event_id": "401803261",
            "description": "NHL: Buffalo Sabres @ New Jersey Devils"
        },
        {
            "sport_key": "basketball_nba",
            "event_id": "401810658", 
            "description": "NBA: Indiana Pacers @ Washington Wizards"
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['description']}")
        print(f"Sport: {test['sport_key']}, Event ID: {test['event_id']}")
        print(f"{'='*60}")
        
        try:
            props = await service.get_player_props(test['sport_key'], test['event_id'])
            
            print(f"\n✓ Service call completed")
            print(f"✓ Returned {len(props)} player props")
            
            if props:
                print(f"\n--- Props Breakdown ---")
                player_props = [p for p in props if p.get('prediction_type') == 'player_prop']
                team_props = [p for p in props if p.get('prediction_type') == 'team_prop']
                
                print(f"  Player Props: {len(player_props)}")
                print(f"  Team Props: {len(team_props)}")
                
                if player_props:
                    print(f"\n--- Sample Player Props ---")
                    for i, prop in enumerate(player_props[:5]):
                        print(f"  {i+1}. {prop.get('player', 'N/A')}")
                        print(f"     Market: {prop.get('market_key', 'N/A')}")
                        print(f"     Line: {prop.get('point', 'N/A')}")
                        print(f"     Prediction: {prop.get('prediction', 'N/A')}")
                        print(f"     Confidence: {prop.get('confidence', 'N/A')}%")
                        print()
            else:
                print(f"\n⚠ No props returned - checking why...")
                # The service should return [] only when no real data available
                print(f"  This is expected if ESPN has no player data for this game yet")
                
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    await service.close()
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_props_with_valid_games())
