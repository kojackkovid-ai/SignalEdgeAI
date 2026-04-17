import asyncio
import httpx
import json

async def test():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get('http://127.0.0.1:8000/api/predictions/?sport=soccer_epl&limit=2')
            if resp.status_code == 200:
                data = resp.json()
                preds = data.get('predictions', [])
                if preds:
                    pred = preds[0]
                    print(f"Sample prediction keys: {list(pred.keys())}")
                    print(f"\nFull first prediction:\n{json.dumps(pred, indent=2, default=str)}")
            else:
                print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
