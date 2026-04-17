import asyncio
import logging
from app.services.espn_prediction_service import ESPNPredictionService

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_recent_form():
    service = ESPNPredictionService()
    
    # Test with LeBron James (NBA)
    athlete_id = "1966"
    sport_key = "basketball_nba"
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/gamelog"
    
    print(f"Testing recent form fetch for athlete {athlete_id}...")
    
    stats = await service._fetch_single_athlete_stats(url, athlete_id, sport_key)
    
    print("\nResult:")
    print(stats)
    
    if stats and athlete_id in stats:
        print("\nStats found:")
        for k, v in stats[athlete_id].items():
            print(f"  {k}: {v:.2f}")
    else:
        print("\nNo stats found.")

if __name__ == "__main__":
    asyncio.run(test_recent_form())