@echo off
echo 🚀 ML Sports Prediction System Setup
echo ======================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo ✅ Virtual environment ready

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install --upgrade pip
pip install pandas numpy scikit-learn xgboost lightgbm tensorflow joblib schedule

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed

REM Run the setup script
echo.
echo 🎯 Running ML system setup...
python setup_ml_system.py

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. To start the daily training scheduler, run: start_ml_system.bat
echo 2. To monitor logs, check: ml-models\logs\
echo 3. Training will run automatically at 2:00 AM daily
echo.
echo Press any key to exit...
pause >nul