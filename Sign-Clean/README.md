# 🎯 Sign Language Recognition System (Clean Version)

A comprehensive sign language recognition system that supports both **250 original gestures** and **custom gestures** with video processing capabilities.

## 🏗️ Architecture

### Dual Recognition System
- **Original 250 Gestures**: TensorFlow Lite model with pre-trained ASL recognition
- **Custom Gestures**: MediaPipe + RandomForest classifier for user-defined gestures
- **Video Processing**: Extract landmarks from video datasets for training

### Technology Stack
- **Backend**: FastAPI, Uvicorn
- **Computer Vision**: MediaPipe, OpenCV
- **Machine Learning**: TensorFlow, scikit-learn, RandomForest
- **Data Processing**: Pandas, NumPy
- **Frontend**: HTML5 + JavaScript + WebRTC

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Check System Status
```bash
python smart_manager.py
```

### 3. Start Web Application
```bash
cd webapp/app
python main.py
```

Visit: http://127.0.0.1:8001

## 📊 Available Endpoints

### Main Endpoints
- `GET /` - Web interface
- `POST /unified/predict` - **Recommended**: Try custom first, fallback to original
- `GET /models/info` - System information

### Specialized Endpoints
- `POST /original/predict` - Original 250 gestures only
- `POST /custom/predict` - Custom gestures only
- `GET /health` - System health check

## 🎨 Adding Custom Gestures

### 1. Record New Gesture
```bash
python record_new_gesture.py
```
- Follow on-screen instructions
- Record multiple variations
- Press SPACE to start/stop recording

### 2. Train the Model
```bash
python train_custom_gestures.py
```
- Automatically processes all recorded data
- Creates classifier files (`.pkl`)
- Shows training accuracy

### 3. Test in Web Interface
- Restart the webapp
- Your gesture will be available immediately

## 📁 Project Structure

```
Sign-Clean/
├── webapp/
│   ├── app/main.py              # FastAPI server
│   ├── module/islr/
│   │   ├── model.py             # Original 250 gestures
│   │   ├── model_simple.py      # Custom gestures  
│   │   ├── model.tflite         # Pre-trained model
│   │   └── dict_sign.csv        # Gesture dictionary
│   └── web/islr/
│       ├── index.html           # Web interface
│       ├── script.js            # Camera handling
│       └── style.css            # Styling
├── gesture_data/                # Training data
├── custom_gesture_*.pkl         # Trained models
├── *_mapping.json              # Gesture mappings
├── train_custom_gestures.py    # Training script
├── record_new_gesture.py       # Recording script
├── smart_manager.py            # Management tool
└── requirements.txt
```

## 🎭 Available Gestures

### Original 250 Gestures
Includes common ASL signs like:
- Common words: hello, thank you, please, sorry
- Numbers: one, two, three, etc.
- Family: mother, father, sister, brother
- Colors: red, blue, green, yellow
- Animals: cat, dog, bird, fish
- And 240+ more...

### Custom Gestures
Add your own gestures:
- **Trained**: Machine learning-based recognition
- **Pattern**: Simple rule-based recognition

## 🔧 Management Commands

### Smart Manager
```bash
python smart_manager.py
```
Interactive menu to:
- Check system status
- List all gestures
- Train models
- Start webapp

### Direct Commands
```bash
# Record new gesture
python record_new_gesture.py

# Train models
python train_custom_gestures.py

# Start webapp
cd webapp/app && python main.py
```

## 🎯 Recognition Flow

1. **Camera Input**: MediaPipe extracts hand/pose landmarks
2. **Custom Check**: Try custom gesture classifier first
3. **Original Fallback**: If no custom match, try 250 original gestures
4. **Result**: Return best prediction with confidence score

## 📈 Performance

- **Original Model**: ~85-90% accuracy on standard ASL
- **Custom Model**: Depends on training data quality
- **Processing**: Real-time (30+ FPS)
- **Latency**: < 100ms per prediction

## 🛠️ Troubleshooting

### No Camera Access
- Check browser permissions
- Ensure camera is not in use by other apps

### Low Recognition Accuracy
- Record more gesture variations
- Ensure good lighting
- Keep hands in camera view
- Record from different angles

### Model Loading Errors
- Check if all `.pkl` files exist
- Verify TensorFlow installation
- Run `python smart_manager.py` to diagnose

## 📝 Example Usage

### Python API
```python
import requests

# Predict gesture
response = requests.post('http://127.0.0.1:8001/unified/predict', 
                        json=landmark_data)
result = response.json()
print(f"Gesture: {result['sign']}")
```

### JavaScript (Frontend)
```javascript
// Send landmarks to API
fetch('/unified/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(landmarkData)
})
.then(response => response.json())
.then(data => console.log('Gesture:', data.sign));
```

## 🤝 Contributing

1. Record new gestures with diverse examples
2. Test accuracy and provide feedback  
3. Report issues with specific gesture names
4. Suggest improvements to recognition logic

## 📄 License

This project is for educational and research purposes.

## 🙏 Acknowledgments

- MediaPipe team for landmark detection
- TensorFlow team for the ML framework
- ASL community for gesture standards

---

**Ready to recognize gestures? Run `python smart_manager.py` to get started! 🚀**
