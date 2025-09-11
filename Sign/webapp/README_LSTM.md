# Custom Gesture Recognition with LSTM

This project now uses an optimized LSTM-based approach for custom gesture recognition while maintaining the original 250 ASL gestures.

## Quick Setup

### 1. Folder Structure
```
Sign/webapp/
├── custom_videos/          # Your gesture videos
│   ├── welcome/           # Videos for "welcome" gesture
│   ├── thank_you/         # Videos for "thank_you" gesture
│   └── hello/             # Videos for "hello" gesture
├── custom_gesture_trainer.py   # Train LSTM model
├── module/islr/
│   └── model_optimized.py      # Optimized prediction engine
└── app/main.py                 # FastAPI server
```

### 2. Record Your Gestures

Create gesture videos in the `custom_videos` folder:
- **Folder per gesture**: Each gesture gets its own folder
- **Video format**: MP4 or AVI files
- **Duration**: 2-4 seconds per video  
- **Count**: 5-10 videos per gesture minimum
- **Quality**: Clear hand/face visibility, good lighting

Example:
```
custom_videos/
├── welcome/
│   ├── welcome_1.mp4
│   ├── welcome_2.mp4
│   └── welcome_3.mp4
└── thank_you/
    ├── thank_you_1.mp4
    └── thank_you_2.mp4
```

### 3. Train the Model

```bash
cd D:\MAJOR-PROJECT\Sign\webapp
python custom_gesture_trainer.py
```

This will:
- Process all videos in `custom_videos/`
- Extract MediaPipe landmarks
- Apply data augmentation (time scaling, noise, flipping)
- Train LSTM model with dropout and regularization
- Save trained model files

### 4. Run the Application

```bash
cd D:\MAJOR-PROJECT\Sign\webapp
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your browser.

## How It Works

### Training Pipeline
1. **Video Processing**: Extracts 30-frame sequences from videos
2. **Landmark Extraction**: Uses MediaPipe to get face, pose, and hand landmarks
3. **Data Augmentation**: Creates variations (speed, noise, horizontal flip)
4. **LSTM Training**: Trains sequence classifier with early stopping
5. **Model Saving**: Saves trained model and label encoder

### Prediction Pipeline
1. **Dual Model**: Runs both original TFLite model and custom LSTM
2. **Smart Fusion**: Chooses custom if confidence > 70% and significantly better than original
3. **Sequence Processing**: Maintains 30-frame rolling window for LSTM
4. **Real-time**: Processes live camera feed frame by frame

### Key Features
- **High Accuracy**: LSTM captures temporal patterns in gestures
- **Data Efficient**: Augmentation multiplies training data 4x
- **Robust**: Works with varying lighting and backgrounds
- **Fast**: Optimized for real-time inference
- **Extensible**: Easy to add new gestures

## Model Architecture

```
LSTM Model:
├── Input: (30 frames, 258 features)
├── BatchNormalization
├── LSTM(128) + Dropout(0.3)
├── LSTM(64) + Dropout(0.3)  
├── LSTM(32) + Dropout(0.3)
├── Dense(64) + Dropout(0.5)
├── Dense(32) + Dropout(0.3)
└── Output: Softmax(num_classes)
```

## Troubleshooting

### "No videos found"
- Check folder structure: `custom_videos/gesture_name/video.mp4`
- Ensure video formats are MP4 or AVI

### "Training failed" 
- Need at least 2 different gestures
- Minimum 5 videos per gesture
- Check video quality (clear landmarks)

### "Custom gestures not detected"
- Retrain model with more data
- Check video similarity to training data
- Verify model files exist: `custom_gesture_lstm.h5`

### Low accuracy
- Add more training videos (10+ per gesture)
- Ensure consistent gesture performance
- Check lighting and background conditions

## Performance Tips

### Recording Best Practices
- **Consistent lighting** across all videos
- **Full hand/face visibility** in frame
- **Natural gesture speed** (not too fast/slow)
- **Slight variations** in angle and position
- **Clean background** preferred but not required

### Training Optimization
- **Balance classes**: Similar number of videos per gesture
- **Quality over quantity**: 10 good videos > 20 poor videos
- **Diverse samples**: Different angles, speeds, lighting
- **Regular retraining**: Add new samples and retrain

This optimized system provides much better accuracy and reliability for custom gesture recognition while maintaining compatibility with the original 250 ASL gestures.
