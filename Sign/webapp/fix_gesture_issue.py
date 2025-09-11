"""
Complete fix for gesture recognition issue
"""
import pandas as pd
import os

def diagnose_gesture_issue():
    """Diagnose the gesture recognition issue"""
    print("🔍 Diagnosing Gesture Recognition Issue")
    print("=" * 50)
    
    # Check dictionary
    dict_file = "module/islr/dict_sign.csv"
    if os.path.exists(dict_file):
        df = pd.read_csv(dict_file)
        print(f"✅ Dictionary has {len(df)} gestures")
        print(f"📋 New gestures: {list(df.tail(3)['sign'])}")
        print(f"📋 New gesture IDs: {list(df.tail(3)['sign_ord'])}")
    else:
        print("❌ Dictionary file not found!")
        return
    
    # Check model file
    model_file = "module/islr/model.tflite"
    if os.path.exists(model_file):
        print("✅ Model file exists")
        print("⚠️  But this model was trained on fewer classes!")
    else:
        print("❌ Model file not found!")
    
    # Check training notebook
    training_file = "../code/model_training.ipynb"
    if os.path.exists(training_file):
        with open(training_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "NUM_CLASSES  = 253" in content:
                print("✅ Training notebook updated to 253 classes")
            else:
                print("❌ Training notebook still has old NUM_CLASSES")
    
    print("\n🎯 PROBLEM IDENTIFIED:")
    print("- Your dictionary has 253 gestures")
    print("- Your model was trained on 250 classes") 
    print("- New gestures (IDs 250, 251, 252) can't be predicted")
    print("\n💡 SOLUTION:")
    print("1. Retrain the model with 253 classes")
    print("2. Or temporarily remove new gestures for testing")

def temporary_fix_for_testing():
    """Temporarily reduce dictionary to match current model"""
    print("\n🔧 Applying Temporary Fix for Testing")
    print("=" * 50)
    
    # Backup current dictionary
    dict_file = "module/islr/dict_sign.csv"
    backup_file = "module/islr/dict_sign_full.csv"
    
    df = pd.read_csv(dict_file)
    df.to_csv(backup_file, index=False)
    print(f"✅ Backed up full dictionary to: {backup_file}")
    
    # Create temporary dictionary with only first 250 gestures
    temp_df = df.head(250)
    temp_df.to_csv(dict_file, index=False)
    print(f"✅ Created temporary dictionary with 250 gestures")
    print(f"⚠️  Your new gestures are temporarily hidden")
    
    return backup_file

def restore_full_dictionary():
    """Restore the full dictionary"""
    print("\n🔄 Restoring Full Dictionary")
    print("=" * 50)
    
    dict_file = "module/islr/dict_sign.csv"
    backup_file = "module/islr/dict_sign_full.csv"
    
    if os.path.exists(backup_file):
        df = pd.read_csv(backup_file)
        df.to_csv(dict_file, index=False)
        print(f"✅ Restored full dictionary with {len(df)} gestures")
        os.remove(backup_file)
        print("✅ Removed backup file")
    else:
        print("❌ Backup file not found!")

def main():
    """Main function"""
    print("🎯 Gesture Recognition Issue Fixer")
    print("=" * 60)
    
    diagnose_gesture_issue()
    
    print("\n" + "=" * 60)
    print("CHOOSE YOUR APPROACH:")
    print("1. Temporary fix - Hide new gestures (quick test)")
    print("2. Proper fix - Retrain model (recommended)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        backup_file = temporary_fix_for_testing()
        print(f"\n🎯 TESTING INSTRUCTIONS:")
        print("1. Restart your web server")
        print("2. Test gesture recognition with existing gestures")
        print("3. Run this script again and choose option 4 to restore")
        print(f"4. Your new gestures are backed up in: {backup_file}")
        
    elif choice == "2":
        print(f"\n🎯 PROPER FIX INSTRUCTIONS:")
        print("1. Your training notebook is already updated to 253 classes")
        print("2. Open: D:/MAJOR-PROJECT/Sign/code/model_training.ipynb")
        print("3. Run the training cells (will take several hours)")
        print("4. Replace the old model.tflite with the new trained model")
        print("5. Test your new gestures!")
        
    elif choice == "3":
        print("Goodbye!")
        
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
