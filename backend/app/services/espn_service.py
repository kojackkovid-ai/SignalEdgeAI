import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ESPNService:
    """
    Service to fetch live scores and game results from ESPN's public API.
    Used for result tracking and resolving predictions.
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    
    # Mapping from OddsAPI sport keys to ESPN endpoints
    SPORT_MAPPING = {
        "basketball_nba": "basketball/nba",
        "icehockey_nhl": "hockey/nhl",
        "americanfootball_nfl": "football/nfl",
        "soccer_epl": "soccer/eng.1",
        "soccer_usa_mls": "soccer/usa.1",
        # Add more as needed
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_scoreboard(self, sport_key: str, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch scoreboard data for a given sport.
        date_str format: YYYYMMDD (e.g., '20231105')
        """
        espn_path = self.SPORT_MAPPING.get(sport_key)
        if not espn_path:
            logger.warning(f"No ESPN mapping found for sport: {sport_key}")
            return []

        url = f"{self.BASE_URL}/{espn_path}/scoreboard"
        params = {"limit": 100} # Fetch all games
        if date_str:
            params["dates"] = date_str

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            results = []
            
            for event in events:
                try:
                    competition = event["competitions"][0]
                    competitors = competition["competitors"]
                    
                    # Identify Home/Away
                    home_team = next((c for c in competitors if c["homeAway"] == "home"), None)
                    away_team = next((c for c in competitors if c["homeAway"] == "away"), None)
                    
                    if not home_team or not away_team:
                        continue
                        
                    status = event["status"]["type"]["name"] # STATUS_FINAL, STATUS_SCHEDULED, etc.
                    completed = event["status"]["type"]["completed"]
                    
                    results.append({
                        "id": event["id"],
                        "date": event["date"], # ISO format
                        "status": status,
                        "completed": completed,
                        "home_team": {
                            "name": home_team["team"]["displayName"],
                            "score": int(home_team.get("score", 0)) if completed or status == "STATUS_IN_PROGRESS" else 0,
                            "winner": home_team.get("winner", False)
                        },
                        "away_team": {
                            "name": away_team["team"]["displayName"],
                            "score": int(away_team.get("score", 0)) if completed or status == "STATUS_IN_PROGRESS" else 0,
                            "winner": away_team.get("winner", False)
                        }
                    })
                except Exception as e:
                    logger.error(f"Error parsing ESPN event: {e}")
                    continue
            
            return results

        except Exception as e:
            logger.error(f"Error fetching ESPN scoreboard for {sport_key}: {e}")
            return []

    async def close(self):
        await self.client.aclose()
