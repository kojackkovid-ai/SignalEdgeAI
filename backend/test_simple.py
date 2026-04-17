#!/usr/bin/env python3
"""
Simple test to verify predictions without Redis dependency
"""
import asyncio
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def test_predictions():
    """Test prediction generation"""
    from app.services.espn_prediction_service import ESPNPredictionService
    
    # Create service without Redis
    service = ESPNPredictionService()
    # Disable Redis to avoid connection issues
    service._redis = None
    
    try:
        print("\n" + "="*60)
        print("TEST: Get Available Sports")
        print("="*60)
        sports = await service.get_sports()
        print(f"✓ Found {len(sports)} sports")
        for sport in sports:
            print(f"  - {sport['key']}: {sport['title']}")
        
        # Check NCAAB is present
        ncaa_sport = next((s for s in sports if s['key'] == 'basketball_ncaa'), None)
        if ncaa_sport:
            print(f"\n✓ NCAAB sport found: {ncaa_sport['title']}")
        else:
            print("\n✗ NCAAB sport NOT found!")
            return False
        
        print("\n" + "="*60)
        print("TEST: Fetch NBA Games")
        print("="*60)
        nba_games = await service.get_upcoming_games('basketball_nba')
        print(f"✓ Found {len(nba_games)} NBA games")
        if nba_games:
            print(f"  Sample: {nba_games[0]['away_team']} @ {nba_games[0]['home_team']}")
            print(f"  Home record: {nba_games[0].get('home_record', 'N/A')}")
            print(f"  Away record: {nba_games[0].get('away_record', 'N/A')}")
        
        print("\n" + "="*60)
        print("TEST: Fetch NCAAB Games")
        print("="*60)
        ncaa_games = await service.get_upcoming_games('basketball_ncaa')
        print(f"✓ Found {len(ncaa_games)} NCAAB games")
        if ncaa_games:
            print(f"  Sample: {ncaa_games[0]['away_team']} @ {ncaa_games[0]['home_team']}")
            print(f"  Home record: {ncaa_games[0].get('home_record', 'N/A')}")
            print(f"  Away record: {ncaa_games[0].get('away_record', 'N/A')}")
        
        print("\n" + "="*60)
        print("TEST: Generate Predictions")
        print("="*60)
        predictions = await service.get_predictions()
        print(f"✓ Generated {len(predictions)} total predictions")
        
        if not predictions:
            print("✗ NO PREDICTIONS GENERATED - THIS IS THE BUG!")
            return False
        
        # Breakdown by sport
        by_sport = {}
        for p in predictions:
            sport = p.get('sport', 'Unknown')
            by_sport[sport] = by_sport.get(sport, 0) + 1
        
        print(f"\nPredictions by sport:")
        for sport, count in sorted(by_sport.items()):
            print(f"  - {sport}: {count}")
        
        # Check NCAAB predictions
        ncaa_preds = [p for p in predictions if p.get('sport') == 'NCAAB']
        print(f"\n✓ NCAAB predictions: {len(ncaa_preds)}")
        
        # Show sample prediction with reasoning
        if predictions:
            first = predictions[0]
            print(f"\nSample prediction:")
            print(f"  ID: {first.get('id')}")
            print(f"  Sport: {first.get('sport')}")
            print(f"  League: {first.get('league')}")
            print(f"  Matchup: {first.get('matchup')}")
            print(f"  Prediction: {first.get('prediction')}")
            print(f"  Confidence: {first.get('confidence')}%")
            print(f"  Type: {first.get('prediction_type')}")
            
            # Check reasoning
            reasoning = first.get('reasoning', [])
            print(f"\n  Reasoning ({len(reasoning)} factors):")
            for i, r in enumerate(reasoning[:3], 1):
                print(f"    {i}. {r.get('factor')}: {r.get('explanation')[:80]}...")
            
            # Check models
            models = first.get('models', [])
            print(f"\n  Models ({len(models)} models):")
            for m in models:
                print(f"    - {m.get('name')}: {m.get('confidence')}%")
            
            # Check if it has all required fields
            required = ['id', 'sport', 'league', 'matchup', 'prediction', 'confidence', 'reasoning']
            missing = [f for f in required if not first.get(f)]
            if missing:
                print(f"\n  ✗ Missing fields: {missing}")
            else:
                print(f"\n  ✓ All required fields present")
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()

if __name__ == "__main__":
    success = asyncio.run(test_predictions())
    sys.exit(0 if success else 1)
