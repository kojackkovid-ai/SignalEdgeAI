@echo off
echo 🚀 Starting ML Sports Prediction System
echo ======================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found. Running with system Python...
)

echo 📅 Starting daily training scheduler...
echo This will run continuously and train models daily at 2:00 AM
echo.
echo 📝 Logs will be saved to: ml-models\logs\
echo 🎯 Press Ctrl+C to stop the scheduler
echo.

REM Run the daily scheduler
python ml-models\training\daily_scheduler_new.py

echo.
echo Scheduler stopped.
pause