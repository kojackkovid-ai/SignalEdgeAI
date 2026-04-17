"""
Test script to debug MLB player props 404 errors.
Tests fetching current MLB games and their player props.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_current_mlb_games():
    """Test getting current MLB games and their props"""
    print("\n" + "="*80)
    print("TESTING CURRENT MLB GAMES")
    print("="*80)
    
    service = ESPNPredictionService()
    
    # Get current MLB games
    print("\n1. Fetching current MLB games...")
    games = await service.get_upcoming_games('baseball_mlb')
    print(f"   Found {len(games)} MLB games")
    
    if not games:
        print("   ⚠️  No games found - checking why...")
        # Try to understand why no games
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
            today = "20250120"  # Try a specific date
            try:
                resp = await client.get(url, params={"dates": today})
                print(f"   ESPN API status for {today}: {resp.status_code}")
            except Exception as e:
                print(f"   Error: {e}")
        return False
    
    # Test each game's player props
    success_count = 0
    fail_count = 0
    
    for i, game in enumerate(games[:5]):  # Test first 5 games
        game_id = game.get('id', '')
        home_team = game.get('home_team', {}).get('name', 'Unknown')
        away_team = game.get('away_team', {}).get('name', 'Unknown')
        date = game.get('date', '')
        status = game.get('status', '')
        
        print(f"\n2.{i+1} Game: {game_id}")
        print(f"   {away_team} @ {home_team}")
        print(f"   Date: {date}, Status: {status}")
        
        # Try to get player props
        try:
            props = await service.get_player_props('baseball_mlb', game_id)
            
            if props and len(props) > 0:
                print(f"   ✅ SUCCESS: Generated {len(props)} player props")
                # Show sample
                sample = props[0]
                print(f"   Sample: {sample.get('player')} - {sample.get('prediction')}")
                success_count += 1
            else:
                print(f"   ❌ FAILED: No props generated (404 or empty)")
                fail_count += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            fail_count += 1
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total games tested: {len(games[:5])}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    
    return success_count > 0

async def test_invalid_game_id():
    """Test what happens with an invalid game ID"""
    print("\n" + "="*80)
    print("TESTING INVALID GAME ID")
    print("="*80)
    
    service = ESPNPredictionService()
    
    # Try with a clearly invalid ID
    invalid_id = "999999999"
    print(f"\nTesting with invalid ID: {invalid_id}")
    
    try:
        props = await service.get_player_props('baseball_mlb', invalid_id)
        print(f"Result: {len(props)} props returned")
        if props:
            print(f"Sample: {props[0] if props else 'N/A'}")
    except Exception as e:
        print(f"Exception: {e}")

async def main():
    """Run all tests"""
    results = {
        "current_games": await test_current_mlb_games(),
        "invalid_id": await test_invalid_game_id(),
    }
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    return 0 if results.get("current_games", False) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
