# Testing Guide - Sign Language Integration

## 🧪 Complete Testing Procedure

Follow these steps to test the sign language integration:

## Step 1: Start All Services

### 1.1 Start Backend API (Node.js)
```bash
cd backend
npm install  # if first time
node index.js
```
**Expected**: Server running on port 5000

### 1.2 Start Frontend (React)
```bash
cd frontend
npm install  # if first time
npm start
```
**Expected**: React app on http://localhost:3000

### 1.3 Start Python Service (Face/Voice Auth)
```bash
cd python_service
pip install -r ../requirements.txt  # if first time
python app.py
```
**Expected**: Flask app on port 5001

### 1.4 Start Sign Language Service
```bash
cd Sign
start_service.bat  # Windows
# or
./start_service.sh  # Linux/Mac
```
**Expected**: Flask app on http://127.0.0.1:8000

## Step 2: Verify Services

### 2.1 Check Backend
```bash
curl http://localhost:5000/api/razorpay/test
```
**Expected**: JSON response about Razorpay

### 2.2 Check Python Service
```bash
curl http://127.0.0.1:5001/
```
**Expected**: 404 or method not allowed (service is running)

### 2.3 Check Sign Service
```bash
curl http://127.0.0.1:8000/api/health
```
**Expected**:
```json
{
  "status": "ok",
  "sign_model_loaded": true,
  "slm_model_loaded": true
}
```

### 2.4 Check Frontend
Open browser: http://localhost:3000
**Expected**: BankAssist AI home page

## Step 3: Test User Flow

### 3.1 Login
1. Go to http://localhost:3000
2. Click "Login"
3. Login with your credentials
4. **Expected**: Redirected to Dashboard

### 3.2 Navigate to Sign Recognition
1. On Dashboard, locate "Quick Actions" section
2. Click "Customer Support" button
3. **Expected**: 
   - Page loads
   - Service health check runs
   - Sign recognition interface loads in iframe

### 3.3 Test Camera Access
1. Browser will prompt for camera permission
2. Click "Allow"
3. **Expected**: 
   - Webcam feed appears
   - Status shows "Ready - Click 'Start Recording' to begin"

### 3.4 Test Sign Recognition
1. Click "Start Recording" button
2. **Expected**: 
   - Button becomes disabled
   - Status shows "RECORDING..." (red, pulsing)
   - "Stop Recording" button enabled

3. Perform a clear sign gesture (hold for 2-3 seconds)
4. Click "Stop Recording"
5. **Expected**:
   - Status shows "Processing..."
   - Loading spinner appears
   - After 1-2 seconds, keyword appears in list
   - Status shows "Added: [KEYWORD] (Confidence: XX%)"

### 3.5 Test Multi-Word Recording
1. Repeat Step 3.4 for 2-3 different signs
2. **Expected**: 
   - Multiple keywords in the list
   - Each with colored tag
   - "Generate Query" button enabled

### 3.6 Test Sentence Generation
1. Click "Generate Query" button
2. **Expected**:
   - Loading spinner appears
   - Status shows "Generating query..."
   - After 2-4 seconds:
     - Green box appears with generated sentence
     - Status shows "Query generated successfully!"

### 3.7 Test Controls
1. Click "Remove Last" button
   - **Expected**: Last keyword removed

2. Click "Clear All" button
   - **Expected**: All keywords cleared, buttons disabled

3. Try recording without holding pose
   - **Expected**: "Prediction uncertain" message

### 3.8 Test Navigation
1. Click "← Back to Dashboard"
2. **Expected**: 
   - Return to dashboard
   - Login session maintained
   - No re-authentication needed

## Step 4: Browser Console Checks

### 4.1 Open DevTools (F12)
1. Go to Console tab
2. Check for errors
3. **Expected**: No red errors (warnings are OK)

### 4.2 Network Tab
1. Record a sign
2. Check Network tab
3. **Expected**: Successful API calls to:
   - `/api/process-frame` (during recording)
   - `/api/predict` (after stopping)
   - `/api/generate-sentence` (when generating)

## Step 5: Error Handling Tests

### 5.1 Test Service Offline
1. Stop the sign service (Ctrl+C)
2. Refresh /sign-recognition page
3. **Expected**: 
   - Error message shown
   - Instructions to start service
   - "Back to Dashboard" button works

### 5.2 Test Camera Denied
1. Deny camera permission
2. **Expected**: 
   - Error message about camera access
   - Instructions to enable camera
   - Can still navigate away

### 5.3 Test Short Recording
1. Click "Start Recording"
2. Immediately click "Stop Recording"
3. **Expected**: "Recording too short" message

## Step 6: Performance Tests

### 6.1 Frame Rate
1. Open DevTools Console
2. Record a sign
3. Check console logs
4. **Expected**: ~10 frames processed per second

### 6.2 Prediction Time
1. Record a 3-second sign
2. Note time from "Stop" to result
3. **Expected**: 100-500ms

### 6.3 Generation Time
1. Generate sentence with 3 keywords
2. Note time from click to result
3. **Expected**: 1-3 seconds (first time may take longer)

## Step 7: Integration Tests

### 7.1 Test Multiple Sessions
1. Login in one browser
2. Go to sign recognition
3. Open private/incognito window
4. Try to access /sign-recognition directly
5. **Expected**: Redirected to login (not authenticated)

