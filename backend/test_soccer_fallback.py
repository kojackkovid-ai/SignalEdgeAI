#!/usr/bin/env python3
"""Test soccer props with fallback roster extraction."""

import asyncio
import sys
sys.path.insert(0, '/c/Users/bigba/Desktop/New\ folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_soccer_props():
    """Test that soccer props work with fallback."""
    service = ESPNPredictionService()
    
    # Test with a real soccer game
    sport_key = "soccer_usa_mls"
    
    # Get upcoming games first
    print("Getting upcoming soccer games...")
    games = await service.get_upcoming_games(sport_key)
    
    if not games:
        print("❌ No upcoming games found")
        return False
    
    print(f"✓ Found {len(games)} upcoming games")
    
    # Get props for first game
    game = games[0]
    event_id = str(game.get('id', ''))
    
    print(f"\nTesting props for game: {game.get('name', 'N/A')}")
    print(f"Event ID: {event_id}")
    
    try:
        props = await service.get_player_props(sport_key, event_id)
        
        if props:
            print(f"\n✅ SUCCESS: Got {len(props)} props!")
            
            # Check first prop
            first = props[0]
            print(f"\nFirst prop sample:")
            print(f"  Player: {first.get('player', 'N/A')}")
            print(f"  Market: {first.get('market_key', 'N/A')}")
            print(f"  Prediction: {first.get('prediction', 'N/A')}")
            print(f"  Confidence: {first.get('confidence', 'N/A')}")
            print(f"  Season Avg: {first.get('season_avg', 'N/A')}")
            print(f"  Recent 10: {first.get('recent_10_avg', 'N/A')}")
            
            # Count by type
            goals = [p for p in props if p.get('market_key') == 'goals']
            assists = [p for p in props if p.get('market_key') == 'assists']
            
            print(f"\nProp breakdown:")
            print(f"  Goals: {len(goals)}")
            print(f"  Assists: {len(assists)}")
            
            return len(props) > 0
        else:
            print(f"❌ No props returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_soccer_props())
    print(f"\n{'='*60}")
    print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    sys.exit(0 if result else 1)
