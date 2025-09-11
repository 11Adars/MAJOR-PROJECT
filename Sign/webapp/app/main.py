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
import module.islr.model_simple as model

# Initialize the FastAPI app
app = FastAPI()
model = model.SimpleIsolatedASLRecognition(model_path="../module/islr")

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

# Serve static files (CSS and JS) from the "web" folder
app.mount("/web/islr", StaticFiles(directory="../web/islr"), name="web_islr")

# Serve the main HTML page
@app.get("/")
async def read_root():
    return FileResponse(Path("../web/islr/index_simple.html"))

# Test page for debugging
@app.get("/test")
async def test_page():
    return FileResponse(Path("../web/islr/test_prediction.html"))

# Prediction endpoint
@app.post("/islr/predict")
async def predict(data: List[LandmarkData]):
    result = model.predict(data)
    return result

# Run the app with Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)