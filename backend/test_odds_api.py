
import asyncio
import httpx

API_KEY = "5189cc6c8f4efbdbc75c32761ccbc512"
BASE_URL = "https://api.the-odds-api.com/v4"

async def test_api():
    async with httpx.AsyncClient() as client:
        # Check usage quota
        url = f"{BASE_URL}/sports"
        params = {"apiKey": API_KEY}
        
        print(f"Testing API Key: {API_KEY}")
        try:
            response = await client.get(url, params=params)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
            else:
                print("Success! Sports fetched:")
                print(response.json()[:3]) # Print first 3
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
