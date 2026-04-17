import asyncio
import aiohttp
from datetime import datetime

async def test_analytics():
    async with aiohttp.ClientSession() as session:
        url = "http://127.0.0.1:8000/api/analytics/accuracy?days=90"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Total predictions: {data.get('total_predictions')}")
                print(f"Win rate: {data.get('win_rate')}")
                print(f"ROI: {data.get('roi')}")
                print(f"By sport: {data.get('by_sport')}")
        except asyncio.TimeoutError:
            print("Request timed out")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_analytics())
