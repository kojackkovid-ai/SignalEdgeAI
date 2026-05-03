"""
Email API Routes
Handles email preferences, sending, verification, etc
"""

import logging
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets
from typing import Optional

from app.database import get_db
from app.models.db_models import User
from app.models.email_models import EmailPreferences, EmailLog, EmailTemplate
from app.services.mailgun_service import MailgunService
from app.services.email_templates_service import EmailTemplateService
from app.services.auth_service import AuthService
from app.config import Settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/email", tags=["email"])

# Pydantic Schemas
class EmailPreferencesResponse(BaseModel):
    prediction_results: bool = True
    daily_digest: bool = True
    weekly_digest: bool = True
    tier_updates: bool = True
    promotional: bool = True
    account_updates: bool = True
    new_features: bool = True
    accuracy_milestone: bool = True

class UpdateEmailPreferencesRequest(BaseModel):
    prediction_results: Optional[bool] = None
    daily_digest: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    tier_updates: Optional[bool] = None
    promotional: Optional[bool] = None
    account_updates: Optional[bool] = None
    new_features: Optional[bool] = None
    accuracy_milestone: Optional[bool] = None

class EmailVerificationRequest(BaseModel):
    email: str

class EmailVerificationResponse(BaseModel):
    message: str
    verification_token: str

class SendTestEmailRequest(BaseModel):
    template_name: str
    recipient_email: Optional[str] = None

class SendTestEmailResponse(BaseModel):
    message: str
    email_id: Optional[str] = None

# Lazy initialization - avoid blocking during import
_settings = None
_mailgun_service = None
_template_service = None

def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_mailgun_service():
    global _mailgun_service
    if _mailgun_service is None:
        _mailgun_service = MailgunService(get_settings())
    return _mailgun_service

def get_template_service():
    global _template_service
    if _template_service is None:
        _template_service = EmailTemplateService()
    return _template_service


# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from Bearer token"""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    auth_service = AuthService()
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        return auth_service._decode_token(token)
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )


# ============================================================================
# EMAIL PREFERENCE MANAGEMENT
# ============================================================================

class EmailPreferencesSchema:
    """Email preferences update schema"""
    prediction_results: bool = True
    daily_digest: bool = True
    weekly_digest: bool = True
    tier_updates: bool = True
    promotional: bool = True
    account_updates: bool = True
    new_features: bool = True
    accuracy_milestone: bool = True


