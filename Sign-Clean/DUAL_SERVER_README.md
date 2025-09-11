# Dual Server Setup - Sign Language Recognition

This project now has **two independent servers** for testing and development:

## 🖥️ Server 1: Original Gestures (250+ ASL Gestures)

**Location**: `Sign-Clean/original-server/`
**Port**: `8001`
**URL**: http://127.0.0.1:8001

### Features:
- ✅ **TensorFlow Lite** model with 253 pre-trained ASL gestures
- ✅ **Real-time recognition** using MediaPipe
- ✅ **Web interface** for live testing
- ✅ **Health monitoring** and model information endpoints

### Technology Stack:
- **Model**: TensorFlow Lite (`model.tflite`)
- **Framework**: FastAPI
- **Frontend**: HTML5, JavaScript, MediaPipe
- **Dictionary**: `dict_sign.csv` (253 gestures)

### Usage:
```bash
cd Sign-Clean/original-server
python main.py
```

---

## 🤖 Server 2: Custom Gestures (User-Trained)

**Location**: `Sign-Clean/custom-server/`
**Port**: `8002`
**URL**: http://127.0.0.1:8002

### Features:
- ✅ **LSTM Neural Network** (primary model)
- ✅ **RandomForest Classifier** (fallback model)
- ✅ **Custom gesture training** support
- ✅ **Dual prediction system** for higher accuracy
- ✅ **Real-time recognition** using MediaPipe

### Technology Stack:
- **Models**: LSTM + RandomForest
- **Framework**: FastAPI
- **Frontend**: HTML5, JavaScript, MediaPipe
- **Data**: Custom trained gestures (`custom_gesture_*.pkl`)

### Usage:
```bash
cd Sign-Clean/custom-server
python main.py
```

---

## 🔄 Future Integration Plan

Both servers are designed with **identical APIs** to enable easy combination later:

### Common Endpoints:
- `GET /` - Web interface
- `GET /health` - Server health check
- `GET /info` - Model information
- `POST /predict` - Gesture prediction

### Integration Steps (Later):
1. **Unified Server**: Combine both models in one FastAPI application
2. **Model Selection**: Choose between original/custom based on user preference
3. **Ensemble Prediction**: Use both models for higher accuracy
4. **Dynamic Loading**: Load models based on request type

---

## 🚀 Quick Start

### Start Both Servers:
```bash
# Terminal 1 - Original Gestures
cd Sign-Clean/original-server
python main.py

# Terminal 2 - Custom Gestures  
cd Sign-Clean/custom-server
python main.py
```

### Test Both Interfaces:
- **Original**: http://127.0.0.1:8001
- **Custom**: http://127.0.0.1:8002

---

## 📊 Model Information

### Original Server (Port 8001):
- **Gestures**: 253 pre-trained ASL signs
- **Technology**: TensorFlow Lite
- **Performance**: Optimized for real-time inference
- **Use Case**: Standard ASL recognition

### Custom Server (Port 8002):
- **Gestures**: User-defined custom gestures
- **Technology**: LSTM + RandomForest
- **Performance**: High accuracy for trained gestures
- **Use Case**: Personalized gesture recognition

---

## 🛠️ Development Benefits

### Separated Architecture:
- ✅ **Independent Testing**: Test each model separately
- ✅ **Isolated Development**: Work on features without conflicts
- ✅ **Easy Debugging**: Clear separation of concerns
- ✅ **Scalable**: Each server can be deployed independently

### Clean Structure:
- ✅ **No Pattern-Based Recognition**: Removed complex rule-based system
- ✅ **Focused Models**: Each server has a single responsibility
- ✅ **Maintainable Code**: Clear organization and documentation
- ✅ **Future-Ready**: Designed for easy integration

---

## 📁 Directory Structure

```
Sign-Clean/
├── original-server/           # 250+ Original ASL Gestures
│   ├── main.py               # FastAPI server
│   ├── module/
│   │   └── islr/
│   │       ├── model.py      # TensorFlow Lite implementation
│   │       ├── model.tflite  # Pre-trained model
│   │       └── dict_sign.csv # Gesture dictionary
│   └── web/islr/             # Web interface
│
├── custom-server/            # Custom User Gestures
│   ├── main.py              # FastAPI server
│   ├── module/
│   │   └── custom_model.py  # LSTM + RandomForest
│   ├── web/islr/            # Web interface
│   ├── custom_gesture_classifier.pkl
│   ├── custom_gesture_mapping.json
│   └── custom_gesture_scaler.pkl
│
└── README.md                # This file
```

---

**Status**: ✅ Both servers are running and tested successfully!
**Next Step**: Independent testing and validation of both recognition systems.
