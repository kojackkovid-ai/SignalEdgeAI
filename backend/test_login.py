import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.services.auth_service import AuthService

async def test_auth():
    try:
        print("Testing auth service...")
        auth_service = AuthService()

        print("Getting database session...")
        async for session in get_db():
            print("Authenticating user...")
            user = await auth_service.authenticate_user(session, 'test@example.com', 'password123')
            print(f'User found: {user}')
            if user:
                print(f'User ID: {user.id}, Email: {user.email}')
                print("✓ Authentication successful!")
            else:
                print('✗ User not found or password incorrect')
            break
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth())
