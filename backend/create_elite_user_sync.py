#!/usr/bin/env python3
"""
Create Elite User - Direct Database Access
Creates a new elite tier user without relying on app initialization
"""

import bcrypt
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Database URL components
db_user = os.getenv("DB_USER", "postgres")
db_pass = os.getenv("DB_PASS", "sports_predictions_password")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "sports_predictions_prod")

DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

# Try importing SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
    print("✅ SQLAlchemy imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SQLAlchemy: {e}")
    exit(1)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_elite_user(email: str, password: str, username: str = None):
    """Create elite user directly in database"""
    
    if username is None:
        username = f"elite_{uuid.uuid4().hex[:8]}"
    
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    now = datetime.utcnow()
    
    try:
        # Create engine
        print(f"Connecting to database: {db_host}:{db_port}...")
        engine = create_engine(DATABASE_URL, echo=False, connect_args={"connect_timeout": 10})
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Insert user
        with Session(engine) as session:
            # Check if user exists
            result = session.execute(
                text("""
                    SELECT id FROM users 
                    WHERE email = :email OR username = :username
                """),
                {"email": email, "username": username}
            )
            
            existing = result.fetchone()
            if existing:
                print(f"❌ User already exists with email {email} or username {username}")
                return None
            
            # Insert new elite user
            insert_query = text("""
                INSERT INTO users (
                    id, email, username, password_hash, subscription_tier,
                    subscription_start, is_active, created_at, updated_at
                ) VALUES (
                    :id, :email, :username, :password_hash, :subscription_tier,
                    :subscription_start, :is_active, :created_at, :updated_at
                )
            """)
            
            session.execute(insert_query, {
                "id": user_id,
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "subscription_tier": "elite",
                "subscription_start": now,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            })
            
            session.commit()
            
            print("✅ Elite user created successfully!")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            print(f"   Tier: elite")
            print(f"   User ID: {user_id}")
            
            return user_id
    
    except Exception as e:
        print(f"❌ Error creating elite user: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    email = "sportsai@gmail.com"
    password = "bonustester11"
    
    print("Creating Elite User...")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    result = create_elite_user(email, password)
    
    if result:
        print()
        print("✅ User is ready to use for login!")
    else:
        print()
        print("❌ Failed to create user")
        exit(1)
