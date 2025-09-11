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
app = FastAPI(title="Original 250 Gestures Server")

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
    import module.islr.model as original_model
    
    print("🔄 Loading Original 250 Gestures Model...")
    original_asl_model = original_model.OriginalASLRecognition(model_path="module/islr")
    print("✅ Original 250 gestures model loaded successfully")
    model_loaded = True
    
except Exception as e:
    print(f"❌ Error loading original model: {e}")
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
    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "model_type": "original_250_gestures",
        "gesture_count": len(original_asl_model.ORD2SIGN) if model_loaded else 0
    }

# Original 250 gestures prediction endpoint
@app.post("/predict")
async def predict_original(data: List[LandmarkData]):
    """Predict using original 250 gesture TensorFlow Lite model"""
    if not model_loaded:
        return {"error": "Model not loaded", "status": 500}
    
    try:
        result = original_asl_model.predict(data)
        return result
    except Exception as e:
        return {"error": str(e), "status": 500, "model_type": "original_250_gestures"}

# Model information endpoint
@app.get("/info")
async def model_info():
    """Get information about the original model"""
    if not model_loaded:
        return {"error": "Model not loaded"}
    
    gestures = list(original_asl_model.ORD2SIGN.values())
    return {
        "model_type": "original_250_gestures",
        "technology": "tensorflow_lite",
        "gesture_count": len(gestures),
        "sample_gestures": gestures[:20],  # Show first 20
        "all_gestures": gestures,
        "endpoint": "/predict"
    }

# Legacy endpoint for backward compatibility
@app.post("/islr/predict")
async def predict_legacy(data: List[LandmarkData]):
    """Legacy endpoint - redirects to main prediction"""
    return await predict_original(data)

# Run the app with Uvicorn
if __name__ == "__main__":
    print("🚀 Starting Original 250 Gestures Server...")
    print("📍 Server will be available at: http://127.0.0.1:8001")
    print("📊 Model info available at: http://127.0.0.1:8001/info")
    print("🌐 Web interface at: http://127.0.0.1:8001")
    print("🎯 Supports 250+ original ASL gestures")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
