#!/usr/bin/env python3
"""
Test All Gestures - Debug Script
Tests both pattern-based and trained gestures
"""

import requests
import json

def test_gesture_api():
    """Test the gesture prediction API"""
    
    print("🧪 Testing Gesture Recognition API")
    print("=" * 50)
    
    # Create sample landmark data
    sample_data = [
        {
            "timeInSeconds": 0.1,
            "frameNumber": 1,
            "poseLandmarks": [
                {"x": 0.5, "y": 0.5, "z": 0.0} for _ in range(33)
            ],
            "faceLandmarks": [
                {"x": 0.5, "y": 0.3, "z": 0.0} for _ in range(468)
            ],
            "leftHandLandmarks": [
                {"x": 0.3, "y": 0.5, "z": 0.0} for _ in range(21)
            ],
            "rightHandLandmarks": [
                {"x": 0.7, "y": 0.5, "z": 0.0} for _ in range(21)
            ]
        }
    ]
    
    try:
        response = requests.post(
            "http://127.0.0.1:8001/islr/predict",
            json=sample_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response:")
            print(f"   Sign: {result.get('sign', 'N/A')}")
            print(f"   Sentence: {result.get('sentence', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0):.2%}")
            print(f"   Type: {result.get('type', 'N/A')}")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_available_gestures():
    """Check what gestures are available"""
    
    print("\n🎯 Available Gestures")
    print("=" * 30)
    
    print("📋 Pattern-based gestures:")
    pattern_gestures = ['block_mad', 'hello', 'super', 'swipe', 'thank_you', 'victory', 'welcome']
    for gesture in pattern_gestures:
        print(f"   ✅ {gesture}")
    
    print("\n📋 Trained ML gestures:")
    trained_gestures = ['wave']
    for gesture in trained_gestures:
        print(f"   🤖 {gesture}")
    
    print(f"\n📊 Total gestures available: {len(pattern_gestures) + len(trained_gestures)}")

def main():
    print("🚀 Gesture Recognition Test Suite")
    print("=" * 40)
    
    # Check available gestures
    check_available_gestures()
    
    # Test API
    success = test_gesture_api()
    
    if success:
        print("\n✅ System Status: WORKING")
        print("\n💡 Next Steps:")
        print("1. Test with real camera input in the web interface")
        print("2. Try different gestures to see detection")
        print("3. Check console logs for detailed recognition info")
    else:
        print("\n❌ System Status: ERROR")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the server is running")
        print("2. Check for errors in terminal output")
        print("3. Verify landmark data format")

if __name__ == "__main__":
    main()
