#!/usr/bin/env python
"""Start backend with reload"""
import subprocess
import sys
import os

os.chdir(r"c:\Users\bigba\Desktop\New folder\sports-prediction-platform\backend")

# Start with --reload to automatically reload on file changes
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print("Backend started with reload enabled...")
print("Output:")

# Read and print first few lines
for i in range(10):
    line = proc.stdout.readline()
    if line:
        print(line.rstrip())
    else:
        break

print(f"\nStill running... (PID {proc.pid})")
