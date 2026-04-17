import asyncio
import sys
sys.path.append('.')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_ncaab():
    print("Testing NCAAB game fetching...")
    service = ESPNPredictionService()
    try:
        games = await service.get_upcoming_games('basketball_ncaa')
        print(f'✓ Found {len(games)} NCAAB games')
        if games:
            for i, game in enumerate(games[:3]):
                print(f'  {i+1}. {game["away_team"]} @ {game["home_team"]}')
        return len(games) > 0
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()

if __name__ == "__main__":
    result = asyncio.run(test_ncaab())
    print(f'\nNCAAB Test: {"PASSED" if result else "FAILED"}')
    sys.exit(0 if result else 1)
