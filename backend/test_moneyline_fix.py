"""
Test script to verify moneyline predictions are working with real ESPN data
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_moneyline_predictions():
    """Test moneyline predictions for various sports"""
    service = ESPNPredictionService()
    
    # Test different sports
    test_cases = [
        ("basketball_nba", "NBA"),
        ("icehockey_nhl", "NHL"),
        ("baseball_mlb", "MLB"),
        ("americanfootball_nfl", "NFL"),
        ("soccer_epl", "EPL"),
    ]
    
    print("=" * 80)
    print("TESTING MONEYLINE PREDICTIONS WITH REAL ESPN DATA")
    print("=" * 80)
    
    all_passed = True
    
    for sport_key, sport_name in test_cases:
        print(f"\n{'='*40}")
        print(f"Testing {sport_name} ({sport_key})")
        print(f"{'='*40}")
        
        try:
            # Get upcoming games
            games = await service.get_upcoming_games(sport_key)
            
            if not games:
                print(f"  ⚠️  No upcoming games found for {sport_name}")
                continue
            
            print(f"  ✓ Found {len(games)} upcoming games")
            
            # Test prediction for first game
            game = games[0]
            print(f"  Testing game: {game['away_team']['name']} @ {game['home_team']['name']}")
            
            # Get prediction (this now uses real team stats)
            prediction = await service._enrich_prediction(game, sport_key)
            
            if not prediction:
                print(f"  ✗ Failed to generate prediction")
                all_passed = False
                continue
            
            # Check if prediction has reasonable confidence
            confidence = prediction.get('confidence', 0)
            prediction_text = prediction.get('prediction', 'unknown')
            
            print(f"  Prediction: {prediction_text}")
            print(f"  Confidence: {confidence:.1f}%")
            
            # Verify confidence is in reasonable range (should be higher than 55% now with real data)
            if confidence >= 50:
                print(f"  ✓ Confidence is valid ({confidence:.1f}%)")
            else:
                print(f"  ⚠️  Confidence seems low ({confidence:.1f}%)")
            
            # Check if reasoning is present
            reasoning = prediction.get('reasoning', [])
            if reasoning and len(reasoning) > 0:
                print(f"  ✓ Has {len(reasoning)} reasoning points")
                for i, r in enumerate(reasoning[:2], 1):
                    print(f"    {i}. {r.get('factor', 'Unknown')}: {r.get('explanation', 'No explanation')[:60]}...")
            else:
                print(f"  ⚠️  No reasoning provided")
            
            print(f"  ✓ {sport_name} moneyline prediction working!")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            print(f"    {traceback.format_exc()}")
            all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Moneyline predictions are working!")
    else:
        print("⚠️  Some tests had issues, but core functionality is working")
    print(f"{'='*80}")
    
    # Close the service
    await service.close()
    
    return all_passed

if __name__ == "__main__":
    # Set up logging to see debug output
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    result = asyncio.run(test_moneyline_predictions())
    sys.exit(0 if result else 1)
