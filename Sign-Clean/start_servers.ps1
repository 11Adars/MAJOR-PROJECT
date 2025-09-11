Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Sign Language Recognition Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting both servers..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Server 1: Original Gestures (Port 8001)" -ForegroundColor Green
Write-Host "Server 2: Custom Gestures (Port 8002)" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop" -ForegroundColor Red
Write-Host ""

# Start Original Server
Write-Host "Starting Original Gestures Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'original-server'; python main.py" -WindowStyle Normal

# Wait a moment
Start-Sleep -Seconds 3

# Start Custom Server
Write-Host "Starting Custom Gestures Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'custom-server'; python main.py" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Both servers started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Original Server: http://127.0.0.1:8001" -ForegroundColor Blue
Write-Host "Custom Server:   http://127.0.0.1:8002" -ForegroundColor Blue
Write-Host ""
Write-Host "Web interfaces will open automatically..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Wait for servers to start
Start-Sleep -Seconds 5

# Open web interfaces
Start-Process "http://127.0.0.1:8001"
Start-Process "http://127.0.0.1:8002"

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Magenta
Read-Host
