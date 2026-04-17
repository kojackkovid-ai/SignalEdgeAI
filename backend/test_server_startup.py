#!/usr/bin/env python
"""Test server startup"""
import subprocess
import time
import requests
import sys

print("🚀 Starting backend server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Wait for server to start
for i in range(30):
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=2)
        if response.status_code == 200:
            print(f"✅ Server started successfully after {i} seconds!")
            print(f"   Status: {response.status_code}")
            proc.terminate()
            sys.exit(0)
    except:
        pass
    
    time.sleep(1)
    if i % 5 == 0:
        print(f"   Waiting... ({i}s)")

print("❌ Server failed to start within 30 seconds")
proc.terminate()
sys.exit(1)
