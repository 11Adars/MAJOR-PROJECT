# 🏦 NS-AGF Banking System - Complete Setup Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Architecture](#architecture)
4. [Installation Steps](#installation-steps)
5. [Database Setup](#database-setup)
6. [Environment Configuration](#environment-configuration)
7. [Model Training (Optional)](#model-training-optional)
8. [Starting the Application](#starting-the-application)
9. [Testing the System](#testing-the-system)
10. [Troubleshooting](#troubleshooting)

**📦 Quick Links:**
- **[Model Download Guide](MODEL_DOWNLOAD_GUIDE.md)** - Complete model download reference
- **[Quick Start Guide](QUICK_START.md)** - 5-minute setup
- **[Transfer Checklist](TRANSFER_CHECKLIST.md)** - Project handover guide

---

## 🎯 Project Overview           

**NS-AGF Banking System** is a multimodal biometric banking application that supports:
- ✅ **Sign Language Recognition** using NS-AGF (Neuro-Symbolic Adaptive Graph Fusion)
- ✅ **Biometric Authentication** (Face + Hand + Behavioral Style Fusion)
- ✅ **Voice Verification** using Speaker Recognition
- ✅ **Email-based Support** with auto-query generation
- ✅ **Secure Transactions** with JWT authentication

### Key Technologies
- **Frontend**: React.js (Port 3000)
- **Backend**: Node.js/Express (Port 5000)
- **Sign Language**: Python/Flask + NS-AGF Model (Port 5003)
- **Biometric Fusion**: Python/Flask + InsightFace (Port 5002)
- **Voice Recognition**: Python/Flask + SpeechBrain (Port 5001)
- **Database**: PostgreSQL (Supabase)

---

## 💻 System Requirements

### Hardware Requirements
- **RAM**: Minimum 8GB (16GB recommended)
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster inference)
- **Storage**: 10GB free space
- **Camera**: Webcam for biometric enrollment and sign language
- **Microphone**: For voice authentication

### Software Requirements
- **Python**: 3.10 or 3.11 (3.12 may have compatibility issues)
- **Node.js**: v18 or higher
- **PostgreSQL**: 14 or higher (or Supabase account)
- **Git**: For cloning the repository
- **Browser**: Chrome/Edge (recommended for webcam support)

### Operating System
- Windows 10/11 (tested)
- Linux (should work with minor path adjustments)
- macOS (should work with minor path adjustments)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│                      Port 3000                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (Node.js/Express)                  │
│                      Port 5000                              │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐               │
│  │ Auth API │  │ Bank API │  │ Support API│               │
│  └──────────┘  └──────────┘  └────────────┘               │
└────┬────────────┬─────────────┬─────────────┬──────────────┘
     │            │             │             │
     ▼            ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│PostgreSQL│  │Voice Rec │  │Biometric │  │Sign Language │
│Database  │  │Service   │  │Fusion    │  │NS-AGF API    │
│(Supabase)│  │Port 5001 │  │Port 5002 │  │Port 5003     │
└──────────┘  └──────────┘  └──────────┘  └──────────────┘
```

---

## 📦 Installation Steps

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd MAJOR-PROJECT
```

### Step 2: Install Python Dependencies

**Create Python Virtual Environment** (HIGHLY RECOMMENDED):

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

**Install All Python Packages**:

```bash
# Install from consolidated requirements file
pip install -r requirements_complete.txt

# If you encounter errors, try upgrading pip first:
python -m pip install --upgrade pip

# For GPU support (optional):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Common Installation Issues**:

- **Error: Microsoft Visual C++ required**
  - Download and install: https://aka.ms/vs/17/release/vc_redist.x64.exe

- **Error: torch installation fails**
  - Use pre-built wheels: `pip install torch==2.0.0 --index-url https://download.pytorch.org/whl/cu118`

- **Error: mediapipe fails**
  - Install separately: `pip install mediapipe==0.10.8 --no-dependencies`

### Step 3: Install Node.js Dependencies

**Backend**:
```bash
cd backend
npm install
cd ..
```

**Frontend**:
```bash
cd frontend
npm install
cd ..
```

### Step 4: Download Pre-trained Models

#### A. NS-AGF Sign Language Model

The NS-AGF model will auto-download on first run. Alternatively, manually download:

```bash
cd ns_agf
python -c "from src.utils.model_loader import fetch_trained_weights; fetch_trained_weights()"
cd ..
```

#### B. SLM (Small Language Model) for Query Generation

The **TinyLlama** model auto-downloads on first use via `ctransformers`:

```bash
# Test SLM download (optional - will auto-download when needed)
cd ns_agf
python -c "from src.slm.query_generator import QueryGenerator; qg = QueryGenerator(use_slm=True)"
cd ..
```

**What happens**:
- Downloads `TinyLlama-1.1B-Chat-v1.0` (quantized GGUF format, ~600MB)
- Cached in: `Sign/slm_model_cache/` or HuggingFace cache
- First download takes 2-5 minutes (depending on internet speed)
- Subsequent runs use cached model (instant)

**If download fails**:
```bash
# Manual download option:
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF', filename='tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')"
```

#### C. Speaker Verification Models

Auto-downloaded by SpeechBrain on first run (no manual action needed).

**Expected Model Locations**:
- `ns_agf/models/nsagf_wlasl100_best.pth` - Sign language model (~50MB)
- `Sign/slm_model_cache/` or `~/.cache/huggingface/` - TinyLlama SLM (~600MB)
- `python_service/pretrained_models/` - Speaker verification models (~200MB)
- Total disk space needed: ~1GB for all models

---

## 🗄️ Database Setup

### Option 1: Using Supabase (Recommended - Cloud)

1. **Create Supabase Account**:
   - Go to https://supabase.com
   - Create new project
   - Note your connection string

2. **Run SQL Scripts**:
   - Open SQL Editor in Supabase Dashboard
   - Run `backend/database_schema_biometric.sql`
   - Run `backend/database_schema_tickets.sql`

3. **Get Connection String**:
   ```
   Format: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
   Example: postgresql://postgres:yourpassword@db.xxx.supabase.co:5432/postgres
   ```

### Option 2: Using Local PostgreSQL

1. **Install PostgreSQL**:
   ```bash
   # Windows: Download from https://www.postgresql.org/download/windows/
   # Linux: sudo apt-get install postgresql postgresql-contrib
   ```

2. **Create Database**:
   ```bash
   psql -U postgres
   CREATE DATABASE banking_system;
   \c banking_system
   ```

3. **Run SQL Scripts**:
   ```bash
   psql -U postgres -d banking_system -f backend/database_schema_biometric.sql
   psql -U postgres -d banking_system -f backend/database_schema_tickets.sql
   ```

### Database Tables Created:
- `users` - User accounts with biometric data
- `transactions` - Transaction history
- `support_tickets` - Sign language support queries
- `ticket_responses` - Bank responses to tickets
- `biometric_auth_log` - Authentication audit trail

---

## 🔐 Environment Configuration

### Backend Configuration (`backend/.env`)

Create `backend/.env` file:

```env
# ============================================
# Database Configuration
# ============================================
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres

# ============================================
# JWT Secret (Generate a strong random key)
# ============================================
JWT_SECRET=YOUR_STRONG_SECRET_KEY_HERE

# ============================================
# Python Microservices URLs
# ============================================
# Voice Recognition Service
PYTHON_SERVICE_URL=http://127.0.0.1:5001/embed

# Biometric Fusion Service
NS_AGF_SERVICE_URL=http://127.0.0.1:5002

# Sign Language Service
SIGN_SERVICE_URL=http://127.0.0.1:5003

# ============================================
# Server Configuration
# ============================================
PORT=5000

# ============================================
# Email Configuration (Gmail Example)
# ============================================
# User email for sending notifications
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_app_password
EMAIL_APP_PASSWORD=your_app_password

# Bank support email (receives customer queries)
BANK_SUPPORT_EMAIL=bank.support@gmail.com
BANK_EMAIL_PASS=bank_app_password

# IMAP Configuration (for reading emails)
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993

# ============================================
# Payment Gateway (Razorpay - Optional)
# ============================================
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

**🔑 How to Get Gmail App Password**:
1. Enable 2-Factor Authentication on your Gmail account
2. Go to: https://myaccount.google.com/apppasswords
3. Create app password for "Mail"
4. Copy the 16-character password (without spaces)
5. Paste in `.env` file

### Frontend Configuration (Optional)

If needed, create `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_NS_AGF_URL=http://localhost:5003
```

---

## 🎓 Model Training (Optional)

**Note**: Pre-trained models are included. Skip this section unless you want to retrain.

### Sign Language Model Training

#### Step 1: Get Dataset from Kaggle

```bash
# Install Kaggle CLI
pip install kaggle

# Configure Kaggle credentials
# 1. Go to https://www.kaggle.com/settings
# 2. Create API token (downloads kaggle.json)
# 3. Place in: C:\Users\YourName\.kaggle\kaggle.json (Windows)

# Download WLASL dataset
kaggle datasets download -d risangbaskoro/wlasl-processed

# Extract to: ns_agf/data/WLASL/
```

#### Step 2: Preprocess Data

```bash
cd ns_agf
python src/data/preprocessing.py \
    --raw_data_path "data/WLASL/videos" \
    --output_path "data/processed" \
    --num_workers 4
```

**Output**:
- `features_landmarks.npy` - Extracted MediaPipe landmarks
- `labels_landmarks.npy` - Sign labels
- `sign_labels.npy` - Class names

#### Step 3: Train Model

```bash
python src/train.py \
    --dataset_path "data/processed" \
    --model_save_path "models/nsagf_custom.pth" \
    --num_epochs 100 \
    --batch_size 32 \
    --learning_rate 0.001
```

**Training Parameters**:
- **Dataset**: WLASL-100 (100 sign classes)
- **Model**: NS-AGF with 6 GCN blocks
- **Optimizer**: Adam with learning rate 0.001
- **Loss**: CrossEntropyLoss
- **Augmentation**: Random spatial/temporal transformations
- **Epochs**: 100-150 (early stopping enabled)

#### Step 4: Validate Model

```bash
python validate_model.py \
    --model_path "models/nsagf_custom.pth" \
    --video_path "test_videos/hello.mp4"
```

---

## 🚀 Starting the Application

### Quick Start (All Services at Once)

**Double-click** `start_all_services.bat` (Windows)

This starts all 5 services in separate terminal windows:
1. Backend Server (Port 5000)
2. Voice Recognition (Port 5001)
3. Biometric Fusion (Port 5002)
4. Sign Language API (Port 5003)
5. Frontend React (Port 3000)

### Manual Start (Individual Services)

#### 1. Start Backend
```bash
cd backend
node index.js
```
**Expected Output**: `Server running on http://localhost:5000`

#### 2. Start Voice Recognition Service
```bash
cd python_service
python app.py
```
**Expected Output**: `Voice service running on http://localhost:5001`

#### 3. Start Biometric Fusion Service
```bash
python biometric_fusion_service_enhanced.py
```
**Expected Output**: `Biometric service running on http://localhost:5002`

#### 4. Start Sign Language Service
```bash
cd ns_agf
python api_service.py
```
**Expected Output**: 
```
Loading NS-AGF model...
✅ Model loaded successfully
API running on http://localhost:5003
```

#### 5. Start Frontend
```bash
cd frontend
npm start
```
**Expected Output**: Browser opens at `http://localhost:3000`

---

## 🧪 Testing the System

### 1. User Registration

1. Navigate to: `http://localhost:3000/register`
2. Fill in:
   - Name, Email, Phone
   - Password (min 8 characters)
   - Account number (10 digits)
3. Click "Register"
4. User created in database

### 2. Biometric Enrollment

1. Login with credentials
2. Go to "Quick Actions" → "Enroll Biometric"
3. Perform sign language gestures (camera required)
4. System captures:
   - **Face features**: 512-dim embedding (InsightFace)
   - **Hand geometry**: 128-dim features
   - **Signing style**: 64-dim behavioral features
5. Biometrics saved to database

### 3. Sign Language Transaction

1. Go to "Sign Recognition" page
2. Toggle **Auto Mode ON**
3. Show hand to camera (triggers auto-recording)
4. Perform sign sequence (e.g., "TRANSFER MONEY 100")
5. System recognizes and displays words
6. Click "Submit Query" to generate ticket

**Example Signs**:
- Financial: TRANSFER, WITHDRAW, DEPOSIT, BALANCE, LOAN
- Numbers: 100, 200, 500, 1000
- Actions: SEND, CHECK, HELP

### 4. Voice Authentication

1. During money transfer
2. Click "Record Voice" button
3. Say any phrase (e.g., "Authorize transfer")
4. System matches against enrolled voice profile

### 5. Support Ticket System

1. Submit sign language query
2. Backend generates natural language query using SLM
3. Email sent to bank support and user
4. Ticket created in database

---

## ⚠️ Troubleshooting

### Common Errors and Solutions

#### 1. Port Already in Use
```
Error: EADDRINUSE: address already in use :::5000
```
**Solution**:
```bash
# Windows: Kill process using port
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Linux/Mac:
lsof -i :5000
kill -9 <process_id>
```

#### 2. Database Connection Failed
```
Error: Connection refused - PostgreSQL
```
**Solution**:
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Test connection: `psql -U postgres -h localhost`
- For Supabase: Check connection string and network

#### 3. Python Module Not Found
```
ModuleNotFoundError: No module named 'torch'
```
**Solution**:
```bash
# Activate virtual environment first!
venv\Scripts\activate
pip install torch mediapipe opencv-python
```

#### 4. Camera Not Working
```
Error: Could not access webcam
```
**Solution**:
- Grant camera permissions in browser
- Check camera is not used by another app
- Use Chrome/Edge (better webcam support)
- Test camera: chrome://settings/content/camera

#### 5. Model Not Found
```
FileNotFoundError: nsagf_wlasl100_best.pth not found
```
**Solution**:
```bash
cd ns_agf
python -c "from src.utils.model_loader import fetch_trained_weights; fetch_trained_weights()"
```

#### 6. CORS Error
```
Access-Control-Allow-Origin blocked
```
**Solution**:
- Ensure `flask-cors` installed: `pip install flask-cors`
- Check backend has `cors` enabled: `npm install cors`
- Restart all services

#### 7. SLM Model Download Failed
```
Error: Cannot download TinyLlama model / Connection timeout
```
**Solution**:
```bash
# Check internet connection
# Try manual download:
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF', filename='tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf', cache_dir='./Sign/slm_model_cache')"

# Or disable SLM (uses fallback queries):
# In api_service.py, set: query_generator = QueryGenerator(use_slm=False)
```

**Note**: SLM is optional - system works with fallback rule-based queries if SLM fails.

#### 8. Email Not Sending
```
Error: Invalid login credentials
```
**Solution**:
- Use App Password, not regular Gmail password
- Enable "Less secure app access" (if not using 2FA)
- Check SMTP settings in `.env`
- Test with: `cd backend && node test_email.js`

#### 9. Frontend Build Errors
```
npm ERR! peer dependency conflict
```
**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### 9. GPU Out of Memory
```
RuntimeError: CUDA out of memory
```
**Solution**:
- Reduce batch size in inference
- Use CPU: Set `device = 'cpu'` in Python services
- Close other GPU applications

#### 10. Slow Recognition Speed
**Solution**:
- Enable GPU if available
- Reduce frame count in `SignRecognition.js` (currently 30 frames)
- Use lighter model (trade-off: accuracy vs speed)

---

## 📊 Service Health Check

Test if all services are running:

```bash
# Backend
curl http://localhost:5000/

# Voice Service
curl http://localhost:5001/health

# Biometric Service
curl http://localhost:5002/health

# Sign Language API
curl http://localhost:5003/health
```

---

## 📁 Project Structure

```
MAJOR-PROJECT/
│
├── backend/                          # Node.js Backend
│   ├── controllers/                  # Route handlers
│   ├── middleware/                   # Auth middleware
│   ├── services/                     # Email polling
│   ├── utils/                        # Email utilities
│   ├── database_schema_biometric.sql # DB schema
│   ├── database_schema_tickets.sql   # Support tickets schema
│   ├── .env                          # Environment variables
│   └── index.js                      # Main server
│
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   │   ├── SignRecognition.js   # Sign language interface
│   │   │   ├── BiometricEnroll.js   # Biometric enrollment
│   │   │   ├── VoiceAuth.js         # Voice authentication
│   │   │   └── ...
│   │   └── App.js                   # Main app
│   └── package.json
│
├── python_service/                   # Voice Recognition Service
│   ├── pretrained_models/           # Speaker verification models
│   └── app.py                       # Flask service (Port 5001)
│
├── ns_agf/                          # Sign Language Service
│   ├── src/
│   │   ├── model/                   # NS-AGF model architecture
│   │   ├── graph/                   # Graph topology
│   │   ├── utils/                   # MediaPipe, preprocessing
│   │   ├── logic/                   # Banking intent verification
│   │   ├── slm/                     # Query generation (TinyLlama)
│   │   └── auth/                    # Biometric fusion
│   ├── models/                      # Trained model weights
│   ├── inference.py                 # Core inference engine
│   └── api_service.py              # Flask API (Port 5003)
│
├── biometric_fusion_service_enhanced.py  # Biometric Service (Port 5002)
├── requirements_complete.txt         # All Python dependencies
├── start_all_services.bat           # Start all services script
└── PROJECT_SETUP_GUIDE.md           # This file
```

---

## 🎯 Key Features

### 1. NS-AGF Sign Language Recognition
- **Architecture**: Adaptive Graph Convolutional Network
- **Input**: MediaPipe Holistic landmarks (75 joints: 33 pose + 21×2 hands)
- **Output**: 100 sign classes (WLASL-100 dataset)
- **Accuracy**: ~92% on validation set
- **Inference Speed**: ~2.3 seconds (30 frames @ 75ms interval)

### 2. Multimodal Biometric Fusion
- **Face**: InsightFace ArcFace embeddings (512-dim)
- **Hand**: Geometric + color features (128-dim)
- **Style**: Optical flow behavioral patterns (64-dim)
- **Fusion**: Weighted score-level (40% face + 35% hand + 25% style)
- **Threshold**: 75% match required for authentication

### 3. Small Language Model (SLM) Integration
- **Model**: TinyLlama-1.1B (quantized INT4)
- **Purpose**: Convert sign words → natural language query
- **Example**: "TRANSFER MONEY 100" → "I want to transfer money, amount is 100 rupees"
- **Fallback**: Rule-based query if SLM unavailable

### 4. Email Auto-Response System
- **Outgoing**: Sends ticket confirmation + query to bank
- **Incoming**: IMAP polling for bank responses
- **Auto-update**: Updates ticket status when reply received

---

## 🔒 Security Features

1. **JWT Authentication**: Secure token-based auth
2. **Password Hashing**: bcrypt with salt rounds
3. **Biometric Encryption**: Base64 pickle serialization
4. **HTTPS Ready**: Configure SSL certificates for production
5. **Rate Limiting**: Prevents brute force attacks
6. **SQL Injection Protection**: Parameterized queries
7. **CORS Configuration**: Restricts API access

---

## 📈 Performance Benchmarks

| Metric | Value |
|--------|-------|
| Sign Recognition Time | ~2.3 seconds (30 frames) |
| Biometric Verification | ~1.5 seconds |
| Voice Authentication | ~2.0 seconds |
| API Response Time | <100ms |
| Database Query Time | <50ms |
| Frontend Load Time | ~3 seconds |

---

## 🤝 Contributing

If you want to contribute to this project:

1. Document any new features
2. Update this setup guide
3. Test on clean environment
4. Update requirements if adding new packages

---

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review console logs in browser (F12)
3. Check terminal outputs for each service
4. Verify all dependencies installed correctly

---

## 📝 Credits

**Developed by**: NS-AGF Team  
**Institution**: [Your Institution]  
**Year**: 2025-2026  
**License**: [Specify License]

**Key Technologies**:
- NS-AGF Architecture (Original Contribution)
- InsightFace (Face Recognition)
- SpeechBrain (Voice Recognition)
- MediaPipe (Landmark Extraction)
- TinyLlama (Query Generation)
- React.js, Node.js, Flask, PostgreSQL

---

## 🎓 Academic References

If using this project for research, please cite:

```
[Your Paper Citation]
Title: NS-AGF: Neuro-Symbolic Adaptive Graph Fusion for Sign Language Banking
Conference/Journal: [Name]
Year: 2026
```

---

**Last Updated**: January 9, 2026  
**Version**: 1.0.0  
**Status**: Production Ready ✅
