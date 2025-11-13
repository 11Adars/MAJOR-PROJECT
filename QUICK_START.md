# 🚀 Quick Start - Sign Language Feature

## Start Everything (Copy & Paste)

### Terminal 1 - Backend
```bash
cd d:\MAJOR-PROJECT\backend
node index.js
```

### Terminal 2 - Frontend
```bash
cd d:\MAJOR-PROJECT\frontend
npm start
```

### Terminal 3 - Python Service
```bash
cd d:\MAJOR-PROJECT\python_service
python app.py
```

### Terminal 4 - Sign Service ⭐
```bash
cd d:\MAJOR-PROJECT\Sign
start_service.bat
```

## Access the Feature

1. **Open**: http://localhost:3000
2. **Login**: Your credentials
3. **Click**: "Customer Support" button on dashboard
4. **Use**: Sign language recognition!

## Quick Test

```bash
# Test if sign service is running
curl http://127.0.0.1:8000/api/health
```

Should return:
```json
{"status": "ok", "sign_model_loaded": true, "slm_model_loaded": true}
```

## Ports Reference

- 🌐 Frontend: **3000**
- 🔧 Backend API: **5000**
- 🎤 Python Service: **5001**
- ✋ Sign Service: **8000**

## File Locations

### Created Files:
```
Sign/
├── sign_service.py          ⭐ Main service
├── templates/
│   └── index.html           ⭐ Web interface
├── requirements.txt
├── start_service.bat        ⭐ Windows startup
├── start_service.sh         ⭐ Linux/Mac startup
├── README.md
├── SETUP.md
└── models/ (your existing files)
```

### Modified Files:
```
frontend/src/components/
├── SignRecognition.js       ⭐ Updated with health check
└── SignRecognition.css      ⭐ Enhanced styling
```

## Usage Flow

```
Login → Dashboard → Customer Support → Sign Recognition
  ↓
Start Recording → Perform Sign → Stop Recording
  ↓
Keyword Recognized → Add More Signs (repeat)
  ↓
Generate Query → Natural Sentence → Submit to Support
```

## Troubleshooting

### Sign service won't start?
```bash
cd Sign
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python sign_service.py
```

### Camera not working?
- Allow browser permissions
- Close other apps using camera
- Refresh page

### Low accuracy?
- Good lighting ✅
- Clear gestures ✅
- Hold 2-3 seconds ✅
- Stay in frame ✅

## Documentation

- 📖 **Full docs**: `Sign/README.md`
- 🚀 **Setup guide**: `Sign/SETUP.md`
- 📝 **Integration**: `INTEGRATION_SUMMARY.md`
- 🧪 **Testing**: `TESTING_GUIDE.md`

## Support

**Service not running?** Check console logs
**Camera issues?** Check browser permissions
**Recognition issues?** Improve lighting & gestures
**Other issues?** See full documentation

---

✅ **You're all set!** Start all services and navigate to Customer Support on the dashboard!
