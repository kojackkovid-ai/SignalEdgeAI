#!/usr/bin/env python3
"""Detailed debug script for daily picks counting issue"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force SQLite for debugging
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.db_models import User, user_predictions, Prediction
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_picks():
    """Debug script to check daily picks"""
    
    # Connect to database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./test.db')
    print(f"\n=== DATABASE_URL: {DATABASE_URL} ===\n")
    
    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"timeout": 30} if 'sqlite' in DATABASE_URL else {})
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        try:
            # Get all users
            result = await db.execute(select(User).limit(5))
            users = result.scalars().all()
            
            print(f"Found {len(users)} users in database\n")
            
            for user in users:
                print(f"\n{'='*80}")
                print(f"User: {user.username} ({user.id})")
                print(f"Tier: {user.subscription_tier}")
                print(f"Club 100 Unlocked: {user.club_100_unlocked}")
                print(f"{'='*80}")
                
                # Count all their predictions
                all_preds = await db.execute(
                    select(func.count()).select_from(user_predictions).where(
                        user_predictions.c.user_id == user.id
                    )
                )
                all_count = all_preds.scalar() or 0
                print(f"Total predictions followed: {all_count}")
                
                # Get UTC today's start
                today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                print(f"Today UTC start (for comparison): {today_utc}")
                
                # Count picks from today onward (the actual logic from prediction_service.py)
                today_count_stmt = select(func.count()).select_from(user_predictions).join(
                    Prediction, user_predictions.c.prediction_id == Prediction.id
                ).where(
                    and_(
                        user_predictions.c.user_id == user.id,
                        user_predictions.c.created_at >= today_utc,
                        Prediction.sport != 'club_100_access'
                    )
                )
                today_result = await db.execute(today_count_stmt)
                today_count = today_result.scalar() or 0
                print(f"Picks from today onwards (sport != 'club_100_access'): {today_count}")
                
                # List actual picks with timestamps
                picks_stmt = select(user_predictions, Prediction.sport, Prediction.id, Prediction.is_club_100_pick).select_from(
                    user_predictions
                ).join(
                    Prediction, user_predictions.c.prediction_id == Prediction.id
                ).where(
                    user_predictions.c.user_id == user.id
                ).order_by(
                    user_predictions.c.created_at.desc()
                ).limit(10)
                
                picks_result = await db.execute(picks_stmt)
                picks = picks_result.all()
                
                print(f"\nLast 10 predictions:")
                for i, pick in enumerate(picks, 1):
                    created_at = pick[0].created_at if hasattr(pick[0], 'created_at') else pick[0][2]  # Try both ways
                    sport = pick[1]
                    pred_id = pick[2]
                    is_club_100 = pick[3]
                    
                    # Get the created_at from user_predictions table directly
                    pred_join = await db.execute(
                        select(user_predictions.c.created_at).where(
                            and_(
                                user_predictions.c.user_id == user.id,
                                user_predictions.c.prediction_id == pred_id
                            )
                        )
                    )
                    created_at = pred_join.scalar()
                    
                    is_today = created_at >= today_utc if created_at else False
                    skip_count = "SKIP" if sport == 'club_100_access' else "COUNT"
                    
                    print(f"  {i}. ID: {pred_id[:8]}... Sport: {sport:20} Club100: {is_club_100} Created: {created_at} Today: {is_today} [{skip_count}]")
                
                # Check Club 100 picks specifically
                club100_count = await db.execute(
                    select(func.count()).select_from(user_predictions).join(
                        Prediction, user_predictions.c.prediction_id == Prediction.id
                    ).where(
                        and_(
                            user_predictions.c.user_id == user.id,
                            Prediction.is_club_100_pick == True
                        )
                    )
                )
                club100_total = club100_count.scalar() or 0
                print(f"\nTotal Club 100 picks: {club100_total}")
                
                # Check if there are any club_100_access sport predictions
                access_count = await db.execute(
                    select(func.count()).select_from(user_predictions).join(
                        Prediction, user_predictions.c.prediction_id == Prediction.id
                    ).where(
                        and_(
                            user_predictions.c.user_id == user.id,
                            Prediction.sport == 'club_100_access'
                        )
                    )
                )
                access_total = access_count.scalar() or 0
                print(f"Total club_100_access (access cost): {access_total}")
                
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_picks())
