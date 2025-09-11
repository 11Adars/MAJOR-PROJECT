@echo off
echo ========================================
echo    Sign Language Recognition Servers
echo ========================================
echo.
echo Starting both servers...
echo.
echo Server 1: Original Gestures (Port 8001)
echo Server 2: Custom Gestures (Port 8002)
echo.
echo Press Ctrl+C in each terminal to stop
echo.

:: Start Original Server
echo Starting Original Gestures Server...
start "Original Gestures Server" cmd /k "cd /d original-server && python main.py"

:: Wait a moment
timeout /t 3 /nobreak >nul

:: Start Custom Server
echo Starting Custom Gestures Server...
start "Custom Gestures Server" cmd /k "cd /d custom-server && python main.py"

echo.
echo ========================================
echo Both servers started successfully!
echo.
echo Original Server: http://127.0.0.1:8001
echo Custom Server:   http://127.0.0.1:8002
echo.
echo Web interfaces will open automatically...
echo ========================================

:: Wait for servers to start
timeout /t 5 /nobreak >nul

:: Open web interfaces
start http://127.0.0.1:8001
start http://127.0.0.1:8002

pause
