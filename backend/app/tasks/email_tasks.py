"""
Email Background Tasks
Handles automated email campaigns (daily/weekly digests, etc)
"""

import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.models.db_models import User
from app.models.email_models import EmailPreferences, EmailLog
from app.models.prediction_records import PredictionRecord
from app.services.mailgun_service import MailgunService
from app.services.email_templates_service import EmailTemplateService
from app.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()
mailgun_service = MailgunService(settings)
template_service = EmailTemplateService()


async def send_daily_digest(db: AsyncSession):
    """
    Send daily digest emails to users
    Contains summary of their picks from the previous day
    """
    logger.info("📧 Starting daily digest email task...")
    
    try:
        # Get all active users who want daily digest emails
        result = await db.execute(
            select(User, EmailPreferences).join(
                EmailPreferences,
                User.id == EmailPreferences.user_id
            ).where(
                and_(
                    User.is_active == True,
                    EmailPreferences.daily_digest == True,
                    EmailPreferences.verified == True
                )
            )
        )
        
        user_prefs = result.all()
        emails_sent = 0
        
        for user, prefs in user_prefs:
            try:
                # Get user's predictions from yesterday
                yesterday = datetime.utcnow().date() - timedelta(days=1)
                
                pred_result = await db.execute(
                    select(PredictionRecord).where(
                        and_(
                            PredictionRecord.user_id == user.id,
                            PredictionRecord.created_at >= datetime.combine(yesterday, datetime.min.time()),
                            PredictionRecord.created_at < datetime.combine(yesterday + timedelta(days=1), datetime.min.time())
                        )
                    )
                )
                picks = pred_result.scalars().all()
                
                if not picks:
                    continue  # Skip if user had no picks yesterday
                
                # Calculate stats
                hits = sum(1 for p in picks if p.outcome == 'hit')
                total = len([p for p in picks if p.outcome in ['hit', 'miss']])
                win_rate = (hits / total * 100) if total > 0 else 0
                
                # Prepare context
                context = {
                    'user_name': user.username,
                    'date': yesterday.strftime('%B %d, %Y'),
                    'picks_count': len(picks),
                    'win_rate': f"{win_rate:.1f}",
                    'tier': user.subscription_tier,
                    'picks': [
                        {
                            'matchup': p.matchup or 'Unknown',
                            'prediction': p.prediction or 'Unknown',
                            'confidence': f"{p.confidence * 100:.0f}",
                            'sport': p.sport_key or 'Unknown'
                        }
                        for p in picks
                    ],
                    'dashboard_url': 'http://localhost:5173/dashboard'
                }
                
                # Send email
                send_result = await mailgun_service.send_templated_email(
                    to_email=user.email,
                    template_name='daily_digest',
                    context=context,
                    db=db,
                    user_id=user.id
                )
                
                if send_result['success']:
                    # Update last digest sent time
                    prefs.last_digest_sent = datetime.utcnow()
                    emails_sent += 1
                    logger.info(f"✅ Sent daily digest to {user.email}")
                else:
                    logger.warning(f"⚠️ Failed to send daily digest to {user.email}")
            
            except Exception as e:
                logger.error(f"Error sending daily digest to {user.email}: {e}")
        
        if emails_sent > 0:
            await db.commit()
        
        logger.info(f"✅ Daily digest task completed - {emails_sent} emails sent")
        return {'success': True, 'emails_sent': emails_sent}
    
    except Exception as e:
        logger.error(f"Error in daily digest task: {e}")
        return {'success': False, 'error': str(e)}


async def send_weekly_digest(db: AsyncSession):
    """
    Send weekly digest emails
    Contains performance summary for the past week
    """
    logger.info("📧 Starting weekly digest email task...")
    
    try:
        # Get all active users who want weekly digest emails
        result = await db.execute(
            select(User, EmailPreferences).join(
                EmailPreferences,
                User.id == EmailPreferences.user_id
            ).where(
                and_(
                    User.is_active == True,
                    EmailPreferences.weekly_digest == True,
                    EmailPreferences.verified == True
                )
            )
        )
        
        user_prefs = result.all()
        emails_sent = 0
        
        for user, prefs in user_prefs:
            try:
                # Get user's predictions from past 7 days
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                
                pred_result = await db.execute(
                    select(PredictionRecord).where(
                        and_(
                            PredictionRecord.user_id == user.id,
                            PredictionRecord.created_at >= seven_days_ago,
                            PredictionRecord.outcome.in_(['hit', 'miss'])  # Only resolved predictions
                        )
                    )
                )
                predictions = pred_result.scalars().all()
                
                if not predictions:
                    continue  # Skip if no resolved predictions
                
                # Calculate stats
                hits = sum(1 for p in predictions if p.outcome == 'hit')
                misses = sum(1 for p in predictions if p.outcome == 'miss')
                total = hits + misses
                win_rate = (hits / total * 100) if total > 0 else 0
                avg_confidence = sum(p.confidence for p in predictions) / len(predictions) * 100 if predictions else 0
                
                # Group by sport
                sports_dict = {}
                for pred in predictions:
                    sport = pred.sport_key or 'Unknown'
                    if sport not in sports_dict:
                        sports_dict[sport] = {'picks': 0, 'hits': 0}
                    sports_dict[sport]['picks'] += 1
                    if pred.outcome == 'hit':
                        sports_dict[sport]['hits'] += 1
                
                top_sports = sorted(
                    [
                        {
                            'name': sport,
                            'picks': data['picks'],
                            'win_rate': f"{(data['hits'] / data['picks'] * 100):.0f}"
                        }
                        for sport, data in sports_dict.items()
                    ],
                    key=lambda x: x['picks'],
                    reverse=True
                )[:3]
                
                # Prepare context
                week_start = (datetime.utcnow() - timedelta(days=7)).strftime('%B %d')
                context = {
                    'user_name': user.username,
                    'week_of': week_start,
                    'total_picks': total,
                    'hits': hits,
                    'misses': misses,
                    'win_rate': f"{win_rate:.1f}",
                    'avg_confidence': f"{avg_confidence:.1f}",
                    'top_sports': top_sports,
                    'dashboard_url': 'http://localhost:5173/dashboard'
                }
                
                # Send email
                send_result = await mailgun_service.send_templated_email(
                    to_email=user.email,
                    template_name='weekly_digest',
                    context=context,
                    db=db,
                    user_id=user.id
                )
                
                if send_result['success']:
                    prefs.last_digest_sent = datetime.utcnow()
                    emails_sent += 1
                    logger.info(f"✅ Sent weekly digest to {user.email}")
                else:
                    logger.warning(f"⚠️ Failed to send weekly digest to {user.email}")
            
            except Exception as e:
                logger.error(f"Error sending weekly digest to {user.email}: {e}")
        
        if emails_sent > 0:
            await db.commit()
        
        logger.info(f"✅ Weekly digest task completed - {emails_sent} emails sent")
        return {'success': True, 'emails_sent': emails_sent}
    
    except Exception as e:
        logger.error(f"Error in weekly digest task: {e}")
        return {'success': False, 'error': str(e)}


