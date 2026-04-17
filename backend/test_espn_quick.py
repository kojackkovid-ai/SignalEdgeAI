#!/usr/bin/env python3
"""
Quick test to verify ESPN predictions are working
"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_espn_predictions():
    service = ESPNPredictionService()
    
    print("Testing ESPN predictions...")
    print("=" * 50)
    
    # Test getting upcoming games for NBA
    print("\n1. Testing get_upcoming_games for basketball_nba...")
    try:
        games = await service.get_upcoming_games("basketball_nba")
        print(f"   Found {len(games)} games")
        if games:
            print(f"   First game: {games[0].get('away_team')} @ {games[0].get('home_team')}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test getting predictions
    print("\n2. Testing get_predictions...")
    try:
        predictions = await service.get_predictions(sport="basketball_nba", limit=5)
        print(f"   Generated {len(predictions)} predictions")
        if predictions:
            for i, pred in enumerate(predictions[:3]):
                print(f"   {i+1}. {pred.get('matchup')} -> {pred.get('prediction')} ({pred.get('confidence')}%)")
        else:
            print("   WARNING: No predictions generated!")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    await service.close()
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_espn_predictions())
