@echo off
echo ========================================
echo   Sign Language Recognition Service
echo   BankAssist AI - Customer Support
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
echo [INFO] Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
) else (
    echo [SUCCESS] Dependencies already installed
)

REM Check if model files exist
echo [INFO] Checking model files...
if not exist "saved_model_landmarks\best_landmark_model.keras" (
    echo [WARNING] Sign recognition model not found!
    echo [WARNING] Expected: saved_model_landmarks\best_landmark_model.keras
    echo [WARNING] The service may not work properly without the model
    echo.
    pause
)

if not exist "processed_data_landmarks\sign_labels.npy" (
    echo [WARNING] Sign labels not found!
    echo [WARNING] Expected: processed_data_landmarks\sign_labels.npy
    echo [WARNING] The service may not work properly without labels
    echo.
    pause
)

echo.
echo ========================================
echo   Starting Sign Language Service
echo   URL: http://127.0.0.1:8000
echo ========================================
echo.
echo [INFO] Press Ctrl+C to stop the service
echo.

REM Start the Flask service
python sign_service.py

REM Deactivate virtual environment on exit
deactivate
