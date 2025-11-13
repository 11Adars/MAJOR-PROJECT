# Quick Setup Guide - Sign Language Recognition

## 🚀 Quick Start (5 Minutes)

### Step 1: Open Terminal in Sign Folder
```bash
cd d:\MAJOR-PROJECT\Sign
```

### Step 2: Run the Startup Script

**For Windows:**
```bash
start_service.bat
```

**For Linux/Mac:**
```bash
chmod +x start_service.sh
./start_service.sh
```

The script will automatically:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Check model files
- ✅ Start the service on port 8000

### Step 3: Access from Main App

1. Open your browser and go to `http://localhost:3000`
2. Login to BankAssist AI
3. Click **"Customer Support"** button on the dashboard
4. Start using sign language recognition!

## 🎯 Usage Flow

```
Dashboard → Customer Support → Sign Recognition Interface
    ↓
Camera Activation → Perform Sign Gesture → Recognition
    ↓
Add Keywords → Generate Natural Query → Submit to Support
```

## 📋 System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Webcam**: Required for video input
- **Ports**: 8000 (Sign Service), 3000 (Frontend), 5000 (Backend)

## 🔧 Manual Setup (If Script Fails)

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Service:**
   ```bash
   python sign_service.py
   ```

## 🐛 Common Issues & Solutions

### Issue: "Camera not accessible"
**Solution:** 
- Close other apps using camera
- Grant camera permissions in browser
- Refresh the page

### Issue: "Model file not found"
**Solution:**
- Verify files exist:
  - `saved_model_landmarks/best_landmark_model.keras`
  - `processed_data_landmarks/sign_labels.npy`
- Contact team if models are missing

### Issue: "Service not connecting"
**Solution:**
- Ensure service is running on port 8000
- Check if port is blocked by firewall
- Verify URL: `http://127.0.0.1:8000`

### Issue: "Low recognition accuracy"
**Solution:**
- Ensure good lighting
- Keep gestures clear and steady
- Hold poses for 2-3 seconds
- Stay within camera frame

## 📦 What's Included

```
Sign/
├── sign_service.py          # Flask backend service
├── interpreter.py           # Standalone interpreter (optional)
├── requirements.txt         # Python dependencies
├── start_service.bat        # Windows startup script
├── start_service.sh         # Linux/Mac startup script
├── README.md               # Full documentation
├── SETUP.md                # This file
├── templates/
│   └── index.html          # Web interface
├── saved_model_landmarks/
│   └── best_landmark_model.keras  # Trained model
├── processed_data_landmarks/
│   ├── sign_labels.npy     # Label mappings
│   ├── features_landmarks.npy
│   └── labels_landmarks.npy
└── slm_model_cache/        # Language model cache
```

## 🎨 Features

- ✅ Real-time hand & pose tracking
- ✅ Sign-to-text recognition
- ✅ Multi-word query building
- ✅ AI-powered sentence generation
- ✅ Banking context optimization
- ✅ User-friendly web interface

## 🔗 Integration Points

1. **Frontend Route**: `/sign-recognition`
2. **Dashboard Button**: "Customer Support"
3. **Service Port**: 8000
4. **API Base**: `http://127.0.0.1:8000/api/`

## 📞 Testing the Service

### Health Check:
```bash
curl http://127.0.0.1:8000/api/health
```

### Expected Response:
```json
{
  "status": "ok",
  "sign_model_loaded": true,
  "slm_model_loaded": true
}
```

## 🎓 How to Use

1. **Click "Start Recording"** - Begin capturing your sign
2. **Perform Sign Gesture** - Make clear, steady gestures
3. **Click "Stop Recording"** - End capture after 2-3 seconds
4. **View Recognized Keyword** - Check if correctly recognized
5. **Add More Signs** - Repeat for multi-word queries
6. **Click "Generate Query"** - Convert to natural language
7. **Use Generated Text** - Submit for customer support

## 🛠️ Development Notes

### API Endpoints:
- `GET /api/health` - Service status
- `POST /api/process-frame` - Frame processing
- `POST /api/predict` - Sign prediction
- `POST /api/generate-sentence` - Text generation

### Technology Stack:
- **Backend**: Flask 3.0
- **ML Framework**: TensorFlow 2.15
- **Computer Vision**: MediaPipe, OpenCV
- **NLP**: TinyLlama (ctransformers)
- **Frontend**: HTML5, JavaScript

## 📈 Performance Metrics

- **Frame Rate**: ~10 FPS
- **Prediction Time**: 100-200ms
- **Generation Time**: 1-3 seconds
- **Memory Usage**: 2-3GB

## 🔐 Security Notes

- Camera access requires user permission
- Video processing is local (not transmitted)
- CORS enabled for localhost only
- Add auth headers for production

## 📚 Additional Resources

- Full documentation: `README.md`
- Original interpreter: `interpreter.py`
- Model training: Contact team for training scripts

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Model files present
- [ ] Service running on port 8000
- [ ] Camera accessible
- [ ] Frontend accessing service
- [ ] Test recognition working

## 🤝 Support

For issues or questions:
1. Check this setup guide
2. Review full README.md
3. Check console for error messages
4. Contact development team

---

**Ready to Start?** Run `start_service.bat` (Windows) or `./start_service.sh` (Linux/Mac)
