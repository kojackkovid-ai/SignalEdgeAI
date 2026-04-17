import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as c:
        for s in ['basketball_nba','americanfootball_nfl','baseball_mlb','icehockey_nhl','soccer_epl']:
            r = await c.get('http://127.0.0.1:8000/api/predictions/', params={'sport': s, 'limit': 5}, timeout=30.0)
            print('sport', s, 'status', r.status_code, 'len', len(r.text))
            print(r.text)

if __name__ == '__main__':
    asyncio.run(main())
