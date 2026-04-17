import asyncio
import logging
from app.services.espn_prediction_service import ESPNPredictionService

# Enable logging
logging.basicConfig(level=logging.INFO)

async def debug_soccer_anytime():
    service = ESPNPredictionService()
    sport_key = 'soccer_epl'

    print("=== DEBUGGING SOCCER ANYTIME GOAL SCORERS ===")

    # Step 1: Get upcoming games
    print("\n1. Getting upcoming soccer games...")
    games = await service.get_upcoming_games(sport_key)
    if not games:
        print("❌ No upcoming soccer games found")
        return

    event_id = games[0]['event_id']
    print(f"✅ Found game: {event_id}")

    # Step 2: Get player props
    print(f"\n2. Getting player props for {sport_key}/{event_id}...")
    all_props = await service.get_player_props(sport_key, event_id)
    print(f"✅ Total props: {len(all_props)}")

    # Step 3: Filter for goals props
    goals_props = [p for p in all_props if p.get("market_key") == "goals"]
    print(f"✅ Goals props: {len(goals_props)}")

    if goals_props:
        print("\n3. Sample goals props:")
        for i, prop in enumerate(goals_props[:4]):
            print(f"   {i+1}. Player: {prop.get('player', 'Unknown')}")
            print(f"      Team: {prop.get('team_name', 'Unknown')}")
            print(f"      Confidence: {prop.get('confidence', 'N/A')}")
            print(f"      Market: {prop.get('market_key', 'N/A')}")
            print()

    # Step 4: Test anytime goal scorers
    print("4. Testing anytime goal scorers endpoint...")
    result = await service.get_anytime_goal_scorers(sport_key, event_id, 'Soccer')

    print("
✅ Anytime goal scorers result:")
    print(f"   Home team: {result.get('home_team', {}).get('name', 'Unknown')}")
    home_scorers = result.get('home_team', {}).get('top_scorers', [])
    print(f"   Home scorers: {len(home_scorers)}")
    for scorer in home_scorers:
        print(f"     - {scorer.get('player', 'Unknown')} (conf: {scorer.get('confidence', 'N/A')})")

    print(f"   Away team: {result.get('away_team', {}).get('name', 'Unknown')}")
    away_scorers = result.get('away_team', {}).get('top_scorers', [])
    print(f"   Away scorers: {len(away_scorers)}")
    for scorer in away_scorers:
        print(f"     - {scorer.get('player', 'Unknown')} (conf: {scorer.get('confidence', 'N/A')})")

    if len(home_scorers) < 2 or len(away_scorers) < 2:
        print("\n❌ ISSUE: Not getting 2 players from each team!")
        print("   This means either:")
        print("   - No goals props generated")
        print("   - Team names not set correctly")
        print("   - Team matching logic failing")
    else:
        print("\n✅ SUCCESS: Got 2 players from each team!")

if __name__ == "__main__":
    asyncio.run(debug_soccer_anytime())