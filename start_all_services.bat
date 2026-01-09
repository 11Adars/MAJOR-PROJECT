@echo off
echo ========================================
echo Starting All NS-AGF Banking Services
echo ========================================
echo.
echo Starting 5 services in separate windows...
echo.

REM Start Backend (Node.js - Port 5000)
echo [1/5] Starting Backend Server (Port 5000)...
start "Backend Server - Port 5000" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\backend" && node index.js"
timeout /t 2 /nobreak >nul

REM Start Python Speaker Verification Service (Port 5001)
echo [2/5] Starting Speaker Verification Service (Port 5001)...
start "Speaker Verification - Port 5001" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\python_service" && python app.py"
timeout /t 2 /nobreak >nul

REM Start Biometric Fusion Service (Port 5002)
echo [3/5] Starting Biometric Fusion Service (Port 5002)...
start "Biometric Fusion - Port 5002" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy" && python biometric_fusion_service_enhanced.py"
timeout /t 2 /nobreak >nul

REM Start NS-AGF Sign Language API (Port 5003)
echo [4/5] Starting NS-AGF Sign Language API (Port 5003)...
start "NS-AGF API - Port 5003" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\ns_agf" && python api_service.py"
timeout /t 3 /nobreak >nul

REM Start Frontend (React - Port 3000)
echo [5/5] Starting Frontend React App (Port 3000)...
start "Frontend React - Port 3000" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\frontend" && npm start"

echo.
echo ========================================
echo All services are starting!
echo ========================================
echo.
echo Service Windows:
echo  1. Backend Server          - Port 5000
echo  2. Speaker Verification    - Port 5001
echo  3. Biometric Fusion        - Port 5002
echo  4. NS-AGF Sign Language    - Port 5003
echo  5. Frontend React          - Port 3000
echo.
echo Wait ~30 seconds for all services to initialize...
echo Frontend will open in browser automatically.
echo.
echo Press any key to close this window...
pause >nul
