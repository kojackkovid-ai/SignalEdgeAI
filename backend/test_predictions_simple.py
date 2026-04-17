import asyncio
import sys
sys.path.insert(0, '.')

from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    print('Testing get_predictions...')
    predictions = await service.get_predictions(limit=5)
    print(f'Found {len(predictions)} predictions')
    if predictions:
        p = predictions[0]
        matchup = p.get('matchup', 'N/A')
        prediction = p.get('prediction', 'N/A')
        print(f'Sample: {matchup} - {prediction}')
    await service.close()

if __name__ == '__main__':
    asyncio.run(test())
