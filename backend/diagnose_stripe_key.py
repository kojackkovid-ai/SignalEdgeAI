#!/usr/bin/env python3
"""
Quick diagnostic to check what value is being used for Stripe API key at runtime
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "=" * 80)
print("STRIPE API KEY DIAGNOSTIC")
print("=" * 80)

# Test 1: Check env file directly
print("\n1. Checking .env file directly...")
try:
    with open(".env", "r") as f:
        env_content = f.read()
    
    # Extract Stripe key
    for line in env_content.split("\n"):
        if "STRIPE_SECRET_KEY=" in line:
            parts = line.split("=")
            if len(parts) == 2:
                key = parts[1].strip()
                masked = key[:20] + "..." + key[-10:] if len(key) > 30 else key
                print(f"   ✓ Found in .env: {masked}")
                print(f"   Length: {len(key)}")
except Exception as e:
    print(f"   ✗ Error reading .env: {e}")

# Test 2: Check os.getenv
print("\n2. Checking os.getenv('STRIPE_SECRET_KEY')...")
env_key = os.getenv("STRIPE_SECRET_KEY")
if env_key:
    masked = env_key[:20] + "..." + env_key[-10:]
    print(f"   ✓ Found: {masked}")
else:
    print(f"   ✗ Returns None")

# Test 3: Check config settings
print("\n3. Checking config.settings.stripe_secret_key...")
try:
    from app.config import settings
    config_key = settings.stripe_secret_key
    if config_key:
        masked = config_key[:20] + "..." + config_key[-10:]
        print(f"   ✓ Found: {masked}")
        print(f"   Length: {len(config_key)}")
        print(f"   Type: {type(config_key)}")
    else:
        print(f"   ✗ Returns None")
except Exception as e:
    print(f"   ✗ Error loading settings: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check what the stripe module receives after _init_stripe()
print("\n4. Testing _init_stripe() and stripe.api_key...")
try:
    from app.services.stripe_service import _init_stripe
    
    stripe_module = _init_stripe()
    
    if stripe_module:
        print(f"   ✓ _init_stripe() succeeded")
        
        if hasattr(stripe_module, 'api_key'):
            if stripe_module.api_key:
                masked = stripe_module.api_key[:20] + "..." + stripe_module.api_key[-10:]
                print(f"   ✓ stripe.api_key is set: {masked}")
                print(f"   Length: {len(stripe_module.api_key)}")
            else:
                print(f"   ✗ stripe.api_key is None or empty!")
        else:
            print(f"   ✗ stripe has no api_key attribute")
    else:
        print(f"   ✗ _init_stripe() returned None")
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Try creating a payment intent
print("\n5. Attempting to create a test payment intent...")
try:
    from app.services.stripe_service import stripe_service
    import asyncio
    
    async def test():
        result = await stripe_service.create_payment_intent(
            amount=100,
            currency="usd",
            metadata={"test": "diagnostic"}
        )
        return result
    
    result = asyncio.run(test())
    print(f"   ✓ Payment intent created: {result.get('payment_intent_id')}")
    
except Exception as e:
    print(f"   ✗ Error creating payment intent:")
    print(f"      {type(e).__name__}: {e}")

print("\n" + "=" * 80 + "\n")
