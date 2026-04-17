"""Quick test for fixes"""
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService

async def quick_test():
    service = ESPNPredictionService()
    
    # Quick test - just NBA
    sport = 'basketball_nba'
    games = await service.get_upcoming_games(sport)
    
    if games:
        game = games[0]
        print(f"Game: {game['home_team']['name']} vs {game['away_team']['name']}")
        
        # Test game time
        gt = service._format_game_time(game.get('date', ''))
        print(f"Game time: {gt[0]} (status: {gt[1]})")
        
        # Test player props
        props = await service.get_player_props(sport, game['id'])
        print(f"Player props: {len(props)}")
        
        if props:
            print(f"Sample prop game_time: {props[0].get('game_time')}")
            print(f"Sample prop confidence: {props[0].get('confidence')}%")
        
        # Test confidence with 0-0
        conf = service._calculate_team_based_confidence(None, None, 0, 0, 0, 0, 0.5, 0.5)
        print(f"Confidence (0-0): {conf}%")
        
        # Test team stats
        stats = await service._fetch_team_stats(str(game['home_team']['id']), sport)
        wins, losses = service._extract_record_from_stats(stats)
        print(f"Team record: {wins}-{losses}")
    
    await service.close()

if __name__ == '__main__':
    asyncio.run(quick_test())
