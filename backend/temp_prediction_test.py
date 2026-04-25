import asyncio
import sys
sys.path.append('.')
from app.services.prediction_service import PredictionService

async def test():
    service = PredictionService()
    try:
        result = await service.get_predictions(['nba', 'nhl', 'mlb'], 'free')
        print(f'Success: Got {len(result)} predictions')
        for pred in result[:3]:
            print(f"  {pred.get('sport', 'unknown')}: {pred.get('game_id', 'unknown')}")
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
