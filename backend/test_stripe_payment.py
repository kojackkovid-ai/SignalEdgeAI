import sys
sys.path.insert(0, '.')

print("Testing Stripe payment intent creation...")

try:
    import stripe
    from app.config import settings
    
    # Initialize
    stripe.api_key = settings.stripe_secret_key
    print(f"✅ Stripe API key configured")
    
    # Try creating a payment intent
    print("\nAttempting to create payment intent...")
    intent = stripe.PaymentIntent.create(
        amount=2900,
        currency="usd",
        metadata={"test": "true"}
    )
    print(f"✅ Payment intent created successfully!")
    print(f"   ID: {intent.id}")
    print(f"   Status: {intent.status}")
    print(f"   Client Secret: {intent.client_secret[:50]}...")
    
except stripe.error.AuthenticationError as e:
    print(f"❌ Authentication Error: {e}")
    print(f"   This means the Stripe API key is invalid")
except stripe.error.InvalidRequestError as e:
    print(f"❌ Invalid Request Error: {e}")
except stripe.error.StripeError as e:
    print(f"❌ Stripe Error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
