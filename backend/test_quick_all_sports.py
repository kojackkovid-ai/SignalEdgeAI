"""Quick test to verify all sports player props are working."""
import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_all_sports():
    """Test player props for all sports."""
    service = ESPNPredictionService()
    
    sports = ['basketball_nba', 'icehockey_nhl', 'baseball_mlb', 'soccer_epl', 'soccer_usa_mls']
    
    results = {}
    
    for sport in sports:
        print(f"\nTesting {sport}...")
        try:
            games = await service.get_upcoming_games(sport)
            print(f"  Games: {len(games)}")
            
            if not games:
                results[sport] = "No games"
                continue
            
            game_id = games[0].get('id')
            props = await service.get_player_props(sport, game_id)
            print(f"  Props: {len(props)}")
            
            if props:
                sample = props[0]
                print(f"  Sample: {sample.get('player', 'N/A')} - {sample.get('prediction', 'N/A')}")
                results[sport] = f"OK ({len(props)} props)"
            else:
                results[sport] = "No props generated"
        except Exception as e:
            print(f"  Error: {e}")
            results[sport] = f"Error: {e}"
    
    await service.close()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for sport, status in results.items():
        print(f"  {sport}: {status}")
    
    return all("OK" in str(v) for v in results.values())

if __name__ == "__main__":
    success = asyncio.run(test_all_sports())
    sys.exit(0 if success else 1)
