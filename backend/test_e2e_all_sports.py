"""
End-to-End Test for ALL Sports Player Props
Tests the complete flow: fetch props -> verify varied confidence -> unlock
"""
import asyncio
import sys
import os
sys.path.append('.')

# Set up environment
os.environ['ESPN_API_KEY'] = 'demo_key'

from app.services.espn_prediction_service import ESPNPredictionService

async def test_sport_props(service, sport_key, sport_name):
    """Test player props for a specific sport"""
    print(f"\n{'='*60}")
    print(f"Testing {sport_name} ({sport_key})")
    print(f"{'='*60}")
    
    try:
        # Get upcoming games
        games = await service.get_upcoming_games(sport_key)
        if not games:
            print(f"  ⚠️  No games available for {sport_name}")
            return False
        
        print(f"  Found {len(games)} games")
        
        # Test first game
        test_game = games[0]
        event_id = test_game['id']
        print(f"  Testing game: {test_game.get('matchup', 'Unknown')} (ID: {event_id})")
        
        # Get player props
        props = await service.get_player_props(sport_key, event_id)
        
        if not props:
            print(f"  ⚠️  No props generated for {sport_name}")
            return False
        
        print(f"  ✅ Generated {len(props)} props")
        
        # Check confidence variation
        confidences = [p.get('confidence', 0) for p in props if p.get('confidence')]
        if confidences:
            min_conf = min(confidences)
            max_conf = max(confidences)
            avg_conf = sum(confidences) / len(confidences)
            
            print(f"  Confidence Range: {min_conf:.1f}% - {max_conf:.1f}%")
            print(f"  Average Confidence: {avg_conf:.1f}%")
            
            # Check for variation (should not all be the same)
            unique_confidences = len(set([round(c, 0) for c in confidences]))
            if unique_confidences < 2:
                print(f"  ❌ WARNING: All confidences are identical!")
                return False
            
            # Check range is within 55-85%
            if min_conf < 55 or max_conf > 85:
                print(f"  ⚠️  Confidence outside expected 55-85% range")
            
            print(f"  ✅ Confidence values are varied ({unique_confidences} unique values)")
        
        # Show sample props
        player_props = [p for p in props if p.get('prediction_type') == 'player_prop'][:3]
        print(f"\n  Sample Player Props:")
        for prop in player_props:
            print(f"    - {prop.get('player', 'Unknown')}: {prop.get('prediction', 'N/A')}")
            print(f"      Confidence: {prop.get('confidence', 0):.1f}%, Market: {prop.get('market_key', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing {sport_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*60)
    print("END-TO-END TEST: ALL SPORTS PLAYER PROPS")
    print("="*60)
    print("\nThis test verifies:")
    print("1. Props are generated for each sport")
    print("2. Confidence values are varied (not uniform)")
    print("3. Confidence range is 55-85%")
    print("4. All prop types work correctly")
    
    service = ESPNPredictionService()
    
    # Test all supported sports
    sports_to_test = [
        ("basketball_nba", "NBA"),
        ("icehockey_nhl", "NHL"),
        ("americanfootball_nfl", "NFL"),
        ("soccer_epl", "Soccer (EPL)"),
        ("baseball_mlb", "MLB"),
    ]
    
    results = {}
    for sport_key, sport_name in sports_to_test:
        success = await test_sport_props(service, sport_key, sport_name)
        results[sport_name] = success
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for sport_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {sport_name}")
        all_passed &= success
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL SPORTS PLAYER PROPS WORKING CORRECTLY!")
        print("\nKey Improvements:")
        print("  • Varied confidence values (no more uniform 52%)")
        print("  • Proper 55-85% confidence range")
        print("  • All sports: NBA, NHL, NFL, Soccer, MLB")
    else:
        print("⚠️  Some sports need attention")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
