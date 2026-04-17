"""
Final comprehensive test for all sports player props
Tests real ESPN API data for NBA, NHL, MLB, NFL, and Soccer
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_all_sports():
    service = ESPNPredictionService()
    
    sports_to_test = [
        ('basketball_nba', 'NBA'),
        ('icehockey_nhl', 'NHL'),
        ('baseball_mlb', 'MLB'),
        ('americanfootball_nfl', 'NFL'),
        ('soccer_epl', 'Soccer (EPL)'),
        ('soccer_usa_mls', 'Soccer (MLS)')
    ]
    
    results = {}
    
    for sport_key, sport_name in sports_to_test:
        print(f"\n{'='*60}")
        print(f"Testing {sport_name} ({sport_key})")
        print('='*60)
        
        try:
            # Get upcoming games
            games = await service.get_upcoming_games(sport_key)
            print(f"✓ Found {len(games)} upcoming games")
            
            if not games:
                results[sport_key] = {'status': 'NO_GAMES', 'props_count': 0}
                continue
            
            # Test first game
            game = games[0]
            game_id = game.get('id')
            matchup = f"{game['away_team']['name']} @ {game['home_team']['name']}"
            print(f"✓ Testing game: {matchup} (ID: {game_id})")
            
            # Get player props
            props = await service.get_player_props(sport_key, game_id)
            print(f"✓ Generated {len(props)} player props")
            
            if props:
                # Check for real player names (not "Unknown")
                real_names = [p for p in props if p.get('player') and p.get('player') != 'Unknown']
                unknown_names = [p for p in props if p.get('player') == 'Unknown']
                
                print(f"  - Props with real player names: {len(real_names)}")
                print(f"  - Props with 'Unknown' names: {len(unknown_names)}")
                
                # Show sample props
                print(f"\n  Sample props:")
                for i, prop in enumerate(props[:3]):
                    player = prop.get('player', 'N/A')
                    prediction = prop.get('prediction', 'N/A')
                    confidence = prop.get('confidence', 0)
                    market = prop.get('market_key', 'N/A')
                    print(f"    {i+1}. {player} - {prediction} ({confidence}%) [{market}]")
                
                results[sport_key] = {
                    'status': 'SUCCESS',
                    'games_count': len(games),
                    'props_count': len(props),
                    'real_names_count': len(real_names),
                    'unknown_names_count': len(unknown_names),
                    'sample_prop': props[0] if props else None
                }
            else:
                results[sport_key] = {
                    'status': 'NO_PROPS',
                    'games_count': len(games),
                    'props_count': 0
                }
                
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results[sport_key] = {'status': 'ERROR', 'error': str(e)}
    
    await service.close()
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    for sport_key, result in results.items():
        status = result.get('status', 'UNKNOWN')
        props_count = result.get('props_count', 0)
        real_names = result.get('real_names_count', 0)
        
        if status == 'SUCCESS':
            print(f"✓ {sport_key}: {props_count} props ({real_names} with real names)")
        elif status == 'NO_GAMES':
            print(f"⚠ {sport_key}: No games available (offseason?)")
        elif status == 'NO_PROPS':
            print(f"⚠ {sport_key}: Games found but no props generated")
        elif status == 'ERROR':
            print(f"✗ {sport_key}: Error - {result.get('error', 'Unknown error')}")
        else:
            print(f"? {sport_key}: Unknown status")
    
    # Overall result
    successful = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
    total = len(sports_to_test)
    
    print(f"\n{'='*60}")
    print(f"RESULT: {successful}/{total} sports working correctly")
    print('='*60)
    
    return results

if __name__ == '__main__':
    results = asyncio.run(test_all_sports())
    
    # Exit with appropriate code
    successful = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
    if successful >= 3:  # At least 3 sports working
        print("\n✓ TEST PASSED - Player props working for multiple sports")
        sys.exit(0)
    else:
        print("\n✗ TEST FAILED - Not enough sports working")
        sys.exit(1)
