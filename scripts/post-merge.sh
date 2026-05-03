#!/bin/bash
set -e

echo "[post-merge] Installing frontend dependencies..."
cd frontend && npm install --legacy-peer-deps --silent
cd ..

echo "[post-merge] Installing backend dependencies..."
cd backend && pip install -r requirements.txt -q
cd ..

echo "[post-merge] Done."