async def send_accuracy_milestone_emails(db: AsyncSession):
    """
    Send congratulations emails when users hit accuracy milestones
    Milestones: 50%, 60%, 70%, 75%, 80%, 90%, 95%, 99%
    """
    logger.info("📧 Checking for accuracy milestone achievements...")
    
    milestones = [50, 60, 70, 75, 80, 90, 95, 99]
    
    try:
        # Get all users with resolved predictions
        user_result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = user_result.scalars().all()
        
        emails_sent = 0
        
        for user in users:
            try:
                # Get user's resolved predictions
                pred_result = await db.execute(
                    select(PredictionRecord).where(
                        and_(
                            PredictionRecord.user_id == user.id,
                            PredictionRecord.outcome.in_(['hit', 'miss'])
                        )
                    )
                )
                predictions = pred_result.scalars().all()
                
                if not predictions:
                    continue
                
                # Calculate current win rate
                hits = sum(1 for p in predictions if p.outcome == 'hit')
                total = len(predictions)
                win_rate = (hits / total * 100) if total > 0 else 0
                
                # Check if user has hit a new milestone
                for milestone in milestones:
                    if win_rate >= milestone:
                        # Calculate percentile
                        percentile = 100 - milestone  # Rough estimate
                        
                        # Get avg confidence
                        avg_confidence = sum(p.confidence for p in predictions) / len(predictions) * 100 if predictions else 0
                        
                        context = {
                            'user_name': user.username,
                            'milestone': milestone,
                            'percentile': percentile,
                            'total_picks': total,
                            'hits': hits,
                            'misses': total - hits,
                            'avg_confidence': f"{avg_confidence:.1f}",
                            'dashboard_url': 'http://localhost:5173/dashboard'
                        }
                        
                        send_result = await mailgun_service.send_templated_email(
                            to_email=user.email,
                            template_name='accuracy_milestone',
                            context=context,
                            db=db,
                            user_id=user.id
                        )
                        
                        if send_result['success']:
                            emails_sent += 1
                            logger.info(f"✅ Sent milestone email to {user.email} ({milestone}% WR)")
                        
                        break  # Only send for highest milestone
            
            except Exception as e:
                logger.error(f"Error processing milestone for user {user.id}: {e}")
        
        logger.info(f"✅ Milestone email task completed - {emails_sent} emails sent")
        return {'success': True, 'emails_sent': emails_sent}
    
    except Exception as e:
        logger.error(f"Error in milestone task: {e}")
        return {'success': False, 'error': str(e)}


async def run_email_task_loop(db_session_maker):
    """
    Background loop for periodic email tasks
    Runs daily digest at 6 AM, weekly digest on Monday at 6 AM
    """
    logger.info("🚀 Starting email task background loop...")
    
    while True:
        try:
            now = datetime.utcnow()
            hour = now.hour
            day_of_week = now.weekday()  # 0 = Monday
            
            async with db_session_maker() as db:
                # Daily digest: 6 AM UTC
                if hour == 6 and now.minute < 5:
                    await send_daily_digest(db)
                
                # Weekly digest: Monday 6 AM UTC
                if day_of_week == 0 and hour == 6 and now.minute < 5:
                    await send_weekly_digest(db)
                
                # Check milestones: every 6 hours
                if hour % 6 == 0 and now.minute < 5:
                    await send_accuracy_milestone_emails(db)
            
            # Check every 5 minutes
            await asyncio.sleep(300)
        
        except asyncio.CancelledError:
            logger.info("Email task loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in email task loop: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute
