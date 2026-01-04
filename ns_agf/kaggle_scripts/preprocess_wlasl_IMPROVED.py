"""
IMPROVED Preprocessing for Sign Language Recognition
Fixes for complex multi-action signs and low confidence issues

Key Improvements:
1. Better temporal augmentation (proper resampling, not zero-padding)
2. More diverse speed variations (0.7x, 0.85x, 1.0x, 1.15x, 1.3x)
3. Added rotation augmentation for robustness
4. Added gaussian noise for generalization
5. Improved frame sampling (maintains temporal dynamics)
6. Better handling of complex signs with multiple actions
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
from tqdm import tqdm
import json

# Configuration
SEQUENCE_LENGTH = 30  # Number of frames per sequence
NUM_NODES = 75  # 33 pose + 21 left hand + 21 right hand
NUM_FEATURES = 3  # x, y, z coordinates
MIN_FRAMES_REQUIRED = 15  # Minimum frames needed for a valid video

# MediaPipe setup
mp_holistic = mp.solutions.holistic


def extract_landmarks(image, holistic):
    """
    Extract landmarks from a single frame using MediaPipe Holistic.
    Returns 75 landmarks (33 pose + 21 left hand + 21 right hand)
    """
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = holistic.process(image_rgb)
    
    # Initialize landmarks array
    landmarks = np.zeros((NUM_NODES, NUM_FEATURES))
    
    # Extract pose landmarks (33 points)
    if results.pose_landmarks:
        for i, lm in enumerate(results.pose_landmarks.landmark):
            landmarks[i] = [lm.x, lm.y, lm.z]
    
    # Extract left hand landmarks (21 points, starting at index 33)
    if results.left_hand_landmarks:
        for i, lm in enumerate(results.left_hand_landmarks.landmark):
            landmarks[33 + i] = [lm.x, lm.y, lm.z]
    
    # Extract right hand landmarks (21 points, starting at index 54)
    if results.right_hand_landmarks:
        for i, lm in enumerate(results.right_hand_landmarks.landmark):
            landmarks[54 + i] = [lm.x, lm.y, lm.z]
    
    return landmarks


def normalize_landmarks(sequence):
    """
    IMPROVED: Normalize landmarks with better stability.
    
    Args:
        sequence: (T, 75, 3) array
    Returns:
        Normalized sequence
    """
    # Center around nose (landmark 0)
    nose_positions = sequence[:, 0:1, :]  # (T, 1, 3)
    centered = sequence - nose_positions
    
    # Scale by shoulder width (more stable than overall range)
    # Left shoulder = 11, Right shoulder = 12
    left_shoulder = sequence[:, 11, :]
    right_shoulder = sequence[:, 12, :]
    shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder, axis=1, keepdims=True)  # (T, 1)
    
    # Use median shoulder distance (more robust to outliers)
    median_shoulder_dist = np.median(shoulder_dist)
    if median_shoulder_dist < 0.01:
        median_shoulder_dist = 1.0
    
    # Scale by median (consistent across entire sequence)
    scaled = centered / median_shoulder_dist
    
    return scaled


def resample_sequence(sequence, target_length):
    """
    IMPROVED: Resample sequence to target length using interpolation.
    Maintains temporal dynamics better than simple uniform sampling.
    
    Args:
        sequence: (T, V, C) array
        target_length: Target number of frames
    Returns:
        Resampled sequence (target_length, V, C)
    """
    current_length = sequence.shape[0]
    
    if current_length == target_length:
        return sequence
    
    # Create indices for interpolation
    original_indices = np.arange(current_length)
    target_indices = np.linspace(0, current_length - 1, target_length)
    
    # Interpolate each coordinate
    resampled = np.zeros((target_length, sequence.shape[1], sequence.shape[2]))
    
    for v in range(sequence.shape[1]):  # For each node
        for c in range(sequence.shape[2]):  # For each coordinate
            resampled[:, v, c] = np.interp(target_indices, original_indices, sequence[:, v, c])
    
    return resampled


def augment_sequence_improved(sequence, augmentation_type='original'):
    """
    IMPROVED: Better augmentation that preserves temporal dynamics.
    
    Augmentation types:
    - original: No change
    - flip: Horizontal flip (swap left/right)
    - slow: 70% speed (more frames, captures finer motion)
    - medium_slow: 85% speed
    - medium_fast: 115% speed  
    - fast: 130% speed (fewer frames, captures overall motion)
    - rotate_small: Small rotation variation
    - noise: Add small gaussian noise
    """
    T, V, C = sequence.shape
    
    if augmentation_type == 'original':
        return sequence.copy()
    
    elif augmentation_type == 'flip':
        # Horizontal flip
        flipped = sequence.copy()
        flipped[:, :, 0] = 1.0 - flipped[:, :, 0]  # Flip x
        
        # Swap left and right hands (indices 33-53 with 54-74)
        left_hand = flipped[:, 33:54, :].copy()
        right_hand = flipped[:, 54:75, :].copy()
        flipped[:, 33:54, :] = right_hand
        flipped[:, 54:75, :] = left_hand
        
        # Swap left and right shoulders/elbows/wrists in pose
        # Left shoulder(11) <-> Right shoulder(12)
        # Left elbow(13) <-> Right elbow(14)
        # Left wrist(15) <-> Right wrist(16)
        for left_idx, right_idx in [(11, 12), (13, 14), (15, 16)]:
            temp = flipped[:, left_idx, :].copy()
            flipped[:, left_idx, :] = flipped[:, right_idx, :]
            flipped[:, right_idx, :] = temp
        
        return flipped
    
    elif augmentation_type in ['slow', 'medium_slow', 'medium_fast', 'fast']:
        # Speed variation using proper resampling
        speed_factors = {
            'slow': 0.7,        # 70% speed = more frames = 30/0.7 = 43 frames
            'medium_slow': 0.85,  # 85% speed = 30/0.85 = 35 frames
            'medium_fast': 1.15,  # 115% speed = 30/1.15 = 26 frames
            'fast': 1.3          # 130% speed = 30/1.3 = 23 frames
        }
        
        speed_factor = speed_factors[augmentation_type]
        new_length = int(T * speed_factor)
        
        # Resample to new length
        stretched = resample_sequence(sequence, new_length)
        
        # Then resample back to target length (maintains temporal patterns)
        final = resample_sequence(stretched, SEQUENCE_LENGTH)
        
        return final
    
    elif augmentation_type == 'rotate_small':
        # Small rotation around z-axis (simulates slight camera angle change)
        angle = np.random.uniform(-5, 5) * np.pi / 180  # ±5 degrees
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        rotated = sequence.copy()
        # Apply 2D rotation to x,y coordinates
        x = sequence[:, :, 0]
        y = sequence[:, :, 1]
        rotated[:, :, 0] = x * cos_a - y * sin_a
        rotated[:, :, 1] = x * sin_a + y * cos_a
        
        return rotated
    
    elif augmentation_type == 'noise':
        # Add small gaussian noise
        noise = np.random.normal(0, 0.01, sequence.shape)
        noisy = sequence + noise
        return noisy
    
    return sequence.copy()


def process_video(video_path, target_frames=SEQUENCE_LENGTH, apply_augmentation=False):
    """
    IMPROVED: Process video with better augmentation strategy.
    
    Args:
        video_path: Path to video file
        target_frames: Number of frames to extract (default 30)
        apply_augmentation: Whether to augment this video
    
    Returns:
        List of sequences with augmentation labels
    """
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        return None
    
    frames_landmarks = []
    frame_count = 0
    
    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            landmarks = extract_landmarks(frame, holistic)
            
            # Check if any landmarks detected (not all zeros)
            if np.any(landmarks):
                frames_landmarks.append(landmarks)
            
            frame_count += 1
    
    cap.release()
    
    if len(frames_landmarks) < MIN_FRAMES_REQUIRED:
        print(f"⚠️  Skipping {video_path.name}: Only {len(frames_landmarks)} valid frames (need {MIN_FRAMES_REQUIRED})")
        return None
    
    # Convert to numpy array
    sequence = np.array(frames_landmarks)  # (T, V, C)
    
    # Normalize first
    sequence = normalize_landmarks(sequence)
    
    # Resample to target length
    sequence = resample_sequence(sequence, target_frames)
    
    results = []
    
    if apply_augmentation:
        # Apply diverse augmentations for training robustness
        augmentation_types = [
            'original',
            'flip',
            'slow',
            'medium_slow', 
            'medium_fast',
            'fast',
            'rotate_small',
            'noise'
        ]
        
        for aug_type in augmentation_types:
            augmented = augment_sequence_improved(sequence, aug_type)
            results.append({
                'sequence': augmented,
                'augmentation': aug_type
            })
    else:
        results.append({
            'sequence': sequence,
            'augmentation': 'original'
        })
    
    return results


def balance_dataset(data_by_class, target_samples_per_class=25):
    """
    IMPROVED: Better dataset balancing strategy.
    
    Args:
        data_by_class: Dict of {class_name: [sequences]}
        target_samples_per_class: Target number of samples per class
    
    Returns:
        Balanced dataset
    """
    balanced_data = []
    
    print("\n📊 Dataset Balancing:")
    print("-" * 70)
    
    for class_name, sequences in data_by_class.items():
        current_count = len(sequences)
        
        print(f"{class_name:15s} | Original: {current_count:3d} | Target: {target_samples_per_class:3d}")
        
        if current_count >= target_samples_per_class:
            # Enough samples, just use target amount
            selected = sequences[:target_samples_per_class]
            balanced_data.extend(selected)
        else:
            # Need augmentation
            balanced_data.extend(sequences)  # Add all originals
            
            needed = target_samples_per_class - current_count
            
            # Augment original sequences
            augmentation_types = ['flip', 'slow', 'medium_slow', 'medium_fast', 'fast', 'rotate_small', 'noise']
            
            aug_idx = 0
            for i in range(needed):
                # Pick sequence to augment (cycle through all)
                seq_idx = i % current_count
                aug_type = augmentation_types[aug_idx % len(augmentation_types)]
                
                augmented = augment_sequence_improved(sequences[seq_idx]['sequence'], aug_type)
                
                balanced_data.append({
                    'sequence': augmented,
                    'label': class_name,
                    'augmentation': f"{aug_type}_generated"
                })
                
                aug_idx += 1
            
            print(f"                | Added {needed} augmented samples")
    
    print("-" * 70)
    print(f"✅ Total balanced samples: {len(balanced_data)}")
    
    return balanced_data


def main():
    """
    Main preprocessing pipeline
    """
    # Get dataset path
    dataset_path = Path('/kaggle/input/custom-sign-dataset')  # Update for Kaggle
    output_path = Path('/kaggle/working/processed_data_improved')
    
    output_path.mkdir(exist_ok=True)
    
    print("🎬 Starting IMPROVED preprocessing...")
    print(f"📁 Dataset path: {dataset_path}")
    print(f"💾 Output path: {output_path}")
    print(f"🎯 Target frames: {SEQUENCE_LENGTH}")
    print(f"🔢 Target samples per class: 320")  # 5x augmentation for journal-quality accuracy (Task 1.1)
    
    # Collect all videos by class
    data_by_class = {}
    
    for class_dir in dataset_path.iterdir():
        if not class_dir.is_dir():
            continue
        
        class_name = class_dir.name
        print(f"\n📂 Processing class: {class_name}")
        
        video_files = list(class_dir.glob('*.mp4')) + list(class_dir.glob('*.avi'))
        print(f"   Found {len(video_files)} videos")
        
        sequences = []
        
        for video_file in tqdm(video_files, desc=f"Processing {class_name}"):
            # Process without augmentation initially
            results = process_video(video_file, apply_augmentation=False)
            
            if results is not None:
                for result in results:
                    sequences.append({
                        'sequence': result['sequence'],
                        'label': class_name,
                        'augmentation': result['augmentation']
                    })
        
        data_by_class[class_name] = sequences
        print(f"   ✅ Extracted {len(sequences)} sequences")
    
    # Balance dataset with improved augmentation
    balanced_data = balance_dataset(data_by_class, target_samples_per_class=320)  # 5x augmentation (Task 1.1)
    
    # Shuffle
    np.random.shuffle(balanced_data)
    
    # Extract features and labels
    X = np.array([item['sequence'] for item in balanced_data])  # (N, T, V, C)
    y = [item['label'] for item in balanced_data]
    
    # Create label mapping
    unique_labels = sorted(set(y))
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    y_encoded = np.array([label_to_idx[label] for label in y])
    
    print(f"\n📊 Final dataset shape: {X.shape}")
    print(f"📊 Number of classes: {len(unique_labels)}")
    print(f"📊 Classes: {unique_labels}")
    
    # Save processed data
    np.save(output_path / 'features.npy', X)
    np.save(output_path / 'labels.npy', y_encoded)
    np.save(output_path / 'label_names.npy', unique_labels)
    
    # Save metadata
    metadata = {
        'num_samples': len(balanced_data),
        'num_classes': len(unique_labels),
        'sequence_length': SEQUENCE_LENGTH,
        'num_nodes': NUM_NODES,
        'num_features': NUM_FEATURES,
        'label_mapping': label_to_idx,
        'classes': unique_labels
    }
    
    with open(output_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Preprocessing complete!")
    print(f"💾 Saved to: {output_path}")
    print(f"📦 Files: features.npy, labels.npy, label_names.npy, metadata.json")


if __name__ == "__main__":
    main()
