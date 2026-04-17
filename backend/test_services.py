#!/usr/bin/env python
"""Test which service hangs"""
import sys
import time
import threading

def print_with_time(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def timeout_after(seconds):
    """Exit after N seconds"""
    time.sleep(seconds)
    print(f"\n💥 TIMEOUT after {seconds} seconds - process HUNG", flush=True)
    import os
    os._exit(1)

# Start timeout thread
timeout_thread = threading.Thread(target=timeout_after, args=(8,), daemon=True)
timeout_thread.start()

try:
    print_with_time("1️⃣  Testing: import logging")
    import logging
    
    print_with_time("2️⃣  Testing: import FastAPI")
    from fastapi import FastAPI
    
    print_with_time("3️⃣  Testing: import config")
    from app.config import settings
    
    print_with_time("4️⃣  Testing: import database")
    from app.database import init_db, Base, engine
    
    print_with_time("5️⃣  Testing: import EnhancedMLService")
    from app.services.enhanced_ml_service import EnhancedMLService
    
    print_with_time("6️⃣  Creating EnhancedMLService instance")
    ml = EnhancedMLService()
    print_with_time("✅ EnhancedMLService OK")
    
    print_with_time("7️⃣  Testing: import EnhancedAutoTrainingPipeline")
    from app.services.enhanced_auto_training import EnhancedAutoTrainingPipeline
    
    print_with_time("8️⃣  Creating EnhancedAutoTrainingPipeline instance")
    auto = EnhancedAutoTrainingPipeline()
    print_with_time("✅ EnhancedAutoTrainingPipeline OK")
    
    print_with_time("9️⃣  Testing: import ModelPerformanceMonitor")
    from app.services.model_monitoring import ModelPerformanceMonitor
    
    print_with_time("🔟 Creating ModelPerformanceMonitor instance")
    monitor = ModelPerformanceMonitor()
    print_with_time("✅ ModelPerformanceMonitor OK")
    
    print_with_time("Testing: import prediction routes")
    from app.routes.predictions import router as pred_router
    print_with_time("✅ Predictions routes OK")
    
    print_with_time("Testing: import auth routes")
    from app.routes.auth import router as auth_router
    print_with_time("✅ Auth routes OK")
    
    print_with_time("Testing: import user routes")
    from app.routes.users import router as user_router
    print_with_time("✅ Users routes OK")
    
    print_with_time("Testing: import model routes")
    from app.routes.models import router as model_router
    print_with_time("✅ Models routes OK")
    
    print_with_time("Testing: import payment routes")
    from app.routes.payment import router as payment_router
    print_with_time("✅ Payment routes OK")
    
    print_with_time("Testing: import main app")
    from app.main import app
    print_with_time("✅ Main app OK")
    
    print_with_time("✅ ALL IMPORTS SUCCESSFUL!")
    sys.exit(0)
    
except KeyboardInterrupt:
    print("\n❌ Interrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
