#!/usr/bin/env python3
"""Minimal test of Stripe initialization without database"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Don't load database
os.environ["SKIP_DB_INIT"] = "1"

print("\n" + "=" * 70)
print("STRIPE INITIALIZATION FIX VERIFICATION")
print("=" * 70)

print("\n1. Loading configuration...")
try:
    from app.config import settings
    print("   ✓ Settings loaded from .env file")
except Exception as e:
    print(f"   ✗ Failed to load settings: {e}")
    sys.exit(1)

print("\n2. Verifying STRIPE_SECRET_KEY is configured...")
if settings.stripe_secret_key:
    masked = settings.stripe_secret_key[:20] + "..." + settings.stripe_secret_key[-10:]
    print(f"   ✓ STRIPE_SECRET_KEY is configured: {masked}")
    key_length = len(settings.stripe_secret_key)
    print(f"   ✓ Key length: {key_length} characters")
else:
    print(f"   ✗ STRIPE_SECRET_KEY is None or empty!")
    sys.exit(1)

print("\n3. Testing Stripe library import...")
try:
    import stripe
    print(f"   ✓ Stripe library imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import stripe: {e}")
    sys.exit(1)

print("\n4. Testing the updated _init_stripe() function...")
try:
    from app.services.stripe_service import _init_stripe
    
    # Reset the global state for testing
    import app.services.stripe_service as ss
    ss.stripe_initialized = False
    ss.stripe = None
    
    # Call the init function
    stripe_instance = _init_stripe()
    
    if stripe_instance:
        print(f"   ✓ Stripe initialized successfully")
        print(f"   ✓ Stripe API key is set: {stripe_instance.api_key[:20]}...")
    else:
        print(f"   ✗ Stripe initialization returned None")
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ Stripe initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ PAYMENT INITIALIZATION FIX VERIFIED SUCCESSFULLY")
print("=" * 70)
print("\nFix Summary:")
print("  • Changed stripe_service.py to import settings directly")
print("  • API key now correctly loaded from pydantic_settings")
print("  • Stripe initialization works without errors")
print("  • Payment tier upgrades should now succeed")
print("\nWhat was changed:")
print("  OLD: env_key = os.getenv('STRIPE_SECRET_KEY')  # Returns None")
print("  NEW: from app.config import settings")
print("       api_key = settings.stripe_secret_key      # Loads from .env")
print("=" * 70 + "\n")
