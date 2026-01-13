# 🚀 Quick Start Guide - NS-AGF Banking System

## ⚡ 3-Minute Setup & Demo

### Step 1: One-Command Start (30 seconds)
```bash
# Double-click this file or run in terminal:
start_all_services.bat

# Wait ~30 seconds for all services to initialize
```

**Services Starting:**
- ✅ Backend (Port 5000) - Node.js Express
- ✅ Python Face/Voice (Port 5001) - AI Service
- ✅ Biometric Fusion (Port 5002) - Transfer Security
- ✅ Sign Language (Port 5003) - Accessibility
- ✅ Frontend (Port 3000) - React App

### Step 2: Register New User (1 minute)

**Navigate to:** http://localhost:3000/register

**3-Step Registration:**

1. **Basic Information**
   - Username: `demouser`
   - Email: `demo@example.com`
   - Password: `Demo@123`
   - Phone: `1234567890` (optional)
   - Click "Next"

2. **Face Capture (Required)**
   - Position face in camera frame
   - Click "Capture Face"
   - Wait for green checkmark ✅
   - Click "Next"

3. **Voice Recording (Optional)**
   - **Option A:** Click "Start Recording" → Speak for 3-5 seconds → "Complete"
   - **Option B:** Click "⏭️ Skip Voice (Register with Face only)"
   
4. **Success!**
   - Auto-logged in
   - Redirected to dashboard
   - See your auth methods: Face ✅, Voice ✅/❌

### Step 3: Test Login (1 minute)

**Logout and try logging in with:**

**Option A: Face Login** (Fastest)
1. Go to http://localhost:3000/login
2. Click "Face Login" tab
3. Enter username: `demouser`
4. Click "Capture Face"
5. ✅ Logged in!

**Option B: Voice Login** (If enrolled)
1. Click "Voice Login" tab
2. Enter username: `demouser`
3. Click "Start Recording" → Speak → "Stop"
4. ✅ Logged in!

**Option C: OTP Login** (Always available)
1. Click "OTP Login" tab
2. Enter email: `demo@example.com`
3. Click "Send OTP"
4. Check email for 6-digit code
5. Enter code
6. ✅ Logged in!

---

## 🎯 Full Feature Demo

### 1. Biometric Transfer (2 minutes)

**Prerequisites:** Enrolled biometrics (one-time setup)

1. **Enroll Biometrics First:**
   - Dashboard → Quick Actions → "Enroll Biometric"
   - Perform sign language gestures for 10-15 seconds
   - Wait for "Enrollment successful"

2. **Make Secure Transfer:**
   - Dashboard → "Transfer Money"
   - Enter beneficiary details
   - Enter amount
   - Click "Authenticate Transfer"
   - System analyzes: Face + Hand + Behavior
   - Transfer approved if biometrics match!

### 2. Sign Language Recognition (2 minutes)

1. **Navigate:**
   - Dashboard → "Sign Recognition" (in navigation)

2. **Test Sign Language:**
   - Toggle "Auto Mode" ON
   - Show hand to camera (auto-starts recording)
   - Perform signs in sequence:
     - ✋ "TRANSFER"
     - 💰 "MONEY"
     - 🔢 "100"
   - Click "Submit Query"

3. **Check Results:**
   - Support ticket created automatically
   - Email sent to you and bank
   - Check email inbox
   - View ticket in "Support Tickets" section

### 3. Account Management (1 minute)

**Check Balance:**
- Dashboard → Shows current balance
- Or: "Account" → "Balance"

**Transaction History:**
- Dashboard → "Transactions" tab
- View all transfers, deposits, withdrawals

**Add Beneficiary:**
- "Transfer Money" → "Add Beneficiary"
- Enter: Name, Account Number, IFSC
- Quick transfers next time!

---

## 🔧 Prerequisites Setup (If Not Already Done)

### 1. Install Dependencies (5 minutes)

**Python:**
```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install packages
pip install -r requirements.txt
```

**Node.js Backend:**
```bash
cd backend
npm install
cd ..
```

**React Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 2. Setup Database (3 minutes)

