from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.stripe_service import stripe_service
from app.services.audit_service import get_audit_service
from app.utils.endpoint_rate_limiter import rate_limit
import logging
import os
from typing import Optional


# Lazy-initialized services to prevent import hangs
_auth_service = None

def get_auth_service():
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# Dependency function to extract current user from Authorization header
async def get_current_user(authorization: Optional[str] = Header(None, description="Bearer token")) -> str:
    """Extract user ID from Bearer token in Authorization header"""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    auth_service = AuthService()
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        return auth_service._decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )


logger = logging.getLogger(__name__)
router = APIRouter()
# Lazy-loaded
auth_service = None

class CreatePaymentIntentRequest(BaseModel):
    plan: str
    billing_cycle: str

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
@rate_limit("payment:create_intent", requests=10, window=60)  # 10 requests per minute
async def create_payment_intent(
    http_request: Request,
    request: CreatePaymentIntentRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe payment intent for subscription upgrade with audit logging
    """
    try:
        logger.info(f"[Payment] Starting payment intent creation for user {current_user_id}")
        logger.info(f"[Payment] Request - plan: {request.plan}, cycle: {request.billing_cycle}")
        
        # Get user
        try:
            user = await get_auth_service().get_user_by_id(db, current_user_id)
            if not user:
                logger.error(f"[Payment] User not found: {current_user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            logger.info(f"[Payment] User found: {user.id} ({user.email}), current tier: {user.subscription_tier}")
        except Exception as e:
            logger.error(f"[Payment] ❌ Error getting user: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")
        
        # Get pricing from tier_features.py for consistency and maintainability
        from app.models.tier_features import TierFeatures
        
        plan = request.plan.lower()
        cycle = request.billing_cycle.lower()
        
        # Validate plan
        try:
            all_tiers = TierFeatures.all_tiers()
            logger.info(f"[Payment] Available tiers: {all_tiers}")
        except Exception as e:
            logger.error(f"[Payment] ❌ Error getting tier list: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to load tier configuration: {str(e)}")
        
        if plan not in all_tiers:
            logger.error(f"[Payment] Invalid plan: {plan}")
            raise HTTPException(status_code=400, detail=f"Invalid plan '{plan}'. Must be one of: {', '.join(all_tiers)}")
        
        # Validate billing cycle
        if cycle not in ['monthly', 'annual']:
            logger.error(f"[Payment] Invalid cycle: {cycle}")
            raise HTTPException(status_code=400, detail="Invalid billing cycle. Must be 'monthly' or 'annual'")
        
        # Get pricing from tier config (in cents)
        try:
            amount = TierFeatures.get_tier_price(plan, cycle)
            if not amount:
                logger.error(f"[Payment] Could not determine price for {plan} ({cycle})")
                raise HTTPException(status_code=400, detail=f"Invalid plan/cycle combination: {plan}/{cycle}")
            
            logger.info(f"[Payment] Amount calculated: ${amount/100:.2f} for {plan} ({cycle}) - from tier_features.py")
        except Exception as e:
            logger.error(f"[Payment] ❌ Error getting tier price: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to calculate price: {str(e)}")
        
        # Create payment intent - StripeService handles Stripe initialization
        try:
            logger.info(f"[Payment] Calling stripe_service.create_payment_intent()")
            result = await stripe_service.create_payment_intent(
                amount=amount,
                currency="usd",
                metadata={
                    "user_id": str(user.id),
                    "user_email": user.email,
                    "plan": plan,
                    "billing_cycle": cycle
                }
            )
            
            logger.info(f"[Payment] ✅ Payment intent created successfully")
            logger.info(f"[Payment] Payment Intent ID: {result['payment_intent_id']}")
            logger.info(f"[Payment] Client Secret (first 30 chars): {result['client_secret'][:30]}...")
        except Exception as e:
            logger.error(f"[Payment] ❌ Error creating Stripe payment intent: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Payment service error: {str(e)[:200]}")
        
        return PaymentIntentResponse(
            client_secret=result["client_secret"],
            payment_intent_id=result["payment_intent_id"],
            amount=result["amount"]
        )
        
    except HTTPException as http_err:
        logger.error(f"[Payment] HTTPException: {http_err.detail}")
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Payment] ❌ Main exception during payment intent creation: {error_msg}", exc_info=True)
        logger.error(f"[Payment] Full exception type: {type(e).__name__}")
        logger.error(f"[Payment] Full exception: {repr(e)}")
        
        # ALWAYS show the actual error for debugging
        error_detail = f"{type(e).__name__}: {error_msg[:200]}"
        logger.error(f"[Payment] Raising error to client: {error_detail}")
        raise HTTPException(
            status_code=503, 
            detail=error_detail
        )

class ConfirmPaymentRequest(BaseModel):
    payment_intent_id: str
    plan: str

@router.post("/confirm-payment")
async def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify payment and upgrade user subscription with audit logging
    """
    try:
        logger.info(f"[Payment] Starting payment confirmation for user {current_user_id}")
        logger.info(f"[Payment] Payment Intent ID: {request.payment_intent_id}")
        logger.info(f"[Payment] Plan: {request.plan}")
        
        # Verify payment with Stripe
        logger.info(f"[Payment] Verifying payment with Stripe...")
        payment_verified = await stripe_service.verify_payment(request.payment_intent_id)
        
        logger.info(f"[Payment] Payment verification result: {payment_verified}")
        
        if not payment_verified:
            logger.error(f"[Payment] ❌ Payment verification failed for {request.payment_intent_id}")
            # Log failed payment
            try:
                audit = await get_audit_service(db)
                await audit.log_action(
                    user_id=current_user_id,
                    action='payment_failed',
                    resource='payment',
                    resource_id=request.payment_intent_id,
                    ip_address=None,
                    user_agent=None,
                    status='failure',
                    error_message='Payment verification failed'
                )
            except Exception as audit_error:
                logger.warning(f"[Payment] Failed to log payment failure: {audit_error}")
            
            raise HTTPException(
                status_code=400, 
                detail="Payment verification failed. Please contact support."
            )
        
        logger.info(f"[Payment] Getting user {current_user_id} ...")
        # Get user
        user = await get_auth_service().get_user_by_id(db, current_user_id)
        if not user:
            logger.error(f"[Payment] User not found: {current_user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"[Payment] User found: {user.email}, current tier: {user.subscription_tier}")
        
        # Validate tier
        valid_tiers = ['basic', 'pro', 'pro_plus', 'elite']
        plan_lower = request.plan.lower()
        if plan_lower not in valid_tiers:
            logger.error(f"[Payment] Invalid tier: {plan_lower}")
            raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}")
        
        logger.info(f"[Payment] Updating user tier from {user.subscription_tier} to {plan_lower}...")
        
        # Update user tier
        old_tier = user.subscription_tier
        user.subscription_tier = plan_lower
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"[Payment] ✅ User tier updated successfully to {user.subscription_tier}")
        
        # Log successful payment and tier change
        try:
            audit = await get_audit_service(db)
            
            # Log payment
            payment_amount = {
                'basic': {'monthly': 1200, 'annual': 12000},
                'pro': {'monthly': 2900, 'annual': 29000},
                'pro_plus': {'monthly': 4900, 'annual': 49000},
                'elite': {'monthly': 9900, 'annual': 99000}
            }.get(plan_lower, {}).get('monthly', 0)
            
            await audit.log_action(
                user_id=current_user_id,
                action='payment_completed',
                resource='payment',
                resource_id=request.payment_intent_id,
                details={
                    'amount_cents': payment_amount,
                    'plan': plan_lower,
                    'payment_intent_id': request.payment_intent_id
                },
                ip_address=None,
                user_agent=None,
                status='success'
            )
            
            # Log tier upgrade
            if old_tier != plan_lower:
                await audit.log_action(
                    user_id=current_user_id,
                    action='tier_upgrade',
                    resource='subscription',
                    resource_id=str(user.id),
                    details={
                        'from_tier': old_tier,
                        'to_tier': plan_lower,
                        'payment_intent_id': request.payment_intent_id
                    },
                    ip_address=None,
                    user_agent=None,
                    status='success'
                )
            
            logger.info(f"[Payment] Audit logs created successfully")
        except Exception as audit_error:
            logger.warning(f"[Payment] Failed to log payment/tier change (non-fatal): {audit_error}")
            # Don't fail the request if audit logging fails
        
        logger.info(f"[Payment] ✅ Payment and tier upgrade complete for user {current_user_id}")
        
        return {
            "success": True,
            "message": "Subscription upgraded successfully",
            "new_tier": user.subscription_tier,
            "payment_intent_id": request.payment_intent_id
        }
    
    except HTTPException as http_err:
        logger.error(f"[Payment] HTTPException: {http_err.detail}")
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Payment] ❌ Exception during payment confirmation: {error_msg}", exc_info=True)
        
        if "connection" in error_msg.lower() or "database" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Database error. Please try again later."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Payment confirmation failed: {error_msg}"
            )
