# Sign Language Recognition Service

This service provides real-time sign language recognition for the BankAssist AI project, enabling customers to communicate with customer support using sign language gestures.

## Features

- **Real-time Sign Recognition**: Uses MediaPipe for hand and pose landmark detection
- **Keyword Extraction**: Recognizes individual sign language gestures as keywords
- **Natural Language Generation**: Converts recognized keywords into natural sentences using a Small Language Model (SLM)
- **Web-based Interface**: Accessible through the BankAssist AI dashboard
- **Banking Context**: Optimized for banking-related queries and support

## Architecture

The service consists of:

1. **Flask Backend** (`sign_service.py`): Handles video processing, sign recognition, and NLG
2. **TensorFlow Model**: Pre-trained landmark-based sign recognition model
3. **MediaPipe**: Real-time hand and pose tracking
4. **TinyLlama SLM**: Converts keywords to natural language queries
5. **Web Interface** (`templates/index.html`): User-friendly webcam interface

## Installation

### Prerequisites

- Python 3.8 or higher
- Webcam
- 4GB RAM minimum (8GB recommended)

### Setup

1. **Navigate to the Sign directory**:
   ```bash
   cd Sign
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify model files exist**:
   - `saved_model_landmarks/best_landmark_model.keras`
   - `processed_data_landmarks/sign_labels.npy`

## Running the Service

1. **Start the Flask server**:
   ```bash
   python sign_service.py
   ```

2. **The service will start on** `http://127.0.0.1:8000`

3. **Access from BankAssist AI**:
   - Login to the main application
   - Navigate to Dashboard
   - Click "Customer Support" button
   - The sign recognition interface will load in an iframe

## API Endpoints

### Health Check
- **GET** `/api/health`
- Returns service status and model availability

### Process Frame
- **POST** `/api/process-frame`
- Accepts: `{ "frame": "base64_image_data" }`
- Returns: Processed frame with landmarks and extracted features

### Predict Sign
- **POST** `/api/predict`
- Accepts: `{ "sequence": [[landmarks], ...] }`
- Returns: Predicted sign label and confidence score

### Generate Sentence
- **POST** `/api/generate-sentence`
- Accepts: `{ "keywords": ["WORD1", "WORD2", ...] }`
- Returns: Natural language sentence

## Usage

1. **Start Recording**: Click "Start Recording" button
2. **Perform Sign**: Make your sign language gesture clearly in front of the camera
3. **Stop Recording**: Click "Stop Recording" after 2-3 seconds
4. **Review Keyword**: The recognized keyword will be added to your list
5. **Add More Signs**: Repeat steps 1-4 to build a multi-word query
6. **Generate Query**: Click "Generate Query" to convert keywords into a natural sentence
7. **Submit to Support**: Use the generated sentence for customer support queries

## Model Information

### Sign Recognition Model
- **Type**: LSTM-based sequence classifier
- **Input**: 30 frames of MediaPipe landmarks (300 features per frame)
- **Output**: Sign label with confidence score
- **Threshold**: 0.7 (70% confidence minimum)

### Landmarks Used
- **Pose**: 33 body keypoints
- **Left Hand**: 21 hand keypoints
- **Right Hand**: 21 hand keypoints
- **Total**: 75 keypoints × 4 coordinates (x, y, z, visibility) = 300 features

### Language Model
- **Model**: TinyLlama 1.1B (GGUF quantized)
- **Purpose**: Convert sign keywords into natural banking queries
- **Context**: Few-shot learning with banking examples

## Troubleshooting

### Camera Not Working
- Grant camera permissions in browser
- Check if another application is using the camera
- Try refreshing the page

### Model Not Loading
- Verify model files exist in `saved_model_landmarks/`
- Check TensorFlow installation: `pip install tensorflow==2.15.0`
- Ensure sufficient RAM available

### Low Recognition Accuracy
- Ensure good lighting
- Keep hand gestures clear and within frame
- Hold poses for 2-3 seconds
- Maintain consistent distance from camera

### SLM Not Generating Sentences
- First time use may take longer (model download)
- Check internet connection for initial download
- Model cached in `slm_model_cache/` after first use
- Verify ctransformers installation

## Performance

- **Frame Processing**: ~10 FPS
- **Sign Prediction**: ~100-200ms
- **Sentence Generation**: ~1-3 seconds (CPU)
- **Memory Usage**: ~2-3GB with models loaded

## Integration with Main Project

The sign recognition service is integrated into the main BankAssist AI project:

1. **Frontend**: React component at `/sign-recognition` route
2. **Backend**: Standalone Flask service on port 8000
3. **Access**: Through "Customer Support" button on dashboard

### Configuration

Set environment variable in frontend `.env`:
```
REACT_APP_SIGN_RECOGNITION_URL=http://127.0.0.1:8000/
```

## Security Considerations

- Camera access restricted to authenticated users only
- Video processing happens locally (not transmitted)
- CORS enabled for localhost development
- Consider HTTPS in production
- Add authentication headers for production deployment

## Future Enhancements

- [ ] GPU acceleration for faster processing
- [ ] Expanded sign vocabulary
- [ ] Multi-language support
- [ ] Sign recording and playback
- [ ] Integration with chatbot
- [ ] Mobile device support
- [ ] Real-time translation display

## Credits

- **MediaPipe**: Google's ML solutions for real-time perception
- **TensorFlow**: Deep learning framework
- **TinyLlama**: Efficient small language model
- **Flask**: Python web framework

## License

Part of the BankAssist AI Major Project

## Support

For issues or questions, please refer to the main project documentation or contact the development team.