**Option A: Supabase (Recommended - Free)**
1. Go to https://supabase.com
2. Create new project
3. Copy connection string
4. Go to SQL Editor
5. Run these SQL files:
   - `backend/database_schema_multiauth.sql`
   - `backend/database_schema_tickets.sql`

**Option B: Local PostgreSQL**
1. Install PostgreSQL
2. Create database: `createdb bankingdb`
3. Run SQL files using pgAdmin or psql

### 3. Configure Environment (2 minutes)

Create `backend/.env`:
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/database

# JWT Secret (use strong random string)
JWT_SECRET=your_super_secret_key_generate_random_string

# Email (for OTP)
EMAIL_USER=your.email@gmail.com
EMAIL_APP_PASSWORD=your_16_digit_app_password

# Port
PORT=5000
```

**Gmail App Password Setup:**
1. Google Account → Security
2. Enable 2-Step Verification
3. App Passwords → Mail → Generate
4. Copy 16-digit password to `.env`

---

## 🐛 Common Issues & Quick Fixes

### Issue 1: Port Already in Use
```bash
# Find and kill process
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Issue 2: Python Service Won't Start
**Check:**
```bash
# Test Python and dependencies
python --version  # Should be 3.12+
pip list | findstr insightface  # Should show version
```

**Fix:**
```bash
pip install -r requirements.txt --upgrade
```

### Issue 3: Voice Auth Shows "Disabled"
```
⚠️ Voice authentication disabled: Could not load this library
```

**Solution:**
```bash
# Reinstall compatible torch versions
pip install torch==2.2.2 torchaudio==2.2.2
```

**Note:** Face + OTP auth still works even if voice is disabled!

### Issue 4: Frontend Won't Start
```bash
cd frontend
npm install --force
npm start
```

### Issue 5: Face Login Says "No Face Registered"
**Solution:** Re-register user with latest code (database schema updated)

### Issue 6: OTP Not Received
**Check:**
- Backend logs show "OTP sent successfully"
- Email in `.env` is correct
- Using Gmail app password (not regular password)
- Check spam folder
- OTP expires in 10 minutes

---

## 📊 System Status Check

### Verify All Services Running

**1. Backend (Port 5000)**
```bash
curl http://localhost:5000/health
# Should return: {"status": "ok"}
```

**2. Python Service (Port 5001)**
```bash
curl http://localhost:5001/
# Should return service info
```

**3. Frontend (Port 3000)**
```
Open: http://localhost:3000
Should load registration page
```

### Check Logs for Errors

**Backend Logs:**
- Window title: "Backend Server - Port 5000"
- Look for: "Server running on port 5000"
- Errors: Check database connection

**Python Service Logs:**
- Window title: "Speaker Verification - Port 5001"
- Look for: "Running on http://127.0.0.1:5001"
- Warnings: Voice may show disabled (OK if face works)

---

## 🎓 Testing Scenarios

### Scenario 1: New User Registration
```

### Camera Not Working
- Grant camera permission in browser
- Use Chrome or Edge
- Close other apps using camera

### Python Module Not Found
```bash
# Make sure virtual environment is activated
venv\Scripts\activate
pip install -r requirements_complete.txt
```

### Database Connection Error
- Check `DATABASE_URL` in `.env`
- Test Supabase connection
- Verify SQL scripts executed

---

## 📚 Full Documentation

For detailed setup, troubleshooting, and model training:
👉 See **PROJECT_SETUP_GUIDE.md**

---

## 🎓 System Architecture

```
Frontend (React 3000) 
    ↓
Backend (Node.js 5000)
    ↓
├─→ Voice Service (Python 5001)
├─→ Biometric Service (Python 5002)
└─→ Sign Language API (Python 5003)
    ↓
PostgreSQL Database
```

---

## ⚙️ Service Ports

| Service | Port | Technology |
|---------|------|------------|
| Frontend | 3000 | React.js |
| Backend | 5000 | Node.js/Express |
| Voice Recognition | 5001 | Python/Flask |
| Biometric Fusion | 5002 | Python/Flask |
| Sign Language | 5003 | Python/Flask |

---

## 📞 Need Help?

1. Check terminal logs for errors
2. Open browser console (F12)
3. Review PROJECT_SETUP_GUIDE.md
4. Check all services are running

---

**Ready to deploy? All services running? Start testing!** 🚀
