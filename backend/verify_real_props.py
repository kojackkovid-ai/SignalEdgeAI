
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.odds_api_service import OddsApiService

# Configure logging
logging.basicConfig(level=logging.INFO)

async def verify_real_props():
    print("--- Verifying Real Player Props from API ---")
    service = OddsApiService()
    
    # 1. Get NBA Events
    print("Fetching NBA events...")
    events = await service.get_events("basketball_nba")
    
    if not events:
        print("❌ No NBA events found. Try another sport or check API key.")
        return

    print(f"✅ Found {len(events)} events.")
    
    # 2. Pick the first event (likely today/tomorrow)
    event = events[0]
    event_id = event['id']
    matchup = f"{event.get('away_team')} @ {event.get('home_team')}"
    print(f"Testing Event: {matchup} (ID: {event_id})")
    
    # 3. Fetch Player Props
    print(f"Fetching props for event {event_id}...")
    props = await service.get_player_props("basketball_nba", event_id)
    
    print(f"Result: {len(props)} props returned.")
    
    if props:
        print("\nSample Prop:")
        p = props[0]
        print(f"Player: {p.get('player')}")
        print(f"Market: {p.get('market_key')}")
        print(f"Prediction: {p.get('prediction')}")
        print(f"Odds: {p.get('odds')} (Type: {type(p.get('odds'))})")
        print(f"Reasoning: {p.get('reasoning')}")
    else:
        print("❌ No props returned. Possible reasons:")
        print("1. API Key doesn't support player props (requires paid plan?)")
        print("2. No props available for this game yet.")
        print("3. Code filtering logic is too strict.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_real_props())
