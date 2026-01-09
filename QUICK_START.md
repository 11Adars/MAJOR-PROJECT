# 🚀 Quick Start Guide - NS-AGF Banking System

## ⚡ 5-Minute Setup

### Step 1: Install Python Dependencies (2 minutes)
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install all Python packages
pip install -r requirements_complete.txt
```

### Step 2: Install Node.js Dependencies (1 minute)
```bash
# Backend
cd backend
npm install
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### Step 3: Configure Environment (1 minute)
Create `backend/.env` file with your credentials:
```env
DATABASE_URL=your_postgresql_connection_string
JWT_SECRET=your_secret_key
PYTHON_SERVICE_URL=http://127.0.0.1:5001/embed
NS_AGF_SERVICE_URL=http://127.0.0.1:5002
PORT=5000

EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_gmail_app_password
BANK_SUPPORT_EMAIL=bank.email@gmail.com
BANK_EMAIL_PASS=bank_app_password
```

### Step 4: Setup Database (1 minute)
1. Go to https://supabase.com (or use local PostgreSQL)
2. Create project and get connection string
3. Run SQL scripts in SQL Editor:
   - `backend/database_schema_biometric.sql`
   - `backend/database_schema_tickets.sql`

### Step 5: Start Application (30 seconds)
```bash
# Double-click this file:
start_all_services.bat

# Or manually start each service:
# Terminal 1: cd backend && node index.js
# Terminal 2: cd python_service && python app.py
# Terminal 3: python biometric_fusion_service_enhanced.py
# Terminal 4: cd ns_agf && python api_service.py
# Terminal 5: cd frontend && npm start
```

### ✅ You're Done!
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- All services running in separate windows

---

## 🎯 Testing the System

### 1. Register New User
- Go to: http://localhost:3000/register
- Fill form and submit

### 2. Enroll Biometrics
- Login → Quick Actions → "Enroll Biometric"
- Perform sign language gestures in front of camera
- Wait for "Biometric enrolled successfully"

### 3. Try Sign Language
- Go to "Sign Recognition" page
- Toggle "Auto Mode" ON
- Show hand to camera (auto-starts recording)
- Perform signs: "TRANSFER", "MONEY", "100"
- Click "Submit Query"

### 4. Check Support Ticket
- Ticket created in database
- Email sent to you and bank
- Check your email inbox

---

## 🔧 Common Issues

### Port Already in Use
```bash
netstat -ano | findstr :5000
taskkill /PID <number> /F
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
