#!/usr/bin/env python
"""Test circular imports"""
import sys
import threading
import time

def timeout():
    time.sleep(5)
    print("💥 TIMEOUT - circular import detected")
    import os
    os._exit(1)

threading.Thread(target=timeout, daemon=True).start()

try:
    print("Attempting direct import...")
    import app.services.linesmate_scraper
    print("✅ Success!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
