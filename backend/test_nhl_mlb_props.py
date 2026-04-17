"""
Test script to verify NHL and MLB player props are working correctly.
Tests the full flow from API call to ESPN data retrieval.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_nhl_props():
    """Test NHL player props generation"""
    print("\n" + "="*80)
    print("TESTING NHL PLAYER PROPS")
    print("="*80)
    
    service = ESPNPredictionService()
    
    # Test with a valid NHL game ID (you may need to update this with a current game)
    # Using a sample game ID - in production this would come from the schedule
    test_games = [
        "401672633",  # Example game ID
        "401672634",  # Another example
    ]
    
    for event_id in test_games:
        print(f"\n--- Testing NHL game {event_id} ---")
        try:
            props = await service.get_player_props("icehockey_nhl", event_id)
            
            if props:
                print(f"✅ SUCCESS: Generated {len(props)} props")
                
                # Categorize props
                player_props = [p for p in props if p.get('prediction_type') == 'player_prop']
                team_props = [p for p in props if p.get('prediction_type') != 'player_prop']
                
                print(f"  - Player Props: {len(player_props)}")
                print(f"  - Team Props: {len(team_props)}")
                
                if player_props:
                    print("\n  Sample Player Props:")
                    for i, prop in enumerate(player_props[:3]):
                        print(f"    {i+1}. {prop.get('player', 'N/A')}: {prop.get('prediction', 'N/A')} "
                              f"(Confidence: {prop.get('confidence', 'N/A')}%)")
                
                return True
            else:
                print(f"⚠️  No props generated for game {event_id}")
                print("   This may be due to off-season or no games scheduled")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    return False

async def test_mlb_props():
    """Test MLB player props generation"""
    print("\n" + "="*80)
    print("TESTING MLB PLAYER PROPS")
    print("="*80)
    
    service = ESPNPredictionService()
    
    # Test with a valid MLB game ID
    test_games = [
        "401672635",  # Example game ID
        "401672636",  # Another example
    ]
    
    for event_id in test_games:
        print(f"\n--- Testing MLB game {event_id} ---")
        try:
            props = await service.get_player_props("baseball_mlb", event_id)
            
            if props:
                print(f"✅ SUCCESS: Generated {len(props)} props")
                
                # Categorize props
                player_props = [p for p in props if p.get('prediction_type') == 'player_prop']
                team_props = [p for p in props if p.get('prediction_type') != 'player_prop']
                
                print(f"  - Player Props: {len(player_props)}")
                print(f"  - Team Props: {len(team_props)}")
                
                if player_props:
                    print("\n  Sample Player Props:")
                    for i, prop in enumerate(player_props[:3]):
                        print(f"    {i+1}. {prop.get('player', 'N/A')}: {prop.get('prediction', 'N/A')} "
                              f"(Confidence: {prop.get('confidence', 'N/A')}%)")
                
                return True
            else:
                print(f"⚠️  No props generated for game {event_id}")
                print("   This may be due to off-season or no games scheduled")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    return False

async def test_player_prop_detection():
    """Test the player prop ID detection function"""
    print("\n" + "="*80)
    print("TESTING PLAYER PROP ID DETECTION")
    print("="*80)
    
    from app.routes.predictions import is_player_prop_id
    
    test_cases = [
        # (prediction_id, expected_result, description)
        ("401672633_home_runs_Aaron_Judge", True, "MLB home runs prop"),
        ("401672633_hits_Mike_Trout", True, "MLB hits prop"),
        ("401672633_rbi_Jose_Altuve", True, "MLB RBI prop"),
        ("401672633_points_LeBron_James", True, "NBA points prop"),
        ("401672633_rebounds_Anthony_Davis", True, "NBA rebounds prop"),
        ("401672633_assists_James_Harden", True, "NBA assists prop"),
        ("401672633_goals_Connor_McDavid", True, "NHL goals prop"),
        ("401672633_assists_Sidney_Crosby", True, "NHL assists prop"),
        ("401672633_pass_yards_Tom_Brady", True, "NFL pass yards prop"),
        ("401672633_rush_yards_Derrick_Henry", True, "NFL rush yards prop"),
        ("401672633_rec_yards_Cooper_Kupp", True, "NFL rec yards prop"),
        ("basketball_nba_401672633", False, "Game prediction ID"),
        ("americanfootball_nfl_401672633", False, "NFL game prediction ID"),
        ("icehockey_nhl_401672633", False, "NHL game prediction ID"),
        ("baseball_mlb_401672633", False, "MLB game prediction ID"),
        ("401672633", False, "Just event ID"),
        ("", False, "Empty string"),
    ]
    
    all_passed = True
    for pred_id, expected, description in test_cases:
        result = is_player_prop_id(pred_id)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result != expected:
            all_passed = False
        print(f"  {status}: {description}")
        print(f"       ID: {pred_id}")
        print(f"       Expected: {expected}, Got: {result}")
        print()
    
    return all_passed

async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("NHL/MLB PLAYER PROPS TEST SUITE")
    print("="*80)
    
    results = {
        "player_prop_detection": await test_player_prop_detection(),
        "nhl_props": await test_nhl_props(),
        "mlb_props": await test_mlb_props(),
    }
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(results.values())
    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
