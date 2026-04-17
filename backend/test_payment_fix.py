#!/usr/bin/env python3
"""Quick test for payment/stripe configuration after fix"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing payment configuration fix...")

try:
    from app.config import settings
    
    print(f"✓ Settings loaded successfully")
    print(f"✓ STRIPE_SECRET_KEY set: {bool(settings.stripe_secret_key)}")
    
    if settings.stripe_secret_key:
        print(f"  - Length: {len(settings.stripe_secret_key)}")
        print(f"  - Starts with: {settings.stripe_secret_key[:20]}")
        
        # Try Stripe init
        try:
            from app.services.stripe_service import _init_stripe
            stripe_module = _init_stripe()
            print(f"✓ Stripe initialized successfully!")
            print(f"✓ Payment should now work")
        except Exception as e:
            print(f"✗ Stripe init failed: {e}")
    else:
        print(f"✗ STRIPE_SECRET_KEY is still None")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
