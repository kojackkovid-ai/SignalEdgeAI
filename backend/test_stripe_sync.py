"""
Test payment with detailed output capture
"""
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.stripe_service import stripe_service
from app.config import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("Testing stripe_service.create_payment_intent() directly...")
print(f"STRIPE_SECRET_KEY set: {bool(settings.stripe_secret_key)}")

try:
    result = asyncio.run(stripe_service.create_payment_intent(
        amount=2900,
        currency="usd",
        metadata={"test": "direct_test"}
    ))
    print(f"\n✅ Success!")
    print(f"Result: {result}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

