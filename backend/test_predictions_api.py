import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from app.services.espn_prediction_service import ESPNPredictionService
    service = ESPNPredictionService()
    
    print('=== Testing NBA predictions ===')
    try:
        preds = await service.get_predictions(sport='basketball_nba', limit=5)
        print(f'Got {len(preds)} NBA predictions')
        for p in preds[:2]:
            print(f'  - {p.get("matchup", "N/A")}: {p.get("prediction", "N/A")} ({p.get("confidence", 0)}%)')
    except Exception as e:
        import traceback
        print(f'Error getting NBA: {e}')
        traceback.print_exc()
    
    print('\n=== Testing MLB predictions ===')
    try:
        preds = await service.get_predictions(sport='baseball_mlb', limit=5)
        print(f'Got {len(preds)} MLB predictions')
        for p in preds[:2]:
            print(f'  - {p.get("matchup", "N/A")}: {p.get("prediction", "N/A")} ({p.get("confidence", 0)}%)')
    except Exception as e:
        import traceback
        print(f'Error getting MLB: {e}')
        traceback.print_exc()
    
    print('\n=== Testing NHL predictions ===')
    try:
        preds = await service.get_predictions(sport='icehockey_nhl', limit=5)
        print(f'Got {len(preds)} NHL predictions')
        for p in preds[:2]:
            print(f'  - {p.get("matchup", "N/A")}: {p.get("prediction", "N/A")} ({p.get("confidence", 0)}%)')
    except Exception as e:
        import traceback
        print(f'Error getting NHL: {e}')
        traceback.print_exc()

asyncio.run(test())
