# Banking System with Sign Language Recognition - Complete Project Overview

## 🏦 Project Vision & Concept

**BankAssist AI** is a comprehensive banking application designed with accessibility at its core, specifically targeting deaf and hearing-impaired users through an innovative **Adaptive Fusion Approach**. The system combines traditional banking functionality with cutting-edge sign language recognition technology to create an inclusive financial platform.

### Core Philosophy
- **Accessibility First**: Built specifically for deaf and hearing-impaired community
- **Multi-Modal Authentication**: Face, Voice, and OTP-based login options
- **Real-time Sign Language Support**: Integrated ASL recognition for customer support
- **Industry-Standard Security**: JWT tokens, bcrypt hashing, rate limiting

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                        BANKASSIST AI ECOSYSTEM                     │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (React)     │  Backend (Node.js)  │  AI Services (Python) │
│  ├─ Authentication    │  ├─ REST APIs        │  ├─ Face Recognition  │
│  ├─ Banking UI        │  ├─ JWT Security     │  ├─ Voice Recognition │
│  ├─ Transactions      │  ├─ PostgreSQL DB    │  ├─ Sign Language AI  │
│  └─ Sign Recognition  │  └─ Razorpay Gateway │  └─ LLM Integration   │
└─────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Frontend Stack
- **Framework**: React 19.1.0 with Create React App
- **Routing**: React Router DOM 6.30.1
- **Styling**: Component-level CSS with design tokens
- **UI Components**: Custom components with React Icons
- **HTTP Client**: Axios for API communication
- **Authentication**: JWT-based session management

### Backend Stack
- **Runtime**: Node.js with Express.js 5.1.0
- **Database**: PostgreSQL (hosted on Supabase)
- **Authentication**: 
  - JWT tokens with bcrypt hashing
  - Multi-modal biometric authentication
  - OTP via Nodemailer
- **Payment Gateway**: Razorpay integration
- **Security**: 
  - CORS configuration
  - Rate limiting with express-rate-limit
  - Input validation with express-validator
  - File upload handling with Multer

### AI/ML Services
- **Face Recognition**: 
  - InsightFace (ArcFace model)
  - OpenCV for image processing
- **Voice Recognition**: 
  - SpeechBrain ECAPA-TDNN model
  - LibROSA for audio feature extraction
  - PyTorch backend
- **Sign Language Recognition**:
  - MediaPipe Holistic for landmark extraction
  - TensorFlow Lite Transformer model
  - FastAPI for ML model serving
  - Gemini LLM for sentence generation

### Infrastructure & Deployment
- **Development**: Local development environment
- **Database**: Supabase PostgreSQL
- **Payment Processing**: Razorpay (Test Mode)
- **ML Model Hosting**: FastAPI with Uvicorn
- **File Storage**: Local uploads directory

## 🔐 Authentication System

### Multi-Modal Authentication Architecture
```
User Login Options:
├─ Face Authentication
│  ├─ InsightFace ArcFace embedding
│  ├─ 512-dimensional face vectors
│  └─ Cosine similarity matching
├─ Voice Authentication  
│  ├─ ECAPA-TDNN speaker verification
│  ├─ MFCC, F0, spectral features
│  └─ Weighted biometric matching
└─ OTP Authentication
   ├─ Email-based OTP delivery
   ├─ 6-digit numeric codes
   └─ Time-based expiration
```

### Security Implementation
- **JWT Tokens**: 1-hour expiration with secure signing
- **Password Hashing**: bcrypt with salt rounds
- **Rate Limiting**: Brute force protection
- **Input Validation**: SQL injection prevention
- **Session Management**: Secure token storage

## 🏛️ Banking System Features

### Core Banking Functionality
1. **Account Management**
   - User registration with biometric enrollment
   - Secure profile management
   - Account balance tracking
   - PIN-based transaction security

2. **Transaction System**
   - Peer-to-peer money transfers
   - Beneficiary management (CRUD operations)
   - Transaction history with filtering
   - Real-time balance updates

3. **Payment Gateway Integration**
   - Razorpay payment processing
   - Add money functionality
   - Payment verification
   - Transaction status tracking

