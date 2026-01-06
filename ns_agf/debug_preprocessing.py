"""
Exact Preprocessing Comparison
================================

Compare preprocessing step-by-step between training and inference.
"""

import cv2
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from inference import SignLanguageInference


def detailed_preprocessing_test(video_path):
    """Test each preprocessing step in detail."""
    
    print("=" * 90)
    print("DETAILED PREPROCESSING ANALYSIS")
    print("=" * 90)
    print(f"Video: {Path(video_path).name}\n")
    
    # Load inference system
    inference_system = SignLanguageInference('models/ns_agcn.pth')
    
    # Extract frames
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while len(frames) < 50:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    
    print(f"Step 1: FRAME EXTRACTION")
    print(f"   Total frames extracted: {len(frames)}")
    print(f"   Frame shape: {frames[0].shape}")
    print()
    
    # Extract landmarks
    landmarks_sequence = []
    for frame in frames:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks, _ = inference_system.extractor.extract_with_results(frame_rgb)
        if landmarks is not None:
            landmarks_sequence.append(landmarks)
    
    print(f"Step 2: LANDMARK EXTRACTION")
    print(f"   Valid landmarks: {len(landmarks_sequence)}/{len(frames)}")
    print(f"   Landmark shape per frame: {landmarks_sequence[0].shape}")
    print()
    
    # Convert to numpy array
    raw_sequence = np.array(landmarks_sequence)
    
    print(f"Step 3: NUMPY CONVERSION")
    print(f"   Raw sequence shape: {raw_sequence.shape}")
    print(f"   Expected: (T, 75, 3)")
    print(f"   Raw stats:")
    print(f"      Mean: {raw_sequence.mean():.6f}")
    print(f"      Std: {raw_sequence.std():.6f}")
    print(f"      Min: {raw_sequence.min():.6f}")
    print(f"      Max: {raw_sequence.max():.6f}")
    print()
    
    # Sampling to 30 frames
    current_length = len(raw_sequence)
    if current_length > 30:
        indices = np.linspace(0, current_length - 1, 30, dtype=int)
        sampled_sequence = raw_sequence[indices]
    elif current_length < 30:
        padding = np.repeat(raw_sequence[-1:], 30 - current_length, axis=0)
        sampled_sequence = np.concatenate([raw_sequence, padding], axis=0)
    else:
        sampled_sequence = raw_sequence
    
    print(f"Step 4: SAMPLING TO 30 FRAMES")
    print(f"   Original: {current_length} frames")
    print(f"   Sampled: {sampled_sequence.shape[0]} frames")
    if current_length > 30:
        print(f"   Indices used: {indices[:5]}...{indices[-5:]}")
    print(f"   Sampled stats:")
    print(f"      Mean: {sampled_sequence.mean():.6f}")
    print(f"      Std: {sampled_sequence.std():.6f}")
    print()
    
    # Normalization - step by step
    print(f"Step 5: NORMALIZATION (CRITICAL!)")
    
    # 5a. Center on nose
    nose_positions = sampled_sequence[:, 0:1, :]
    print(f"   5a. Nose positions shape: {nose_positions.shape}")
    print(f"       Nose mean: {nose_positions.mean():.6f}")
    
    centered = sampled_sequence - nose_positions
    print(f"   5b. After centering:")
    print(f"       Shape: {centered.shape}")
    print(f"       Mean: {centered.mean():.6f}")
    print(f"       Std: {centered.std():.6f}")
    
    # 5c. Calculate shoulder distance
    left_shoulder = sampled_sequence[:, 11, :]
    right_shoulder = sampled_sequence[:, 12, :]
    print(f"   5c. Shoulder landmarks:")
    print(f"       Left shoulder shape: {left_shoulder.shape}")
    print(f"       Right shoulder shape: {right_shoulder.shape}")
    
    shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder, axis=1, keepdims=True)
    print(f"   5d. Shoulder distance:")
    print(f"       Shape: {shoulder_dist.shape}")
    print(f"       Mean distance: {shoulder_dist.mean():.6f}")
    print(f"       Min distance: {shoulder_dist.min():.6f}")
    print(f"       Max distance: {shoulder_dist.max():.6f}")
    
    # 5e. Replace small values
    shoulder_dist_safe = np.where(shoulder_dist > 0.01, shoulder_dist, 1.0)
    replaced_count = np.sum(shoulder_dist <= 0.01)
    print(f"   5e. After safety check:")
    print(f"       Replaced {replaced_count} small values with 1.0")
    print(f"       Mean distance: {shoulder_dist_safe.mean():.6f}")
    
    # 5f. Scale
    print(f"   5f. Scaling:")
    print(f"       centered shape: {centered.shape}")
    print(f"       shoulder_dist_safe shape: {shoulder_dist_safe.shape}")
    print(f"       Broadcasting: shoulder_dist_safe[:, :, np.newaxis]")
    
    scaled = centered / shoulder_dist_safe[:, :, np.newaxis]
    print(f"       Scaled shape: {scaled.shape}")
    print(f"       Scaled stats:")
    print(f"          Mean: {scaled.mean():.6f}")
    print(f"          Std: {scaled.std():.6f}")
    print(f"          Min: {scaled.min():.6f}")
    print(f"          Max: {scaled.max():.6f}")
    print()
    
    # Transpose
    print(f"Step 6: TRANSPOSE FOR MODEL")
    transposed = np.transpose(scaled, (2, 0, 1))
    print(f"   Before: (T, V, C) = {scaled.shape}")
    print(f"   After: (C, T, V) = {transposed.shape}")
    print()
    
    # Make prediction
    print(f"Step 7: PREDICTION")
    result = inference_system.predict_from_sequence(landmarks_sequence)
    
    if 'error' in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✅ Predicted: {result['sign']}")
        print(f"   Confidence: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
        if 'top3' in result:
            print(f"   Top 3:")
            for i, (sign, prob) in enumerate(result['top3'], 1):
                print(f"      {i}. {sign}: {prob:.4f} ({prob*100:.2f}%)")
    
    print("=" * 90)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', '-v', required=True)
    args = parser.parse_args()
    
    detailed_preprocessing_test(args.video)
