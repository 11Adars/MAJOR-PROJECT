# 🧪 End-to-End Testing Guide

## 🎯 **Complete System Testing**

This guide will walk you through testing the entire integrated system from login to sign language support.

---

## 📋 **Pre-Testing Checklist**

### 1. **Start All Services** (Required)

```powershell
# Terminal 1: Backend (Port 5000)
cd "d:\MAJOR-PROJECT - Copy\backend"
node index.js
# Wait for: "Server running on port 5000"

# Terminal 2: Face Service (Port 5001)
cd "d:\MAJOR-PROJECT - Copy\python_service"
python app.py
# Wait for: "Running on http://127.0.0.1:5001"

# Terminal 3: Biometric Fusion (Port 5002)
cd "d:\MAJOR-PROJECT - Copy"
python biometric_fusion_service_enhanced.py
# Wait for: "Running on http://127.0.0.1:5002"

# Terminal 4: NS-AGF Service (Port 5003)
cd "d:\MAJOR-PROJECT - Copy\ns_agf"
python api_service.py
# Wait for: "Running on http://127.0.0.1:5003"

# Terminal 5: SLM Service (Port 5004)
cd "d:\MAJOR-PROJECT - Copy\Sign"
python sign_service.py
# Wait for: "Running on http://127.0.0.1:5004"

# Terminal 6: Frontend (Port 3000)
cd "d:\MAJOR-PROJECT - Copy\frontend"
npm start
# Wait for: Browser opens to http://localhost:3000
```

### 2. **Verify All Services Are Running**

```powershell
# Quick health check
curl http://localhost:5000/api/health
curl http://127.0.0.1:5001/health
curl http://127.0.0.1:5002/api/health
curl http://127.0.0.1:5003/api/health
```

### 3. **Database Status**
```powershell
# Verify database is accessible
psql -U postgres -d Major -c "SELECT 1;"
```

---

## 🚀 **Test Scenario 1: New User Registration & Login**

### Step 1: Register New User
1. Open browser: `http://localhost:3000`
2. Click **"Register"** button
3. Fill in the form:
   - Username: `test_user_001`
   - Email: `test001@example.com`
   - Password: `SecurePass123!`
4. Click **"Capture Face"** button
   - Allow camera access
   - Position your face in the webcam
   - Click capture
5. Click **"Register"** button

**Expected Result:**
- ✅ Success message: "Registration successful"
- ✅ Auto-redirect to login page after 2 seconds
- ✅ Console shows: `POST /api/register 200 OK`

**If Failed:**
- Check Port 5001 terminal for face service errors
- Check Port 5000 backend terminal for registration errors
- Verify webcam is accessible

---

### Step 2: Login with Face Authentication
1. On login page, enter username: `test_user_001`
2. Click **"Capture Face"** button
3. Position face in webcam → Click capture
4. Click **"Login"** button

**Expected Result:**
- ✅ Success message: "Login successful! Redirecting..."
- ✅ JWT token stored in localStorage
- ✅ Redirect to Dashboard
- ✅ Console shows: `POST /api/login 200 OK`

**Verify JWT Token:**
```javascript
// Open browser console (F12)
localStorage.getItem('token')
// Should return: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**If Failed:**
- Check if face image matches registered face
- Check Port 5001 terminal for face recognition errors
- Try re-registering with better face photo

---

## 🔒 **Test Scenario 2: Biometric Enrollment**

### Step 3: View Dashboard Enrollment Banner
1. After login, you should see dashboard
2. **Check for enrollment banner** (should appear at top)

**Expected Result:**
- ✅ Banner visible with:
  - Shield icon
  - Message: "Secure Your Transfers with Biometric Authentication"
  - "Enroll Now" button
  - "Maybe Later" button

**If Banner NOT Visible:**
- Open browser console
- Check if `biometric_enrolled` is `false` in user data
- Banner should only show if NOT already enrolled

---

### Step 4: Enroll Biometrics
1. Click **"Enroll Now"** button on banner
2. Navigate to Biometric Enrollment page
3. Read the instructions
4. Click **"Start Enrollment"** button
5. **Important**: Stay still and:
   - Make different facial expressions
   - Move your hands naturally in view
   - Turn your head slightly
6. Watch the progress bar (0% → 100%)
7. Wait for processing message

**Expected Result:**
- ✅ Progress bar completes (30 frames captured)
- ✅ Processing message: "Processing biometric enrollment..."
- ✅ Success message: "Biometric enrollment successful!"
- ✅ Console shows: `POST /api/biometric/enroll 200 OK`
- ✅ Response includes: `{ success: true, framesProcessed: 30 }`

**Verify Enrollment in Database:**
```powershell
psql -U postgres -d Major -c "SELECT username, biometric_enrolled, biometric_template FROM users WHERE username='test_user_001';"
```

Should show:
```
 username       | biometric_enrolled | biometric_template
