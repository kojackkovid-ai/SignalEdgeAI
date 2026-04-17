#!/usr/bin/env python3
"""Query database directly to debug pick counts"""

import asyncio
import os
from datetime import datetime
import sys

# Use the actual database configuration from docker-compose
async def debug_db():
    # Get connection from environment or defaults
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'sports_predictions_prod')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'password')
    
    print(f"Connecting to: {db_user}@{db_host}:{db_port}/{db_name}")
    
    try:
        import asyncpg
        
        # Connect directly with asyncpg
        conn = await asyncpg.connect(
            user=db_user,
            password=db_password,
            database=db_name,
            host=db_host,
            port=int(db_port),
            timeout=10
        )
        
        try:
            # Get a sample user with starter tier
            users = await conn.fetch("""
                SELECT id, username, subscription_tier FROM users 
                WHERE subscription_tier = 'starter' LIMIT 1
            """)
            
            if not users:
                print("No starter tier users found, trying any user...")
                users = await conn.fetch("""
                    SELECT id, username, subscription_tier FROM users LIMIT 1
                """)
            
            if not users:
                print("No users found in database!")
                return
            
            user_id, username, tier = users[0]
            print(f"\n" + "="*80)
            print(f"Testing User: {username}")
            print(f"Tier: {tier}")
            print(f"ID: {user_id}")
            print("="*80)
            
            # Count all predictions
            all_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_predictions WHERE user_id = $1
            """, user_id)
            print(f"\nTotal predictions followed: {all_count}")
            
            # Count picks from TODAY (UTC)
            today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            print(f"Today UTC start: {today_utc}")
            
            today_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_predictions up
                JOIN predictions p ON up.prediction_id = p.id
                WHERE up.user_id = $1 
                  AND up.created_at >= $2
                  AND p.sport != 'club_100_access'
            """, user_id, today_utc)
            print(f"Picks from today (sport != 'club_100_access'): {today_count}")
            
            # Get the last 15 picks
            picks = await conn.fetch("""
                SELECT 
                  up.prediction_id,
                  up.created_at,
                  p.sport,
                  p.is_club_100_pick
                FROM user_predictions up
                JOIN predictions p ON up.prediction_id = p.id
                WHERE up.user_id = $1
                ORDER BY up.created_at DESC
                LIMIT 15
            """, user_id)
            
            print(f"\nLast 15 predictions:")
            for i, row in enumerate(picks, 1):
                pred_id, created_at, sport, is_club_100 = row
                is_today = created_at >= today_utc if created_at else False
                skip = "SKIP" if sport == 'club_100_access' else "COUNT"
                print(f"  {i:2}. {pred_id[:12]:12} {str(created_at)[:19]:19} {sport:20} Club100:{is_club_100} Today:{is_today} [{skip}]")
            
            # Check for club_100_access picks
            access_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_predictions up
                JOIN predictions p ON up.prediction_id = p.id
                WHERE up.user_id = $1 AND p.sport = 'club_100_access'
            """, user_id)
            print(f"\nClub 100 access picks (should be excluded): {access_count}")
            
            # Check for Club 100 predictions
            club100_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_predictions up
                JOIN predictions p ON up.prediction_id = p.id
                WHERE up.user_id = $1 AND p.is_club_100_pick = true
            """, user_id)
            print(f"Is_club_100_pick predictions: {club100_count}")
            
            # Get user tier config
            print(f"\n{'='*80}")
            print("Checking tier limits in code:")
            
            from app.models.tier_features import TierFeatures
            tier_config = TierFeatures.get_tier_config(tier)
            if tier_config:
                print(f"Tier config found for '{tier}':")
                print(f"  predictions_per_day: {tier_config.get('predictions_per_day')}")
            else:
                print(f"⚠️  NO TIER CONFIG found for '{tier}'!")
            
        finally:
            await conn.close()
            
    except ImportError:
        print("asyncpg not available, trying with psycopg2...")
        import psycopg2
        
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        try:
            cur = conn.cursor()
            
            # Get a sample user
            cur.execute("""
                SELECT id, username, subscription_tier FROM users 
                WHERE subscription_tier = 'starter' LIMIT 1
            """)
            row = cur.fetchone()
            
            if not row:
                cur.execute("SELECT id, username, subscription_tier FROM users LIMIT 1")
                row = cur.fetchone()
            
            if not row:
                print("No users found!")
                return
            
            user_id, username, tier = row
            print(f"\n" + "="*80)
            print(f"Testing User: {username}")
            print(f"Tier: {tier}")
            print(f"ID: {user_id}")
            print("="*80)
            
            # Count all
            cur.execute("SELECT COUNT(*) FROM user_predictions WHERE user_id = %s", (user_id,))
            all_count = cur.fetchone()[0]
            print(f"\nTotal predictions: {all_count}")
            
            # Count today
            today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cur.execute("""
                SELECT COUNT(*) FROM user_predictions up
                JOIN predictions p ON up.prediction_id = p.id
                WHERE up.user_id = %s 
                  AND up.created_at >= %s
                  AND p.sport != 'club_100_access'
            """, (user_id, today_utc))
            today_count = cur.fetchone()[0]
            print(f"Picks from today: {today_count}")
            
            # Get last 15
            cur.execute("""
                SELECT 
                  up.prediction_id,
                  up.created_at,
                  p.sport,
                  p.is_club_100_pick
                FROM user_predictions up
                JOIN predictions p ON up.prediction_id = p.id
                WHERE up.user_id = %s
                ORDER BY up.created_at DESC
                LIMIT 15
            """, (user_id,))
            
            picks = cur.fetchall()
            print(f"\nLast 15 picks:")
            for i, row in enumerate(picks, 1):
                pred_id, created_at, sport, is_club_100 = row
                is_today = created_at >= today_utc if created_at else False
                skip = "SKIP" if sport == 'club_100_access' else "COUNT"
                print(f"  {i:2}. {str(pred_id)[:12]:12} {str(created_at)[:19]:19} {sport:20} {str(is_club_100):5} {str(is_today):5} [{skip}]")
            
            cur.close()
            
        finally:
            conn.close()

if __name__ == "__main__":
    asyncio.run(debug_db())
