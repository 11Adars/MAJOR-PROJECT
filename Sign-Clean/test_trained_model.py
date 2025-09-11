#!/usr/bin/env python3
"""
Test script for the trained gesture recognition model
"""
import joblib
import json
import numpy as np
import pandas as pd
import ast
from pathlib import Path

def load_model(model_name="simple_gesture_classifier"):
    """Load the trained model and its components"""
    models_folder = Path("models")
    
    # Load model
    model = joblib.load(models_folder / f"{model_name}.pkl")
    
    # Load scaler
    scaler = joblib.load(models_folder / f"{model_name}_scaler.pkl")
    
    # Load gesture mapping
    with open(models_folder / f"{model_name}_mapping.json", 'r') as f:
        gesture_mapping = json.load(f)
    
    # Load label encoder
    label_encoder = joblib.load(models_folder / f"{model_name}_encoder.pkl")
    
    return model, scaler, gesture_mapping, label_encoder

def test_sample_prediction():
    """Test the model with a sample from the data"""
    print("🧪 Testing trained model...")
    
    # Load the model
    model, scaler, gesture_mapping, label_encoder = load_model()
    
    print(f"📋 Available gestures: {list(gesture_mapping.values())}")
    
    # Load a sample from test data
    csv_file = Path("gesture_data/done_landmarks.csv")
    df = pd.read_csv(csv_file)
    
    # Take the first sample
    sample_row = df.iloc[0]
    landmarks_str = sample_row['landmarks']
    true_gesture = sample_row['sign']
    
    # Parse landmarks
    landmarks_list = ast.literal_eval(landmarks_str)
    features = np.array(landmarks_list).reshape(1, -1)
    
    # Scale features
    features_scaled = scaler.transform(features)
    
    # Predict
    prediction = model.predict(features_scaled)[0]
    probability = model.predict_proba(features_scaled)[0]
    
    # Get gesture name
    predicted_gesture = gesture_mapping[str(prediction)]
    
    print(f"\n🎯 Test Results:")
    print(f"True gesture: {true_gesture}")
    print(f"Predicted gesture: {predicted_gesture}")
    print(f"Correct: {'✅' if true_gesture == predicted_gesture else '❌'}")
    
    print(f"\n📊 Prediction probabilities:")
    for i, prob in enumerate(probability):
        gesture_name = gesture_mapping[str(i)]
        print(f"   {gesture_name}: {prob:.3f}")
    
    return true_gesture == predicted_gesture

def test_model_info():
    """Display model information"""
    print("\n📋 Model Information:")
    
    model, scaler, gesture_mapping, label_encoder = load_model()
    
    print(f"Model type: {type(model).__name__}")
    print(f"Number of features: {model.n_features_in_}")
    print(f"Number of classes: {len(gesture_mapping)}")
    print(f"Gesture classes: {list(gesture_mapping.values())}")
    
    if hasattr(model, 'feature_importances_'):
        top_features = np.argsort(model.feature_importances_)[-10:]
        print(f"\nTop 10 most important features (indices): {top_features}")

def main():
    print("🔍 Testing Gesture Recognition Model")
    print("=" * 50)
    
    try:
        # Test model info
        test_model_info()
        
        # Test prediction
        success = test_sample_prediction()
        
        if success:
            print("\n✅ Model test passed!")
        else:
            print("\n❌ Model test failed!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
