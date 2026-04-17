#!/usr/bin/env python
"""Debug startup issue by importing modules step by step"""
import sys
import traceback
from pathlib import Path

last_step = "Start"

try:
    last_step = "Import logging"
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    last_step = "Import FastAPI"
    from fastapi import FastAPI
    
    last_step = "Import app.config"
    from app.config import settings
    
    last_step = "Import database"
    from app.database import init_db, Base, engine
    
    last_step = "Import EnhancedMLService"
    from app.services.enhanced_ml_service import EnhancedMLService
    
    last_step = "Initialize EnhancedMLService"
    ml_service = EnhancedMLService()
    print(f"✅ EnhancedMLService created: {ml_service}")
    
    last_step = "Import EnhancedAutoTrainingPipeline"
    from app.services.enhanced_auto_training import EnhancedAutoTrainingPipeline
    
    last_step = "Initialize EnhancedAutoTrainingPipeline"
    auto_training = EnhancedAutoTrainingPipeline()
    print(f"✅ EnhancedAutoTrainingPipeline created: {auto_training}")
    
    last_step = "Import ModelPerformanceMonitor"
    from app.services.model_monitoring import ModelPerformanceMonitor
    
    last_step = "Initialize ModelPerformanceMonitor"
    monitor = ModelPerformanceMonitor()
    print(f"✅ ModelPerformanceMonitor created: {monitor}")
    
    last_step = "Import main app"
    from app.main import app
    
    print("✅ ALL IMPORTS SUCCESSFUL!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR at '{last_step}':")
    print(f"   {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