4. **Dashboard & Analytics**
   - Monthly spending analysis
   - Transaction categorization
   - Account activity overview
   - Security activity monitoring

### Database Schema
```sql
-- Core user table
users (id, username, email, face_embedding, voice_features, created_at)

-- Authentication & Security
user_pins (user_id, pin_hash)
accounts (id, user_id, account_number, balance)

-- Transaction Management  
transactions (id, user_id, type, amount, to_account, status, reference_id, timestamp)
beneficiaries (id, user_id, name, account_number, ifsc)
```

## 🤟 Sign Language Recognition System

### ASL Recognition Pipeline
```
Video Input → MediaPipe → Landmark Extraction → TF Lite Model → Word Prediction → LLM → Sentence
```

### Technical Implementation
1. **Frontend Capture**
   - MediaPipe Holistic in browser
   - Real-time landmark detection (face, pose, hands)
   - Adaptive sampling for performance
   - Canvas-based visualization

2. **ML Model Architecture**
   - **Input**: 543 landmarks × frames × 3D coordinates
   - **Model**: TensorFlow Lite Transformer
   - **Output**: ASL word predictions via sign dictionary
   - **Post-processing**: Gemini LLM for sentence formation

3. **Backend API (FastAPI)**
   - `/islr/predict`: Real-time prediction endpoint
   - `/islr/reset`: Clear accumulated signs
   - `/islr/send`: Email sentence via SMTP
   - Static file serving for web interface

4. **Features**
   - Real-time sign recognition
   - Sentence accumulation and refinement
   - Email integration for communication
   - Responsive web interface
   - Performance optimization with frame sampling

### Gemini LLM Integration
- **Purpose**: Convert ASL gloss tokens to natural English
- **Model**: gemini-1.5-flash for speed and cost efficiency
- **Fallback**: Simple token joining when LLM unavailable
- **Debouncing**: Avoid repeated calls for same token sequence

## 🎨 User Interface Design

### Design System
- **Theme**: Professional light theme with banking aesthetics
- **Colors**: Blue-based palette with gradients
- **Typography**: Clean, accessible font hierarchy
- **Components**: Modular CSS architecture
- **Responsive**: Mobile-first design approach

### Key UI Components
- **Landing Page**: Modern banking website aesthetics
- **Authentication Forms**: Multi-modal login options
- **Dashboard**: Comprehensive financial overview
- **Transaction Interfaces**: Intuitive money transfer flows
- **Sign Recognition**: Embedded iframe integration

## 📁 Project Structure

```
MAJOR-PROJECT/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Home.js/.css   # Landing page
│   │   │   ├── Dashboard.js/.css # Main dashboard
│   │   │   ├── Login.js/.css   # Authentication
│   │   │   ├── Transfer.js/.css # Money transfers
│   │   │   └── SignRecognition.js/.css # ASL integration
│   │   ├── App.js             # Main app router
│   │   └── index.css          # Design system tokens
│   └── package.json           # Dependencies
│
├── backend/                     # Node.js/Express API
│   ├── controllers/
│   │   ├── userController.js   # Authentication logic
│   │   └── bankController.js   # Banking operations
│   ├── middleware/
│   │   └── authMiddleware.js   # JWT validation
│   ├── utils/
│   │   └── emailService.js     # Email/OTP handling
│   ├── db.js                  # Database connection
│   ├── razorpay.js           # Payment gateway
│   └── index.js              # Express server
│
├── python_service/             # AI/ML microservice
│   ├── app.py                 # Flask server
│   └── pretrained_models/     # ML model storage
│
├── Sign-Language-Recognition-main/  # ASL recognition system
│   ├── webapp/
│   │   ├── app/
│   │   │   └── main.py        # FastAPI server
│   │   ├── module/
│   │   │   ├── islr/
│   │   │   │   └── model.py   # TF Lite inference
│   │   │   └── llm/
│   │   │       └── asl_sentence_generator.py # Gemini integration
│   │   └── web/islr/          # Frontend interface
│   │       ├── index.html     # Sign recognition UI
│   │       ├── script.js      # MediaPipe logic
│   │       └── style.css      # Styling
│   └── code/                  # Model training notebooks
│
└── requirements.txt            # Python dependencies
```

