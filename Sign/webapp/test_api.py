#!/usr/bin/env python3
"""
Real-time Custom Gesture Testing
Test your custom gestures with sample data
"""

import requests
import json
import pandas as pd
from pathlib import Path
import ast

def test_api_with_sample_data():
    """Test the API with actual gesture data"""
    print("🧪 Testing API with Real Gesture Data")
    print("=" * 40)
    
    # API endpoint
    url = "http://127.0.0.1:8000/islr/predict"
    
    # Load sample gesture data
    data_dir = Path("processed_data")
    
    for gesture_name in ['welcome', 'bank']:
        print(f"\n🔍 Testing {gesture_name}...")
        
        data_file = data_dir / f"{gesture_name}_training_data.csv"
        
        if not data_file.exists():
            print(f"  ❌ Data file not found: {data_file}")
            continue
        
        try:
            df = pd.read_csv(data_file)
            
            # Take first sequence
            seq_data = df[df['sequence_id'] == 0]
            
            if len(seq_data) == 0:
                print(f"  ❌ No data for sequence 0")
                continue
            
            # Convert to API format
            api_data = []
            
            for idx, row in seq_data.iterrows():
                try:
                    # Parse landmarks
                    landmarks = ast.literal_eval(row['landmarks'])
                    
                    # Create the API format
                    landmark_data = {
                        "timeInSeconds": float(row['frame']) * 0.033,  # Assuming 30fps
                        "frameNumber": int(row['frame']),
                        "poseLandmarks": [],
                        "faceLandmarks": [],
                        "leftHandLandmarks": [],
                        "rightHandLandmarks": []
                    }
                    
                    # Fill landmarks (simplified for testing)
                    # For actual testing, you'd need to properly structure the landmarks
                    # Here we'll create minimal viable data
                    
                    # Add some basic landmarks
                    for i in range(21):  # Hand landmarks
                        if i * 3 + 2 < len(landmarks):
                            landmark_data["rightHandLandmarks"].append({
                                "x": float(landmarks[i * 3]),
                                "y": float(landmarks[i * 3 + 1]),
                                "z": float(landmarks[i * 3 + 2]) if i * 3 + 2 < len(landmarks) else 0.0
                            })
                    
                    api_data.append(landmark_data)
                    
                    if len(api_data) >= 15:  # Limit to 15 frames for testing
                        break
                        
                except Exception as e:
                    print(f"  ⚠️  Error processing frame {idx}: {e}")
                    continue
            
            if not api_data:
                print(f"  ❌ No valid data to send")
                continue
            
            # Make API request
            try:
                response = requests.post(url, json=api_data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    predicted = result.get('sign_name', 'Unknown')
                    pred_type = result.get('prediction_type', 'unknown')
                    confidence = result.get('confidence', 0)
                    
                    if predicted == gesture_name:
                        print(f"  ✅ CORRECT: {predicted} ({pred_type}, {confidence:.1%})")
                    else:
                        print(f"  ❌ WRONG: Expected {gesture_name}, got {predicted} ({pred_type}, {confidence:.1%})")
                else:
                    print(f"  ❌ API Error: {response.status_code}")
                    print(f"     Response: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Connection Error: {e}")
                
        except Exception as e:
            print(f"  ❌ Error processing {gesture_name}: {e}")

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except:
        print("❌ Server is not running")
        return False

def main():
    print("🚀 Custom Gesture API Testing")
    print("=" * 40)
    
    # Check server
    if not check_server_status():
        print("\n💡 Start the server first:")
        print("cd d:\\MAJOR-PROJECT\\Sign\\webapp")
        print("..\\..\\venv\\Scripts\\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000")
        return
    
    # Test with sample data
    test_api_with_sample_data()
    
    print("\n🎯 Testing Complete!")
    print("\n📋 Next Steps:")
    print("1. Open http://127.0.0.1:8000 in your browser")
    print("2. Allow camera access")
    print("3. Try performing your custom gestures:")
    print("   - welcome")
    print("   - bank")
    print("   - block")
    print("4. Check if they are recognized correctly")

if __name__ == "__main__":
    main()
