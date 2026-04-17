#!/usr/bin/env python3
"""
Test Real ML Predictions for NCAAB
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.espn_prediction_service import ESPNPredictionService

async def test_real_ml():
    print("=" * 60)
    print("TESTING REAL ML PREDICTIONS FOR NCAAB")
    print("=" * 60)
    
    ml_service = EnhancedMLService()
    espn_service = ESPNPredictionService()
    
    # Test loading NCAAB models
    print("\n1. Testing model loading...")
    for market in ['moneyline', 'spread', 'total']:
        model_key = f'basketball_ncaa_{market}'
        if model_key in ml_service.models:
            print(f"   ✓ {market}: Loaded successfully")
        else:
            print(f"   ✗ {market}: NOT loaded")
    
    # Get a sample NCAAB game
    print("\n2. Fetching NCAAB games...")
    games = await espn_service.get_upcoming_games('basketball_ncaa')
    if games:
        game = games[0]
        print(f"   ✓ Found game: {game['away_team']} @ {game['home_team']}")
        
        # Get team stats
        print("\n3. Fetching team stats...")
        home_stats = await espn_service.get_team_stats('basketball_ncaa', game['home_team_id'])
        away_stats = await espn_service.get_team_stats('basketball_ncaa', game['away_team_id'])
        print(f"   Home stats: {len(home_stats)} metrics")
        print(f"   Away stats: {len(away_stats)} metrics")
        
        # Test ML prediction
        print("\n4. Testing ML prediction...")
        game_data = {
            'home_team_id': game['home_team_id'],
            'away_team_id': game['away_team_id'],
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'home_record': game.get('home_record', '10-5'),
            'away_record': game.get('away_record', '8-7'),
            'home_stats': home_stats,
            'away_stats': away_stats
        }
        
        result = await ml_service.predict('basketball_ncaa', 'moneyline', game_data)
        print(f"   Prediction: {result['prediction']}")
        print(f"   Confidence: {result['confidence']}%")
        print(f"   Source: {result.get('source', 'unknown')}")
        if result.get('reasoning'):
            print(f"   Reasoning: {len(result['reasoning'])} factors")
            for r in result['reasoning'][:3]:
                print(f"      - {r['factor']}: {r['explanation']}")
    else:
        print("   ✗ No games found")
    
    await espn_service.close()
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_real_ml())
