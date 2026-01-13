@echo off
echo ========================================
echo   MULTI-AUTH SETUP - QUICK START
echo ========================================
echo.
echo This script will guide you through setting up
echo the Multi-Factor Authentication system.
echo.
pause

REM Step 1: Database Migration
echo.
echo ========================================
echo STEP 1: Database Migration
echo ========================================
echo.
echo Please run the following SQL script in your
echo PostgreSQL/Supabase SQL Editor:
echo.
echo File: backend\database_schema_multiauth.sql
echo.
echo Press any key after you've run the migration...
pause >nul

REM Step 2: Environment Variables
echo.
echo ========================================
echo STEP 2: Environment Variables Check
echo ========================================
echo.
echo Please ensure your backend\.env file has:
echo.
echo SMTP_HOST=smtp.gmail.com
echo SMTP_PORT=587
echo SMTP_USER=your-email@gmail.com
echo SMTP_PASS=your-app-password
echo SMTP_FROM=your-email@gmail.com
echo JWT_SECRET=your-secret-key
echo.
echo Press any key to continue...
pause >nul

REM Step 3: Install Dependencies
echo.
echo ========================================
echo STEP 3: Installing Dependencies
echo ========================================
echo.
echo Checking backend dependencies...
cd backend
call npm install form-data axios
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo Checking frontend dependencies...
cd frontend
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo ✅ Dependencies installed successfully!
echo.

REM Step 4: Test Email Service
echo.
echo ========================================
echo STEP 4: Test Email Service (Optional)
echo ========================================
echo.
echo Would you like to test the email service? (Y/N)
set /p test_email=
if /i "%test_email%"=="Y" (
    echo.
    echo Enter your test email address:
    set /p email_address=
    cd backend
    node -e "require('./utils/emailService').sendOTP('%email_address%', '123456').then(r => console.log('✅ Email sent!', r)).catch(e => console.error('❌ Error:', e.message))"
    cd ..
    echo.
    echo Check your email for OTP: 123456
    echo.
    pause
)

REM Step 5: Start Services
echo.
echo ========================================
echo STEP 5: Starting All Services
echo ========================================
echo.
echo Starting services in 5 seconds...
timeout /t 5 /nobreak >nul

echo.
echo [1/5] Starting Backend Server (Port 5000)...
start "Backend Server - Port 5000" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\backend" && node index.js"
timeout /t 2 /nobreak >nul

echo [2/5] Starting Speaker Verification Service (Port 5001)...
start "Speaker Verification - Port 5001" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\python_service" && python app.py"
timeout /t 2 /nobreak >nul

echo [3/5] Starting Biometric Fusion Service (Port 5002)...
start "Biometric Fusion - Port 5002" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy" && python biometric_fusion_service_enhanced.py"
timeout /t 2 /nobreak >nul

echo [4/5] Starting NS-AGF Sign Language API (Port 5003)...
start "NS-AGF API - Port 5003" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\ns_agf" && python api_service.py"
timeout /t 3 /nobreak >nul

echo [5/5] Starting Frontend React App (Port 3000)...
start "Frontend React - Port 3000" cmd /k "cd /d "d:\MAJOR-PROJECT - Copy\frontend" && npm start"

echo.
echo ========================================
echo ✅ ALL SERVICES STARTED!
echo ========================================
echo.
echo Service Windows:
echo  1. Backend Server          - Port 5000
echo  2. Speaker Verification    - Port 5001
echo  3. Biometric Fusion        - Port 5002
echo  4. NS-AGF Sign Language    - Port 5003
echo  5. Frontend React          - Port 3000
echo.
echo Frontend will open automatically in ~30 seconds...
echo.
echo ========================================
echo TESTING GUIDE
echo ========================================
echo.
echo 1. REGISTER NEW USER:
echo    URL: http://localhost:3000/register
echo    - Fill username, email, phone
echo    - Capture face photo
echo    - Record voice (5-10 seconds)
echo    - Click "Complete Registration"
echo.
echo 2. LOGIN:
echo    URL: http://localhost:3000/login
echo    - Enter username
echo    - Choose method: Face / Voice / OTP
echo    - Complete authentication
echo.
echo 3. DASHBOARD:
echo    - View account balance
echo    - Transfer money
echo    - View transaction history
echo.
echo ========================================
echo TROUBLESHOOTING
echo ========================================
echo.
echo ❌ OTP email not received?
echo    - Check backend\.env SMTP settings
echo    - Enable Gmail App Passwords
echo    - Check spam folder
echo.
echo ❌ Face recognition fails?
echo    - Check Python service (Port 5001)
echo    - Allow camera permissions
echo    - Ensure good lighting
echo.
echo ❌ Voice authentication fails?
echo    - Record for at least 5 seconds
echo    - Speak clearly
echo    - Check microphone permissions
echo.
echo ========================================
echo.
echo Press any key to close this window...
pause >nul
