#!/usr/bin/env python
"""Test which specific import/init hangs"""
import sys
import time
import threading

def print_with_time(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def timeout_after(seconds):
    """Exit after N second"""
    time.sleep(seconds)
    print(f"\n💥 TIMEOUT after {seconds} seconds - HUNG HERE", flush=True)
    import os
    os._exit(1)

# Start timeout thread
timeout_thread = threading.Thread(target=timeout_after, args=(8,), daemon=True)
timeout_thread.start()

try:
    print_with_time("Step 1: import LinesMateScraper")
    from app.services.linesmate_scraper import LinesMateScraper
    print_with_time("✅ LinesMateScraper imported")
    
    print_with_time("Step 2: Create LinesMateScraper instance")
    scraper = LinesMateScraper()
    print_with_time("✅ LinesMateScraper instance created")
    
    print_with_time("Step 3: import ESPNPredictionService")
    from app.services.espn_prediction_service import ESPNPredictionService
    print_with_time("✅ ESPNPredictionService imported")
    
    print_with_time("Step 4: Create ESPNPredictionService instance")
    espn = ESPNPredictionService()
    print_with_time("✅ ESPNPredictionService instance created")
    
    print_with_time("✅ SUCCESS!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
