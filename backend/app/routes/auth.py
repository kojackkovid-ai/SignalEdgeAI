from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.audit_service import get_audit_service
from app.utils.endpoint_rate_limiter import rate_limit
from pydantic import BaseModel, field_validator
import logging
import re


# Lazy-initialized services to prevent import hangs
_auth_service = None

def get_auth_service():
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


router = APIRouter()
# Lazy-loaded
auth_service = None
logger = logging.getLogger(__name__)

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if not v or not isinstance(v, str):
            raise ValueError("Email must be a valid string")
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Auto-truncate to 72 bytes for bcrypt BEFORE validation, then validate minimum 6 characters"""
        if not isinstance(v, str):
            raise ValueError("Password must be a string")
        
        # Validate minimum length first
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        # Auto-truncate to bcrypt limit (72 bytes)
        if len(v) > 72:
            v = v[:72]
        
        return v

class LoginRequest(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if not v or not isinstance(v, str):
            raise ValueError("Email must be a valid string")
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Auto-truncate to 72 bytes for bcrypt"""
        if not isinstance(v, str):
            raise ValueError("Password must be a string")
        
        # Auto-truncate to bcrypt limit (72 bytes)
        if len(v) > 72:
            v = v[:72]
        
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    subscription_tier: str

@router.post("/register", response_model=TokenResponse)
@rate_limit("auth:register", requests=5, window=900)  # 5 requests per 15 minutes
async def register(
    http_request: Request,
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Register new user"""
    try:
        # Use full_name if provided, otherwise use username, otherwise generate from email
        username = request.full_name or request.username or request.email.split('@')[0]
        
        user = await get_auth_service().register_user(
            db=db,
            email=request.email,
            password=request.password,
            username=username
        )
        
        logger.info(f"User registered: {user.id}")
        
        token = get_auth_service().create_access_token(data={"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=str(user.id),
            subscription_tier=user.subscription_tier
        )
        
    except ValueError as e:
        # Log failed signup attempt
        try:
            # TEMPORARILY DISABLE AUDIT LOGGING FOR DEBUGGING
            # audit = await get_audit_service(db)
            # await audit.log_action(
            #     user_id='unknown',
            #     action='signup',
            #     resource='user',
            #     ip_address=http_request.client.host if (http_request and http_request.client) else None,
            #     user_agent=http_request.headers.get('user-agent') if http_request else None,
            #     status='failure',
            #     error_message=str(e)
            # )
            pass
        except Exception as audit_error:
            logger.warning(f"Failed to log signup attempt: {audit_error}")
        
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
@rate_limit("auth:login", requests=10, window=900)  # 10 requests per 15 minutes
async def login(
    http_request: Request,
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Login user"""
    try:
        logger.info(f"Login attempt for email: {request.email}")
        user = await get_auth_service().authenticate_user(
            db=db,
            email=request.email,
            password=request.password
        )
        if not user:
            logger.warning(f"Login failed - user not found or invalid password: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Log successful login
        try:
            audit = await get_audit_service(db)
            await audit.log_action(
                user_id=str(user.id),
                action='login',
                resource='user',
                resource_id=str(user.id),
                ip_address=None,
                user_agent=None,
                status='success'
            )
            logger.info(f"Login logged for user: {user.id}")
        except Exception as audit_error:
            logger.warning(f"Failed to log login for user {user.id}: {audit_error}")
            # Don't fail the request if audit logging fails
        
        token = get_auth_service().create_access_token(data={"sub": str(user.id)})
        logger.info(f"Login successful for user: {user.id}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=str(user.id),
            subscription_tier=user.subscription_tier
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log login error
        try:
            audit = await get_audit_service(db)
            await audit.log_action(
                user_id='unknown',
                action='login',
                resource='user',
                ip_address=None,
                user_agent=None,
                status='error',
                error_message=str(e)
            )
        except Exception as audit_error:
            logger.warning(f"Failed to log login error: {audit_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout(
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """Logout user"""
    logger.info(f"User {current_user_id} logged out")
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token(current_user_id: str = Depends(lambda: get_auth_service().get_current_user())):
    """Refresh access token"""
    token = get_auth_service().create_access_token(data={"sub": current_user_id})
    return {
        "access_token": token,
        "token_type": "bearer"
    }


class ForgotPasswordRequest(BaseModel):
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if not v or not isinstance(v, str):
            raise ValueError("Email must be a valid string")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


@router.post("/forgot-password")
@rate_limit("auth:forgot_password", requests=5, window=900)  # 5 requests per 15 minutes
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email"""
    try:
        # First check if user exists
        from sqlalchemy import select
        from app.models.db_models import User
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalars().first()
        
        if user:
            # User exists - generate token and send email
            token = await get_auth_service().create_password_reset_token(db, request.email)
            
            # Send reset email via Mailgun
            from app.services.email_integration_service import EmailIntegrationService
            from app.services.mailgun_service import MailgunService
            from app.config import settings
            
            mailgun = MailgunService(settings)
            email_service = EmailIntegrationService(settings, mailgun)
            
            await email_service.send_password_reset_email(
                db=db,
                user_id=user.id,
                reset_token=token
            )
            logger.info(f"Password reset email sent to {request.email}")
        else:
            logger.warning(f"Password reset requested for non-existent user: {request.email}")
        
        # Return success regardless (security: don't reveal if email exists)
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password reset request"
        )


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password"""
        if not isinstance(v, str):
            raise ValueError("Password must be a string")
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(v) > 72:
            v = v[:72]
        return v


@router.post("/reset-password")
@rate_limit("auth:reset_password", requests=5, window=900)  # 5 requests per 15 minutes
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        await get_auth_service().reset_password(db, request.token, request.new_password)
        logger.info("Password reset successfully")
        return {"message": "Password reset successfully"}
    except ValueError as e:
        logger.warning(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password"
        )
