"""
Quick test to verify your new gesture integration
"""
import pandas as pd
import os

def quick_gesture_test(gesture_name="welcome"):
    """Quick test of newly added gesture"""
    print(f"🧪 Testing gesture: '{gesture_name}'")
    print("=" * 50)
    
    # Test 1: Check if gesture is in dictionary
    dict_file = "module/islr/dict_sign.csv"
    if os.path.exists(dict_file):
        df = pd.read_csv(dict_file)
        gesture_row = df[df['sign'] == gesture_name]
        
        if not gesture_row.empty:
            gesture_id = gesture_row['sign_ord'].iloc[0]
            print(f"✅ Test 1 PASSED: Gesture '{gesture_name}' found with ID {gesture_id}")
        else:
            print(f"❌ Test 1 FAILED: Gesture '{gesture_name}' not in dictionary")
            return False
    else:
        print("❌ Test 1 FAILED: Dictionary file not found")
        return False
    
    # Test 2: Check raw data
    raw_files = [f for f in os.listdir("custom_gestures") if f.startswith(gesture_name)]
    if raw_files:
        raw_file = os.path.join("custom_gestures", raw_files[0])
        raw_df = pd.read_csv(raw_file)
        sequences = raw_df['sequence_id'].nunique()
        print(f"✅ Test 2 PASSED: Found raw data with {sequences} sequences")
    else:
        print(f"❌ Test 2 FAILED: No raw data found for '{gesture_name}'")
        return False
    
    # Test 3: Check processed data
    processed_file = f"processed_data/{gesture_name}_training_data.csv"
    if os.path.exists(processed_file):
        processed_df = pd.read_csv(processed_file)
        print(f"✅ Test 3 PASSED: Found processed data with {len(processed_df)} samples")
    else:
        print(f"❌ Test 3 FAILED: No processed data found")
        return False
    
    # Test 4: Check data format
    try:
        sample_landmarks = eval(processed_df['landmarks'].iloc[0])
        expected_size = 543 * 3  # 543 landmarks * 3 coordinates
        if len(sample_landmarks) == expected_size:
            print(f"✅ Test 4 PASSED: Data format correct ({len(sample_landmarks)} features)")
        else:
            print(f"⚠️  Test 4 WARNING: Unexpected data size ({len(sample_landmarks)} vs {expected_size})")
    except Exception as e:
        print(f"❌ Test 4 FAILED: Data format error - {e}")
        return False
    
    # Test 5: Check model configuration
    try:
        model_file = "module/islr/model.py"
        if os.path.exists(model_file):
            with open(model_file, 'r') as f:
                content = f.read()
                if f"NUM_CLASSES = {len(df)}" in content:
                    print(f"✅ Test 5 PASSED: Model updated with {len(df)} classes")
                else:
                    print(f"⚠️  Test 5 WARNING: Model classes might not be updated")
        else:
            print("⚠️  Test 5 WARNING: Model file not found")
    except Exception as e:
        print(f"❌ Test 5 FAILED: Model check error - {e}")
    
    print("\n🎉 Overall: Gesture integration looks good!")
    print("\n📋 Next Steps:")
    print("1. Run live testing to verify data quality")
    print("2. Retrain the model with your new gesture")
    print("3. Test recognition in the main application")
    
    return True

if __name__ == "__main__":
    # Test the welcome gesture you just added
    quick_gesture_test("welcome")
    
    # You can test other gestures too
    gesture_name = input("\nEnter another gesture name to test (or press Enter to skip): ").strip()
    if gesture_name:
        quick_gesture_test(gesture_name)
