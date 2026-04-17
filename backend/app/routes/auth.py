from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.audit_service import get_audit_service
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
async def register(
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
async def login(
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
