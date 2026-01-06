"""
Advanced Model Diagnostic Script
=================================

Compare predictions on training videos to identify issues:
- Check if normalization is correct
- Verify bone feature computation
- Analyze prediction probabilities
- Compare preprocessing steps
"""

import cv2
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from inference import SignLanguageInference


def diagnose_prediction(video_path, expected_sign=None):
    """Run comprehensive diagnostic on a video."""
    
    print("=" * 80)
    print("ADVANCED MODEL DIAGNOSTIC")
    print("=" * 80)
    print(f"Video: {Path(video_path).name}")
    print(f"Expected Sign: {expected_sign or 'Unknown'}")
    print()
    
    # Load model
    model_path = model_path_override if 'model_path_override' in globals() else 'models/test.pth'
    print(f"   Using model: {model_path}\n")
    inference_system = SignLanguageInference(model_path)
    
    # Extract frames
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    
    while len(frames) < 50:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    print(f"📹 Extracted {len(frames)} frames")
    
    # Extract landmarks (same as API)
    landmarks_sequence = []
    
    for i, frame in enumerate(frames):
        # BGR to RGB (CRITICAL!)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks, _ = inference_system.extractor.extract_with_results(frame_rgb)
        
        if landmarks is not None:
            landmarks_sequence.append(landmarks)
    
    print(f"✅ Valid landmarks: {len(landmarks_sequence)}/{len(frames)}")
    
    if len(landmarks_sequence) < 10:
        print("❌ Insufficient landmarks")
        return
    
    # Diagnostic 1: Check raw landmarks stats
    raw_sequence = np.array(landmarks_sequence)
    print(f"\n📊 RAW LANDMARKS:")
    print(f"   Shape: {raw_sequence.shape}")
    print(f"   Mean: {raw_sequence.mean():.6f}")
    print(f"   Std: {raw_sequence.std():.6f}")
    print(f"   Min: {raw_sequence.min():.6f}, Max: {raw_sequence.max():.6f}")
    
    # Diagnostic 2: Check normalized landmarks
    normalized = inference_system.normalize_landmarks(raw_sequence)
    print(f"\n📊 NORMALIZED LANDMARKS:")
    print(f"   Shape: {normalized.shape}")
    print(f"   Mean: {normalized.mean():.6f}")
    print(f"   Std: {normalized.std():.6f}")
    print(f"   Min: {normalized.min():.6f}, Max: {normalized.max():.6f}")
    
    # Diagnostic 3: Check motion
    hand_landmarks = raw_sequence[:, 33:, :]
    motion_variance = np.var(hand_landmarks)
    print(f"\n📊 MOTION ANALYSIS:")
    print(f"   Hand variance: {motion_variance:.6f}")
    print(f"   Status: {'✅ Good motion' if motion_variance > 0.00005 else '⚠️ Low motion'}")
    
    # Diagnostic 4: Check sampling
    current_length = len(landmarks_sequence)
    print(f"\n📊 SAMPLING:")
    print(f"   Original frames: {current_length}")
    
    if current_length > 30:
        indices = np.linspace(0, current_length - 1, 30, dtype=int)
        print(f"   Sampled indices (uniform): {indices[:5]}...{indices[-5:]}")
    elif current_length < 30:
        print(f"   Will pad to 30 frames")
    else:
        print(f"   Exactly 30 frames, no sampling needed")
    
    # Diagnostic 5: Make prediction
    print(f"\n🔮 MAKING PREDICTION...")
    result = inference_system.predict_from_sequence(landmarks_sequence)
    
    print(f"\n{'=' * 80}")
    print("PREDICTION RESULTS")
    print(f"{'=' * 80}")
    
    if 'error' in result:
        print(f"❌ ERROR: {result['error']}")
    else:
        predicted = result['sign']
        confidence = result['confidence']
        entropy = result.get('entropy', 0)
        
        # Check if correct
        is_correct = (expected_sign and predicted.lower() == expected_sign.lower())
        status = "✅ CORRECT" if is_correct else "❌ WRONG"
        
        print(f"{status}")
        print(f"   Expected: {expected_sign or 'N/A'}")
        print(f"   Predicted: {predicted}")
        print(f"   Confidence: {confidence:.4f} ({confidence*100:.2f}%)")
        print(f"   Entropy: {entropy:.4f}")
        
        if 'top3' in result and result['top3']:
            print(f"\n📊 Top 3 Predictions:")
            for i, (sign, prob) in enumerate(result['top3'], 1):
                marker = "✅" if sign.lower() == (expected_sign or '').lower() else "  "
                print(f"   {marker} {i}. {sign}: {prob:.4f} ({prob*100:.2f}%)")
    
    print(f"{'=' * 80}")
    
    # Diagnostic 6: Check if expected sign is in class list
    if expected_sign:
        class_names_lower = [c.lower() for c in inference_system.class_names]
        if expected_sign.lower() in class_names_lower:
            idx = class_names_lower.index(expected_sign.lower())
            print(f"\n✅ '{expected_sign}' is class #{idx} in model")
        else:
            print(f"\n❌ WARNING: '{expected_sign}' is NOT in model classes!")
            print(f"   Available classes: {inference_system.class_names}")
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnose sign language predictions')
    parser.add_argument('--video', '-v', required=True, help='Path to video file')
    parser.add_argument('--expected', '-e', help='Expected sign name')
    parser.add_argument('--model', '-m', default='models/test.pth', help='Model path (default: test.pth)')
    
    args = parser.parse_args()
    
    # Override model path with command line argument
    global model_path_override
    model_path_override = args.model
    
    diagnose_prediction(args.video, args.expected)
