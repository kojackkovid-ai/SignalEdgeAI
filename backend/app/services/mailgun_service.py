"""
Mailgun Email Service
Handles all email sending through Mailgun API
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import Settings
from app.models.email_models import EmailLog, EmailPreferences, EmailTemplate

logger = logging.getLogger(__name__)


class MailgunService:
    """Service for sending emails via Mailgun"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.mailgun_api_key
        self.domain = settings.mailgun_domain
        self.sender = settings.mailgun_sender
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
        self.is_configured = bool(self.api_key and self.domain)
        
        if not self.is_configured:
            logger.warning("[MAILGUN] Mailgun not configured. Email sending will be disabled.")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        email_type: str = "transactional",
        user_id: Optional[str] = None,
        template_name: Optional[str] = None,
        context_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send email via Mailgun
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text alternative
            email_type: Type of email (prediction_result, daily_digest, etc)
            user_id: User ID for logging
            template_name: Template name used
            context_data: Data used in email (for logging)
        
        Returns:
            Dict with mailgun_id and status
        """
        if not self.is_configured:
            logger.warning(f"❌ Mailgun not configured. Cannot send email to {to_email}")
            return {'success': False, 'error': 'Mailgun not configured'}
        
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'from': self.sender,
                    'to': to_email,
                    'subject': subject,
                    'html': html_body,
                }
                
                if text_body:
                    data['text'] = text_body
                
                # Add tracking tags
                data['o:tracking'] = 'True'  # Enable open tracking
                data['o:tracking-clicks'] = 'true'  # Enable click tracking
                
                # Send via Mailgun
                async with session.post(
                    f"{self.base_url}/messages",
                    auth=aiohttp.BasicAuth('api', self.api_key),
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        message_id = response.get('id', '')
                        logger.info(f"✅ Email sent to {to_email} | Type: {email_type} | ID: {message_id}")
                        
                        # Log email send
                        if user_id:
                            try:
                                # Note: We'll log this in the database in a follow-up
                                pass
                            except Exception as e:
                                logger.warning(f"Failed to log email: {e}")
                        
                        return {
                            'success': True,
                            'mailgun_id': message_id,
                            'status': 'sent'
                        }
                    else:
                        error_text = await resp.text()
                        logger.error(f"❌ Mailgun error ({resp.status}): {error_text}")
                        return {
                            'success': False,
                            'error': f"Mailgun error: {resp.status}",
                            'details': error_text
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ Mailgun request timeout for {to_email}")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"❌ Error sending email to {to_email}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def send_templated_email(
        self,
        to_email: str,
        template_name: str,
        context: Dict[str, Any],
        db: AsyncSession,
        user_id: Optional[str] = None,
        email_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using a template with context variables
        
        Args:
            to_email: Recipient email
            template_name: Name of template to use
            context: Variables for template rendering
            db: Database session
            user_id: User ID
            email_type: Type of email
        
        Returns:
            Result dict
        """
        try:
            # Get template from database
            result = await db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.name == template_name,
                    EmailTemplate.is_active == True
                )
            )
            template = result.scalar_one_or_none()
            
            if not template:
                logger.warning(f"Template '{template_name}' not found")
                return {'success': False, 'error': f'Template {template_name} not found'}
            
            # Render template with context
            subject_template = Template(str(template.subject))  # type: ignore
            html_template = Template(str(template.html_body))  # type: ignore
            
            subject = subject_template.render(**context)
            html_body = html_template.render(**context)
            text_body = None
            
            template_text = getattr(template, 'text_body', None)
            if template_text:
                text_template = Template(str(template_text))  # type: ignore
                text_body = text_template.render(**context)
            
            # Send email
            result = await self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                email_type=email_type or template_name,
                user_id=user_id,
                template_name=template_name,
                context_data=context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending templated email: {e}")
            return {'success': False, 'error': str(e)}
    
    async def send_batch_emails(
        self,
        recipients: List[Dict[str, Any]],  # List of {email, context, ...}
        template_name: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Send emails to multiple recipients (batch)
        
        Args:
            recipients: List of dicts with email and context
            template_name: Template to use
            db: Database session
        
        Returns:
            List of results
        """
        results = []
        
        for recipient in recipients:
            result = await self.send_templated_email(
                to_email=recipient['email'],
                template_name=template_name,
                context=recipient.get('context', {}),
                db=db,
                user_id=recipient.get('user_id'),
                email_type=recipient.get('email_type')
            )
            results.append(result)
            
            # Rate limit: small delay between sends
            await asyncio.sleep(0.1)
        
        return results
    
    async def log_email(
        self,
        db: AsyncSession,
        user_id: str,
        recipient_email: str,
        subject: str,
        email_type: str,
        template_name: str,
        mailgun_message_id: Optional[str],
        context_data: Optional[Dict] = None
    ):
        """Log email in database for tracking"""
        try:
            log = EmailLog(
                user_id=user_id,
                recipient_email=recipient_email,
                subject=subject,
                email_type=email_type,
                template_name=template_name,
                mailgun_message_id=mailgun_message_id,
                context_data=context_data or {}
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to log email: {e}")
    
    def generate_unsubscribe_token(self, user_id: str) -> str:
        """Generate secure unsubscribe token"""
        token = secrets.token_urlsafe(32)
        return token
    
    async def check_email_preferences(
        self,
        db: AsyncSession,
        user_id: str,
        email_type: str
    ) -> bool:
        """
        Check if user wants to receive this type of email
        
        Args:
            db: Database session
            user_id: User ID
            email_type: Type of email (prediction_result, daily_digest, etc)
        
        Returns:
            True if user wants email, False otherwise
        """
        try:
            result = await db.execute(
                select(EmailPreferences).where(
                    EmailPreferences.user_id == user_id
                )
            )
            prefs = result.scalar_one_or_none()
            
            if not prefs:
                return True  # Default: send emails
            
            # Map email types to preference fields
            preference_map = {
                'prediction_result': getattr(prefs, 'prediction_results', True),
                'daily_digest': getattr(prefs, 'daily_digest', True),
                'weekly_digest': getattr(prefs, 'weekly_digest', True),
                'tier_update': getattr(prefs, 'tier_updates', True),
                'promotional': getattr(prefs, 'promotional', True),
                'account': getattr(prefs, 'account_updates', True),
                'feature': getattr(prefs, 'new_features', True),
                'milestone': getattr(prefs, 'accuracy_milestone', True),
            }
            
            return preference_map.get(email_type, True)  # type: ignore
            
        except Exception as e:
            logger.warning(f"Error checking email preferences: {e}")
            return True  # Default: send emails
    
    async def verify_email_address(
        self,
        db: AsyncSession,
        user_id: str,
        email: str
    ) -> bool:
        """Mark email as verified"""
        try:
            result = await db.execute(
                select(EmailPreferences).where(
                    EmailPreferences.user_id == user_id
                )
            )
            prefs = result.scalar_one_or_none()
            
            if prefs:
                prefs.verified = True  # type: ignore
                await db.commit()
                logger.info(f"✅ Email verified for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False
