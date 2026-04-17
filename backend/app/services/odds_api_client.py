import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class OddsAPIClient:
    def __init__(self):
        self.api_key = settings.odds_api_key
        self.base_url = getattr(settings, 'odds_api_base_url', 'https://api.the-odds-api.com/v4/')

    async def get_sports(self):
        url = f"{self.base_url}sports/"
        params = {"apiKey": self.api_key}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_odds(self, sport_key: str, regions: str = "us", markets: str = "h2h,spreads,totals", odds_format: str = "american"):
        url = f"{self.base_url}sports/{sport_key}/odds/"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
