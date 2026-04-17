import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    games = await service.get_upcoming_games('basketball_nba')
    print(f'Found {len(games)} games')
    if games:
        game = games[0]
        home_name = game["home_team"]["name"]
        away_name = game["away_team"]["name"]
        print(f'Testing game: {game["id"]} - {home_name} vs {away_name}')
        pred = await service._enrich_prediction(game, 'basketball_nba')
        print(f'Confidence: {pred.get("confidence")}')
        print(f'Game time: {pred.get("game_time")}')
    await service.close()

asyncio.run(test())
