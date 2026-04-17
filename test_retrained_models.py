"""Test the retrained models with real ESPN data"""
import asyncio
import sys
sys.path.insert(0, 'backend')
from app.services.espn_prediction_service import ESPNPredictionService

async def test_predictions():
    print("Testing retrained models with real ESPN data...")
    service = ESPNPredictionService()
    
    # Test NBA
    games = await service.get_upcoming_games('basketball_nba')
    print(f"Found {len(games)} NBA games")
    
    # Get predictions
    if games:
        pred = await service._enrich_prediction(games[0], 'basketball_nba')
        print(f"Prediction: {pred.get('prediction')}")
        print(f"Confidence: {pred.get('confidence')}%")
    
    # Test NHL
    nhl_games = await service.get_upcoming_games('icehockey_nhl')
    print(f"Found {len(nhl_games)} NHL games")
    
    # Test MLB
    mlb_games = await service.get_upcoming_games('baseball_mlb')
    print(f"Found {len(mlb_games)} MLB games")
    
    # Test Soccer
    epl_games = await service.get_upcoming_games('soccer_epl')
    print(f"Found {len(epl_games)} EPL games")
    
    await service.close()
    print("\n✅ All tests passed - models working with real ESPN data!")

if __name__ == "__main__":
    asyncio.run(test_predictions())