## 🚀 Development Workflow

### Service Architecture
1. **Frontend Development Server**: `npm start` (Port 3000)
2. **Backend API Server**: `node index.js` (Port 5000)  
3. **Python AI Service**: `python app.py` (Port 5001)
4. **Sign Recognition API**: `uvicorn app.main:app` (Port 8000)

### Development Process
1. **Authentication Flow**: User registers → Biometric enrollment → JWT token generation
2. **Banking Operations**: Authenticated requests → Database operations → Response
3. **Sign Recognition**: MediaPipe capture → FastAPI prediction → LLM sentence generation
4. **Integration**: React iframe embedding for seamless ASL support

## 🎯 Key Achievements

### Completed Features ✅
- ✅ Multi-modal authentication (Face, Voice, OTP)
- ✅ Complete banking functionality (transfers, beneficiaries, history)
- ✅ Razorpay payment gateway integration
- ✅ Real-time sign language recognition
- ✅ Gemini LLM sentence generation
- ✅ Professional UI/UX design
- ✅ Secure JWT-based authentication
- ✅ PostgreSQL database integration
- ✅ Email/SMTP services
- ✅ Responsive web design
- ✅ Component-based architecture



Banking System:
✅ User registration with biometric enrollment
✅ Multi-modal authentication (face/voice/OTP)
✅ Account balance management
✅ Peer-to-peer money transfers
✅ Beneficiary management (CRUD)
✅ Transaction history with analytics
✅ Razorpay payment gateway integration
✅ PIN-based security

Sign Language Recognition:
✅ Real-time MediaPipe landmark extraction
✅ TensorFlow Lite transformer model inference
✅ ASL word prediction with 543-landmark input
✅ Gemini LLM sentence generation
✅ Email integration for sending recognized sentences
✅ Responsive web interface with performance optimization

Security & Authentication:
✅ JWT-based session management
✅ Face recognition with ArcFace embeddings
✅ Voice recognition with ECAPA-TDNN
✅ OTP via email with Nodemailer
✅ bcrypt password hashing
✅ Rate limiting and CORS protection

### Technical Innovations
- **Adaptive Fusion Approach**: Novel combination of banking + accessibility
- **Multi-Modal Biometrics**: Face + Voice authentication in banking context
- **Real-time ASL Integration**: Live sign language recognition in web browser
- **LLM-Enhanced Communication**: AI-powered sentence generation from signs
- **Seamless Integration**: Iframe embedding of ML services in React app

## 🔧 Current Implementation Status

### Production-Ready Components
- Authentication system with biometric enrollment
- Core banking operations (balance, transfers, history)
- Payment gateway integration
- Sign language recognition with LLM enhancement
- Professional UI with accessibility features

### Environment Configuration
```bash
# Backend .env
DATABASE_URL=postgresql://...
JWT_SECRET=...
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
EMAIL_USER=...
EMAIL_APP_PASSWORD=...

# ASL Service .env  
ENABLE_SENTENCE_GEN=true
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash
```

## 🌟 Unique Value Proposition

1. **Accessibility Focus**: First banking app designed specifically for deaf/hearing-impaired users
2. **Multi-Modal Security**: Three different authentication methods for user preference
3. **Real-time ASL Support**: Live sign language recognition for customer service
4. **Industry Standards**: Professional banking features with payment gateway integration
5. **AI-Enhanced**: LLM integration for natural language communication from signs

## 🎓 Academic Context

This project serves as a **Master's Degree final project** demonstrating:
- Full-stack web development proficiency
- AI/ML integration in real-world applications  
- Accessibility-focused design principles
- Industry-standard security implementations
- Modern software architecture patterns
- Database design and integration
- Payment gateway integration
- Multi-service orchestration

The project showcases advanced technical skills while addressing a real social need - creating accessible banking solutions for the deaf and hearing-impaired community.

---

**Project Status**: ✅ **Production Ready** - All core features implemented and functional  
**Target Users**: Deaf and hearing-impaired individuals seeking accessible banking solutions  
**Technical Achievement**: Successful integration of banking, biometrics, and sign language AI in a cohesive system