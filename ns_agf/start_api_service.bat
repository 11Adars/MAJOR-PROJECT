@echo off
REM Start NS-AGF API Service
REM This script starts the Flask REST API for NS-AGF

echo ========================================
echo Starting NS-AGF API Service
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing Flask dependencies...
    pip install -r api_requirements.txt
)

echo.
echo Starting Flask server on http://127.0.0.1:5002
echo Press Ctrl+C to stop
echo.

REM Start the API service
python api_service.py

pause
