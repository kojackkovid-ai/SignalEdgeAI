from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, constr
from enum import Enum
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
    logger.debug(f"[Payment Auth] Authorization header present: {bool(authorization)}")
    
    if authorization is None:
        logger.warning("[Payment Auth] Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    auth_service = AuthService()
    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2:
            logger.warning(f"[Payment Auth] Invalid header format - expected 'Bearer <token>', got: {len(parts)} parts")
            raise ValueError("Invalid format")
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            logger.warning(f"[Payment Auth] Invalid scheme: {scheme}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        logger.debug(f"[Payment Auth] Decoding token: {token[:30]}...")
        user_id = auth_service._decode_token(token)
        logger.info(f"[Payment Auth] ✅ User extracted: {user_id}")
        return user_id
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"[Payment Auth] Invalid authorization header format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    except Exception as e:
        logger.error(f"[Payment Auth] ❌ Token decode error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


logger = logging.getLogger(__name__)
router = APIRouter()
# Lazy-loaded
auth_service = None

class PlanEnum(str, Enum):
    basic = "basic"
    pro = "pro"
    pro_plus = "pro_plus"
    elite = "elite"


class BillingCycleEnum(str, Enum):
    monthly = "monthly"
    annual = "annual"


class CreatePaymentIntentRequest(BaseModel):
    plan: PlanEnum
    billing_cycle: BillingCycleEnum
    idempotency_key: Optional[constr(min_length=1)] = None


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
        
        # Validate user ID format
        if not current_user_id or not isinstance(current_user_id, str):
            logger.error(f"[Payment] Invalid user ID format: {current_user_id} (type: {type(current_user_id)})")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get user with detailed error handling
        user = None
        user_lookup_error = None
        try:
            logger.info(f"[Payment] Looking up user by ID: {current_user_id}")
            user = await get_auth_service().get_user_by_id(db, current_user_id)
            
            if not user:
                logger.error(f"[Payment] ❌ User not found in database: {current_user_id}")
                raise HTTPException(
                    status_code=401,
                    detail="User session is invalid. Please log in again."
                )
            
            logger.info(f"[Payment] ✅ User found: {user.id} ({user.email}), tier: {user.subscription_tier}")
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"[Payment] ❌ Error getting user: {type(e).__name__}: {str(e)}", exc_info=True)
            error_detail = user_lookup_error or f"Failed to retrieve user information: {str(e)}"
            raise HTTPException(status_code=401, detail=error_detail)
        
        # Get pricing from tier_features.py for consistency and maintainability
        from app.models.tier_features import TierFeatures
        
        plan = request.plan.value.lower()
        cycle = request.billing_cycle.value.lower()
        
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
        if cycle not in [billing.value for billing in BillingCycleEnum]:
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
                },
                idempotency_key=request.idempotency_key,
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
    payment_intent_id: constr(min_length=10)
    plan: PlanEnum

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
        payment_info = await stripe_service.verify_payment(request.payment_intent_id)
        
        logger.info(f"[Payment] Payment verification result: %s", payment_info)
        
        if payment_info.get("status") != "succeeded":
            logger.error(f"[Payment] ❌ Payment verification failed for {request.payment_intent_id}")
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
                    error_message=payment_info.get('error', 'Payment verification failed')
                )
            except Exception as audit_error:
                logger.warning(f"[Payment] Failed to log payment failure: {audit_error}")
            
            raise HTTPException(
                status_code=400, 
                detail="Payment verification failed. Please contact support."
            )

        intent_metadata = payment_info.get('metadata', {}) or {}
        if intent_metadata.get('user_id') and intent_metadata.get('user_id') != current_user_id:
            logger.error("[Payment] Payment intent user mismatch: %s != %s", intent_metadata.get('user_id'), current_user_id)
            raise HTTPException(status_code=403, detail="Payment intent does not belong to the authenticated user.")

        if intent_metadata.get('plan') and intent_metadata.get('plan').lower() != request.plan.value.lower():
            logger.error("[Payment] Payment intent plan mismatch: %s != %s", intent_metadata.get('plan'), request.plan.value)
            raise HTTPException(status_code=400, detail="Payment intent metadata does not match requested plan.")
        
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
            try:
                payment_amount = TierFeatures.get_tier_price(plan_lower, 'monthly') or 0
            except Exception:
                payment_amount = 0
            
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


