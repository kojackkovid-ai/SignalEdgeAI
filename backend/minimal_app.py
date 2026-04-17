#!/usr/bin/env python3
"""Lightweight backend startup without problematic imports"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[1] Starting minimal backend...", flush=True)

from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("[2] FastAPI imported", flush=True)

app = FastAPI(title="Sports Prediction API - Minimal")

print("[3] App created", flush=True)

from app.config import settings
print("[4] Config loaded", flush=True)

from app.database import init_db, get_db
print("[5] Database module loaded", flush=True)

@app.get("/health")
async def health():
    return {"status": "ok"}

print("[6] Health endpoint added", flush=True)

if __name__ == "__main__":
    import uvicorn
    print("[7] Starting Uvicorn...", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8000)
