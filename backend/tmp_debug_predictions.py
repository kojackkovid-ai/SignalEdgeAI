import asyncio
from app.services.espn_prediction_service import ESPNPredictionService

async def run():
    print('START', flush=True)
    service = ESPNPredictionService()
    try:
        preds = await asyncio.wait_for(service.get_predictions(sport='basketball_nba', limit=5), timeout=30.0)
        print('GOT', len(preds), 'predictions', flush=True)
        if preds:
            print('SAMPLE', preds[0], flush=True)
    except asyncio.TimeoutError:
        print('Timeout fetching predictions', flush=True)
    except Exception as e:
        print('Error fetching predictions', e, flush=True)
    print('END', flush=True)

asyncio.run(run())
