"""Test the ESPN Player Stats Service"""
import asyncio
from app.services.espn_player_stats_service import ESPNPlayerStatsService

async def test():
    service = ESPNPlayerStatsService()
    
    print('=== Testing NBA Player Stats Service ===')
    games = await service.get_today_games_player_stats('nba')
    print(f'Found {len(games)} games with player stats')
    
    for game in games[:2]:
        print(f"\nGame: {game.get('game', {}).get('name')}")
        
        # Show leaders
        print('Top Performers:')
        for leader in game.get('leaders', [])[:6]:
            athlete = leader.get('athlete', {})
            print(f"  - {athlete.get('fullName')}: {leader.get('display_value')} {leader.get('category')}")
        
        # Generate props
        props = service.generate_player_props_from_leaders(game, 'nba')
        print(f"\nGenerated {len(props)} player props:")
        for prop in props[:5]:
            recent = prop['recent_performance']
            line = prop['line']
            name = prop['player_name']
            cat = prop['category']
            print(f"  - {name}: {cat} O/{line} (recent: {recent})")

asyncio.run(test())
