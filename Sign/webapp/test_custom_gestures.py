"""
Test script for custom gesture system
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import mediapipe as mp
        print("✓ MediaPipe imported")
    except ImportError as e:
        print(f"✗ MediaPipe import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas imported")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy imported")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    return True

def test_gesture_manager():
    """Test gesture manager functionality"""
    print("\nTesting Gesture Manager...")
    
    try:
        from gesture_manager import GestureManager
        manager = GestureManager()
        
        # Test loading dictionary
        df = manager.load_gesture_dict()
        print(f"✓ Loaded {len(df)} gestures from dictionary")
        
        # Test adding a test gesture
        test_gesture = "test_gesture_temp"
        gesture_id = manager.add_new_gesture(test_gesture)
        print(f"✓ Added test gesture with ID: {gesture_id}")
        
        # Test removing the test gesture
        success = manager.remove_gesture(test_gesture)
        if success:
            print("✓ Removed test gesture")
        
        return True
        
    except Exception as e:
        print(f"✗ Gesture Manager test failed: {e}")
        return False

def test_data_processor():
    """Test data processor functionality"""
    print("\nTesting Data Processor...")
    
    try:
        from data_processor import GestureDataProcessor
        processor = GestureDataProcessor()
        print("✓ Data processor initialized")
        return True
        
    except Exception as e:
        print(f"✗ Data Processor test failed: {e}")
        return False

def test_camera():
    """Test camera access"""
    print("\nTesting Camera...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("✗ Camera not accessible")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            print(f"✓ Camera working - Frame shape: {frame.shape}")
            return True
        else:
            print("✗ Camera not providing frames")
            return False
            
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False

def test_mediapipe():
    """Test MediaPipe holistic model"""
    print("\nTesting MediaPipe...")
    
    try:
        import mediapipe as mp
        import cv2
        import numpy as np
        
        # Initialize MediaPipe
        mp_holistic = mp.solutions.holistic
        holistic = mp_holistic.Holistic(
            static_image_mode=True,
            model_complexity=2,
            refine_face_landmarks=True
        )
        
        # Create a dummy image
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Process the image
        results = holistic.process(dummy_image)
        
        holistic.close()
        print("✓ MediaPipe holistic model working")
        return True
        
    except Exception as e:
        print(f"✗ MediaPipe test failed: {e}")
        return False

def test_file_structure():
    """Test if required files exist"""
    print("\nTesting File Structure...")
    
    required_files = [
        "module/islr/dict_sign.csv",
        "gesture_collector.py",
        "gesture_manager.py",
        "data_processor.py",
        "custom_gesture_workflow.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("=== Custom Gesture System Test ===\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Gesture Manager", test_gesture_manager),
        ("Data Processor", test_data_processor),
        ("Camera", test_camera),
        ("MediaPipe", test_mediapipe)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} Test")
        print('='*50)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("Run: python custom_gesture_workflow.py")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please check the issues above.")
        print("Run: python setup_custom_gestures.py")

if __name__ == "__main__":
    main()
