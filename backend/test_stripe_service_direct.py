#!/usr/bin/env python3
"""Direct test of StripeService to confirm the fix works"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_stripe_service():
    """Test the StripeService directly"""
    print("\n" + "=" * 70)
    print("STRIPE SERVICE DIRECT TEST")
    print("=" * 70)
    
    try:
        # Import the fixed stripe service
        from app.services.stripe_service import stripe_service
        from app.config import settings
        
        print("\n1. Verifying Stripe configuration...")
        if settings.stripe_secret_key:
            masked = settings.stripe_secret_key[:20] + "..." + settings.stripe_secret_key[-10:]
            print(f"   ✓ STRIPE_SECRET_KEY configured: {masked}")
        else:
            print(f"   ✗ STRIPE_SECRET_KEY is not configured!")
            return False
            
        print("\n2. Testing payment intent creation via StripeService...")
        
        result = await stripe_service.create_payment_intent(
            amount=2900,
            currency="usd",
            metadata={
                "user_id": "test_user_123",
                "plan": "pro",
                "billing_cycle": "monthly"
            }
        )
        
        if result and "client_secret" in result:
            print(f"   ✓ Payment intent created successfully")
            print(f"      Payment Intent ID: {result['payment_intent_id']}")
            print(f"      Amount: ${result['amount']/100:.2f}")
            print(f"      Currency: {result['currency']}")
            print(f"      Client Secret: {result['client_secret'][:50]}...")
            success = True
        else:
            print(f"   ✗ Payment intent creation returned invalid result")
            print(f"      Result: {result}")
            success = False
            
        print("\n" + "=" * 70)
        if success:
            print("✓ PAYMENT INITIALIZATION FIX VERIFIED")
            print("\nThe issue has been resolved:")
            print("  • Stripe API key is properly loaded from settings")
            print("  • Payment intents are successfully created")
            print("  • User tier upgrades should now work correctly")
        else:
            print("✗ PAYMENT INITIALIZATION TEST FAILED")
        print("=" * 70)
        
        return success
        
    except Exception as e:
        print(f"\n✗ Error during test: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_stripe_service())
    sys.exit(0 if success else 1)
