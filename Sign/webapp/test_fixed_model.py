#!/usr/bin/env python3
"""
Test script to verify the fixed model can handle LandmarkData structure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import Landmark, LandmarkData
import module.islr.model_simple as model_simple

def create_test_landmark_data():
    """Create test data in the format that comes from the frontend"""
    
    # Create sample landmark data similar to MediaPipe output
    landmarks = []
    
    # Create a few frames of data
    for frame_num in range(5):
        # Sample right hand landmarks (21 points for MediaPipe hand)
        right_hand_landmarks = []
        for i in range(21):
            landmark = Landmark(
                x=0.5 + (i * 0.01) + (frame_num * 0.002),  # Slight movement
                y=0.4 + (i * 0.005) + (frame_num * 0.003),
                z=0.0,
                visibility=0.95
            )
            right_hand_landmarks.append(landmark)
        
        # Sample left hand landmarks
        left_hand_landmarks = []
        for i in range(21):
            landmark = Landmark(
                x=0.3 + (i * 0.008) + (frame_num * 0.001),
                y=0.4 + (i * 0.004) + (frame_num * 0.004),
                z=0.0,
                visibility=0.93
            )
            left_hand_landmarks.append(landmark)
        
        # Create LandmarkData object
        frame_data = LandmarkData(
            timeInSeconds=frame_num * 0.033,  # ~30 FPS
            frameNumber=frame_num,
            rightHandLandmarks=right_hand_landmarks,
            leftHandLandmarks=left_hand_landmarks,
            poseLandmarks=None,
            faceLandmarks=None
        )
        landmarks.append(frame_data)
    
    return landmarks

def test_model():
    """Test the fixed model with correct data structure"""
    print("🧪 Testing fixed gesture recognition model...")
    
    # Initialize model
    try:
        model = model_simple.SimpleIsolatedASLRecognition(model_path="module/islr")
        print("✅ Model initialized successfully")
    except Exception as e:
        print(f"❌ Model initialization failed: {e}")
        return False
    
    # Create test data
    test_data = create_test_landmark_data()
    print(f"✅ Created {len(test_data)} frames of test data")
    
    # Test prediction
    try:
        result = model.predict(test_data)
        print(f"✅ Prediction successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_model()
    if success:
        print("\n🎉 All tests passed! The model is working correctly.")
    else:
        print("\n💥 Tests failed. There are still issues with the model.")
