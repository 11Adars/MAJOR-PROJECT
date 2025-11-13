# System Architecture Diagram

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  React Frontend (http://localhost:3000)                         │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │   │
│  │  │   Home       │  │   Login      │  │   Register       │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘    │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │              Dashboard (Protected)                        │ │   │
│  │  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌─────────────┐   │ │   │
│  │  │  │Balance │  │Transfer│  │History │  │Customer     │   │ │   │
│  │  │  │        │  │        │  │        │  │Support  ⭐  │   │ │   │
│  │  │  └────────┘  └────────┘  └────────┘  └─────────────┘   │ │   │
│  │  │                                            │             │ │   │
│  │  └────────────────────────────────────────────┼─────────────┘ │   │
│  │                                                │                │   │
│  │  ┌─────────────────────────────────────────────▼─────────────┐│   │
│  │  │  SignRecognition Component (/sign-recognition)            ││   │
│  │  │  ┌──────────────────────────────────────────────────┐    ││   │
│  │  │  │  Health Check (checks port 8000)                 │    ││   │
│  │  │  └──────────────────┬───────────────────────────────┘    ││   │
│  │  │                     │                                      ││   │
│  │  │                     ▼                                      ││   │
│  │  │  ┌──────────────────────────────────────────────────┐    ││   │
│  │  │  │  iframe: http://127.0.0.1:8000/                  │    ││   │
│  │  │  │  (Embeds Sign Language Interface)                │    ││   │
│  │  │  └──────────────────────────────────────────────────┘    ││   │
│  │  └──────────────────────────────────────────────────────────┘│   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘

                                │
                                │ API Calls
                                ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES LAYER                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Node.js Backend (http://localhost:5000)                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │   │
│  │  │ User Auth    │  │ Bank Ops     │  │ Transaction     │    │   │
│  │  │ Routes       │  │ Routes       │  │ History         │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘    │   │
│  │         │                 │                    │                │   │
│  └─────────┼─────────────────┼────────────────────┼────────────────┘   │
│            │                 │                    │                     │
│  ┌─────────▼─────────────────▼────────────────────▼────────────────┐   │
│  │             PostgreSQL Database                                  │   │
│  │  ┌───────┐  ┌───────────┐  ┌──────────────┐  ┌─────────────┐  │   │
│  │  │ Users │  │ Accounts  │  │ Transactions │  │ Beneficiaries│  │   │
│  │  └───────┘  └───────────┘  └──────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Python Service (http://127.0.0.1:5001)                         │   │
│  │  ┌──────────────┐  ┌──────────────┐                            │   │
│  │  │ Face Auth    │  │ Voice Auth   │                            │   │
│  │  │ (ArcFace)    │  │ (ECAPA-TDNN) │                            │   │
│  │  └──────────────┘  └──────────────┘                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Sign Service (http://127.0.0.1:8000) ⭐ NEW                    │   │
│  │                                                                  │   │
│  │  ┌────────────────────────────────────────────────────────┐   │   │
│  │  │  Flask Web Server                                       │   │   │
│  │  │                                                          │   │   │
│  │  │  Routes:                                                │   │   │
│  │  │  • GET  /                  → HTML Interface            │   │   │
│  │  │  • GET  /api/health        → Service Status            │   │   │
│  │  │  • POST /api/process-frame → Landmark Extraction      │   │   │
│  │  │  • POST /api/predict       → Sign Recognition         │   │   │
│  │  │  • POST /api/generate-sentence → NLG                  │   │   │
│  │  └────────────────────────────────────────────────────────┘   │   │
│  │                           │                                     │   │
│  │  ┌────────────────────────▼─────────────────────────────────┐ │   │
│  │  │  Processing Pipeline                                      │ │   │
│  │  │                                                            │ │   │
│  │  │  1. ┌──────────────┐                                     │ │   │
│  │  │     │  MediaPipe   │  Extract hand & pose landmarks     │ │   │
│  │  │     │  Holistic    │  75 keypoints × 4 coords = 300     │ │   │
│  │  │     └──────┬───────┘                                     │ │   │
│  │  │            │                                              │ │   │
│  │  │  2. ┌──────▼───────┐                                     │ │   │
│  │  │     │  TensorFlow  │  Sequence Classification           │ │   │
│  │  │     │  LSTM Model  │  30 frames → Sign Label            │ │   │
│  │  │     └──────┬───────┘                                     │ │   │
│  │  │            │                                              │ │   │
│  │  │  3. ┌──────▼───────┐                                     │ │   │
│  │  │     │  TinyLlama   │  Keyword → Natural Language        │ │   │
│  │  │     │  SLM (1.1B)  │  Banking Context Aware             │ │   │
│  │  │     └──────────────┘                                     │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  │                                                                │   │
│  │  Models & Data:                                               │   │
│  │  • saved_model_landmarks/best_landmark_model.keras           │   │
│  │  • processed_data_landmarks/sign_labels.npy                 │   │
│  │  • slm_model_cache/ (TinyLlama weights)                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘

                                │
                                │
                                ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                    CLIENT HARDWARE                                       │
│  ┌────────────────┐                                                     │
│  │   Webcam       │  Video Feed → MediaPipe → Landmarks                │
│  └────────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Sign Recognition Process

```
┌─────────────┐
│   USER      │  Clicks "Customer Support" on Dashboard
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  SignRecognition Component Loads                │
│  • Checks service health (GET /api/health)      │
│  • If OK: Loads iframe                          │
│  • If NOT: Shows error with instructions        │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Sign Interface Loads (HTML page)               │
│  • Requests camera permissions                  │
│  • Initializes MediaPipe                        │
│  • Ready for recording                          │
└──────────────────┬──────────────────────────────┘
                   │
                   │  User clicks "Start Recording"
                   ▼
┌─────────────────────────────────────────────────┐
│  Recording Phase (2-3 seconds)                  │
│  ┌───────────────────────────────────────────┐ │
│  │  1. Capture video frame                   │ │
│  │  2. Convert to base64                     │ │
│  │  3. POST /api/process-frame               │ │
│  │  4. Receive landmarks                     │ │
│  │  5. Store in sequence array               │ │
│  │  6. Repeat every 100ms                    │ │
│  └───────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────┘
                   │
                   │  User clicks "Stop Recording"
                   ▼
┌─────────────────────────────────────────────────┐
│  Sign Prediction Phase                          │
│  ┌───────────────────────────────────────────┐ │
│  │  1. Collect all landmarks from sequence   │ │
│  │  2. Resample to exactly 30 frames         │ │
│  │  3. POST /api/predict                     │ │
│  │     {                                      │ │
│  │       "sequence": [[landmarks], ...]      │ │
│  │     }                                      │ │
│  │  4. Server processes with LSTM model      │ │
│  │  5. Returns prediction & confidence       │ │
│  │     {                                      │ │
│  │       "success": true,                    │ │
│  │       "prediction": "HELP",               │ │
│  │       "confidence": 0.85                  │ │
│  │     }                                      │ │
│  │  6. Add keyword to list                   │ │
│  └───────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────┘
                   │
                   │  User records multiple signs
                   │  Keywords: ["HELP", "ACCOUNT", "BALANCE"]
                   │
                   │  User clicks "Generate Query"
                   ▼
┌─────────────────────────────────────────────────┐
│  Sentence Generation Phase                      │
│  ┌───────────────────────────────────────────┐ │
│  │  1. POST /api/generate-sentence           │ │
│  │     {                                      │ │
│  │       "keywords": ["HELP","ACCOUNT",...]  │ │
│  │     }                                      │ │
│  │  2. Server builds prompt with examples    │ │
│  │  3. TinyLlama processes request           │ │
│  │  4. Generates natural sentence            │ │
│  │     {                                      │ │
│  │       "success": true,                    │ │
│  │       "sentence": "I need help with my    │ │
│  │                    account balance"       │ │
│  │     }                                      │ │
│  │  5. Display generated query               │ │
│  └───────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  User can now:                                  │
│  • Copy the generated text                     │
│  • Submit to customer support chatbot          │
│  • Add more signs                              │
│  • Clear and start over                        │
│  • Navigate back to dashboard                  │
└─────────────────────────────────────────────────┘
```

## Component Integration Map

```
App.js
  ├── Home
  ├── Login
  ├── Register
  └── Dashboard ✓ (Protected Route)
      ├── BalanceCard
      ├── QuickActions
      │   ├── Beneficiaries Button
      │   ├── Transfer Button
      │   ├── History Button
      │   └── Customer Support Button ⭐
      │       └── navigate('/sign-recognition')
      └── TransactionHistory

SignRecognition Component ⭐
  ├── useEffect()
  │   └── Health Check → fetch('/api/health')
  │       ├── Success → Load iframe
  │       └── Fail → Show error
  │
  ├── Iframe Container
  │   └── src="http://127.0.0.1:8000/"
  │       └── templates/index.html
  │           ├── Video Element (webcam)
  │           ├── Control Buttons
  │           ├── Keywords Display
  │           ├── Sentence Display
  │           └── JavaScript Logic
  │               ├── initCamera()
  │               ├── processFrame()
  │               ├── startRecording()
  │               ├── stopRecording()
  │               └── generateSentence()
  │
  └── Back to Dashboard Button
```

## Port Mapping

```
┌──────────────────────┬──────┬─────────────────────────────┐
│ Service              │ Port │ Purpose                     │
├──────────────────────┼──────┼─────────────────────────────┤
│ React Frontend       │ 3000 │ User Interface              │
│ Node.js Backend      │ 5000 │ Main API & Business Logic   │
│ Python Auth Service  │ 5001 │ Face/Voice Recognition      │
│ Sign Service ⭐      │ 8000 │ Sign Language Recognition   │
│ PostgreSQL           │ 5432 │ Database                    │
└──────────────────────┴──────┴─────────────────────────────┘
```

## File Structure

```
d:\MAJOR-PROJECT\
│
├── backend/                     (Port 5000)
│   ├── index.js                 Main API server
│   ├── controllers/
│   │   ├── userController.js
│   │   └── bankController.js
│   └── middleware/
│       └── authMiddleware.js
│
├── frontend/                    (Port 3000)
│   ├── src/
│   │   ├── App.js               Router setup
│   │   └── components/
│   │       ├── Dashboard.js     Main dashboard
│   │       ├── QuickActions.js  Customer Support btn ⭐
│   │       ├── SignRecognition.js     ⭐ Modified
│   │       └── SignRecognition.css    ⭐ Modified
│   └── package.json
│
├── python_service/              (Port 5001)
│   └── app.py                   Face/Voice auth
│
├── Sign/ ⭐                     (Port 8000)
│   ├── sign_service.py          ⭐ Flask server
│   ├── interpreter.py           Standalone version
│   ├── requirements.txt         ⭐ Dependencies
│   ├── start_service.bat        ⭐ Windows startup
│   ├── start_service.sh         ⭐ Linux startup
│   ├── README.md                ⭐ Full docs
│   ├── SETUP.md                 ⭐ Setup guide
│   ├── templates/
│   │   └── index.html           ⭐ Web interface
│   ├── saved_model_landmarks/
│   │   └── best_landmark_model.keras
│   └── processed_data_landmarks/
│       └── sign_labels.npy
│
├── INTEGRATION_SUMMARY.md       ⭐ Overview
├── TESTING_GUIDE.md             ⭐ Test procedures
└── QUICK_START.md               ⭐ Quick reference
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
├─────────────────────────────────────────────────────────────┤
│  React 18 + React Router                                    │
│  Axios (HTTP client)                                         │
│  CSS Modules                                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Node.js + Express                                           │
│  PostgreSQL                                                  │
│  JWT Authentication                                          │
│  Multer (File Upload)                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    AI/ML Services                            │
├─────────────────────────────────────────────────────────────┤
│  Python Services:                                            │
│  • Face Auth: ArcFace (InsightFace)                         │
│  • Voice Auth: ECAPA-TDNN (SpeechBrain)                     │
│  • Sign Recognition: TensorFlow LSTM ⭐                      │
│  • NLG: TinyLlama 1.1B (ctransformers) ⭐                   │
│  • Computer Vision: MediaPipe + OpenCV ⭐                    │
└─────────────────────────────────────────────────────────────┘
```

## Success Flow Visualization

```
✅ Start All Services
    ↓
✅ Navigate to Dashboard
    ↓
✅ Click "Customer Support"
    ↓
✅ Service Health Check Passes
    ↓
✅ Camera Access Granted
    ↓
✅ Record Sign Gesture
    ↓
✅ Sign Recognized (>70% confidence)
    ↓
✅ Keywords Accumulated
    ↓
✅ Generate Natural Sentence
    ↓
✅ Submit to Support / Use Query
    ↓
✅ Navigate Back to Dashboard
```

---

**Legend:**
- ⭐ = New/Modified in this integration
- ✅ = Working/Complete
- ✓ = Existing and working
