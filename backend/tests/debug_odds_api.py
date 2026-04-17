
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

from app.services.odds_api_service import OddsApiService

async def test_api():
    print("Testing OddsApiService...")
    service = OddsApiService()
    
    # 1. Test get_sports
    print("\n--- Fetching Sports ---")
    sports = await service.get_sports()
    print(f"Found {len(sports)} sports")
    for s in sports[:5]:
        print(f" - {s['key']} ({s['title']})")
        
    # 2. Test get_events for NBA
    print("\n--- Fetching NBA Events ---")
    events = await service.get_events("basketball_nba")
    print(f"Found {len(events)} NBA events")
    if events:
        print(f"Sample Event: {events[0].get('home_team')} vs {events[0].get('away_team')}")
        print(f"Bookmakers: {len(events[0].get('bookmakers', []))}")
        
    # 3. Test get_predictions
    print("\n--- Fetching Predictions (All) ---")
    preds = await service.get_predictions()
    print(f"Generated {len(preds)} predictions")
    for p in preds:
        print(f" - {p['sport']} | {p['matchup']} | {p['prediction']} ({p['confidence']}%)")

if __name__ == "__main__":
    asyncio.run(test_api())
