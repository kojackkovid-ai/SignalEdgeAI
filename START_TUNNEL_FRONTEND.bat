@echo off
REM Frontend Tunnel - Run this in a separate window!

title Frontend Tunnel - Sports Prediction Platform
echo.
echo Starting frontend tunnel (port 5173)...
echo Keep this window open while testing.
echo.

npm install -g localtunnel >nul 2>&1
lt --port 5173
