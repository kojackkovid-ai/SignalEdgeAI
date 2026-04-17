#!/usr/bin/env python3
"""Quick database initialization"""
import asyncio
import sys

async def main():
    sys.path.insert(0, '/app')
    from app.database import init_db
    
    try:
        print("Initializing database...")
        await init_db()
        print("✓ Database tables created")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
