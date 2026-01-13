# Multi-Factor Authentication Setup Guide

## Overview

The NS-AGF Banking System now supports **Multi-Factor Authentication (MFA)** with three authentication methods:
- 🔐 **Face Recognition** - Biometric face authentication
- 🎤 **Voice Authentication** - Voice biometric verification
- 📧 **OTP (One-Time Password)** - Email-based OTP verification (for login only)

Users register with **Face and Voice**, then can login using **any method** (Face, Voice, or OTP) for maximum security and flexibility.

---

## Table of Contents

1. [Database Setup](#database-setup)
2. [Backend Configuration](#backend-configuration)
3. [Frontend Components](#frontend-components)
4. [API Endpoints](#api-endpoints)
5. [Testing Guide](#testing-guide)
6. [Troubleshooting](#troubleshooting)

---

## Database Setup

### Step 1: Run Database Migration

Execute the SQL script to add multi-auth support to your database:

```bash
# In Supabase SQL Editor or PostgreSQL client
psql -U your_user -d your_database -f backend/database_schema_multiauth.sql
```

Or copy and paste the contents of `backend/database_schema_multiauth.sql` into your Supabase SQL Editor.

### Step 2: Verify Tables

The migration creates/updates the following:

**Users Table Columns:**
- `phone` - User phone number
- `otp` - One-time password for login (6 digits)
- `otp_expires` - OTP expiration timestamp
- `otp_verified` - Whether user verified email via OTP
- `voice_registered` - Voice authentication status
- `voice_data` - Voice biometric data (JSONB)
- `face_embedding` - Face biometric embedding (JSONB)

**New Tables:**
- `temp_registrations` - Temporary storage for registration OTPs

### Step 3: Verify Migration

```sql
-- Check if columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('phone', 'otp', 'voice_data', 'face_embedding');

-- Check if temp_registrations table exists
SELECT * FROM temp_registrations LIMIT 1;
```

---

## Backend Configuration

### Step 1: Update Environment Variables

Ensure your `.env` file has email configuration:

```env
# Email Configuration (for OTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=your-email@gmail.com

# JWT Secret
JWT_SECRET=your-secret-key-here

# API Ports
PORT=5000
VOICE_SERVICE_PORT=5001
BIOMETRIC_SERVICE_PORT=5002
```

### Step 2: Install Dependencies

```bash
cd backend
npm install form-data axios
```

### Step 3: Start Backend Services

```bash
# Option 1: Start all services at once
.\start_all_services.bat

# Option 2: Start services individually
cd backend
node index.js

cd python_service
python app.py

cd ..
python biometric_fusion_service_enhanced.py

cd ns_agf
python api_service.py

cd frontend
npm start
```

---

## Frontend Components

### New Components Created

1. **MultiAuthRegister.js** - Multi-step registration with Face, Voice, and OTP
2. **MultiAuthLogin.js** - Unified login with method selection (Face, Voice, or OTP)
3. **MultiAuth.css** - Comprehensive styling for both components

### Component Features

#### Registration Flow:
1. **Step 1:** Basic Information (username, email, phone)
2. **Step 2:** Face Authentication (capture photo)
3. **Step 3:** Voice Authentication (record audio)
4. **Step 4:** OTP Verification (email-based)
5. **Step 5:** Success & Redirect to Dashboard

#### Login Flow:
- **Tab-based selection:** Choose Face, Voice, or OTP
- **Unified interface:** Single component handles all methods
- **Real-time validation:** Immediate feedback on authentication

### Routes Updated

```javascript
// New multi-auth routes
/register → MultiAuthRegister (Face + Voice + OTP)
/login → MultiAuthLogin (Face OR Voice OR OTP)

// Legacy routes (backwards compatibility)
/register-face → Register (Face only)
/login-face → Login (Face only)
/voice/register → Register (Voice only)
/voice/login → Login (Voice only)
/otp-login → OTPLogin (OTP only)
```

---

## API Endpoints

### Registration Endpoints

#### 1. Send OTP for Registration
```http
POST /api/auth/send-otp-register
Content-Type: application/json

{
  "email": "user@example.com"
}

Response:
{
  "success": true,
  "message": "OTP sent successfully",
  "email": "user@example.com"
}
```

#### 2. Multi-Auth Registration
```http
POST /api/auth/register-multi
Content-Type: multipart/form-data

Fields:
- username: string
- email: string
- phone: string
- face: file (image/jpeg)
- voice: file (audio/wav)

Response:
{
  "success": true,
  "message": "Registration successful",
  "token": "jwt-token-here",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### Login Endpoints

#### 3. Face Login
```http
POST /api/login
Content-Type: multipart/form-data

Fields:
- username: string
- image: file (image/jpeg)

Response:
{
  "success": true,
  "token": "jwt-token-here",
  "user": { ... }
}
```

#### 4. Voice Login
```http
POST /api/voice/login
Content-Type: multipart/form-data

Fields:
- username: string
- audio: file (audio/wav)

Response:
{
  "success": true,
  "token": "jwt-token-here",
  "scores": {
    "combined": 0.85,
    "embedding": 0.90,
    "biometric": 0.75
  }
}
```

#### 5. OTP Login (Send)
```http
POST /api/otp/send
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "john_doe"
}

Response:
{
  "success": true,
  "message": "OTP sent successfully",
  "email": "u***@example.com"
}
```

#### 6. OTP Login (Verify)
```http
POST /api/otp/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "john_doe",
  "otp": "123456"
}

Response:
{
  "success": true,
  "token": "jwt-token-here",
  "username": "john_doe"
}
```

---

## Testing Guide

### Test Registration Flow

1. **Navigate to Registration Page**
   ```
   http://localhost:3000/register
   ```

2. **Fill Basic Information**
   - Enter unique username
   - Enter valid email
   - Enter phone number (10+ digits)

3. **Capture Face**
   - Allow camera access
   - Position face in frame
   - Click "Capture Face"

4. **Record Voice**
   - Allow microphone access
   - Click "Start Recording"
   - Speak clearly for 5-10 seconds
   - Click "Stop Recording"

5. **Complete Registration**
   - Click "Complete Registration"
   - Wait for processing

6. **Verify Success**
   - Should see success message
   - Redirected to dashboard
   - JWT token stored in localStorage

### Test Login Flow

#### Face Login
1. Navigate to `http://localhost:3000/login`
2. Enter username
3. Select "Face" tab
4. Capture face photo
5. Click "Login with Face"

#### Voice Login
1. Navigate to `http://localhost:3000/login`
2. Enter username
3. Select "Voice" tab
4. Record voice sample
5. Click "Login with Voice"

#### OTP Login
1. Navigate to `http://localhost:3000/login`
2. Enter username or email
3. Select "OTP" tab
4. Click "Send OTP"
5. Enter 6-digit OTP from email
6. Click "Login with OTP"

---

## Troubleshooting

### Issue: OTP Email Not Received

**Solution:**
1. Check SMTP configuration in `.env`
2. Verify email service is running
3. Check spam folder
4. For Gmail, enable "App Passwords": https://myaccount.google.com/apppasswords

```bash
# Test email service
cd backend
node -e "require('./utils/emailService').sendOTP('test@example.com', '123456').then(console.log)"
```

### Issue: Face Recognition Fails

**Solution:**
1. Ensure Python service is running on port 5001
2. Check face is clearly visible in webcam
3. Verify adequate lighting

```bash
# Test face service
cd python_service
python app.py
# Visit http://localhost:5001/health
```

### Issue: Voice Authentication Fails

**Solution:**
1. Ensure Python service is running on port 5001
2. Record for at least 5 seconds
3. Speak clearly in quiet environment
4. Check microphone permissions

```bash
# Test voice service
curl -X POST http://localhost:5001/voice-verify \
  -F "audio=@test.wav"
```

### Issue: Database Schema Not Updated

**Solution:**
1. Verify migration script ran successfully
2. Check for SQL errors in console
3. Manually verify columns exist

```sql
-- Verify users table columns
\d users;

-- Check temp_registrations table
SELECT * FROM temp_registrations;
```

### Issue: CORS Errors

**Solution:**
1. Ensure backend allows frontend origin
2. Check CORS configuration in `backend/index.js`

```javascript
// backend/index.js
app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true
}));
```

### Issue: File Upload Errors

**Solution:**
1. Ensure `backend/uploads/` directory exists
2. Check file size limits (10MB max)
3. Verify multer configuration

```bash
# Create uploads directory
mkdir backend/uploads
```

---

## Security Best Practices

1. **OTP Expiration:** OTPs expire after 5 minutes
2. **Password Hashing:** Use bcrypt for password storage (if added)
3. **JWT Expiration:** Tokens expire after 1 hour
4. **HTTPS:** Use HTTPS in production
5. **Rate Limiting:** Limit OTP requests per email/IP
6. **Input Validation:** Sanitize all user inputs
7. **File Validation:** Validate image/audio file types and sizes

---

## Next Steps

1. ✅ Database migration complete
2. ✅ Backend endpoints configured
3. ✅ Frontend components created
4. ⏳ Test registration flow
5. ⏳ Test login flow (all 3 methods)
6. ⏳ Deploy to production

---

## Support

For issues or questions:
- Check logs in browser console (F12)
- Check backend logs in terminal
- Review error messages in UI
- Check database records in Supabase

---

## Summary

You now have a complete **Multi-Factor Authentication** system with:
- ✅ Face Recognition
- ✅ Voice Authentication
- ✅ OTP Verification
- ✅ Unified Registration Flow
- ✅ Flexible Login Options
- ✅ Comprehensive Error Handling
- ✅ Professional UI/UX

Users can register with all three methods and login using any single method they prefer!
