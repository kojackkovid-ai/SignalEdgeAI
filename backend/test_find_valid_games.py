"""
Find valid ESPN game IDs for testing player props.
"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def find_valid_games():
    """Find valid games with upcoming events"""
    service = ESPNPredictionService()
    
    print("=" * 80)
    print("FINDING VALID ESPN GAMES FOR TESTING")
    print("=" * 80)
    
    sports = [
        "basketball_nba",
        "icehockey_nhl", 
        "americanfootball_nfl",
        "baseball_mlb",
        "soccer_epl",
        "soccer_usa_mls"
    ]
    
    for sport_key in sports:
        print(f"\n{'='*60}")
        print(f"Sport: {sport_key}")
        print(f"{'='*60}")
        
        try:
            games = await service.get_upcoming_games(sport_key)
            
            if games:
                print(f"Found {len(games)} games")
                print(f"\nFirst 3 games:")
                for i, game in enumerate(games[:3]):
                    print(f"  {i+1}. ID: {game.get('id')}")
                    print(f"     Matchup: {game.get('away_team')} @ {game.get('home_team')}")
                    print(f"     Time: {game.get('game_time_display')}")
                    print(f"     Status: {game.get('status')}")
            else:
                print("No games found")
                
        except Exception as e:
            print(f"Error: {e}")
    
    await service.close()
    print(f"\n{'='*80}")
    print("DONE")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(find_valid_games())