class WebhookEventLog(BaseModel):
    event_id: str
    event_type: str
    created: int
    processed_at: str
    status: str
    user_id: Optional[str] = None
    payment_intent_id: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    error_message: Optional[str] = None

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events (payment_intent.succeeded).
    Requires STRIPE_WEBHOOK_SECRET environment variable.
    This is the reliable fallback when the browser closes before confirm-payment is called.
    """
    from app.config import settings
    import time
    from datetime import datetime

    webhook_secret = settings.stripe_webhook_secret
    if not webhook_secret:
        logger.warning("[Webhook] STRIPE_WEBHOOK_SECRET not configured — endpoint disabled")
        raise HTTPException(status_code=503, detail="Webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        logger.error("[Webhook] Missing Stripe-Signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Parse payload for logging
    try:
        event_data = json.loads(payload)
        event_id = event_data.get("id")
        event_type = event_data.get("type")
        created = event_data.get("created")
    except json.JSONDecodeError:
        logger.error("[Webhook] Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Validate event structure
    if not event_id or not event_type:
        logger.error(f"[Webhook] Missing event_id or event_type in payload")
        raise HTTPException(status_code=400, detail="Invalid event structure")

    # Check for duplicate events (idempotency)
    try:
        # In a real implementation, you'd check a database/cache for processed event_ids
        # For now, we'll just log and continue
        logger.info(f"[Webhook] Processing event {event_id} of type {event_type}")
    except Exception as e:
        logger.warning(f"[Webhook] Event validation warning: {e}")

    try:
        event = stripe_service.verify_webhook_signature(payload, sig_header, webhook_secret)
    except Exception as e:
        logger.error(f"[Webhook] Signature verification failed for event {event_id}: {e}")
        # Log failed webhook attempt
        await _log_webhook_event(
            db, event_id, event_type, created, "signature_failed",
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Log successful signature verification
    await _log_webhook_event(db, event_id, event_type, created, "received")

    # Process different event types
    if event_type == "payment_intent.succeeded":
        success = await _process_payment_intent_succeeded(db, event, event_id)
        status = "processed" if success else "failed"
        await _log_webhook_event(
            db, event_id, event_type, created, status,
            user_id=event.get("data", {}).get("object", {}).get("metadata", {}).get("user_id"),
            payment_intent_id=event.get("data", {}).get("object", {}).get("id")
        )

    elif event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
        # Log failed/canceled payments
        payment_intent = event.get("data", {}).get("object", {})
        await _log_webhook_event(
            db, event_id, event_type, created, "logged",
            user_id=payment_intent.get("metadata", {}).get("user_id"),
            payment_intent_id=payment_intent.get("id"),
            error_message=event_type
        )

    else:
        # Log unhandled event types
        logger.info(f"[Webhook] Unhandled event type: {event_type}")
        await _log_webhook_event(db, event_id, event_type, created, "ignored")

    return {"status": "ok"}

async def _process_payment_intent_succeeded(db: AsyncSession, event: dict, event_id: str) -> bool:
    """Process payment_intent.succeeded event"""
    payment_intent = event["data"]["object"]
    metadata = payment_intent.get("metadata", {})
    user_id = metadata.get("user_id")
    plan = metadata.get("plan")
    payment_intent_id = payment_intent.get("id")

    # Validate required metadata
    if not user_id or not plan:
        logger.warning(f"[Webhook] Missing user_id/plan in metadata for {payment_intent_id}")
        return False

    # Validate plan
    valid_tiers = ["basic", "pro", "pro_plus", "elite"]
    plan_lower = plan.lower()
    if plan_lower not in valid_tiers:
        logger.warning(f"[Webhook] Invalid plan in metadata: {plan}")
        return False

    try:
        user = await get_auth_service().get_user_by_id(db, user_id)
        if not user:
            logger.error(f"[Webhook] User not found: {user_id}")
            return False

        if user.subscription_tier == plan_lower:
            logger.info(f"[Webhook] Tier already set to {plan_lower} for user {user_id} — idempotent skip")
            return True

        old_tier = user.subscription_tier
        user.subscription_tier = plan_lower
        await db.commit()
        logger.info(f"[Webhook] ✅ Tier updated via webhook: user={user_id} {old_tier}→{plan_lower}")

        # Audit log
        try:
            audit = await get_audit_service(db)
            await audit.log_action(
                user_id=user_id,
                action="tier_upgrade",
                resource="payment",
                resource_id=payment_intent_id,
                ip_address=None,
                user_agent=None,
                status="success",
                details={"old_tier": old_tier, "new_tier": plan_lower, "source": "stripe_webhook"},
            )
        except Exception as audit_err:
            logger.warning(f"[Webhook] Audit log failed: {audit_err}")

        return True

    except Exception as e:
        logger.error(f"[Webhook] Error processing payment_intent.succeeded: {e}", exc_info=True)
        return False

async def _log_webhook_event(
    db: AsyncSession,
    event_id: str,
    event_type: str,
    created: int,
    status: str,
    user_id: Optional[str] = None,
    payment_intent_id: Optional[str] = None,
    amount: Optional[int] = None,
    currency: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Log webhook event to database for audit trail"""
    try:
        # In a real implementation, you'd have a WebhookEvent model
        # For now, we'll just log to the audit service
        audit = await get_audit_service(db)
        await audit.log_action(
            user_id=user_id or "system",
            action="webhook_received",
            resource="stripe",
            resource_id=event_id,
            ip_address=None,
            user_agent=None,
            status=status,
            details={
                "event_type": event_type,
                "created": created,
                "payment_intent_id": payment_intent_id,
                "amount": amount,
                "currency": currency,
                "error_message": error_message
            },
        )
    except Exception as e:
        logger.warning(f"[Webhook] Failed to log webhook event: {e}")

    try:
        # Audit log the subscription change
        await audit_service.log_user_action(
            user_id=user_id,
            action="subscription_updated",
            resource_type="subscription",
            resource_id=payment_intent_id,
            ip_address=None,
            user_agent=None,
            status="success",
            details={"old_tier": old_tier, "new_tier": plan_lower, "source": "stripe_webhook"},
        )
    except Exception as audit_err:
        logger.warning(f"[Webhook] Audit log failed: {audit_err}")

    except Exception as e:
        logger.error(f"[Webhook] Error processing payment_intent.succeeded: {e}", exc_info=True)

    return {"status": "ok"}
