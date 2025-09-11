# Project Cleanup Plan

## Core Architecture Decision
- **Original 250 Gestures**: TensorFlow Lite model (model.py) - WORKING ✅
- **Custom Gestures**: MediaPipe + RandomForest (model_simple.py) - WORKING ✅
- **Technology Stack**: FastAPI + MediaPipe + TensorFlow Lite + RandomForest

## Files to KEEP

### 1. Original 250 Gesture System (CORE)
```
Sign/webapp/
├── app/main.py                    # FastAPI server
├── module/islr/
│   ├── model.py                   # Original 250 gestures (TensorFlow Lite)
│   ├── model.tflite              # Pre-trained model
│   ├── dict_sign.csv             # 250 gesture dictionary
├── web/islr/
│   ├── index.html                # Main web interface
│   ├── script.js                 # JavaScript for webcam
│   └── style.css                 # Styling
```

### 2. Custom Gesture System (WORKING)
```
├── module/islr/model_simple.py    # Integrated custom + pattern recognition
├── custom_gesture_classifier.pkl  # Trained custom classifier
├── custom_gesture_scaler.pkl      # Feature scaler
├── custom_gesture_mapping.json    # Custom gesture mapping
├── simple_custom_mapping.json     # Pattern-based gestures
├── gesture_data/wave_landmarks.csv # Training data
```

### 3. Training Tools (ESSENTIAL)
```
├── train_custom_gestures.py       # Train new custom gestures
├── record_new_gesture.py          # Record new gesture data
├── smart_manager.py               # Gesture management
```

## Files to DELETE (Cleanup List)

### Backend Components (NOT NEEDED)
- backend/ (entire folder - face/voice auth not needed)
- frontend/ (entire folder - React frontend not needed)
- python_service/ (entire folder - separate ML service not needed)

### Experimental Training Files
- compatible_lstm_trainer.py
- complete_landmark_trainer.py
- custom_gesture_trainer.py
- incremental_lstm_trainer.py
- landmark_lstm_trainer.py
- simple_lstm_trainer.py
- improved_lstm_trainer.py
- fixed_lstm_trainer.py
- retrain_enhanced_classifier.py
- All other trainer variants

### Duplicate/Test Files
- test_*.py (multiple test files)
- quick_*.py (multiple quick scripts)
- simple_*.py (except model_simple.py)
- fix_*.py
- diagnose_*.py
- setup_*.py

### Unused Model Files
- module/islr/model_enhanced*.py
- module/islr/model_optimized.py
- module/islr/model_compatible.py
- module/islr/model_minimal.py

### Cache/Temp Directories
- __pycache__/
- training_cache/
- processed_data/
- custom_videos/ (keep structure, clean contents)

## Final Clean Structure
```
MAJOR-PROJECT/
├── Sign/
│   ├── webapp/
│   │   ├── app/
│   │   │   └── main.py
│   │   ├── module/islr/
│   │   │   ├── model.py              # 250 gestures
│   │   │   ├── model_simple.py       # Custom gestures
│   │   │   ├── model.tflite
│   │   │   └── dict_sign.csv
│   │   ├── web/islr/
│   │   │   ├── index.html
│   │   │   ├── script.js
│   │   │   └── style.css
│   │   ├── train_custom_gestures.py
│   │   ├── record_new_gesture.py
│   │   └── smart_manager.py
│   └── README.md
├── custom_gesture_classifier.pkl
├── custom_gesture_scaler.pkl
├── custom_gesture_mapping.json
├── simple_custom_mapping.json
├── gesture_data/
│   └── wave_landmarks.csv
└── requirements.txt
```

## Benefits After Cleanup
1. ✅ Clear separation: 250 original vs custom gestures
2. ✅ Single technology stack: FastAPI + MediaPipe + TensorFlow
3. ✅ Simple training workflow for new gestures
4. ✅ Unified web interface
5. ✅ 90% reduction in file count
6. ✅ Easy to understand and maintain
