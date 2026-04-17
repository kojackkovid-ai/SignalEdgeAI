"""Comprehensive test for all sports fixes"""
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService

async def test_all_sports():
    service = ESPNPredictionService()
    
    sports = [
        'basketball_nba',
        'icehockey_nhl', 
        'baseball_mlb',
        'americanfootball_nfl',
        'soccer_epl'
    ]
    
    results = {'game_time': [], 'player_props': [], 'confidence': [], 'records': []}
    
    for sport in sports:
        print(f'\n=== Testing {sport} ===')
        
        # Test upcoming games
        games = await service.get_upcoming_games(sport)
        print(f'Found {len(games)} games')
        
        if games:
            game = games[0]
            
            # Test game time
            game_time = service._format_game_time(game.get('date', ''))
            print(f'Game time: {game_time[0]} (status: {game_time[1]})')
            results['game_time'].append({'sport': sport, 'time': game_time[0]})
            
            # Test confidence calculation with 0-0 records
            conf = service._calculate_team_based_confidence(None, None, 0, 0, 0, 0, 0.5, 0.5)
            print(f'Confidence (0-0 records): {conf}%')
            results['confidence'].append({'sport': sport, 'confidence': conf})
            
            # Test player props
            props = await service.get_player_props(sport, game['id'])
            print(f'Player props: {len(props)} props found')
            
            if props:
                sample_prop = props[0]
                print(f'  Sample prop game_time: {sample_prop.get("game_time", "MISSING")}')
                print(f'  Sample prop confidence: {sample_prop.get("confidence")}%')
                results['player_props'].append({'sport': sport, 'count': len(props), 'game_time': sample_prop.get('game_time')})
            else:
                results['player_props'].append({'sport': sport, 'count': 0, 'game_time': None})
            
            # Test team stats for records
            team_id = game['home_team']['id']
            stats = await service._fetch_team_stats(str(team_id), sport)
            wins, losses = service._extract_record_from_stats(stats)
            print(f'Team record from API: {wins}-{losses}')
            results['records'].append({'sport': sport, 'wins': wins, 'losses': losses})
        else:
            print('No games found')
            results['game_time'].append({'sport': sport, 'time': 'NO GAMES'})
            results['confidence'].append({'sport': sport, 'confidence': 0})
            results['player_props'].append({'sport': sport, 'count': 0, 'game_time': None})
            results['records'].append({'sport': sport, 'wins': 0, 'losses': 0})
    
    await service.close()
    
    print('\n' + '='*60)
    print('SUMMARY')
    print('='*60)
    
    print('\nGame Times:')
    for r in results['game_time']:
        print(f'  {r["sport"]}: {r["time"]}')
    
    print('\nPlayer Props:')
    for r in results['player_props']:
        print(f'  {r["sport"]}: {r["count"]} props, game_time={r["game_time"]}')
    
    print('\nConfidence (0-0 records):')
    for r in results['confidence']:
        print(f'  {r["sport"]}: {r["confidence"]}%')
    
    print('\nTeam Records from API:')
    for r in results['records']:
        print(f'  {r["sport"]}: {r["wins"]}-{r["losses"]}')

if __name__ == '__main__':
    asyncio.run(test_all_sports())
