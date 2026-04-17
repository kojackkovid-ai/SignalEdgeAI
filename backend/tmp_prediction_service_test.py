import asyncio
from app.services.prediction_service import PredictionService

async def run():
    service = PredictionService()
    # create dummy user with subscription tier
    class User: pass
    u = User(); u.subscription_tier = 'elite'
    # Call predictions; no db required for this test since service uses none before return
    preds = await service.get_predictions(db=None, user=u, sport='basketball_nba', limit=5)
    print('returned', len(preds), 'predictions')
    if preds:
        print(preds[0])

asyncio.run(run())
