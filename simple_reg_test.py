import httpx
import asyncio

async def test_registration():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/api/auth/register",
            json={
                "email": "test999@test.com",
                "password": "TestPassword123!",
                "username": "testuser999"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_registration())
