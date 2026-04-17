@echo off
REM Week 1 Implementation Test Runner (Windows)

setlocal enabledelayedexpansion

echo ===============================================
echo   WEEK 1 IMPLEMENTATION TEST SUITE
echo ===============================================
echo.

REM Navigate to backend directory
cd backend || exit /b 1

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo pytest not found. Installing...
    pip install pytest pytest-asyncio -q
)

echo Running Data Validation Tests...
echo ---
python -m pytest tests/unit/test_data_validation.py -v --tb=short
set DATA_VALIDATION_STATUS=%ERRORLEVEL%

echo.
echo Running Tier Features Tests...
echo ---
python -m pytest tests/unit/test_tier_features.py -v --tb=short
set TIER_FEATURES_STATUS=%ERRORLEVEL%

echo.
echo ===============================================
echo   TEST SUMMARY
echo ===============================================
echo.

if %DATA_VALIDATION_STATUS% == 0 (
    echo [OK] Data Validation Tests: PASSED
) else (
    echo [FAILED] Data Validation Tests: FAILED
)

if %TIER_FEATURES_STATUS% == 0 (
    echo [OK] Tier Features Tests: PASSED
) else (
    echo [FAILED] Tier Features Tests: FAILED
)

echo.

if %DATA_VALIDATION_STATUS% == 0 if %TIER_FEATURES_STATUS% == 0 (
    echo All tests passed!
    echo.
    echo Next steps:
    echo 1. Review WEEK_1_IMPLEMENTATION.md for integration guide
    echo 2. Update espn_prediction_service.py to use validation
    echo 3. Create database migration for audit_logs
    echo 4. Integrate audit logging into API routes
    exit /b 0
) else (
    echo Some tests failed. Review output above.
    exit /b 1
)
