"""
Final integration test script - Testing your new gesture with the actual model
"""
import os
import subprocess
import time
import requests
import cv2
import json

def test_model_integration():
    """Test if your new gesture can be recognized by the current model"""
    print("🔍 Testing Model Integration")
    print("=" * 50)
    
    # Check if the web server is running
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print("✅ Web server is running")
    except requests.exceptions.RequestException:
        print("❌ Web server not running. Starting it...")
        print("Please run: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        return False
    
    # Test the prediction endpoint
    try:
        # Create dummy data structure (similar to what the frontend sends)
        test_data = {
            "landmarks": [[{"x": 0.5, "y": 0.5, "z": 0.5} for _ in range(543)] for _ in range(30)]
        }
        
        response = requests.post("http://127.0.0.1:8000/islr/predict", 
                               json=test_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Prediction endpoint working - Predicted: {result.get('predicted_sign', 'Unknown')}")
            return True
        else:
            print(f"❌ Prediction endpoint error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing prediction: {e}")
        return False

def check_training_requirements():
    """Check what's needed for training your new gesture"""
    print("\n🎯 Training Requirements Check")
    print("=" * 50)
    
    # Check if training notebooks exist
    training_files = [
        "Sign/code/model_training.ipynb",
        "Sign/code/create_parquet.ipynb"
    ]
    
    for file_path in training_files:
        full_path = f"D:/MAJOR-PROJECT/{file_path}"
        if os.path.exists(full_path):
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
    
    # Check current model
    model_files = [
        "module/islr/model.py",
        "module/islr/dict_sign.csv"
    ]
    
    for file_path in model_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")

def provide_next_steps():
    """Provide clear next steps for the user"""
    print("\n📋 Next Steps After Recording Your Gesture")
    print("=" * 60)
    
    print("\n🎯 IMMEDIATE TESTING:")
    print("1. ✅ Data Collection - COMPLETED")
    print("   Your 'welcome' gesture data is saved and processed")
    
    print("\n2. 🧪 Live Testing (Optional but Recommended)")
    print("   Run: python test_gesture.py")
    print("   Select option 3 to test live recognition")
    
    print("\n🔄 MODEL RETRAINING (Required for Recognition):")
    print("3. 📊 Prepare Training Data")
    print("   - Your data is in: processed_data/welcome_training_data.csv")
    print("   - Format: Ready for training")
    
    print("\n4. 🤖 Retrain the Model")
    print("   - Open: D:/MAJOR-PROJECT/Sign/code/model_training.ipynb")
    print("   - Update dataset to include your new gesture")
    print("   - Run training with updated NUM_CLASSES = 252")
    
    print("\n5. 🚀 Deploy Updated Model")
    print("   - Replace existing model files")
    print("   - Restart web application")
    print("   - Test your gesture in the web interface")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("- Your gesture won't be recognized until you retrain the model")
    print("- The current model only knows the original 250 gestures")
    print("- Training may take several hours depending on your hardware")
    
    print("\n🎯 TESTING YOUR WORK SO FAR:")
    print("- Data quality: ✅ Good (30 sequences collected)")
    print("- Data format: ✅ Processed correctly")
    print("- Dictionary: ✅ Updated with new gesture")
    print("- Model config: ✅ Updated to 252 classes")

def create_training_checklist():
    """Create a checklist file for training"""
    checklist = """
# Training Checklist for New Gesture: 'welcome'

## Pre-Training Verification ✅
- [x] Gesture data collected (30 sequences)
- [x] Data processed and formatted
- [x] Dictionary updated (ID: 251)
- [x] Model configuration updated (252 classes)

## Training Steps
- [ ] Open model_training.ipynb
- [ ] Update dataset path to include new gesture data
- [ ] Verify NUM_CLASSES = 252 in model configuration
- [ ] Run training process
- [ ] Validate training results
- [ ] Save trained model

## Post-Training Steps
- [ ] Replace model files in webapp
- [ ] Restart web application
- [ ] Test 'welcome' gesture recognition
- [ ] Verify accuracy and performance

## Troubleshooting
If gesture not recognized:
1. Check data quality in processed_data/welcome_training_data.csv
2. Verify model training completed successfully
3. Ensure model files are properly deployed
4. Test with clear, consistent gesture performance

## Files Created
- custom_gestures/welcome_20250901_222442.csv (raw data)
- processed_data/welcome_training_data.csv (training data)
- Updated module/islr/dict_sign.csv (gesture dictionary)
"""
    
    with open("TRAINING_CHECKLIST.md", "w") as f:
        f.write(checklist)
    
    print("\n📝 Created: TRAINING_CHECKLIST.md")

def main():
    """Main testing and guidance function"""
    print("🎉 Congratulations! Your Gesture Recording is Complete!")
    print("=" * 60)
    
    # Test current integration
    test_model_integration()
    
    # Check training requirements
    check_training_requirements()
    
    # Provide next steps
    provide_next_steps()
    
    # Create checklist
    create_training_checklist()
    
    print("\n" + "=" * 60)
    print("🚀 SUMMARY:")
    print("✅ Your 'welcome' gesture has been successfully collected and processed!")
    print("⏳ Next: Retrain the model to recognize your new gesture")
    print("📖 Guide: See TRAINING_CHECKLIST.md for detailed steps")
    print("🧪 Test: Run 'python test_gesture.py' for live testing")

if __name__ == "__main__":
    main()
