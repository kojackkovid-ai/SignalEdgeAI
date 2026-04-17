#!/usr/bin/env python
"""Start backend server with output to file"""
import subprocess
import sys
import os
import time

backend_dir = r"c:\Users\bigba\Desktop\New folder\sports-prediction-platform\backend"

print(f"Starting backend from {backend_dir}")
print(f"Current working directory: {os.getcwd()}")

# Change to backend directory
os.chdir(backend_dir)

# Start uvicorn with output redirected to file
log_file = open("backend_startup_debug.log", "w")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=log_file,
    stderr=subprocess.STDOUT,
    cwd=backend_dir
)

print(f"Backend process started with PID {proc.pid}")
print(f"Output is being logged to backend_startup_debug.log")
print(f"Waiting 5 seconds for startup...")
time.sleep(5)

# Check if process is still running
if proc.poll() is None:
    print("Backend is running successfully")
else:
    print(f"Backend failed with exit code {proc.returncode}")
    log_file.close()
    with open("backend_startup_debug.log", "r") as f:
        print("Error output:")
        print(f.read())
