#!/usr/bin/env pwsh
# Start the FastAPI backend server

$BackendPath = "C:\Users\bigba\Desktop\New folder\sports-prediction-platform\backend"
Set-Location $BackendPath

Write-Host "🚀 Starting Sports Prediction Platform Backend..."
Write-Host "📍 Location: $BackendPath"
Write-Host "🌐 Server will run on: http://127.0.0.1:8000"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
