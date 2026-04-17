#!/usr/bin/env python
"""Quick test to verify backend can start"""
import sys
sys.path.insert(0, 'backend')

try:
    print("Testing imports...")
    from app.routes.predictions import get_prediction_service, get_auth_service
    from app.routes.users import get_prediction_service as gps_users
    print("✅ Route imports OK")
    
    # Test service creation
    print("Testing service instantiation...")
    auth_svc = get_auth_service()
    print(f"✅ AuthService created: {type(auth_svc).__name__}")
    
    pred_svc = get_prediction_service()
    print(f"✅ PredictionService created: {type(pred_svc).__name__}")
    
    print("\n✅ All checks passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
