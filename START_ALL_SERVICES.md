# 🚀 START ALL SERVICES - Complete Integration Guide

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- ✅ Node.js (v16+) and npm installed
- ✅ Python (v3.8+) installed
- ✅ PostgreSQL/Supabase database configured
- ✅ All dependencies installed (see below)

---

## 🔧 STEP 1: Database Setup

### Run Database Schema Scripts

Open your **PostgreSQL/Supabase SQL Editor** and execute:

1. **Biometric Schema** (if not already done):
```bash
# Open: backend/database_schema_biometric.sql
# Execute all SQL commands in your database
```

2. **Support Tickets Schema** (if not already done):
```bash
# Open: backend/database_schema_tickets.sql
# Execute all SQL commands in your database
```

### Verify Database Tables:
```sql
-- Check users table has biometric columns
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name LIKE '%biometric%';

-- Expected: face_biometric, hand_biometric, style_biometric, biometric_registered_at

-- Check support tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('support_tickets', 'ticket_responses', 'biometric_auth_log');
```

---

## 🐍 STEP 2: Install Python Dependencies

### Terminal 1: Install NS-AGF Dependencies

```powershell
# Navigate to project root
cd "d:\MAJOR-PROJECT - Copy"

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask; import cv2; import numpy; print('✅ Python dependencies installed')"
```

**Expected packages:**
- Flask 3.1.1
- flask-cors 5.0.1
- opencv-python
- numpy
- torch
- speechbrain
- insightface
- mediapipe

---

## 📦 STEP 3: Install Node.js Dependencies

### Terminal 2: Install Backend Dependencies

```powershell
# Navigate to backend
cd "d:\MAJOR-PROJECT - Copy\backend"

# Install dependencies
npm install

# Verify installation
npm list axios express pg jsonwebtoken form-data
```

**Expected packages:**
- express 5.1.0
- axios 1.9.0
- pg 8.16.0
- jsonwebtoken 9.0.2
- bcrypt 6.0.0
- multer
- nodemailer
- razorpay

### Terminal 3: Install Frontend Dependencies

```powershell
# Navigate to frontend
cd "d:\MAJOR-PROJECT - Copy\frontend"

# Install dependencies
npm install

# Verify installation
npm list react react-router-dom react-webcam axios
```

**Expected packages:**
- react 19.1.0
- react-router-dom 6.30.1
- react-webcam 7.2.0
- axios 1.10.0
- bootstrap 5.3.6

---

## 🎯 STEP 4: Configure Environment Variables

### Backend Configuration

Create/update `backend/.env`:

```env
# Database Configuration (Supabase)
DB_USER=your_database_user
DB_HOST=your_supabase_host.supabase.co
DB_NAME=postgres
DB_PASSWORD=your_database_password
DB_PORT=5432

# JWT Secret
JWT_SECRET=your_secret_key_here

# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret

# Email Configuration (for support tickets)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# NS-AGF Service URL
NS_AGF_SERVICE_URL=http://127.0.0.1:5002

# Server Configuration
PORT=5000
NODE_ENV=development
```

---

## 🚀 STEP 5: Start All Services (3 Terminals)

### Terminal 1: Start NS-AGF Python API Service (Port 5002)

```powershell
# Navigate to ns_agf directory
cd "d:\MAJOR-PROJECT - Copy\ns_agf"

# Start the Flask API service
python api_service.py
```

**Expected Output:**
```
========================================
NS-AGF REST API Service Starting...
========================================

✅ Sign Language Inference System loaded
✅ Biometric Fusion Authenticator initialized
✅ User Biometric Database ready

 * Serving Flask app 'api_service'
 * Debug mode: on
 * Running on http://127.0.0.1:5002

Press CTRL+C to quit
```

**API Endpoints Available:**
- GET  `http://127.0.0.1:5002/api/health` - Health check
- POST `http://127.0.0.1:5002/api/sign/recognize` - Sign language recognition
- POST `http://127.0.0.1:5002/api/biometric/enroll` - Biometric enrollment
- POST `http://127.0.0.1:5002/api/biometric/verify` - Biometric verification

---

### Terminal 2: Start Node.js Backend (Port 5000)

```powershell
# Navigate to backend directory
cd "d:\MAJOR-PROJECT - Copy\backend"

# Start the backend server
node index.js
```

**Expected Output:**
```
Server is running on http://localhost:5000
Database connected successfully!
✅ Email polling service started
```