----------------+--------------------+--------------------
 test_user_001  | t                  | [binary data]
```

**If Failed:**
- Check Port 5002 terminal for biometric fusion errors
- Ensure webcam captured at least 20 frames
- Try enrolling again with better lighting

---

## 💸 **Test Scenario 3: Secure Transfer**

### Step 5: Add Beneficiary (if needed)
1. Click **"Beneficiaries"** from dashboard
2. Click **"Add Beneficiary"**
3. Fill in:
   - Name: `John Doe`
   - Account Number: `1234567890`
4. Click **"Add Beneficiary"**

---

### Step 6: Perform Secure Transfer
1. From dashboard, click **"Transfer"** button
2. Select beneficiary: `John Doe`
3. Enter amount: `100`
4. Click **"Transfer with Biometric Auth"**
5. Webcam activates automatically
6. **Stay still** for 3 seconds while it captures
7. Watch authentication progress (0% → 100%)
8. Wait for biometric verification

**Expected Result (SUCCESS - Score ≥ 0.65):**
- ✅ Progress bar completes
- ✅ Message: "Authenticating with biometrics..."
- ✅ Success: "Transfer successful! New balance: ₹X"
- ✅ Biometric scores displayed:
  ```
  Face Score: 92%
  Hand Score: 85%
  Style Score: 78%
  Fusion Score: 88% ✅ (≥ 65% threshold)
  ```
- ✅ Redirect to dashboard after 3 seconds
- ✅ Transaction appears in history

**Expected Result (FAIL - Score < 0.65):**
- ❌ Message: "Authentication failed (Score: 0.38)"
- ❌ Biometric scores shown below threshold
- ❌ Transfer NOT completed
- ❌ Balance unchanged

**Verify Transfer in Database:**
```powershell
psql -U postgres -d Major -c "SELECT * FROM transactions WHERE from_user = (SELECT id FROM users WHERE username='test_user_001') ORDER BY timestamp DESC LIMIT 1;"
```

**If Transfer Failed:**
- Make sure you're the same person who enrolled
- Ensure good lighting conditions
- Try to match the enrollment conditions (similar position, distance)
- Check Port 5002 terminal for verification errors

---

## 🤟 **Test Scenario 4: Sign Language Support**

### Step 7: Submit Sign Language Query
1. From dashboard, click **"Support"** menu
2. Click **"Sign Language Recognition"**
3. Click **"Start Recording"** button
4. Wait for 3-second countdown (3... 2... 1...)
5. **Perform sign language** for 5 seconds:
   - Example signs to try:
     - HELP (raised hand)
     - MONEY (rubbing fingers)
     - ACCOUNT (pointing gesture)
     - PROBLEM (crossed hands)
6. Watch progress bar (0% → 100%)
7. Wait for recognition processing

**Expected Result:**
- ✅ Recording completes (50 frames captured)
- ✅ Message: "Recognizing sign language with hybrid system..."
- ✅ Recognition result displayed:
  ```
  Sign: "HELP"
  Intent: customer_support
  Confidence: 95%
  (Enhanced by SLM)
  ```
- ✅ Generated query shown:
  ```
  "I need help with banking services"
  ```
- ✅ Ticket auto-created
- ✅ Auto-redirect to Support Tickets page after 2 seconds

**Verify Ticket in Database:**
```powershell
psql -U postgres -d Major -c "SELECT id, query_text, sign_recognized, intent_detected, slm_used, confidence_score FROM support_tickets WHERE user_id = (SELECT id FROM users WHERE username='test_user_001') ORDER BY created_at DESC LIMIT 1;"
```

Should show:
```
 id | query_text                              | sign_recognized | intent_detected    | slm_used | confidence_score
