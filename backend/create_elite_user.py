#!/usr/bin/env python3
"""
Create Elite User Script
Creates a new elite tier user for testing/development
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.db_models import User
from app.services.auth_service import AuthService
import uuid
from datetime import datetime


async def create_elite_user(email: str, password: str, username: str = None):
    """Create a new elite tier user"""
    
    # Generate username if not provided
    if username is None:
        username = f"elite_{uuid.uuid4().hex[:8]}"
    
    # Create auth service
    auth_service = AuthService()
    
    # Get database session
    async with AsyncSessionLocal() as db:
        try:
            # Check if user already exists
            result = await db.execute(
                select(User).where((User.email == email) | (User.username == username))
            )
            existing_user = result.scalars().first()
            
            if existing_user:
                print(f"❌ User already exists with email {email} or username {username}")
                return None
            
            # Create new elite user
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=username,
                password_hash=auth_service.hash_password(password),
                subscription_tier="elite",  # Set to elite tier
                subscription_start=datetime.utcnow(),
                is_active=True
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"✅ Elite user created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Tier: {user.subscription_tier}")
            print(f"   User ID: {user.id}")
            
            return user
            
        except Exception as e:
            print(f"❌ Error creating elite user: {str(e)}")
            await db.rollback()
            return None


async def main():
    """Main entry point"""
    email = "sportsai@gmail.com"
    password = "bonustester11"
    
    print("Creating Elite User...")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    user = await create_elite_user(email, password)
    
    if user:
        print()
        print("User ready to use!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
