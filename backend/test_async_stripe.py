import sys
import os
sys.path.insert(0, '.')

# Directly test stripe_service.create_payment_intent() method
print("Testing stripe_service.create_payment_intent() method...")

# First, let's manually run what the function does
try:
    from app.services.stripe_service import _init_stripe
    from app.config import settings
    
    print("1. Initializing stripe...")
    stripe_module = _init_stripe()
    print(f"   ✅ Stripe initialized")
    
    print("2. Creating payment intent...")
    intent = stripe_module.PaymentIntent.create(
        amount=2900,
        currency="usd",
        metadata={"test": "manual"},
        automatic_payment_methods={"enabled": True}
    )
    print(f"   ✅ Intent created: {intent.id}")
    
    print("\n3. Now testing through async function...")
    import asyncio
    from app.services.stripe_service import stripe_service
    
    async def run_test():
        result = await stripe_service.create_payment_intent(
            amount=2900,
            currency="usd",
            metadata={"test": "async"}
        )
        return result
    
    result = asyncio.run(run_test())
    print(f"   ✅ Result: {result.get('payment_intent_id')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
