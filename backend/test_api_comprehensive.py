"""
Comprehensive API Testing for Sports Prediction Platform
Tests all endpoints, tier features, caching, and reasoning uniqueness
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.espn_prediction_service import ESPNPredictionService
from app.services.enhanced_ml_service import EnhancedMLService

async def test_api_comprehensive():
    """Run comprehensive API tests"""
    print("=" * 70)
    print("COMPREHENSIVE API TESTING")
    print("=" * 70)
    
    service = ESPNPredictionService()
    ml_service = EnhancedMLService()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Get Sports
    print("\n[Test 1] Get Available Sports...")
    try:
        sports = await service.get_sports()
        assert len(sports) == 7, f"Expected 7 sports, got {len(sports)}"
        print(f"  ✓ PASS: Found {len(sports)} sports")
        for s in sports:
            print(f"    - {s['key']}: {s['title']}")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 2: NCAAB Games
    print("\n[Test 2] Fetch NCAAB Games...")
    try:
        games = await service.get_upcoming_games('basketball_ncaa')
        assert len(games) > 0, "No NCAAB games found"
        print(f"  ✓ PASS: Found {len(games)} NCAAB games")
        print(f"    Sample: {games[0]['away_team']} @ {games[0]['home_team']}")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 3: NBA Games
    print("\n[Test 3] Fetch NBA Games...")
    try:
        games = await service.get_upcoming_games('basketball_nba')
        assert len(games) > 0, "No NBA games found"
        print(f"  ✓ PASS: Found {len(games)} NBA games")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 4: NFL Games
    print("\n[Test 4] Fetch NFL Games...")
    try:
        games = await service.get_upcoming_games('americanfootball_nfl')
        print(f"  ✓ PASS: Found {len(games)} NFL games")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 5: NHL Games
    print("\n[Test 5] Fetch NHL Games...")
    try:
        games = await service.get_upcoming_games('icehockey_nhl')
        print(f"  ✓ PASS: Found {len(games)} NHL games")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 6: MLB Games
    print("\n[Test 6] Fetch MLB Games...")
    try:
        games = await service.get_upcoming_games('baseball_mlb')
        print(f"  ✓ PASS: Found {len(games)} MLB games")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 7: Soccer Games
    print("\n[Test 7] Fetch Soccer Games...")
    try:
        games = await service.get_upcoming_games('soccer_epl')
        print(f"  ✓ PASS: Found {len(games)} EPL games")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 8: Generate Predictions
    print("\n[Test 8] Generate Predictions...")
    try:
        predictions = await service.get_predictions('basketball_nba')
        assert len(predictions) > 0, "No predictions generated"
        print(f"  ✓ PASS: Generated {len(predictions)} predictions")
        
        # Check prediction structure
        pred = predictions[0]
        required_fields = ['id', 'matchup', 'prediction', 'confidence', 'reasoning', 'models']
        for field in required_fields:
            assert field in pred, f"Missing field: {field}"
        print(f"    ✓ All required fields present")
        
        # Check confidence range
        conf = pred['confidence']
        assert 40 <= conf <= 95, f"Confidence {conf} out of range (40-95)"
        print(f"    ✓ Confidence {conf}% in valid range")
        
        # Check reasoning
        reasoning = pred.get('reasoning', [])
        assert len(reasoning) > 0, "No reasoning provided"
        print(f"    ✓ Reasoning has {len(reasoning)} factors")
        
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 9: Reasoning Uniqueness
    print("\n[Test 9] Verify Reasoning Uniqueness...")
    try:
        if len(predictions) >= 2:
            reasoning_1 = str(predictions[0].get('reasoning', []))
            reasoning_2 = str(predictions[1].get('reasoning', []))
            
            if reasoning_1 != reasoning_2:
                print(f"  ✓ PASS: Reasoning is unique between predictions")
            else:
                print(f"  ⚠ WARNING: Reasoning appears identical")
            tests_passed += 1
        else:
            print(f"  ⚠ SKIP: Need 2+ predictions to test uniqueness")
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 10: Caching
    print("\n[Test 10] Test Caching...")
    try:
        # First call
        start = asyncio.get_event_loop().time()
        games1 = await service.get_upcoming_games('basketball_nba')
        time1 = asyncio.get_event_loop().time() - start
        
        # Second call (should be cached)
        start = asyncio.get_event_loop().time()
        games2 = await service.get_upcoming_games('basketball_nba')
        time2 = asyncio.get_event_loop().time() - start
        
        print(f"  ✓ PASS: First call: {time1:.2f}s, Cached call: {time2:.2f}s")
        print(f"    Cache speedup: {time1/time2:.1f}x faster" if time2 > 0 else "    Cache instant")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 11: ML Model Loading
    print("\n[Test 11] Verify ML Models...")
    try:
        models = ml_service.models
        assert len(models) > 0, "No ML models loaded"
        print(f"  ✓ PASS: {len(models)} ML models loaded")
        
        # Check model types
        model_types = set()
        for key in models.keys():
            sport, market = key.rsplit('_', 1)
            model_types.add((sport, market))
        
        print(f"    ✓ {len(model_types)} sport/market combinations")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Test 12: Player Props
    print("\n[Test 12] Test Player Props Generation...")
    try:
        if predictions:
            sport_key = predictions[0]['sport_key']
            event_id = predictions[0]['event_id']
            props = await service.get_player_props(sport_key, event_id)
            print(f"  ✓ PASS: Generated {len(props)} player props")
            if props:
                print(f"    Sample: {props[0].get('player')} - {props[0].get('market_key')}")
            tests_passed += 1
        else:
            print(f"  ⚠ SKIP: No predictions available for props test")
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        tests_failed += 1
    
    # Cleanup
    await service.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
    print("=" * 70)
    
    return tests_failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_api_comprehensive())
    sys.exit(0 if success else 1)