**API Endpoints Available:**
- POST `http://localhost:5000/api/auth/register-face` - Face registration
- POST `http://localhost:5000/api/auth/login-face` - Face login
- POST `http://localhost:5000/api/auth/send-otp` - Send OTP
- POST `http://localhost:5000/api/auth/verify-otp` - Verify OTP
- POST `http://localhost:5000/api/biometric/enroll` - Enroll biometrics
- POST `http://localhost:5000/api/account/secure-transfer` - Secure transfer
- POST `http://localhost:5000/api/biometric/recognize-sign` - Recognize sign
- GET  `http://localhost:5000/api/support/tickets` - Get support tickets
- POST `http://localhost:5000/api/support/tickets` - Create support ticket

---

### Terminal 3: Start React Frontend (Port 3000)

```powershell
# Navigate to frontend directory
cd "d:\MAJOR-PROJECT - Copy\frontend"

# Start the React development server
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled successfully
```

**Frontend Routes Available:**
- `/` - Home page
- `/register` - User registration (face + biometric enrollment)
- `/login` - User login (face or OTP)
- `/dashboard` - User dashboard
- `/transfer` - Money transfer (with biometric auth)
- `/support-tickets` - Support tickets list
- `/sign-recognition` - Sign language recognition for support

---

## 🧪 STEP 6: Test the Complete Integration

### Test 1: Health Checks

```powershell
# Test NS-AGF API health
curl http://127.0.0.1:5002/api/health

# Expected: {"status": "healthy", "message": "NS-AGF API is running"}

# Test Backend health
curl http://localhost:5000/api/health

# Expected: {"status": "OK"}
```

### Test 2: User Registration Flow

1. **Open Browser**: http://localhost:3000
2. **Click "Register"**
3. **Enter details** (name, email, phone, password)
4. **Capture face** (webcam will activate)
5. **Automatic biometric enrollment** happens after face registration
6. **Check console logs** for biometric enrollment success

**What happens behind the scenes:**
```
Frontend (Register.js) 
  → POST /api/auth/register-face (Node.js Backend)
  → Stores user in database
  → Triggers enrollBiometrics()
  → POST /api/biometric/enroll (Node.js Backend)
  → biometricService.enrollBiometrics() (Node.js Service)
  → POST /api/biometric/enroll (NS-AGF Python API)
  → Returns face/hand/style features
  → Stores in users table (face_biometric, hand_biometric, style_biometric)
```

### Test 3: Secure Transfer Flow

1. **Login to dashboard**
2. **Navigate to "Transfer Money"**
3. **Select beneficiary and enter amount**
4. **Click "Transfer"**
5. **Webcam activates** for biometric authentication
6. **Watch progress bar** (0-100%)
7. **See biometric scores** (face, hand, style)
8. **Transfer completes** if authentication successful

**What happens behind the scenes:**
```
Frontend (Transfer.js)
  → Captures 30 video frames
  → POST /api/account/secure-transfer with videoFrames
  → bankController.secureTransfer() (Node.js Backend)
  → biometricService.verifyBiometrics() (Node.js Service)
  → POST /api/biometric/verify (NS-AGF Python API)
  → Returns similarity scores
  → Checks if scores > 0.7 threshold
  → Executes transfer or rejects
  → Logs to biometric_auth_log table
```

### Test 4: Sign Language Recognition

1. **Navigate to "Support Tickets"**
2. **Click "New Sign Language Query"**
3. **Click "Start Recording"**
4. **3-second countdown** appears
5. **5-second recording** (50 frames)
6. **Watch progress bar**
7. **See recognized text**
8. **Edit if needed** and submit

**What happens behind the scenes:**
```
Frontend (SignRecognition.js)
  → Captures 50 video frames over 5 seconds
  → POST /api/biometric/recognize-sign with videoFrames
  → userController.recognizeSignLanguage() (Node.js Backend)
  → biometricService.recognizeSign() (Node.js Service)
  → POST /api/sign/recognize (NS-AGF Python API)
  → Returns recognized signs and sentence
  → Frontend displays editable text
  → POST /api/support/tickets with query_source: 'sign_language'
  → Ticket created in database
```

---

## 🔍 STEP 7: Monitor and Debug

### Check NS-AGF Service Logs (Terminal 1)

