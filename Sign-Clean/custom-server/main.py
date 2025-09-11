import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize the FastAPI app
app = FastAPI(title="Custom Gestures Server")

# Set up CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models for data validation
class Landmark(BaseModel):
    x: float
    y: float
    z: Optional[float] = None
    visibility: Optional[float] = None

class LandmarkData(BaseModel):
    timeInSeconds: float
    frameNumber: int
    poseLandmarks: Optional[List[Landmark]] = None
    faceLandmarks: Optional[List[Landmark]] = None
    leftHandLandmarks: Optional[List[Landmark]] = None
    rightHandLandmarks: Optional[List[Landmark]] = None

# Import model after FastAPI setup
try:
    import module.custom_model as custom_model
    
    print("🔄 Loading Custom Gestures Model...")
    custom_gesture_model = custom_model.CustomGestureRecognition()
    print("✅ Custom gestures model loaded successfully")
    model_loaded = True
    
except Exception as e:
    print(f"❌ Error loading custom model: {e}")
    model_loaded = False

# Serve static files from the "web" folder
app.mount("/web/islr", StaticFiles(directory="web/islr"), name="web_islr")

# Serve the main HTML page
@app.get("/")
async def read_root():
    return FileResponse(Path("web/islr/index.html"))

# Health check endpoint
@app.get("/health")
async def health_check():
    model_info = {}
    if model_loaded:
        model_info = {
            "has_lstm": custom_gesture_model.lstm_model is not None,
            "has_classifier": custom_gesture_model.custom_classifier is not None,
            "gestures": list(custom_gesture_model.gesture_mapping.keys()) if custom_gesture_model.gesture_mapping else []
        }
    
    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "model_type": "custom_gestures",
        "model_info": model_info
    }

# Custom gestures prediction endpoint
@app.post("/predict")
async def predict_custom(data: List[LandmarkData]):
    """Predict using custom gesture models (LSTM or RandomForest)"""
    if not model_loaded:
        return {"error": "Model not loaded", "status": 500}
    
    try:
        result = custom_gesture_model.predict(data)
        return result
    except Exception as e:
        return {"error": str(e), "status": 500, "model_type": "custom_gestures"}

# Model information endpoint
@app.get("/info")
async def model_info():
    """Get information about the custom model"""
    if not model_loaded:
        return {"error": "Model not loaded"}
    
    gestures = list(custom_gesture_model.gesture_mapping.keys())
    model_types = []
    
    if custom_gesture_model.lstm_model:
        model_types.append("LSTM")
    if custom_gesture_model.custom_classifier:
        model_types.append("RandomForest")
    
    return {
        "model_type": "custom_gestures",
        "technology": " + ".join(model_types) if model_types else "none",
        "gesture_count": len(gestures),
        "available_gestures": gestures,
        "endpoint": "/predict",
        "has_lstm": custom_gesture_model.lstm_model is not None,
        "has_classifier": custom_gesture_model.custom_classifier is not None
    }

# Training data endpoint
@app.get("/training-data")
async def training_data_info():
    """Get information about available training data"""
    training_data_path = Path("../gesture_data")
    training_files = []
    
    if training_data_path.exists():
        csv_files = list(training_data_path.glob("*_landmarks.csv"))
        for file in csv_files:
            gesture_name = file.stem.replace("_landmarks", "")
            training_files.append({
                "gesture": gesture_name,
                "file": file.name,
                "size": file.stat().st_size if file.exists() else 0
            })
    
    return {
        "training_data_available": len(training_files),
        "training_files": training_files,
        "training_data_path": str(training_data_path)
    }

# Legacy endpoint for backward compatibility
@app.post("/islr/predict")
async def predict_legacy(data: List[LandmarkData]):
    """Legacy endpoint - redirects to main prediction"""
    return await predict_custom(data)

# Run the app with Uvicorn
if __name__ == "__main__":
    print("🚀 Starting Custom Gestures Server...")
    print("📍 Server will be available at: http://127.0.0.1:8002")
    print("📊 Model info available at: http://127.0.0.1:8002/info")
    print("🌐 Web interface at: http://127.0.0.1:8002")
    print("🎯 Supports custom trained gestures (LSTM + RandomForest)")
    
    uvicorn.run(app, host="127.0.0.1", port=8002)
