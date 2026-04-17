"""
Final verification test for player props and predictions
Tests all sports with real ESPN API data
"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_all_sports():
    """Test player props for all sports"""
    service = ESPNPredictionService()
    
    sports_to_test = [
        ("basketball_nba", "NBA"),
        ("icehockey_nhl", "NHL"),
        ("baseball_mlb", "MLB"),
        ("americanfootball_nfl", "NFL"),
        ("soccer_epl", "EPL"),
        ("basketball_ncaa", "NCAAB")
    ]
    
    results = {}
    
    for sport_key, sport_name in sports_to_test:
        print(f"\n{'='*50}")
        print(f"Testing {sport_name} ({sport_key})")
        print(f"{'='*50}")
        
        try:
            # Get upcoming games
            games = await service.get_upcoming_games(sport_key)
            print(f"Found {len(games)} upcoming games")
            
            if not games:
                results[sport_key] = {"status": "NO_GAMES", "games": 0, "props": 0}
                continue
            
            # Test first game
            test_game = games[0]
            event_id = test_game["id"]
            print(f"Testing game: {event_id}")
            print(f"Matchup: {test_game['away_team']['name']} @ {test_game['home_team']['name']}")
            
            # Get player props
            props = await service.get_player_props(sport_key, event_id)
            print(f"Generated {len(props)} player props")
            
            if props:
                # Show first 3 props
                for i, prop in enumerate(props[:3]):
                    print(f"  - {prop.get('player')}: {prop.get('prediction')} ({prop.get('confidence')}%)")
                
                results[sport_key] = {
                    "status": "SUCCESS",
                    "games": len(games),
                    "props": len(props),
                    "sample_prop": props[0]
                }
            else:
                results[sport_key] = {"status": "NO_PROPS", "games": len(games), "props": 0}
                
        except Exception as e:
            print(f"ERROR: {e}")
            results[sport_key] = {"status": "ERROR", "error": str(e)}
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    for sport_key, result in results.items():
        status = result.get("status", "UNKNOWN")
        games = result.get("games", 0)
        props = result.get("props", 0)
        print(f"{sport_key}: {status} - {games} games, {props} props")
    
    # Check if all working
    all_working = all(r.get("status") == "SUCCESS" for r in results.values())
    print(f"\nAll sports working: {all_working}")
    
    await service.close()
    return results

if __name__ == "__main__":
    results = asyncio.run(test_all_sports())
    
    # Exit with appropriate code
    all_success = all(r.get("status") == "SUCCESS" for r in results.values())
    sys.exit(0 if all_success else 1)
