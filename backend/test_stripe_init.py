#!/usr/bin/env python3
"""Debug Stripe initialization"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("STRIPE INITIALIZATION DIAGNOSTIC")
print("=" * 60)

# Test 1: Check environment variable
print("\n1. Checking STRIPE_SECRET_KEY in environment...")
stripe_key = os.getenv("STRIPE_SECRET_KEY")
if stripe_key:
    masked = stripe_key[:20] + "..." + stripe_key[-10:]
    print(f"   ✓ STRIPE_SECRET_KEY found: {masked}")
    print(f"   Length: {len(stripe_key)}")
else:
    print("   ✗ STRIPE_SECRET_KEY not found in environment")

# Test 2: Check config settings
print("\n2. Checking STRIPE_SECRET_KEY in config settings...")
try:
    from app.config import settings
    config_key = settings.stripe_secret_key
    if config_key:
        masked = config_key[:20] + "..." + config_key[-10:]
        print(f"   ✓ stripe_secret_key found in settings: {masked}")
        print(f"   Length: {len(config_key)}")
    else:
        print("   ✗ stripe_secret_key is None in settings")
except Exception as e:
    print(f"   ✗ Error loading settings: {e}")

# Test 3: Try importing stripe
print("\n3. Testing Stripe library import...")
try:
    import stripe
    print(f"   ✓ Stripe library imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import stripe: {e}")
    sys.exit(1)

# Test 4: Try setting API key directly
print("\n4. Testing direct Stripe API key assignment...")
try:
    stripe.api_key = stripe_key or settings.stripe_secret_key
    if stripe.api_key:
        masked = stripe.api_key[:20] + "..." + stripe.api_key[-10:]
        print(f"   ✓ API key set: {masked}")
    else:
        print("   ✗ API key is empty after assignment")
except Exception as e:
    print(f"   ✗ Error setting API key: {e}")

# Test 5: Try initializing a payment intent
print("\n5. Testing payment intent creation...")
try:
    intent = stripe.PaymentIntent.create(
        amount=2900,
        currency="usd",
        automatic_payment_methods={"enabled": True}
    )
    print(f"   ✓ Payment intent created: {intent.id}")
    print(f"   Client secret: {intent.client_secret[:50]}...")
except stripe.error.AuthenticationError as e:
    print(f"   ✗ Authentication error: {e}")
    print(f"      Error message: {e.user_message}")
except stripe.error.InvalidRequestError as e:
    print(f"   ✗ Invalid request error: {e}")
    print(f"      Error message: {e.user_message}")
except Exception as e:
    print(f"   ✗ Unexpected error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
