#!/usr/bin/env python3
"""
Startup verification script to check database connectivity and configuration.
Run this before starting the main app to catch configuration issues early.
"""
import os
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

def is_running_in_docker():
    """Check if this script is running inside a Docker container"""
    return os.path.exists('/.dockerenv')

async def check_database_connection():
    """Check if we can connect to the database"""
    print("\n" + "="*60)
    print("[STARTUP] Database Configuration Check")
    
    in_docker = is_running_in_docker()
    db_url = settings.database_url
    
    # If running on host, override localhost to use Docker port mapping
    if not in_docker and 'localhost' in db_url:
        print(f"[STARTUP] Running on HOST - detected Docker environment")
        db_url = db_url.replace('postgres:5432', 'localhost:5432')
        print(f"[STARTUP] Using host port mapping for database connection")
    
    try:
        engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            pool_pre_ping=True
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ [STARTUP] Database connection successful!")
            return True
            
    except Exception as e:
        print(f"❌ [STARTUP] Database connection failed!")
        print(f"Error: {type(e).__name__}: {str(e)}")
        if not in_docker:
            print(f"[STARTUP] Running on HOST - ensure Docker containers are exposed via port mapping")
        return False

async def check_redis_connection():
    """Check if we can connect to Redis"""
    print("\n" + "="*60)
    print("[STARTUP] Redis Configuration Check")
    
    in_docker = is_running_in_docker()
    redis_url = settings.redis_url
    
    # If running on host, override localhost to use Docker port mapping
    if not in_docker and 'redis:6379' in redis_url:
        print(f"[STARTUP] Running on HOST - detected Docker environment")
        redis_url = redis_url.replace('redis:6379', 'localhost:6379')
        print(f"[STARTUP] Using host port mapping for Redis connection")
    
    try:
        try:
            import redis.asyncio as aioredis
        except ModuleNotFoundError:
            import redis.asyncio as aioredis

        redis = await aioredis.from_url(redis_url)
        await redis.ping()
        print("✅ [STARTUP] Redis connection successful!")
        await redis.aclose()
        return True
    except Exception as e:
        print(f"❌ [STARTUP] Redis connection failed (non-critical)")
        print(f"Error: {type(e).__name__}: {str(e)}")
        if not in_docker:
            print(f"[STARTUP] Running on HOST - ensure Docker containers are exposed via port mapping")
        return False

async def main():
    print("\n🔍 Starting Platform Startup Verification...\n")
    
    in_docker = is_running_in_docker()
    env_text = "INSIDE Docker Container" if in_docker else "on HOST Machine"
    print(f"[STARTUP] Running {env_text}")
    
    db_ok = await check_database_connection()
    redis_ok = await check_redis_connection()
    
    print("\n" + "="*60)
    print("[STARTUP] Summary")
    print("="*60)
    print(f"Environment: {env_text}")
    print(f"Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"Redis: {'✅ OK' if redis_ok else '⚠️  FAILED (non-critical)'}")
    
    if not db_ok:
        print("\n⚠️  Database connection not yet available - will retry during API initialization")
        print("This is normal during Docker Compose startup - services initialize in sequence")
        print("="*60 + "\n")
        # Don't exit - let the API start and handle database initialization
        return
    
    print("\n✅ All critical services are ready!")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
