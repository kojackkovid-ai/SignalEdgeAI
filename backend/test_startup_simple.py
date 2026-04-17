#!/usr/bin/env python
"""Simple server startup test"""
import subprocess
import time
import socket
import sys

def is_port_open(port, host="127.0.0.1"):
    """Check if port is open"""
    try:
        sock = socket.create_connection((host, port), timeout=1)
        sock.close()
        return True
    except:
        return False

print("🚀 Starting backend server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Wait for port to open
for i in range(20):
    if is_port_open(8000):
        print(f"✅ Server started successfully after {i} seconds!")
        proc.terminate()
        sys.exit(0)
    
    time.sleep(1)
    print(f"   Waiting... ({i}s)") if i % 5 == 0 else None

print("❌ Server failed to start")
proc.terminate()
sys.exit(1)
