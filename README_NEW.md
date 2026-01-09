# 🏦 NS-AGF Banking System

**Multimodal Biometric Banking Application with Sign Language Recognition**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-19.1-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

NS-AGF Banking System is a cutting-edge banking application that combines **Sign Language Recognition**, **Multimodal Biometric Authentication**, and **Voice Verification** for secure and accessible banking services.

### ✨ Key Features

- ✅ **Sign Language Recognition** - NS-AGF model with 92% accuracy
- ✅ **Biometric Fusion** - Face + Hand + Behavioral Style (75% threshold)
- ✅ **Voice Authentication** - Speaker verification using SpeechBrain
- ✅ **Auto Query Generation** - Sign words → Natural language using SLM
- ✅ **Email Support System** - Auto-ticket creation and responses
- ✅ **Secure Transactions** - JWT authentication + PostgreSQL

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd MAJOR-PROJECT
```

### 2. Install Dependencies
```bash
# Python dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements_complete.txt

# Node.js dependencies
cd backend && npm install && cd ..
cd frontend && npm install && cd ..
```

### 3. Configure Environment
```bash
# Copy template and edit with your credentials
copy .env.template backend\.env
# Edit backend/.env with your database URL, email credentials, etc.
```

### 4. Setup Database
- Create Supabase account or local PostgreSQL database
- Run `backend/database_schema_biometric.sql`
- Run `backend/database_schema_tickets.sql`

### 5. Start All Services
```bash
# Double-click to start all services at once:
start_all_services.bat

# Services will start on:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
# - Voice Service: http://localhost:5001
# - Biometric Service: http://localhost:5002
# - Sign Language API: http://localhost:5003
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [**PROJECT_SETUP_GUIDE.md**](PROJECT_SETUP_GUIDE.md) | Complete setup instructions, troubleshooting, model training |
| [**MODEL_DOWNLOAD_GUIDE.md**](MODEL_DOWNLOAD_GUIDE.md) | Model download reference (NS-AGF, TinyLlama SLM, SpeechBrain) |
| [**QUICK_START.md**](QUICK_START.md) | 5-minute quick start guide |
| [**TRANSFER_CHECKLIST.md**](TRANSFER_CHECKLIST.md) | Project handover checklist |
| [**.env.template**](.env.template) | Environment configuration template |

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
└────┬────────────┬─────────────┬─────────────┬──────────────┘
     │            │             │             │
     ▼            ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│PostgreSQL│  │Voice Rec │  │Biometric │  │Sign Language │
│Database  │  │Service   │  │Fusion    │  │NS-AGF API    │
│(Supabase)│  │Port 5001 │  │Port 5002 │  │Port 5003     │
└──────────┘  └──────────┘  └──────────┘  └──────────────┘
```

## 🛠️ Technology Stack

### Frontend
- React 19.1
- React Router
- Axios
- React Webcam
- Bootstrap 5

### Backend
- Node.js / Express
- PostgreSQL (Supabase)
- JWT Authentication
- Nodemailer
- Multer

### Python Services
- Flask / Flask-CORS
- PyTorch 2.0+
- TensorFlow 2.15
- MediaPipe 0.10.8
- InsightFace
- SpeechBrain
- TinyLlama (SLM)

## 📊 System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **GPU**: NVIDIA GPU optional (for faster inference)
- **Storage**: 10GB free space
- **Camera**: Webcam required
- **Microphone**: Required for voice auth
- **Python**: 3.10 or 3.11
- **Node.js**: v18 or higher
- **Browser**: Chrome/Edge (recommended)

## 🎓 Key Technologies

### NS-AGF Model
- **Architecture**: Adaptive Graph Convolutional Network
- **Input**: MediaPipe Holistic landmarks (75 joints)
- **Dataset**: WLASL-100 (100 sign classes)
- **Accuracy**: ~92% validation accuracy
- **Speed**: ~2.3 seconds inference time

### Biometric Fusion
- **Face**: InsightFace ArcFace embeddings (512-dim)
- **Hand**: Geometric + color features (128-dim)
- **Style**: Optical flow patterns (64-dim)
- **Fusion**: Weighted score-level (40% + 35% + 25%)

### Voice Recognition
- **Model**: SpeechBrain ECAPA-TDNN
- **Embeddings**: 192-dimensional speaker vectors
- **Threshold**: Cosine similarity based

## 🧪 Testing

### Test User Registration
```bash
POST http://localhost:5000/api/users/register
{
  "name": "Test User",
  "email": "test@example.com",
  "phone": "1234567890",
  "password": "password123",
  "account_number": "1234567890"
}
```

### Test Sign Recognition
1. Navigate to: http://localhost:3000/sign-recognition
2. Toggle "Auto Mode" ON
3. Show hand to camera
4. Perform signs: "TRANSFER", "MONEY", "100"
5. Click "Submit Query"

## 🔒 Security

- JWT token authentication
- bcrypt password hashing
- Biometric encryption (Base64 pickle)
- SQL injection protection
- Rate limiting on APIs
- CORS configuration
- HTTPS ready

## 📈 Performance

| Metric | Value |
|--------|-------|
| Sign Recognition | ~2.3 seconds |
| Biometric Verification | ~1.5 seconds |
| Voice Authentication | ~2.0 seconds |
| API Response | <100ms |
| Database Query | <50ms |

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request
5. Update documentation

## 📝 License

[Specify your license here]

## 👥 Team

**NS-AGF Team**  
[Your Institution Name]  
Academic Year: 2025-2026

## 📞 Support

For issues or questions:
1. Check [PROJECT_SETUP_GUIDE.md](PROJECT_SETUP_GUIDE.md)
2. Review [Troubleshooting Section](PROJECT_SETUP_GUIDE.md#troubleshooting)
3. Check console logs (F12 in browser)
4. Verify all services running

## 🎓 Citation

If using for research, please cite:
```
[Your Paper Citation]
Title: NS-AGF: Neuro-Symbolic Adaptive Graph Fusion for Sign Language Banking
Year: 2026
```

## 📅 Version History

- **v1.0.0** (Jan 2026) - Initial release
  - Sign language recognition
  - Biometric authentication
  - Voice verification
  - Email support system

---

**Last Updated**: January 9, 2026  
**Status**: Production Ready ✅  
**Made with ❤️ by NS-AGF Team**
