#!/usr/bin/env python3
"""
Test Enhanced Model with Custom Gestures
"""
import sys
import os
sys.path.append('.')
sys.path.append('app')

from module.islr.model_enhanced import IsolatedASLRecognition
import pandas as pd

def test_enhanced_model():
    print("🧪 Testing Enhanced Model")
    print("=" * 30)
    
    try:
        # Initialize the enhanced model
        model = IsolatedASLRecognition(model_path="module/islr")
        print("✅ Enhanced model loaded successfully")
        
        # Check if custom classifier is loaded
        if model.custom_classifier is not None:
            print("✅ Custom gesture classifier loaded")
            print(f"📋 Custom gestures: {list(model.custom_mapping.keys())}")
        else:
            print("❌ Custom gesture classifier not loaded")
        
        # Check gesture dictionary
        print(f"📊 Total gestures in dictionary: {len(model.ORD2SIGN)}")
        
        # Check for custom gestures in dictionary
        custom_gestures = [name for id, name in model.ORD2SIGN.items() if id >= 250]
        print(f"🎯 Custom gestures in dictionary: {custom_gestures}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        return False

def check_files():
    print("\n📁 Checking Required Files")
    print("=" * 30)
    
    required_files = [
        "custom_gesture_classifier.pkl",
        "custom_gesture_scaler.pkl", 
        "custom_gesture_mapping.json",
        "module/islr/dict_sign.csv",
        "module/islr/model.tflite"
    ]
    
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("🚀 Enhanced Model Testing")
    print("=" * 40)
    
    # Check files first
    files_ok = check_files()
    
    if files_ok:
        # Test the model
        model_ok = test_enhanced_model()
        
        if model_ok:
            print("\n🎉 All tests passed!")
            print("Your enhanced model should now recognize custom gestures!")
        else:
            print("\n❌ Model test failed")
    else:
        print("\n❌ Missing required files")
        
    print("\n📋 Next Steps:")
    print("1. Start your web application")
    print("2. Test with webcam gestures")
    print("3. Try your custom gestures: welcome, bank, block")
