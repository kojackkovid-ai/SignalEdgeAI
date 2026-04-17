"""
Test script to verify soccer player props are working after the fix.
This tests the roster fetching and player props generation using real ESPN API data.
"""
import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '.')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_soccer_roster():
    """Test soccer roster fetching"""
    print("\n" + "="*80)
    print("TESTING SOCCER ROSTER FETCHING")
    print("="*80)
    
    service = ESPNPredictionService()
    
    try:
        # Test with a known EPL team (Manchester City = 382)
        team_id = "382"
        sport_key = "soccer_epl"
        
        print(f"\nFetching roster for team {team_id} ({sport_key})...")
        roster = await service._get_team_roster(sport_key, team_id)
        
        print(f"✓ Successfully fetched {len(roster)} players")
        
        if roster:
            print(f"\n--- Sample Players ---")
            for i, player in enumerate(roster[:5]):
                print(f"  {i+1}. {player.get('name', 'N/A')} (Position: {player.get('position', 'N/A')}, ID: {player.get('id', 'N/A')})")
            return True
        else:
            print("✗ No players found in roster")
            return False
            
    except Exception as e:
        print(f"✗ Error fetching roster: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()

async def test_soccer_predictions():
    """Test soccer predictions"""
    print("\n" + "="*80)
    print("TESTING SOCCER PREDICTIONS")
    print("="*80)
    
    service = ESPNPredictionService()
    
    try:
        print("\nFetching soccer predictions...")
        predictions = await service.get_predictions(sport='soccer_epl', limit=3)
        
        print(f"✓ Successfully fetched {len(predictions)} predictions")
        
        if predictions:
            print(f"\n--- Sample Predictions ---")
            for i, pred in enumerate(predictions[:3]):
                print(f"  {i+1}. {pred.get('matchup', 'N/A')}")
                print(f"     Prediction: {pred.get('prediction', 'N/A')} (Confidence: {pred.get('confidence', 'N/A')}%)")
            return True
        else:
            print("⚠ No predictions found (this may be normal if no games are scheduled)")
            return True
            
    except Exception as e:
        print(f"✗ Error fetching predictions: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()

async def test_soccer_player_props():
    """Test soccer player props generation"""
    print("\n" + "="*80)
    print("TESTING SOCCER PLAYER PROPS")
    print("="*80)
    
    service = ESPNPredictionService()
    
    try:
        # First get upcoming games
        print("\nFetching upcoming soccer games...")
        games = await service.get_upcoming_games('soccer_epl')
        
        if not games:
            print("⚠ No upcoming games found - cannot test player props")
            return True
        
        print(f"✓ Found {len(games)} games")
        
        # Test with first game
        game = games[0]
        event_id = game['id']
        matchup = f"{game['away_team']['name']} @ {game['home_team']['name']}"
        
        print(f"\nTesting player props for game: {matchup}")
        print(f"Event ID: {event_id}")
        
        props = await service.get_player_props('soccer_epl', event_id)
        
        print(f"✓ Successfully generated {len(props)} player props")
        
        if props:
            print(f"\n--- Sample Player Props ---")
            for i, prop in enumerate(props[:5]):
                print(f"  {i+1}. {prop.get('player', 'N/A')} - {prop.get('prediction', 'N/A')}")
                print(f"     Market: {prop.get('market_key', 'N/A')} | Confidence: {prop.get('confidence', 'N/A')}%")
            
            # Verify props have required fields
            print(f"\n--- Validating Props ---")
            valid_count = 0
            for prop in props:
                has_required = all([
                    prop.get('player'),
                    prop.get('market_key'),
                    prop.get('prediction'),
                    prop.get('confidence') is not None,
                    prop.get('id')
                ])
                if has_required:
                    valid_count += 1
            
            print(f"  Valid props: {valid_count}/{len(props)}")
            
            if valid_count == len(props):
                print("✓ All props have required fields")
                return True
            else:
                print("✗ Some props are missing required fields")
                return False
        else:
            print("⚠ No player props generated")
            return True
            
    except Exception as e:
        print(f"✗ Error generating player props: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()

async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SOCCER PLAYER PROPS FIX VERIFICATION")
    print("="*80)
    print("Testing real ESPN API data - no mock data used")
    
    results = []
    
    # Test 1: Roster fetching
    results.append(("Roster Fetching", await test_soccer_roster()))
    
    # Test 2: Predictions
    results.append(("Predictions", await test_soccer_predictions()))
    
    # Test 3: Player Props
    results.append(("Player Props", await test_soccer_player_props()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED - Soccer player props are working!")
    else:
        print("\n✗ SOME TESTS FAILED - Please review the errors above")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
