"""Test Club 100 API endpoint"""
import asyncio
import httpx
import json

async def test_club100():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            print("\n=== Testing Club 100 Endpoint ===\n")
            
            # Test the GET /api/predictions/club-100/data endpoint
            response = await client.get(
                'http://127.0.0.1:8000/api/predictions/club-100/data',
                headers={'Authorization': 'Bearer test_token'}
            )
            print(f'Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                print(f'Success: {data.get("success")}')
                print(f'\nClub 100 Players by Sport:')
                
                for sport, players in data.get('data', {}).items():
                    print(f'\n{sport.upper()}: {len(players)} players')
                    for player in players:
                        print(f'  {player["name"]} ({player["team"]}) - {player["position"]}')
                        if player.get('last_4_games'):
                            lines = player['last_4_games'].get('cleared_lines', [])
                            print(f'    Last 4 games: {lines}')
                        if player.get('last_5_games'):
                            lines = player['last_5_games'].get('cleared_lines', [])
                            print(f'    Last 5 games: {lines}')
            else:
                print(f'Error: {response.text[:500]}')
                
        except Exception as e:
            print(f'Exception: {type(e).__name__}: {str(e)}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_club100())
