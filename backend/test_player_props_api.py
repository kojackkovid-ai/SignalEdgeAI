import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from app.services.espn_prediction_service import ESPNPredictionService
    service = ESPNPredictionService()
    
    print('=== Testing NBA Player Props ===')
    try:
        props = await service.get_player_props('basketball_nba', '401810707')
        print(f'Got {len(props)} NBA player props')
        for p in props[:3]:
            print(f'  - {p.get("player", "N/A")}: {p.get("prediction", "N/A")} ({p.get("confidence", 0)}%)')
    except Exception as e:
        import traceback
        print(f'Error getting NBA props: {e}')
        traceback.print_exc()

asyncio.run(test())
