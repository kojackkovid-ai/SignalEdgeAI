import sys
sys.path.insert(0, '.')

import stripe
from app.config import settings

# Initialize
stripe.api_key = settings.stripe_secret_key

print("Testing Stripe payment intent with automatic_payment_methods...")

try:
    # Try WITH automatic_payment_methods
    print("\n1. WITH automatic_payment_methods parameter:")
    intent1 = stripe.PaymentIntent.create(
        amount=2900,
        currency="usd",
        metadata={"test": "with_automatic"},
        automatic_payment_methods={"enabled": True}
    )
    print(f"✅ Success: {intent1.id}")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    # Try WITHOUT automatic_payment_methods
    print("\n2. WITHOUT automatic_payment_methods parameter:")
    intent2 = stripe.PaymentIntent.create(
        amount=2900,
        currency="usd",
        metadata={"test": "without_automatic"}
    )
    print(f"✅ Success: {intent2.id}")
except Exception as e:
    print(f"❌ Error: {e}")
