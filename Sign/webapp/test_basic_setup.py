import os
import json
import numpy as np
from pathlib import Path
import joblib

# Simple test to see if we can create a basic model without complex training

def create_simple_mapping():
    """Create a simple mapping for the gestures we have"""
    
    # Check available gestures
    custom_videos_path = Path("custom_videos")
    if not custom_videos_path.exists():
        print("❌ Custom videos directory not found")
        return False
    
    gesture_dirs = [d for d in custom_videos_path.iterdir() if d.is_dir()]
    gesture_names = [d.name for d in gesture_dirs]
    
    print(f"📁 Found gestures: {gesture_names}")
    
    # Create mapping
    gesture_mapping = {gesture: idx for idx, gesture in enumerate(gesture_names)}
    
    # Save mapping
    with open("simple_custom_mapping.json", 'w') as f:
        json.dump(gesture_mapping, f, indent=2)
    
    print(f"💾 Mapping saved: {gesture_mapping}")
    
    # Create a simple mock label encoder
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    label_encoder.fit(gesture_names)
    
    joblib.dump(label_encoder, "simple_custom_labels.pkl")
    print("💾 Label encoder saved")
    
    return True

def test_tensorflow():
    """Test if TensorFlow is working"""
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow {tf.__version__} is working")
        
        # Create a simple model
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(30, 100)),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(len(json.load(open("simple_custom_mapping.json"))), activation='softmax')
        ])
        
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        
        # Save the model
        model.save("simple_custom_lstm.h5")
        print("💾 Simple model created and saved")
        
        return True
    except Exception as e:
        print(f"❌ TensorFlow error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing basic setup...")
    
    if create_simple_mapping():
        if test_tensorflow():
            print("✅ Basic setup complete!")
        else:
            print("❌ TensorFlow test failed")
    else:
        print("❌ Mapping creation failed")
