@echo off
REM Quick Deployment Setup Script for Windows
REM Run this to prepare for production deployment

echo.
echo 🚀 Sports Prediction Platform - Production Deployment Setup
echo ===========================================================

REM Check if .env.production exists
if not exist ".env.production" (
    echo ❌ .env.production not found
    echo Creating from template...
    if exist ".env.example" (
        copy .env.example .env.production
    ) else (
        echo ERROR: No .env.example found
        exit /b 1
    )
    echo ✅ Created .env.production - EDIT THIS FILE with your values!
)

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not installed. Install from https://www.docker.com/products/docker-desktop
    exit /b 1
)
for /f "tokens=*" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo ✅ Docker found: %DOCKER_VERSION%

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose not installed
    exit /b 1
)
for /f "tokens=*" %%i in ('docker-compose --version') do set DOCKER_COMPOSE_VERSION=%%i
echo ✅ Docker Compose found: %DOCKER_COMPOSE_VERSION%

echo.
echo 🔨 Building Docker images...
docker-compose -f docker-compose.prod.yml build --no-cache

echo.
echo ✅ Setup complete!
echo.
echo 📝 Next steps:
echo    1. Edit .env.production with your actual values
echo    2. Run: docker-compose -f docker-compose.prod.yml up -d
echo    3. Check status: docker-compose -f docker-compose.prod.yml ps
echo    4. View logs: docker-compose -f docker-compose.prod.yml logs -f
echo.
echo 🌐 For Railway.app deployment, see PRODUCTION_DEPLOYMENT_GUIDE.md
echo.
pause
