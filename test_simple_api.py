"""
Direct HTTP test of the backend API endpoint
"""
import asyncio
import httpx
import json

async def test_api():
    async with httpx.AsyncClient(timeout=120) as client:
        url = "http://localhost:8000/api/predictions/game/soccer_usa_mls/761502/full"
        
        print(f"Testing: {url}")
        try:
            resp = await client.get(url)
            print(f"\nStatus: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"\n✓ Response received successfully")
                print(f"\n📊 Props Summary:")
                props_summary = data.get("props_summary", {})
                for key, val in props_summary.items():
                    print(f"  {key}: {val}")
                
                print(f"\n🎯 Goals count: {len(data.get('goals', []))}")
                if data.get('goals'):
                    print(f"  First goal prop: {data['goals'][0].get('player')} - {data.get('goals')[0].get('prediction')}")
                
                print(f"\n🎯 Assists count: {len(data.get('assists', []))}")
                if data.get('assists'):
                    print(f"  First assist prop: {data['assists'][0].get('player')} - {data['assists'][0].get('prediction')}")
                
                print(f"\n🎯 Team Props count: {len(data.get('team_props', []))}")
                
                print(f"\n📄 Full Response Keys: {list(data.keys())}")
                
            else:
                print(f"Error response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
