import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy import for Stripe - it can hang on some systems
stripe = None
stripe_initialized = False
stripe_init_error = None

def _init_stripe():
    """Initialize Stripe lazily to avoid import hangs"""
    global stripe, stripe_initialized, stripe_init_error
    
    logger.debug("[Stripe] _init_stripe() called")
    logger.debug("[Stripe] Already initialized: %s", stripe_initialized)
    
    # If already initialized, return the result
    if stripe_initialized:
        if stripe_init_error:
            logger.error("[Stripe] Cached error being raised")
            raise stripe_init_error
        logger.debug("[Stripe] Returning cached stripe module")
        return stripe
    
    try:
        logger.info("[Stripe] Importing stripe module...")
        import stripe as stripe_module
        logger.info(f"[Stripe] ✅ Stripe module imported: {stripe_module}")
        
        # Get API key from settings (loads from .env file via pydantic_settings)
        logger.debug("[Stripe] Loading settings...")
        from app.config import settings
        logger.debug("[Stripe] Settings loaded")
        
        api_key = settings.stripe_secret_key
        
        logger.info("[Stripe] Stripe API key configured: %s", bool(api_key))
        
        if not api_key:
            error = ValueError("STRIPE_SECRET_KEY is not configured. Set it in environment or .env file")
            stripe_init_error = error
            stripe_initialized = True
            logger.error(f"[Stripe] ❌ Initialization failed: {error}")
            raise error
        
        # Set the API key on the stripe module
        logger.info("[Stripe] Setting API key on stripe module...")
        stripe_module.api_key = api_key
        logger.info("[Stripe] ✅ API key set successfully")
        
        # Store the module
        stripe = stripe_module
        stripe_initialized = True
        
        logger.info("[Stripe] ✅ Stripe initialized successfully with API key")
        return stripe
        
    except Exception as e:
        logger.error(f"[Stripe] ❌ Exception during initialization: {type(e).__name__}: {str(e)}", exc_info=True)
        # Store the error for subsequent calls
        if not stripe_init_error:
            stripe_init_error = e
        stripe_initialized = True
        logger.error(f"[Stripe] Caching error for future calls: {stripe_init_error}")
        raise

class StripeService:
    """Service for handling Stripe payment operations"""
    
    @staticmethod
    async def create_payment_intent(
        amount: int,
        currency: str = "usd",
        metadata: Dict[str, Any] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent
        
        Args:
            amount: Amount in cents (e.g., 2900 for $29.00)
            currency: Currency code (default: usd)
            metadata: Additional metadata to attach to the payment
            idempotency_key: Optional key to ensure idempotent request retries
            
        Returns:
            Payment intent object with client_secret
        """
        try:
            logger.info("[Stripe] create_payment_intent() called")
            logger.info(f"[Stripe] Amount: ${amount/100:.2f}, Currency: {currency}")
            
            logger.info("[Stripe] Initializing stripe module...")
            stripe_module = _init_stripe()
            logger.info(f"[Stripe] ✅ Stripe module initialized: {bool(stripe_module)}")
            
            logger.info("[Stripe] Creating payment intent...")
            stripe_args = {
                "amount": amount,
                "currency": currency,
                "metadata": metadata or {},
                "automatic_payment_methods": {"enabled": True},
            }
            if idempotency_key:
                stripe_args["idempotency_key"] = idempotency_key
                logger.info("[Stripe] Using idempotency key: %s", idempotency_key)
            intent = stripe_module.PaymentIntent.create(**stripe_args)
            logger.info(f"[Stripe] ✅ Payment intent created: {intent.id}")
            
            result = {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency
            }
            logger.info(f"[Stripe] ✅ Returning result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[Stripe] ❌ Error creating payment intent: {type(e).__name__}: {str(e)}", exc_info=True)
            raise Exception(f"Stripe payment error: {type(e).__name__}: {str(e)}")
    
    @staticmethod
    async def verify_payment(payment_intent_id: str) -> Dict[str, Any]:
        """
        Verify that a payment was successful
        
        Args:
            payment_intent_id: The Stripe payment intent ID
            
        Returns:
            A dictionary with payment status and metadata
        """
        try:
            stripe_module = _init_stripe()
            intent = stripe_module.PaymentIntent.retrieve(payment_intent_id)
            
            result = {
                "status": intent.status,
                "amount": getattr(intent, "amount", None),
                "currency": getattr(intent, "currency", None),
                "metadata": dict(getattr(intent, "metadata", {}) or {}),
            }
            if intent.status == "succeeded":
                logger.info("Payment verified: %s", payment_intent_id)
            else:
                logger.warning("Payment not successful: %s - Status: %s", payment_intent_id, intent.status)
            return result
                
        except Exception as e:
            logger.error("Error verifying payment: %s", e, exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "metadata": {}
            }
    
    @staticmethod
    async def create_customer(email: str, name: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a Stripe customer
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Stripe customer ID
        """
        try:
            stripe_module = _init_stripe()
                
            customer = stripe_module.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise Exception(f"Customer creation failed: {str(e)}")
    
    @staticmethod
    async def cancel_payment_intent(payment_intent_id: str) -> bool:
        """
        Cancel a payment intent
        
        Args:
            payment_intent_id: The Stripe payment intent ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            stripe_module = _init_stripe()
            # _init_stripe() now raises exception instead of returning None
                
            intent = stripe_module.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Cancelled payment intent: {payment_intent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling payment: {str(e)}")
            return False

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str, webhook_secret: str):
        """
        Verify an incoming Stripe webhook signature.

        Args:
            payload: Raw request body bytes
            sig_header: Value of the Stripe-Signature header
            webhook_secret: STRIPE_WEBHOOK_SECRET from environment

        Returns:
            Parsed Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If the signature is invalid
        """
        stripe_module = _init_stripe()
        return stripe_module.Webhook.construct_event(payload, sig_header, webhook_secret)


stripe_service = StripeService()
