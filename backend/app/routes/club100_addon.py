"""
Club 100 $4.99 One-Time Unlock Implementation
Allows users to purchase Club 100 access as a one-time $4.99 add-on
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.stripe_service import stripe_service
from app.models.db_models import User
from sqlalchemy import select
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/club100", tags=["Club 100"])

# ============= MODELS =============

class Club100UnlockRequest(BaseModel):
    currency: str = "usd"
    country: Optional[str] = None

class Club100UnlockResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str

class Club100StatusResponse(BaseModel):
    is_club_100_unlocked: bool
    unlock_price: float  # $4.99
    unlock_timestamp: Optional[str]
    can_follow_club_100: bool

# ============= PAYMENT ENDPOINT =============

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from Bearer token"""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    auth_service = AuthService()
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        return auth_service._decode_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

@router.post("/unlock", response_model=Club100UnlockResponse)
async def create_club100_unlock_payment(
    request: Club100UnlockRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create payment intent for Club 100 $4.99 one-time unlock
    
    This endpoint:
    - Creates a Stripe payment intent for $4.99
    - Includes user and unlocking details in metadata
    - Returns client_secret for frontend payment processing
    """
    try:
        logger.info(f"[Club100] Unlock request from user: {current_user_id}")
        
        # Verify user exists
        query = select(User).where(User.id == current_user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error(f"[Club100] User not found: {current_user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already unlocked
        if user.club_100_unlocked:
            logger.warning(f"[Club100] User already has Club 100: {current_user_id}")
            raise HTTPException(
                status_code=400,
                detail="Club 100 is already unlocked on this account"
            )
        
        # Club 100 pricing
        CLUB_100_PRICE_CENTS = 499  # $4.99
        CLUB_100_PRICE_USD = 4.99
        
        logger.info(f"[Club100] Creating payment intent for ${CLUB_100_PRICE_USD}")
        
        # Create Stripe payment intent
        result = await stripe_service.create_payment_intent(
            amount=CLUB_100_PRICE_CENTS,
            currency=request.currency.lower() or "usd",
            metadata={
                "user_id": str(user.id),
                "user_email": user.email,
                "product_type": "club_100_unlock",
                "product_name": "Club 100 One-Time Unlock",
                "price": f"${CLUB_100_PRICE_USD}"
            }
        )
        
        logger.info(f"[Club100] ✅ Payment intent created: {result['payment_intent_id']}")
        
        return Club100UnlockResponse(
            client_secret=result["client_secret"],
            payment_intent_id=result["payment_intent_id"],
            amount=result["amount"],
            currency=result["currency"]
        )
        
    except HTTPException as http_err:
        logger.error(f"[Club100] HTTP Error: {http_err.detail}")
        raise
    except Exception as e:
        logger.error(f"[Club100] ❌ Error creating payment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Payment creation failed: {str(e)[:100]}")

# ============= VERIFICATION ENDPOINT =============

@router.post("/verify-unlock/{payment_intent_id}")
async def verify_club100_unlock(
    payment_intent_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify Club 100 payment and unlock access
    
    Called after successful Stripe payment to:
    - Verify payment was successful
    - Mark user's club_100_unlocked as True
    - Add unlock timestamp
    """
    try:
        logger.info(f"[Club100] Verifying unlock for user: {current_user_id}")
        
        # Verify payment with Stripe
        logger.info(f"[Club100] Verifying payment intent: {payment_intent_id}")
        payment_verified = await stripe_service.verify_payment(payment_intent_id)
        
        if not payment_verified:
            logger.warning(f"[Club100] Payment verification failed: {payment_intent_id}")
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        logger.info(f"[Club100] ✅ Payment verified!")
        
        # Get user and unlock Club 100
        query = select(User).where(User.id == current_user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Unlock Club 100
        user.club_100_unlocked = True
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"[Club100] ✅ Club 100 unlocked for user: {current_user_id}")
        
        return {
            "success": True,
            "message": "Club 100 access unlocked!",
            "club_100_unlocked": True,
            "user_id": str(current_user_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Club100] ❌ Error verifying unlock: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============= STATUS ENDPOINT =============

@router.get("/status", response_model=Club100StatusResponse)
async def get_club100_status(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Club 100 unlock status for current user
    
    Returns:
    - is_club_100_unlocked: Whether user has Club 100 unlocked
    - unlock_price: $4.99
    - unlock_timestamp: When Club 100 was unlocked (if applicable)
    - can_follow_club_100: Whether user can follow Club 100 picks
    """
    try:
        query = select(User).where(User.id == current_user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Determine if user can follow Club 100
        # Starter tier cannot access Club 100
        can_follow = user.subscription_tier != 'starter' or user.club_100_unlocked
        
        return Club100StatusResponse(
            is_club_100_unlocked=user.club_100_unlocked,
            unlock_price=4.99,
            unlock_timestamp=user.club_100_unlock_timestamp.isoformat() if user.club_100_unlock_timestamp else None,
            can_follow_club_100=can_follow
        )
        
    except Exception as e:
        logger.error(f"[Club100] Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= ADMIN ENDPOINT =============

@router.post("/admin/unlock/{user_id}")
async def admin_unlock_club100(
    user_id: str,
    admin_token: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to manually unlock Club 100 for a user
    (For testing or support purposes)
    """
    # Verify admin token
    admin_secret = os.getenv("ADMIN_SECRET_KEY", "dev-admin-key")
    if admin_token != admin_secret:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.club_100_unlocked = True
        await db.commit()
        
        logger.info(f"[Club100] Admin unlocked Club 100 for user: {user_id}")
        
        return {
            "success": True,
            "message": f"Club 100 unlocked for user {user_id}",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"[Club100] Admin unlock error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
