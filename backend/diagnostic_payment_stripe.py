#!/usr/bin/env python3
"""Diagnostic script for Stripe/Payment configuration"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Direct env check
print("=== Test 1: Direct os.environ check (before load_dotenv) ===")
key = os.getenv('STRIPE_SECRET_KEY')
print(f"STRIPE_SECRET_KEY in os.environ: {bool(key)}")
if key:
    print(f"  Length: {len(key)}, Starts with: {key[:20]}")

# Test 2: Dotenv loading
print("\n=== Test 2: After dotenv.load_dotenv() ===")
from dotenv import load_dotenv
result = load_dotenv(verbose=True)
print(f"load_dotenv() result (True = file found): {result}")
key = os.getenv('STRIPE_SECRET_KEY')
print(f"STRIPE_SECRET_KEY in os.environ: {bool(key)}")
if key:
    print(f"  Length: {len(key)}, Starts with: {key[:20]}")
else:
    print(f"  STRIPE_SECRET_KEY is: {repr(key)}")

# Test 3: Settings loading
print("\n=== Test 3: Pydantic Settings ===")
from app.config import settings
print(f"settings.stripe_secret_key available: {bool(settings.stripe_secret_key)}")
if settings.stripe_secret_key:
    print(f"  Length: {len(settings.stripe_secret_key)}")
    print(f"  Starts with: {settings.stripe_secret_key[:20]}")
else:
    print(f"  Value is: {repr(settings.stripe_secret_key)}")
    print(f"  Type: {type(settings.stripe_secret_key)}")

# Test 4: Try Stripe initialization
print("\n=== Test 4: Stripe Initialization ===")
try:
    from app.services.stripe_service import _init_stripe
    stripe = _init_stripe()
    print("✅ Stripe initialized successfully")
    print(f"  Stripe module: {stripe}")
except Exception as e:
    print(f"❌ Stripe initialization failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test 5: Check .env file existence ===")
cwd = os.getcwd()
print(f"Current working directory: {cwd}")

for possible_path in [".env", os.path.join(cwd, ".env"), os.path.join(os.path.dirname(__file__), ".env")]:
    exists = os.path.exists(possible_path)
    print(f"  {possible_path}: {exists}")

print("\n✅ Diagnostic complete")