Look for:
- ✅ `Processing sign recognition request...`
- ✅ `Biometric enrollment completed successfully`
- ✅ `Biometric verification result: face_score=0.85, hand_score=0.82, style_score=0.78`

### Check Backend Logs (Terminal 2)

Look for:
- ✅ `Sign language recognition started`
- ✅ `Processing 50 frames for sign recognition`
- ✅ `Biometric verification result: {face: 0.85, hand: 0.82, style: 0.78}`
- ✅ `Transfer authorized: true`

### Check Browser Console (Terminal 3 / Browser DevTools)

Look for:
- ✅ `Biometric enrollment successful`
- ✅ `Transfer successful`
- ✅ `Sign recognition completed`

### Common Issues and Solutions

**Issue 1: "NS-AGF service unavailable"**
```powershell
# Solution: Make sure Terminal 1 is running api_service.py
cd "d:\MAJOR-PROJECT - Copy\ns_agf"
python api_service.py
```

**Issue 2: "Database connection failed"**
```powershell
# Solution: Check .env file in backend folder
# Verify DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
```

**Issue 3: "Webcam not working"**
```
# Solution: Grant browser permission for camera
# Chrome: Settings → Privacy → Camera → Allow
```

**Issue 4: "Port already in use"**
```powershell
# Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Find and kill process using port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Find and kill process using port 5002
netstat -ano | findstr :5002
taskkill /PID <PID> /F
```

---

## 📊 STEP 8: Verify Database Changes

### Check User Biometric Data

```sql
-- Check if users have biometric data enrolled
SELECT 
  id, 
  email, 
  face_biometric IS NOT NULL as has_face,
  hand_biometric IS NOT NULL as has_hand,
  style_biometric IS NOT NULL as has_style,
  biometric_registered_at
FROM users
WHERE email = 'your_test_email@example.com';
```

### Check Authentication Logs

```sql
-- Check biometric authentication attempts
SELECT 
  user_id,
  transaction_type,
  face_score,
  hand_score,
  style_score,
  fusion_score,
  is_authorized,
  created_at
FROM biometric_auth_log
ORDER BY created_at DESC
LIMIT 10;
```

### Check Support Tickets

```sql
-- Check support tickets from sign language
SELECT 
  id,
  user_email,
  query_text,
  query_source,
  status,
  created_at
FROM support_tickets
WHERE query_source = 'sign_language'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🎉 SUCCESS CHECKLIST

✅ **NS-AGF Python API** running on port 5002  
✅ **Node.js Backend** running on port 5000  
✅ **React Frontend** running on port 3000  
✅ **Database schema** updated with biometric columns  
✅ **User registration** with automatic biometric enrollment working  
✅ **Secure transfer** with biometric authentication working  
✅ **Sign language recognition** for support tickets working  
✅ **All API endpoints** responding correctly  
✅ **Webcam capture** working in frontend  
✅ **Database logs** recording authentication attempts  

---

## 🔄 STOP ALL SERVICES

When you're done testing:

**Terminal 1 (NS-AGF API):** Press `Ctrl+C`  
**Terminal 2 (Backend):** Press `Ctrl+C`  
**Terminal 3 (Frontend):** Press `Ctrl+C`

---

## 📚 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER (PORT 3000)                │
│  React Frontend: Register, Login, Transfer, SignRecognition│
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  NODE.JS BACKEND (PORT 5000)                │
│  - userController: register, login, enroll, recognizeSign   │
│  - bankController: secureTransfer                           │
│  - biometricService: enrollBiometrics, verifyBiometrics     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               NS-AGF PYTHON API (PORT 5002)                 │
│  - Flask REST API                                           │
│  - Sign Language Recognition (93% accuracy)                 │
│  - Biometric Fusion (face + hand + style)                   │
│  - MediaPipe + InsightFace + Behavioral Analysis            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            POSTGRESQL DATABASE (SUPABASE)                   │
│  - users table (with biometric columns)                     │
│  - biometric_auth_log table                                 │
│  - support_tickets table                                    │
│  - accounts, transactions, beneficiaries                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Next Steps

1. **Production Deployment**: Use environment variables for production
2. **SSL/HTTPS**: Configure HTTPS for secure communication
3. **Load Testing**: Test with multiple concurrent users
4. **Error Monitoring**: Set up logging and monitoring (e.g., Sentry)
5. **Backup Strategy**: Implement database backup procedures

---

**🎊 Congratulations! Your NS-AGF integrated banking system is fully operational!**
