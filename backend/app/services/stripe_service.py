import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Lazy import for Stripe - it can hang on some systems
stripe = None
stripe_initialized = False
stripe_init_error = None

def _init_stripe():
    """Initialize Stripe lazily to avoid import hangs"""
    global stripe, stripe_initialized, stripe_init_error
    
    logger.info("[Stripe] _init_stripe() called")
    logger.info(f"[Stripe] Already initialized: {stripe_initialized}")
    
    # If already initialized, return the result
    if stripe_initialized:
        logger.info(f"[Stripe] Returning cached result - stripe:{bool(stripe)}, error:{bool(stripe_init_error)}")
        if stripe_init_error:
            logger.error(f"[Stripe] Cached error being raised: {stripe_init_error}")
            raise stripe_init_error
        logger.info(f"[Stripe] Returning cached stripe module: {stripe}")
        return stripe
    
    try:
        logger.info("[Stripe] Importing stripe module...")
        import stripe as stripe_module
        logger.info(f"[Stripe] ✅ Stripe module imported: {stripe_module}")
        
        # Get API key from settings (loads from .env file via pydantic_settings)
        logger.info("[Stripe] Loading settings...")
        from app.config import settings
        logger.info(f"[Stripe] Settings loaded")
        
        api_key = settings.stripe_secret_key
        
        # Debug logging
        logger.info(f"[Stripe] API key configured: {bool(api_key)}")
        logger.info(f"[Stripe] API key length: {len(api_key) if api_key else 0}")
        if api_key:
            logger.info(f"[Stripe] API key starts with: {api_key[:30]}...")
        
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
    async def create_payment_intent(amount: int, currency: str = "usd", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a Stripe payment intent
        
        Args:
            amount: Amount in cents (e.g., 2900 for $29.00)
            currency: Currency code (default: usd)
            metadata: Additional metadata to attach to the payment
            
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
            intent = stripe_module.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {}
            )
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
    async def verify_payment(payment_intent_id: str) -> bool:
        """
        Verify that a payment was successful
        
        Args:
            payment_intent_id: The Stripe payment intent ID
            
        Returns:
            True if payment succeeded, False otherwise
        """
        try:
            stripe_module = _init_stripe()
            # _init_stripe() now raises exception instead of returning None
                
            intent = stripe_module.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == "succeeded":
                logger.info(f"Payment verified: {payment_intent_id}")
                return True
            else:
                logger.warning(f"Payment not successful: {payment_intent_id} - Status: {intent.status}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False
    
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

stripe_service = StripeService()
