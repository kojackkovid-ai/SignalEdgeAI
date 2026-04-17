@echo off
REM Quick Tunnel Setup - No Auth Required!
REM This uses localtunnel which doesn't need authentication

echo.
echo ============================================
echo   Sports Prediction Platform - Remote Testing
echo ============================================
echo.

REM Check if localtunnel is installed
npm list -g localtunnel >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing localtunnel...
    npm install -g localtunnel
)

echo.
echo 🚀 Starting tunnels...
echo.
echo INFO: Keep this window open while testing!
echo Close it with Ctrl+C when done.
echo.

REM Start backend tunnel and capture output
title Backend Tunnel - Sports Prediction Platform
echo Starting backend tunnel (port 8000)...
lt --port 8000
