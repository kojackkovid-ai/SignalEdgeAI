import sys
import os
sys.path.insert(0, '.')

# Test stripe initialization
from app.services.stripe_service import stripe_service
print('✅ Stripe service imported')

# Try to create a test payment intent
import asyncio
try:
    result = asyncio.run(stripe_service.create_payment_intent(2900, 'usd', {'test': 'true'}))
    print('✅ Payment intent created:', result['payment_intent_id'])
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
