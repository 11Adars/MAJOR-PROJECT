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
app = FastAPI(title="Sign Language Recognition System")

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

# Import models after FastAPI setup
try:
    import module.islr.model as original_model
    import module.islr.model_simple as custom_model
    
    # Initialize models
    print("🔄 Loading Sign Language Recognition Models...")
    
    # Original 250 gestures model
    original_asl_model = original_model.IsolatedASLRecognition(model_path="../module/islr")
    print("✅ Original 250 gestures model loaded")
    
    # Custom gestures model  
    custom_asl_model = custom_model.SimpleIsolatedASLRecognition(model_path="../module/islr")
    print("✅ Custom gestures model loaded")
    
    models_loaded = True
    
except Exception as e:
    print(f"❌ Error loading models: {e}")
    models_loaded = False

# Serve static files (CSS and JS) from the "web" folder
app.mount("/web/islr", StaticFiles(directory="../web/islr"), name="web_islr")

# Serve the main HTML page
@app.get("/")
async def read_root():
    return FileResponse(Path("../web/islr/index.html"))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": models_loaded,
        "available_endpoints": [
            "/original/predict",  # 250 original gestures
            "/custom/predict",    # Custom gestures
            "/unified/predict"    # Try custom first, fallback to original
        ]
    }

# Original 250 gestures prediction endpoint
@app.post("/original/predict")
async def predict_original(data: List[LandmarkData]):
    """Predict using original 250 gesture TensorFlow Lite model"""
    if not models_loaded:
        return {"error": "Models not loaded", "status": 500}
    
    try:
        result = original_asl_model.predict(data)
        result["model_type"] = "original_250_gestures"
        return result
    except Exception as e:
        return {"error": str(e), "status": 500, "model_type": "original_250_gestures"}

# Custom gestures prediction endpoint  
@app.post("/custom/predict")
async def predict_custom(data: List[LandmarkData]):
    """Predict using custom gesture classifier"""
    if not models_loaded:
        return {"error": "Models not loaded", "status": 500}
    
    try:
        result = custom_asl_model.predict(data)
        result["model_type"] = "custom_gestures"
        return result
    except Exception as e:
        return {"error": str(e), "status": 500, "model_type": "custom_gestures"}

# Unified prediction endpoint (recommended)
@app.post("/unified/predict")
async def predict_unified(data: List[LandmarkData]):
    """
    Unified prediction: Try custom gestures first, then fallback to original 250
    This provides the best user experience with both custom and original gestures
    """
    if not models_loaded:
        return {"error": "Models not loaded", "status": 500}
    
    try:
        # First try custom gestures
        custom_result = custom_asl_model.predict(data)
        
        # If custom model found a confident prediction, return it
        if (custom_result.get("confidence", 0) > 0.7 and 
            custom_result.get("sign") != "no_action"):
            custom_result["model_type"] = "custom_gestures"
            custom_result["source"] = "custom_classifier"
            return custom_result
        
        # Otherwise, try original 250 gestures model
        original_result = original_asl_model.predict(data)
        
        # Return the original model result
        if original_result.get("status") == 200:
            result = {
                "sign": original_result.get("sign_name", "unknown"),
                "sentence": original_result.get("pred_sentence", ""),
                "confidence": 0.85,  # Original model doesn't provide confidence
                "model_type": "original_250_gestures", 
                "source": "tensorflow_lite",
                "status": 200
            }
            return result
        
        # If both fail, return the custom result anyway
        custom_result["model_type"] = "custom_gestures_fallback"
        return custom_result
        
    except Exception as e:
        return {"error": str(e), "status": 500, "model_type": "unified_error"}

# Legacy endpoint for backward compatibility
@app.post("/islr/predict")
async def predict_legacy(data: List[LandmarkData]):
    """Legacy endpoint - redirects to unified prediction"""
    return await predict_unified(data)

# Model information endpoint
@app.get("/models/info")
async def models_info():
    """Get information about available models"""
    info = {
        "models_loaded": models_loaded,
        "available_models": []
    }
    
    if models_loaded:
        # Get original model info
        try:
            original_gestures = list(original_asl_model.ORD2SIGN.values())
            info["available_models"].append({
                "name": "Original 250 Gestures",
                "type": "tensorflow_lite",
                "gesture_count": len(original_gestures),
                "gestures": original_gestures[:10] + ["..."] if len(original_gestures) > 10 else original_gestures,
                "endpoint": "/original/predict"
            })
        except:
            pass
        
        # Get custom model info
        try:
            if hasattr(custom_asl_model, 'trained_gesture_mapping'):
                custom_gestures = list(custom_asl_model.trained_gesture_mapping.keys())
            else:
                custom_gestures = list(custom_asl_model.custom_mapping.keys())
            
            info["available_models"].append({
                "name": "Custom Gestures", 
                "type": "random_forest + pattern_matching",
                "gesture_count": len(custom_gestures),
                "gestures": custom_gestures,
                "endpoint": "/custom/predict"
            })
        except:
            pass
    
    return info

# Run the app with Uvicorn
if __name__ == "__main__":
    print("🚀 Starting Sign Language Recognition Server...")
    print("📍 Server will be available at: http://127.0.0.1:8001")
    print("📊 Model info available at: http://127.0.0.1:8001/models/info")
    print("🌐 Web interface at: http://127.0.0.1:8001")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