----+-----------------------------------------+-----------------+--------------------+----------+-----------------
 45 | I need help with banking services       | HELP            | customer_support   | t        | 0.95
```

**If Failed:**
- Check Port 5003 terminal (NS-AGF service) for recognition errors
- Check Port 5004 terminal (SLM service) for query generation errors
- Try performing clearer, more distinct signs
- Ensure good lighting and clear hand visibility

---

## 📊 **Test Scenario 5: View Support Tickets**

### Step 8: View Ticket List
1. After auto-redirect to `/support-tickets`
2. You should see your newly created ticket

**Expected Result:**
- ✅ Ticket list displays with:
  - Ticket ID
  - Query text: "I need help with banking services"
  - Status: "pending"
  - Sign recognized: "HELP"
  - Intent: "customer_support"
  - Created timestamp

---

## 🔍 **Verification Commands**

### Check All Database Data:
```powershell
# Users table
psql -U postgres -d Major -c "SELECT id, username, email, face_registered, biometric_enrolled FROM users WHERE username='test_user_001';"

# Transactions table
psql -U postgres -d Major -c "SELECT * FROM transactions WHERE from_user = (SELECT id FROM users WHERE username='test_user_001');"

# Support tickets table
psql -U postgres -d Major -c "SELECT * FROM support_tickets WHERE user_id = (SELECT id FROM users WHERE username='test_user_001');"
```

---

## 🐛 **Troubleshooting**

### Issue 1: "Face not recognized" during login
**Solution:**
- Re-register with better face photo
- Ensure good lighting
- Face camera directly
- Remove glasses/hats if worn during registration

---

### Issue 2: "Biometric verification service unavailable"
**Solution:**
```powershell
# Restart biometric service
cd "d:\MAJOR-PROJECT - Copy"
python biometric_fusion_service_enhanced.py
# Wait for "Running on http://127.0.0.1:5002"
```

---

### Issue 3: "Biometric authentication failed" during transfer
**Causes:**
- Different person attempting transfer
- Poor lighting conditions
- Face/hands not clearly visible
- Too much movement during capture

**Solution:**
- Ensure same person who enrolled
- Improve lighting
- Stay still during capture
- Re-enroll if consistently failing

---

### Issue 4: "Sign not recognized"
**Solution:**
- Perform clearer, more distinct signs
- Ensure hands are fully visible
- Better lighting
- Try common banking signs (MONEY, HELP, ACCOUNT)

---

### Issue 5: Frontend won't start
**Solution:**
```powershell
# Reinstall dependencies
cd "d:\MAJOR-PROJECT - Copy\frontend"
npm install
npm start
```

---

## ✅ **Complete Test Checklist**

```
□ Register new user with face
□ Login with face authentication
□ Dashboard loads with enrollment banner
□ Click "Enroll Now"
□ Complete biometric enrollment (30 frames)
□ Return to dashboard (banner disappears)
□ Navigate to Transfer page
□ Select beneficiary and enter amount
□ Complete biometric verification (30 frames)
□ Transfer succeeds with score ≥ 0.65
□ Transaction appears in history
□ Navigate to Sign Recognition
□ Record sign language (50 frames)
□ Sign recognized with intent detection
□ SLM generates banking query
□ Ticket auto-created
□ View ticket in Support Tickets page
□ All database records verified
```

---

## 🎉 **Success Criteria**

**System is PRODUCTION READY if:**
- ✅ All 5 services running without errors
- ✅ User can register and login with face
- ✅ Dashboard shows enrollment banner
- ✅ Biometric enrollment completes successfully
- ✅ Secure transfer works with biometric verification
- ✅ Sign language recognition creates ticket with hybrid AI
- ✅ All database records are correct
- ✅ No console errors in browser or terminals

---

## 📞 **Support**

If you encounter persistent issues:

1. **Check Service Logs**:
   - Look at all terminal outputs
   - Check for Python errors
   - Check for Node.js errors

2. **Verify Ports**:
   ```powershell
   netstat -ano | findstr "5000 5001 5002 5003 5004 3000"
   ```

3. **Restart Everything**:
   - Stop all terminals (Ctrl+C)
   - Wait 10 seconds
   - Restart all services in order

4. **Check Database**:
   ```powershell
   psql -U postgres -d Major -c "\dt"
   ```

---

**Last Updated**: January 4, 2026  
**Testing Status**: Ready for Execution 🚀
