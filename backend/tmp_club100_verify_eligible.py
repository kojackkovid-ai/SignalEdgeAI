import os
import sys
import asyncio

# Force local SQLite and stable secret key
os.environ['USE_SQLITE'] = 'true'
os.environ['SECRET_KEY'] = 'localtestkey1234567890123456789012'
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import AuthService
from app.database import get_db
from app.models.db_models import User
from sqlalchemy import select

client = TestClient(app, base_url='http://127.0.0.1')

def ensure_elite_user():
    auth = AuthService()
    email = 'elite_test_user@example.com'
    username = 'elite_test_user'
    user_id = None
    async def _do():
        async for db in get_db():
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user is None:
                user = User(email=email, username=username, password_hash=auth.hash_password('Password123!'), subscription_tier='elite')
                db.add(user)
                await db.commit()
                await db.refresh(user)
            else:
                user.subscription_tier = 'elite'
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user.id
    return asyncio.run(_do())

if __name__ == '__main__':
    user_id = ensure_elite_user()
    auth = AuthService()
    token = auth.create_access_token({'sub': user_id})
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/api/predictions/club-100/data?force_refresh=true', headers=headers)
    print('status_code=', response.status_code)
    print(response.text)