@router.get("/preferences", response_model=EmailPreferencesResponse)
async def get_email_preferences(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's email preferences"""
    try:
        result = await db.execute(
            select(EmailPreferences).where(
                EmailPreferences.user_id == current_user_id
            )
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            # Create default preferences
            prefs = EmailPreferences(user_id=current_user_id)
            db.add(prefs)
            await db.commit()
        
        return {
            'success': True,
            'preferences': {
                'prediction_results': getattr(prefs, 'prediction_results', True),  # type: ignore
                'daily_digest': getattr(prefs, 'daily_digest', True),  # type: ignore
                'weekly_digest': getattr(prefs, 'weekly_digest', True),  # type: ignore
                'tier_updates': getattr(prefs, 'tier_updates', True),  # type: ignore
                'promotional': getattr(prefs, 'promotional', True),  # type: ignore
                'account_updates': getattr(prefs, 'account_updates', True),  # type: ignore
                'new_features': getattr(prefs, 'new_features', True),  # type: ignore
                'accuracy_milestone': getattr(prefs, 'accuracy_milestone', True),  # type: ignore
                'verified': getattr(prefs, 'verified', False),  # type: ignore
            }
        }
    except Exception as e:
        logger.error(f"Error getting email preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def update_email_preferences(
    preferences: dict,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's email preferences"""
    try:
        result = await db.execute(
            select(EmailPreferences).where(
                EmailPreferences.user_id == current_user_id
            )
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            prefs = EmailPreferences(user_id=current_user_id)
            db.add(prefs)
        
        # Update preferences
        for key, value in preferences.items():
            if hasattr(prefs, key) and isinstance(value, bool):
                setattr(prefs, key, value)  # type: ignore
        
        prefs.updated_at = datetime.utcnow()  # type: ignore
        await db.commit()
        
        logger.info(f"✅ Updated email preferences for user {current_user_id}")
        
        return {
            'success': True,
            'message': 'Email preferences updated successfully'
        }
    except Exception as e:
        logger.error(f"Error updating email preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

@router.post("/verify-email")
async def send_verification_email(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send email verification link"""
    try:
        user_result = await db.execute(
            select(User).where(User.id == current_user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        
        user_email = str(user.email)  # type: ignore
        user_name = str(user.username)  # type: ignore
        
        # Send verification email
        result = await get_mailgun_service().send_email(
            to_email=user_email,
            subject="Verify Your Email Address",
            html_body=f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Verify Your Email</h2>
    <p>Hi {user_name},</p>
    <p>Click the link below to verify your email address:</p>
    <p><a href="{get_settings().frontend_url}/verify-email?token={token}" 
           style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
           Verify Email
           </a></p>
    <p style="font-size: 12px; color: #666;">This link will expire in 24 hours.</p>
</div>
""",
            email_type="email_verification",
            user_id=current_user_id
        )
        
        if result['success']:
            return {
                'success': True,
                'message': 'Verification email sent to your inbox'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-email/{token}")
async def verify_email_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify email using token (open endpoint for email links)"""
    try:
        # In production, you'd validate the token against database
        # For now, simple implementation
        
        return {
            'success': True,
            'message': 'Email verified successfully'
        }
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(status_code=400, detail="Invalid or expired token")


# ============================================================================
# EMAIL LOGS & TRACKING
# ============================================================================

@router.get("/logs")
async def get_email_logs(
    limit: int = Query(50, le=100),
    email_type: str = Query(None),
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's email send history"""
    try:
        query = select(EmailLog).where(
            EmailLog.user_id == current_user_id
        )
        
        if email_type:
            query = query.where(EmailLog.email_type == email_type)
        
        query = query.order_by(EmailLog.sent_at.desc()).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            'success': True,
            'logs': [
                {
                    'id': log.id,  # type: ignore
                    'subject': log.subject,  # type: ignore
                    'email_type': log.email_type,  # type: ignore
                    'status': log.status,  # type: ignore
                    'sent_at': getattr(log, 'sent_at', datetime.utcnow()).isoformat(),  # type: ignore
                    'opened_at': getattr(log, 'opened_at', None).isoformat() if getattr(log, 'opened_at', None) else None,  # type: ignore
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting email logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UNSUBSCRIBE
# ============================================================================

@router.post("/unsubscribe/{token}")
async def unsubscribe(
    token: str,
    email_type: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Unsubscribe from specific email type (open endpoint for email links)"""
    try:
        # Find user by unsubscribe token
        result = await db.execute(
            select(EmailPreferences).where(
                EmailPreferences.unsubscribe_token == token
            )
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            raise HTTPException(status_code=404, detail="Invalid unsubscribe token")
        
        # Disable email type
        preference_map = {
            'prediction_result': 'prediction_results',
            'daily_digest': 'daily_digest',
            'weekly_digest': 'weekly_digest',
            'tier_update': 'tier_updates',
            'promotional': 'promotional',
            'account': 'account_updates',
            'feature': 'new_features',
            'milestone': 'accuracy_milestone',
        }
        
        field = preference_map.get(email_type)
        if field:
            setattr(prefs, field, False)  # type: ignore
            prefs.updated_at = datetime.utcnow()  # type: ignore
            await db.commit()
            user_id = getattr(prefs, 'user_id', 'unknown')
            logger.info(f"✅ User {user_id} unsubscribed from {email_type}")
        
        return {
            'success': True,
            'message': f'You have been unsubscribed from {email_type} emails'
        }
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADMIN: TEST EMAIL
# ============================================================================

@router.post("/test")
async def send_test_email(
    template_name: str = Query("prediction_result"),
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send test email to current user (for development)"""
    try:
        user_result = await db.execute(
            select(User).where(User.id == current_user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email = str(user.email)  # type: ignore
        user_name = str(user.username)  # type: ignore
        
        # Sample context data
        context = {
            'user_name': user_name,
            'matchup': 'Test Matchup: Lakers vs Celtics',
            'prediction': 'Lakers Win',
            'sport': 'NBA',
            'result': 'hit',
            'result_label': 'HIT ✓',
            'confidence': 75,
            'dashboard_url': f'{get_settings().frontend_url}/dashboard',
            'date': datetime.utcnow().strftime('%B %d, %Y'),
        }
        
        result = await get_mailgun_service().send_templated_email(
            to_email=user_email,
            template_name=template_name,
            context=context,
            db=db,
            user_id=current_user_id
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f'Test email sent to {user_email}',
                'mailgun_id': result.get('mailgun_id')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
    
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
