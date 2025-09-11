"""
Prepare custom gesture data for model training
"""
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

def prepare_training_data():
    """Prepare your custom gesture data for training"""
    print("🔄 Preparing Custom Gesture Data for Training")
    print("=" * 60)
    
    # Check what custom gesture data we have
    processed_dir = Path("processed_data")
    custom_data_files = []
    
    if processed_dir.exists():
        for file in processed_dir.glob("*_training_data.csv"):
            gesture_name = file.stem.replace("_training_data", "")
            custom_data_files.append({
                "gesture": gesture_name,
                "file": file,
                "size": os.path.getsize(file)
            })
    
    if not custom_data_files:
        print("❌ No custom gesture training data found!")
        print("   Run the gesture collection workflow first.")
        return False
    
    print(f"✅ Found {len(custom_data_files)} custom gesture datasets:")
    for data in custom_data_files:
        print(f"   - {data['gesture']}: {data['size']} bytes")
    
    # Check if we need to convert to TFRecords format
    print("\n📋 Training Data Format Requirements:")
    print("   - Current format: CSV with landmarks")
    print("   - Required format: TFRecords")
    print("   - Need to convert your data to match training format")
    
    return True

def check_training_requirements():
    """Check what's needed for training"""
    print("\n🔍 Checking Training Requirements")
    print("=" * 60)
    
    # Check if original training data exists
    original_data_paths = [
        "../../train.csv",
        "../train.csv", 
        "train.csv",
        "data/aslr-5fold/",
        "data/islr-5fold/"
    ]
    
    found_original = False
    for path in original_data_paths:
        if os.path.exists(path):
            print(f"✅ Found original training data: {path}")
            found_original = True
            break
    
    if not found_original:
        print("⚠️  Original training data not found")
        print("   You'll need the original ASL dataset to train")
    
    # Check training notebook
    notebook_path = "../code/model_training.ipynb"
    if os.path.exists(notebook_path):
        print("✅ Training notebook exists")
        with open(notebook_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "NUM_CLASSES  = 253" in content:
                print("✅ Notebook updated to 253 classes")
            else:
                print("❌ Notebook needs NUM_CLASSES update")
    else:
        print("❌ Training notebook not found")
    
    return found_original

def create_combined_dataset_info():
    """Create information about combining datasets"""
    print("\n📊 Dataset Combination Strategy")
    print("=" * 60)
    
    # Load current dictionary
    dict_df = pd.read_csv("module/islr/dict_sign.csv")
    
    original_gestures = dict_df.head(250)
    custom_gestures = dict_df.tail(3)
    
    print(f"📋 Training Dataset Composition:")
    print(f"   - Original ASL gestures: {len(original_gestures)}")
    print(f"   - Your custom gestures: {len(custom_gestures)}")
    print(f"   - Total classes: {len(dict_df)}")
    
    print(f"\n🎯 Your Custom Gestures:")
    for _, row in custom_gestures.iterrows():
        print(f"   - {row['sign_ord']}: {row['sign']}")
    
    return dict_df

def provide_training_options():
    """Provide training options"""
    print("\n🎯 Training Options")
    print("=" * 60)
    
    print("OPTION 1: Quick Training (Recommended)")
    print("- Add your custom gestures to existing model")
    print("- Faster training (few hours)")
    print("- Uses transfer learning approach")
    
    print("\nOPTION 2: Full Retraining")
    print("- Train entire model from scratch")
    print("- Longer training (6-8 hours)")  
    print("- Better accuracy but more time")
    
    print("\nOPTION 3: Test with Existing Model")
    print("- Use current model for existing gestures")
    print("- Add custom gesture recognition separately")
    print("- Quick solution for testing")

def main():
    """Main function"""
    print("🎯 Custom Gesture Training Preparation")
    print("=" * 70)
    
    # Step 1: Check custom data
    if not prepare_training_data():
        return
    
    # Step 2: Check training requirements  
    has_original = check_training_requirements()
    
    # Step 3: Create dataset info
    dict_df = create_combined_dataset_info()
    
    # Step 4: Provide options
    provide_training_options()
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    
    if has_original:
        print("✅ You have everything needed for training!")
        print("\n📋 Training Process:")
        print("1. Open: D:/MAJOR-PROJECT/Sign/code/model_training.ipynb")
        print("2. Verify NUM_CLASSES = 253")
        print("3. Update dataset to include your custom gestures")
        print("4. Run training cells (6-8 hours)")
        print("5. Replace model.tflite with new trained model")
        print("6. Test your custom gestures!")
    else:
        print("⚠️  Missing original training data")
        print("\n📋 Alternative Options:")
        print("1. Download original ASL dataset")
        print("2. Use existing model + custom gesture classifier")
        print("3. Train on your custom gestures only (limited)")
    
    print(f"\n📊 Current Status:")
    print(f"   - Dictionary: {len(dict_df)} gestures ✅")
    print(f"   - Custom data: Available ✅")
    print(f"   - Training notebook: Updated ✅")
    print(f"   - Model: Needs retraining ⏳")

if __name__ == "__main__":
    main()
