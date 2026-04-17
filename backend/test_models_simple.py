#!/usr/bin/env python3
"""
Simple test to verify ML models are working without Unicode characters
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.enhanced_ml_service import EnhancedMLService

async def test_models():
    """Test that models load and can make predictions"""
    print("=" * 60)
    print("TESTING ML MODELS")
    print("=" * 60)
    
    # Initialize service (this loads all models)
    ml_service = EnhancedMLService()
    
    print(f"\nLoaded {len(ml_service.models)} model sets:")
    for key in sorted(ml_service.models.keys()):
        print(f"  - {key}")
    
    # Test prediction for NBA
    print("\n" + "=" * 60)
    print("TESTING NBA PREDICTION")
    print("=" * 60)
    
    test_game = {
        "event_id": "test_nba_001",
        "home_team": "Lakers",
        "away_team": "Warriors",
        "home_wins": 45,
        "home_losses": 20,
        "away_wins": 40,
        "away_losses": 25,
        "home_recent_wins": 4,
        "away_recent_wins": 3,
        "home_form": 0.8,
        "away_form": 0.6,
        "home_sos": 0.52,
        "away_sos": 0.48,
        "rest_days_diff": 1
    }
    
    try:
        result = await ml_service.predict("basketball_nba", "spread", test_game)
        print(f"Prediction: {result.get('prediction')}")
        print(f"Confidence: {result.get('confidence', 0):.1f}%")
        print(f"Status: {result.get('status')}")
        if result.get('status') == 'success':
            print("NBA SPREAD: WORKING")
        else:
            print(f"NBA SPREAD: FAILED - {result.get('message')}")
    except Exception as e:
        print(f"NBA SPREAD: ERROR - {e}")
    
    # Test prediction for NFL
    print("\n" + "=" * 60)
    print("TESTING NFL PREDICTION")
    print("=" * 60)
    
    test_game_nfl = {
        "event_id": "test_nfl_001",
        "home_team": "Chiefs",
        "away_team": "Ravens",
        "home_wins": 12,
        "home_losses": 4,
        "away_wins": 11,
        "away_losses": 5,
        "home_recent_wins": 4,
        "away_recent_wins": 3,
        "home_form": 0.8,
        "away_form": 0.6,
        "home_sos": 0.55,
        "away_sos": 0.50,
        "rest_days_diff": 2
    }
    
    try:
        result = await ml_service.predict("americanfootball_nfl", "moneyline", test_game_nfl)
        print(f"Prediction: {result.get('prediction')}")
        print(f"Confidence: {result.get('confidence', 0):.1f}%")
        print(f"Status: {result.get('status')}")
        if result.get('status') == 'success':
            print("NFL MONEYLINE: WORKING")
        else:
            print(f"NFL MONEYLINE: FAILED - {result.get('message')}")
    except Exception as e:
        print(f"NFL MONEYLINE: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_models())
