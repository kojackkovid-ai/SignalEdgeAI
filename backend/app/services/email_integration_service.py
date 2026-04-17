"""
Email Integration Service
Integrates Mailgun email sending into existing platform workflows
Handles: tier upgrades, password resets, prediction results, subscription confirmations
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import Settings
from app.services.mailgun_service import MailgunService
from app.models.db_models import User

logger = logging.getLogger(__name__)


class EmailIntegrationService:
    """Service to integrate emails into platform workflows"""
    
    def __init__(self, settings: Settings, mailgun_service: MailgunService):
        self.settings = settings
        self.mailgun_service = mailgun_service
    
    async def send_tier_upgrade_email(
        self,
        db: AsyncSession,
        user_id: str,
        new_tier: str,
        features: list
    ):
        """
        Send email when user upgrades to a new tier
        
        Args:
            db: Database session
            user_id: User ID
            new_tier: New tier name (pro, pro_plus, elite)
            features: List of features unlocked
        """
        try:
            # Get user
            user = await db.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found for tier upgrade email")
                return
            
            # Check user preferences
            can_send = await self.mailgun_service.check_email_preferences(
                db, user_id, 'tier_update'
            )
            if not can_send:
                logger.info(f"User {user_id} has disabled tier update emails")
                return
            
            # Map tier to daily limit
            tier_limits = {
                'basic': 50,
                'pro': 9999,
                'pro_plus': 9999,
                'elite': 9999
            }
            
            daily_limit = tier_limits.get(new_tier, 50)
            
            # Prepare context
            context = {
                'user_name': user.username,
                'new_tier': new_tier.replace('_', ' ').title(),
                'daily_limit': daily_limit,
                'features': features,
                'dashboard_url': 'http://localhost:5173/dashboard'
            }
            
            # Send email
            result = await self.mailgun_service.send_templated_email(
                to_email=user.email,
                template_name='tier_upgrade',
                context=context,
                db=db,
                user_id=user_id,
                email_type='tier_update'
            )
            
            if result['success']:
                logger.info(f"✅ Tier upgrade email sent to {user.email}")
            else:
                logger.warning(f"⚠️ Failed to send tier upgrade email: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error sending tier upgrade email: {e}")
    
    async def send_password_reset_email(
        self,
        db: AsyncSession,
        user_id: str,
        reset_token: str
    ):
        """
        Send password reset email
        
        Args:
            db: Database session
            user_id: User ID
            reset_token: Reset token for email link
        """
        try:
            # Get user
            user = await db.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found for password reset")
                return
            
            # Check preferences - account updates
            can_send = await self.mailgun_service.check_email_preferences(
                db, user_id, 'account'
            )
            if not can_send:
                logger.info(f"User {user_id} has disabled account emails")
                return
            
            # Prepare context - NOTE: In production, send via secure link
            context = {
                'user_name': user.username,
                'reset_url': f'http://localhost:5173/reset-password?token={reset_token}',
            }
            
            # Send email
            result = await self.mailgun_service.send_templated_email(
                to_email=user.email,
                template_name='password_reset',
                context=context,
                db=db,
                user_id=user_id,
                email_type='account'
            )
            
            if result['success']:
                logger.info(f"✅ Password reset email sent to {user.email}")
            else:
                logger.warning(f"⚠️ Failed to send password reset email: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
    
    async def send_email_verification(
        self,
        db: AsyncSession,
        user_id: str,
        verification_token: str
    ):
        """
        Send email verification link
        
        Args:
            db: Database session
            user_id: User ID
            verification_token: Token for verification link
        """
        try:
            user = await db.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found for verification")
                return
            
            context = {
                'user_name': user.username,
                'verification_url': f'http://localhost:5173/verify-email?token={verification_token}',
            }
            
            result = await self.mailgun_service.send_templated_email(
                to_email=user.email,
                template_name='email_verification',
                context=context,
                db=db,
                user_id=user_id,
                email_type='account'
            )
            
            if result['success']:
                logger.info(f"✅ Verification email sent to {user.email}")
            else:
                logger.warning(f"⚠️ Failed to send verification email: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
    
    async def send_prediction_result_email(
        self,
        db: AsyncSession,
        user_id: str,
        matchup: str,
        prediction: str,
        result: str,
        confidence: float,
        sport: str,
        resolved_at: Optional[datetime] = None
    ):
        """
        Send email when prediction resolves with result
        
        Args:
            db: Database session
            user_id: User ID
            matchup: Game matchup string
            prediction: Prediction text
            result: Result (hit/miss/void)
            confidence: Prediction confidence 0-1
            sport: Sport key
            resolved_at: When prediction was resolved
        """
        try:
            # Get user
            user = await db.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return
            
            # Check preferences
            can_send = await self.mailgun_service.check_email_preferences(
                db, user_id, 'prediction_result'
            )
            if not can_send:
                logger.info(f"User {user_id} has disabled prediction result emails")
                return
            
            # Map result to label
            result_label = {
                'hit': '✓ HIT',
                'miss': '✗ MISS',
                'void': '- VOID',
                'push': '- PUSH'
            }.get(result, result.upper())
            
            # Prepare context
            context = {
                'user_name': user.username,
                'matchup': matchup,
                'prediction': prediction,
                'sport': sport,
                'result': result,
                'result_label': result_label,
                'confidence': int(confidence * 100),
                'dashboard_url': 'http://localhost:5173/dashboard'
            }
            
            # Send email
            send_result = await self.mailgun_service.send_templated_email(
                to_email=user.email,
                template_name='prediction_result',
                context=context,
                db=db,
                user_id=user_id,
                email_type='prediction_result'
            )
            
            if send_result['success']:
                logger.info(f"✅ Prediction result email sent to {user.email}")
            else:
                logger.warning(f"⚠️ Failed to send prediction result email: {send_result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error sending prediction result email: {e}")
    
    async def send_promotional_email(
        self,
        db: AsyncSession,
        user_ids: list,  # List of user IDs to send to
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ):
        """
        Send promotional/marketing emails to users
        Respects user preferences for promotional emails
        
        Args:
            db: Database session
            user_ids: List of user IDs
            subject: Email subject
            html_body: HTML content
            text_body: Plain text alternative
        """
        sent_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                # Check preferences
                can_send = await self.mailgun_service.check_email_preferences(
                    db, user_id, 'promotional'
                )
                if not can_send:
                    continue
                
                # Get user email
                user = await db.get(User, user_id)
                if not user:
                    continue
                
                # Send email
                result = await self.mailgun_service.send_email(
                    to_email=user.email,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    email_type='promotional',
                    user_id=user_id
                )
                
                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1
            
            except Exception as e:
                logger.warning(f"Error sending to user {user_id}: {e}")
                failed_count += 1
        
        logger.info(f"Promotional email campaign: {sent_count} sent, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}
