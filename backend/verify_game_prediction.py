
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.odds_api_service import OddsApiService

# Configure logging
logging.basicConfig(level=logging.INFO)

async def verify_game_prediction():
    print("--- Verifying Game Prediction Reasoning ---")
    service = OddsApiService()
    
    # 1. Get NBA Events
    print("Fetching NBA events...")
    events = await service.get_events("basketball_nba")
    
    if not events:
        print("❌ No NBA events found.")
        return

    event = events[0]
    print(f"Testing Event: {event.get('away_team')} @ {event.get('home_team')}")

    # 2. Transform to prediction (this calls ml_service.predict_from_odds)
    print("Transforming to prediction...")
    pred = await service.transform_event_to_prediction(event, "basketball_nba")
    
    if pred:
        print(f"Prediction: {pred.get('prediction')}")
        print(f"Confidence: {pred.get('confidence')}%")
        print("Reasoning:")
        for r in pred.get('reasoning', []):
            print(f" - {r.get('factor')} ({r.get('weight')}): {r.get('explanation')}")
    else:
        print("❌ Failed to generate prediction.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_game_prediction())