### 7.2 Test Cross-Browser
Test in:
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if Mac)

**Expected**: Works in all browsers

### 7.3 Test Mobile/Tablet (Optional)
If you have mobile device:
1. Access http://[your-ip]:3000
2. Login and test sign recognition
3. **Expected**: Interface adapts to smaller screen

## 🐛 Common Issues & Solutions

### Issue: "Health check failed"
**Cause**: Sign service not running
**Solution**: 
```bash
cd Sign
python sign_service.py
```

### Issue: "Camera not accessible"
**Cause**: Permission denied or camera in use
**Solution**:
- Grant camera permissions
- Close other apps using camera
- Refresh page

### Issue: "Model not loaded"
**Cause**: Model files missing
**Solution**:
- Check `saved_model_landmarks/best_landmark_model.keras` exists
- Check `processed_data_landmarks/sign_labels.npy` exists

### Issue: "Prediction always uncertain"
**Cause**: Poor lighting or unclear gestures
**Solution**:
- Improve lighting
- Make clearer, slower gestures
- Hold poses for 2-3 seconds

### Issue: "SLM not generating sentences"
**Cause**: First-time model download or network issue
**Solution**:
- Wait 30-60 seconds on first use
- Check internet connection
- Model will cache after first use

### Issue: "CORS error in console"
**Cause**: Sign service not allowing frontend origin
**Solution**: Already handled with `flask-cors`, but verify CORS is enabled

## ✅ Success Checklist

Mark each item as you test:

- [ ] All 4 services start successfully
- [ ] Health checks pass for all services
- [ ] Can login to main application
- [ ] Dashboard loads correctly
- [ ] Customer Support button visible
- [ ] Sign recognition page loads
- [ ] Camera permission granted
- [ ] Webcam feed visible
- [ ] Can start recording
- [ ] Can stop recording
- [ ] Signs are recognized (>70% confidence)
- [ ] Keywords appear in list
- [ ] Can remove keywords
- [ ] Can clear all keywords
- [ ] Sentence generation works
- [ ] Generated text makes sense
- [ ] Can navigate back to dashboard
- [ ] Session persists across navigation
- [ ] Error handling works correctly
- [ ] No console errors (warnings OK)
- [ ] All network calls succeed

## 📊 Test Results Template

```
Date: __________
Tester: __________

Service Status:
- Backend (5000): [ ] Running [ ] Failed
- Frontend (3000): [ ] Running [ ] Failed
- Python Service (5001): [ ] Running [ ] Failed
- Sign Service (8000): [ ] Running [ ] Failed

Functionality:
- Login: [ ] Pass [ ] Fail
- Navigation: [ ] Pass [ ] Fail
- Camera Access: [ ] Pass [ ] Fail
- Sign Recording: [ ] Pass [ ] Fail
- Sign Recognition: [ ] Pass [ ] Fail
- Sentence Generation: [ ] Pass [ ] Fail
- Error Handling: [ ] Pass [ ] Fail

Performance:
- Frame Rate: _____ FPS
- Prediction Time: _____ ms
- Generation Time: _____ seconds

Issues Found:
1. ___________________________
2. ___________________________
3. ___________________________

Overall: [ ] PASS [ ] FAIL

Notes:
_________________________________
_________________________________
```

## 🎯 Quick Test Script

Save this as `test.ps1` (PowerShell):

```powershell
Write-Host "Testing BankAssist AI Sign Language Integration" -ForegroundColor Cyan

# Test Backend
Write-Host "`n[1/4] Testing Backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/razorpay/test" -UseBasicParsing
    Write-Host "✓ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Backend not responding" -ForegroundColor Red
}

# Test Frontend
Write-Host "`n[2/4] Testing Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    Write-Host "✓ Frontend is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Frontend not responding" -ForegroundColor Red
}

# Test Python Service
Write-Host "`n[3/4] Testing Python Service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5001" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✓ Python Service is running" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "✓ Python Service is running" -ForegroundColor Green
    } else {
        Write-Host "✗ Python Service not responding" -ForegroundColor Red
    }
}

# Test Sign Service
Write-Host "`n[4/4] Testing Sign Language Service..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
    if ($response.status -eq "ok") {
        Write-Host "✓ Sign Service is running" -ForegroundColor Green
        Write-Host "  - Sign Model: $($response.sign_model_loaded)" -ForegroundColor Gray
        Write-Host "  - SLM Model: $($response.slm_model_loaded)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Sign Service not responding" -ForegroundColor Red
}

Write-Host "`nTest complete!" -ForegroundColor Cyan
Write-Host "Open http://localhost:3000 and login to test the full feature." -ForegroundColor White
```

Run with:
```bash
powershell -ExecutionPolicy Bypass -File test.ps1
```

## 🎉 Final Verification

If all tests pass:
1. ✅ Sign language model is fully integrated
2. ✅ Users can access via Customer Support button
3. ✅ Real-time recognition works
4. ✅ Natural language generation works
5. ✅ Error handling is robust
6. ✅ Navigation flows correctly

**Congratulations!** Your sign language integration is complete and working! 🚀

---

**Need Help?** 
- Check console logs
- Review SETUP.md
- See INTEGRATION_SUMMARY.md
- Contact development team
