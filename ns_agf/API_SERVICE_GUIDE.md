# NS-AGF API Service - Quick Start Guide

## ✅ Step 1 Complete: NS-AGF API Service Created!

### 📁 Files Created

1. **`ns_agf/api_service.py`** (750 lines)
   - Flask REST API wrapper for NS-AGF
   - 5 endpoints: health, sign recognition, enroll, verify, list users
   - Integrates biometric authentication modules
   - Error handling and logging

2. **`ns_agf/api_requirements.txt`**
   - Flask dependencies for API service

3. **`ns_agf/start_api_service.bat`**
   - Windows startup script

4. **`ns_agf/test_api_service.py`**
   - Test script to verify API endpoints

---

## 🚀 How to Start the NS-AGF API Service

### Option 1: Using the Batch Script (Windows)
```bash
cd ns_agf
start_api_service.bat
```

### Option 2: Manual Start
```bash
cd ns_agf

# Install dependencies (first time only)
pip install -r api_requirements.txt

# Start the service
python api_service.py
```

The service will start on **http://127.0.0.1:5002**

---

## 🧪 Testing the API

After starting the service, test it:

```bash
# In a new terminal
cd ns_agf
python test_api_service.py
```

You should see:
```
✅ Health check PASSED
✅ Sign recognition PASSED (or partial - depending on dummy data)
✅ List users PASSED
```

---

## 📡 API Endpoints

### 1. **Health Check**
```http
GET http://127.0.0.1:5002/api/health
```

Response:
```json
{
  "status": "ok",
  "service": "NS-AGF API",
  "inference_ready": true,
  "biometric_ready": true,
  "enrolled_users": 0
}
```

---

### 2. **Sign Language Recognition** (Customer Support)
```http
POST http://127.0.0.1:5002/api/sign/recognize
Content-Type: application/json

{
  "frames": ["base64_image1", "base64_image2", ...],
  "return_sentence": true
}
```

Response:
```json
{
  "success": true,
  "sign": "hello",
  "confidence": 0.95,
  "sentence": "hello",
  "frames_processed": 30,
  "valid_frames": 28,
  "intent": {
    "is_banking": false
  }
}
```

---

### 3. **Biometric Enrollment** (During Registration)
```http
POST http://127.0.0.1:5002/api/biometric/enroll
Content-Type: multipart/form-data

user_id: "user123"
frame_0: <image file>
frame_1: <image file>
...
frame_29: <image file>
```

Response:
```json
{
  "success": true,
  "user_id": "user123",
  "face_biometric": "base64_encoded_pickle",
  "hand_biometric": "base64_encoded_pickle",
  "style_biometric": "base64_encoded_pickle",
  "frames_processed": 30,
  "valid_frames": 28
}
```

---

### 4. **Biometric Verification** (During Transfer)
```http
POST http://127.0.0.1:5002/api/biometric/verify
Content-Type: multipart/form-data

user_id: "user123"
frame_0: <image file>
frame_1: <image file>
...
frame_29: <image file>
```

Response:
```json
{
  "authenticated": true,
  "fusion_score": 0.87,
  "face_score": 0.92,
  "hand_score": 0.85,
  "style_score": 0.79,
  "user_id": "user123",
  "frames_processed": 30,
  "threshold": 0.65
}
```

---

### 5. **List Enrolled Users**
```http
GET http://127.0.0.1:5002/api/biometric/users
```

Response:
```json
{
  "users": [
    {
      "user_id": "user123",
      "enrolled_date": "2026-01-01 10:30:00",
      "authentication_count": 5,
      "last_authenticated": "2026-01-01 14:20:00"
    }
  ],
  "total": 1
}
```

---

## 🔗 How Backend Will Use This API

### Example: Enrollment (Backend -> NS-AGF API)
```javascript
// backend/services/biometricService.js
const FormData = require('form-data');
const axios = require('axios');

async function enrollBiometrics(frames, userId) {
  const form = new FormData();
  form.append('user_id', userId);
  
  frames.forEach((frame, i) => {
    form.append(`frame_${i}`, frame, `frame_${i}.jpg`);
  });
  
  const response = await axios.post(
    'http://127.0.0.1:5002/api/biometric/enroll',
    form,
    { headers: form.getHeaders() }
  );
  
  return response.data;
}
```

---

## 📊 System Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   React     │         │   Node.js   │         │   NS-AGF    │
│  Frontend   │ ◄─────► │   Backend   │ ◄─────► │  API (5002) │
│  (Port 3000)│         │  (Port 5000)│         │   Python    │
└─────────────┘         └─────────────┘         └─────────────┘
                                                        │
                                                        ▼
                                              ┌──────────────────┐
                                              │  Biometric DB    │
                                              │  (SQLite)        │
                                              └──────────────────┘
```

---

## ✅ What's Next?

**Step 1 is COMPLETE!** ✨

You now have a working REST API that bridges your NS-AGF Python code with the Node.js backend.

### Next Steps:
- **Step 2**: Create `backend/services/biometricService.js`
- **Step 3**: Update database schema (add biometric columns)
- **Step 4**: Add enrollment endpoint in backend
- **Step 5**: Update transfer with biometric verification

---

## 🐛 Troubleshooting

### Service won't start
```bash
# Check if port 5002 is already in use
netstat -ano | findstr :5002

# Kill the process if needed
taskkill /PID <process_id> /F

# Try starting again
python api_service.py
```

### Model not found error
```
❌ Model not found at: D:\MAJOR-PROJECT - Copy\ns_agf\models\ns_agcn.pth
```

**Solution**: Ensure `ns_agcn.pth` exists in the `models/` folder.

### Biometric modules error
```
⚠️ Biometric auth disabled: No module named 'src.auth'
```

**Solution**: Ensure all NS-AGF modules are properly installed:
```bash
cd ns_agf
pip install -r requirements_nsagf.txt
```

---

## 📝 Testing Checklist

- [x] API service starts without errors
- [x] Health check returns status "ok"
- [x] Can list enrolled users (empty initially)
- [ ] Sign recognition works (needs real webcam frames)
- [ ] Biometric enrollment works (needs real webcam frames)
- [ ] Biometric verification works (needs enrolled users)

---

## 🎉 Success!

The NS-AGF API Service is now the **bridge** between:
- Your existing NS-AGF sign language recognition
- Your Node.js backend
- Your React frontend

All communication will go through this API! 🚀
