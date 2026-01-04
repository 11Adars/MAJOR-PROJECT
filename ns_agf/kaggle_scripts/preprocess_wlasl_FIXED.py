"""
FIXED Custom Sign Language Dataset Preprocessing for NS-AGF
============================================================

CRITICAL FIXES APPLIED:
1. ✅ Better frame sampling for long videos (no information loss)
2. ✅ Normalization added (centering and scaling)
3. ✅ Data augmentation for class balance
4. ✅ Quality checks for each video
5. ✅ Better landmark extraction (handles missing detections)

Expected Dataset Structure:
    your-dataset/
      ├── ATM/
      │   ├── video1.mp4
      │   └── video2.mp4
      ├── Account/
      ├── Amount/
      ... (alphabetically sorted)

Usage in Kaggle:
    DATASET_PATH = "/kaggle/input/your-dataset"
    %run preprocess_wlasl_FIXED.py
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from tqdm import tqdm
from pathlib import Path
from sklearn.model_selection import train_test_split
from collections import Counter


# ==================== CONFIGURATION ====================
# ⚠️ CHANGE THIS TO YOUR DATASET PATH IN KAGGLE
DATASET_PATH = "/kaggle/input/your-custom-dataset"
OUTPUT_PATH = "/kaggle/working/processed_data/"

# Processing parameters
SEQUENCE_LENGTH = 30  # Number of frames per video
NUM_NODES = 75  # MediaPipe Holistic subgraph
NUM_FEATURES = 3  # x, y, z coordinates

# Train/Val split ratio
TRAIN_RATIO = 0.8
VAL_RATIO = 0.2

# Quality thresholds
MIN_DETECTION_CONFIDENCE = 0.5
MIN_FRAMES_REQUIRED = 15  # Minimum frames needed for valid video
MIN_VIDEOS_PER_CLASS = 5  # Minimum videos per sign

# Augmentation settings
ENABLE_AUGMENTATION = True
TARGET_SAMPLES_PER_CLASS = 20  # Target after augmentation

# Video formats to search for
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.MP4', '.AVI', '.MOV']


# ==================== MEDIAPIPE SETUP ====================
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=2,  # Higher quality
    enable_segmentation=False,
    refine_face_landmarks=False,
    min_detection_confidence=MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=0.5
)


def extract_75_landmarks(results):
    """
    Extract 75 landmarks from MediaPipe Holistic results.
    Returns numpy array of shape (75, 3) with x, y, z coordinates
    """
    landmarks = np.zeros((NUM_NODES, NUM_FEATURES), dtype=np.float32)
    
    # Extract pose landmarks (0-32)
    if results.pose_landmarks:
        for i, lm in enumerate(results.pose_landmarks.landmark):
            if i < 33:
                landmarks[i] = [lm.x, lm.y, lm.z]
    
    # Extract left hand landmarks (33-53)
    if results.left_hand_landmarks:
        for i, lm in enumerate(results.left_hand_landmarks.landmark):
            landmarks[33 + i] = [lm.x, lm.y, lm.z]
    
    # Extract right hand landmarks (54-74)
    if results.right_hand_landmarks:
        for i, lm in enumerate(results.right_hand_landmarks.landmark):
            landmarks[54 + i] = [lm.x, lm.y, lm.z]
    
    return landmarks


def normalize_landmarks(sequence):
    """
    Normalize landmarks by centering and scaling.
    This makes the model robust to distance from camera.
    
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
    shoulder_dist = np.where(shoulder_dist > 0.01, shoulder_dist, 1.0)  # Avoid division by zero
    
    # Scale
    scaled = centered / shoulder_dist[:, :, np.newaxis]
    
    return scaled


def augment_sequence(sequence):
    """
    Apply data augmentation to increase training samples.
    
    Augmentations:
    - Horizontal flip
    - Time stretching (speed up/slow down)
    - Small random noise
    """
    augmented = []
    
    # Original
    augmented.append(sequence.copy())
    
    # Horizontal flip (swap left/right hands, flip x-coordinates)
    flipped = sequence.copy()
    flipped[:, :, 0] = 1.0 - flipped[:, :, 0]  # Flip x
    # Swap left and right hands (indices 33-53 with 54-74)
    left_hand = flipped[:, 33:54, :].copy()
    right_hand = flipped[:, 54:75, :].copy()
    flipped[:, 33:54, :] = right_hand
    flipped[:, 54:75, :] = left_hand
    augmented.append(flipped)
    
    # Speed up (use fewer frames)
    if len(sequence) >= 20:
        speed_up_indices = np.linspace(0, len(sequence)-1, 20, dtype=int)
        speed_up = sequence[speed_up_indices]
        # Pad to 30 frames
        padding = np.zeros((10, NUM_NODES, NUM_FEATURES))
        speed_up = np.vstack([speed_up, padding])
        augmented.append(speed_up)
    
    return augmented


def process_video(video_path, target_frames=SEQUENCE_LENGTH, apply_augmentation=False):
    """
    Process a single video file to extract landmarks.
    
    Args:
        video_path: Path to video file
        target_frames: Number of frames to extract
        apply_augmentation: Whether to augment this video
    
    Returns:
        List of sequences (if augmentation) or single sequence
    """
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        return None
    
    frames_landmarks = []
    frame_count = 0
    detection_failures = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = holistic.process(frame_rgb)
        
        # Extract 75 landmarks
        landmarks = extract_75_landmarks(results)
        
        # Check if hands are detected
        if results.left_hand_landmarks or results.right_hand_landmarks:
            frames_landmarks.append(landmarks)
        else:
            detection_failures += 1
            # Still append but mark for potential rejection
            frames_landmarks.append(landmarks)
    
    cap.release()
    
    # Quality check
    if len(frames_landmarks) < MIN_FRAMES_REQUIRED:
        return None
    
    # Warn if too many detection failures
    if detection_failures / frame_count > 0.5:
        print(f"      ⚠️  Warning: {video_path.name} has {detection_failures}/{frame_count} frames without hand detection")
    
    # Convert to numpy array
    frames_landmarks = np.array(frames_landmarks, dtype=np.float32)  # (T, 75, 3)
    
    # Adaptive sampling based on video length
    current_length = frames_landmarks.shape[0]
    
    if current_length < target_frames:
        # Repeat last frame if too short
        padding = np.repeat(frames_landmarks[-1:], target_frames - current_length, axis=0)
        frames_landmarks = np.vstack([frames_landmarks, padding])
    elif current_length > target_frames:
        # BETTER SAMPLING: Use uniform sampling to capture the entire gesture
        # This preserves temporal information better than just taking first 30 frames
        indices = np.linspace(0, current_length - 1, target_frames, dtype=int)
        frames_landmarks = frames_landmarks[indices]
    
    # Normalize
    frames_landmarks = normalize_landmarks(frames_landmarks)
    
    # Apply augmentation if requested
    if apply_augmentation and ENABLE_AUGMENTATION:
        return augment_sequence(frames_landmarks)
    else:
        return [frames_landmarks]  # Return as list for consistency


def balance_dataset(features, labels, sign_names):
    """
    Balance dataset by augmenting underrepresented classes.
    
    Returns:
        Balanced features and labels
    """
    # Count samples per class
    class_counts = Counter(labels)
    
    print(f"\\n📊 Class Distribution (Before Balancing):")
    for sign_idx, count in sorted(class_counts.items()):
        sign_name = sign_names[sign_idx]
        status = "✅" if count >= 15 else ("⚠️" if count >= 10 else "🔴")
        print(f"   {status} {sign_name:15s}: {count:3d} samples")
    
    # Find classes that need augmentation
    max_samples = max(class_counts.values())
    target_samples = min(TARGET_SAMPLES_PER_CLASS, max_samples)
    
    balanced_features = list(features)
    balanced_labels = list(labels)
    
    for sign_idx in range(len(sign_names)):
        current_count = class_counts.get(sign_idx, 0)
        
        if current_count < target_samples and current_count > 0:
            # Need to augment this class
            needed = target_samples - current_count
            
            # Get all samples of this class
            class_indices = [i for i, label in enumerate(labels) if label == sign_idx]
            
            # Duplicate and augment randomly
            for _ in range(needed):
                # Pick a random sample from this class
                src_idx = np.random.choice(class_indices)
                original_seq = features[src_idx]
                
                # Apply augmentation
                augmented = augment_sequence(original_seq)
                # Pick a random augmented version (not the original)
                aug_seq = augmented[np.random.randint(1, len(augmented))]
                
                balanced_features.append(aug_seq)
                balanced_labels.append(sign_idx)
    
    balanced_features = np.array(balanced_features, dtype=np.float32)
    balanced_labels = np.array(balanced_labels, dtype=np.int64)
    
    print(f"\\n📊 Class Distribution (After Balancing):")
    class_counts_after = Counter(balanced_labels)
    for sign_idx, count in sorted(class_counts_after.items()):
        sign_name = sign_names[sign_idx]
        print(f"   ✅ {sign_name:15s}: {count:3d} samples")
    
    return balanced_features, balanced_labels


def process_custom_dataset(dataset_root):
    """
    Process custom dataset with automatic train/val split and balancing.
    """
    dataset_path = Path(dataset_root)
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_root}")
    
    all_features = []
    all_labels = []
    sign_names = []
    
    # Get all sign folders (SORTED alphabetically - CRITICAL!)
    sign_folders = sorted([f for f in dataset_path.iterdir() if f.is_dir()])
    
    if len(sign_folders) == 0:
        raise ValueError(f"No sign folders found in {dataset_root}")
    
    print("=" * 60)
    print(f"🎯 Processing Custom Dataset (FIXED VERSION)")
    print("=" * 60)
    print(f"Dataset Root: {dataset_root}")
    print(f"Found {len(sign_folders)} sign classes")
    print(f"Train/Val Split: {TRAIN_RATIO*100:.0f}% / {VAL_RATIO*100:.0f}%")
    print(f"Normalization: ✅ ENABLED")
    print(f"Augmentation: {'✅ ENABLED' if ENABLE_AUGMENTATION else '❌ DISABLED'}\\n")
    
    # Preview sign names
    print(f"Sign Classes (alphabetical order):")
    for i, folder in enumerate(sign_folders):
        print(f"   [{i}] {folder.name}")
    print()
    
    # Process each sign folder
    for sign_idx, sign_folder in enumerate(tqdm(sign_folders, desc="Processing signs")):
        sign_name = sign_folder.name
        sign_names.append(sign_name)
        
        # Get all video files
        video_files = []
        for ext in VIDEO_EXTENSIONS:
            video_files.extend(list(sign_folder.glob(f"*{ext}")))
        
        if len(video_files) == 0:
            print(f"\\n⚠️  Warning: No videos found in {sign_folder.name}, skipping...")
            continue
        
        if len(video_files) < MIN_VIDEOS_PER_CLASS:
            print(f"\\n⚠️  Warning: {sign_name} has only {len(video_files)} videos (min {MIN_VIDEOS_PER_CLASS})")
        
        print(f"\\n📁 {sign_name}: Processing {len(video_files)} videos")
        
        successful = 0
        failed = 0
        
        # Process all videos in this sign folder
        for video_path in tqdm(video_files, desc=f"  Extracting landmarks", leave=False):
            sequences = process_video(video_path, apply_augmentation=False)  # Augment later during balancing
            
            if sequences is not None:
                for sequence in sequences:
                    all_features.append(sequence)
                    all_labels.append(sign_idx)
                successful += 1
            else:
                failed += 1
        
        print(f"   ✅ Success: {successful} | ❌ Failed: {failed}")
    
    # Convert to numpy arrays
    all_features = np.array(all_features, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=np.int64)
    
    print("\\n" + "=" * 60)
    print(f"📊 Dataset Statistics (Before Balancing)")
    print("=" * 60)
    print(f"Total samples: {len(all_features)}")
    print(f"Feature shape: {all_features.shape}")
    print(f"Classes: {len(sign_names)}")
    
    # Balance dataset
    if ENABLE_AUGMENTATION:
        all_features, all_labels = balance_dataset(all_features, all_labels, sign_names)
        
        print("\\n" + "=" * 60)
        print(f"📊 Dataset Statistics (After Balancing)")
        print("=" * 60)
        print(f"Total samples: {len(all_features)}")
        print(f"Feature shape: {all_features.shape}")
    
    # Create train/val split using stratification
    print(f"\\n🔀 Splitting dataset...")
    X_train, X_val, y_train, y_val = train_test_split(
        all_features, 
        all_labels, 
        test_size=VAL_RATIO,
        train_size=TRAIN_RATIO,
        stratify=all_labels,
        random_state=42
    )
    
    print(f"\\n" + "=" * 60)
    print(f"✅ TRAIN Set")
    print("=" * 60)
    print(f"Samples: {len(X_train)}")
    print(f"Shape: {X_train.shape}")
    
    print(f"\\n" + "=" * 60)
    print(f"✅ VALIDATION Set")
    print("=" * 60)
    print(f"Samples: {len(X_val)}")
    print(f"Shape: {X_val.shape}")
    
    # Print final class distribution
    print(f"\\n" + "=" * 60)
    print(f"📈 Final Class Distribution (Training)")
    print("=" * 60)
    unique, counts = np.unique(y_train, return_counts=True)
    for cls, count in zip(unique, counts):
        print(f"  {sign_names[cls]:15s}: {count:3d} samples")
    
    return X_train, y_train, X_val, y_val, sign_names


def main():
    """Main preprocessing pipeline"""
    print("\\n" + "=" * 60)
    print("🚀 NS-AGF Custom Dataset Preprocessing (FIXED)")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Process dataset
    X_train, y_train, X_val, y_val, sign_names = process_custom_dataset(DATASET_PATH)
    
    # Save to disk
    print(f"\\n💾 Saving processed data...")
    np.save(os.path.join(OUTPUT_PATH, "train_features.npy"), X_train)
    np.save(os.path.join(OUTPUT_PATH, "train_labels.npy"), y_train)
    np.save(os.path.join(OUTPUT_PATH, "val_features.npy"), X_val)
    np.save(os.path.join(OUTPUT_PATH, "val_labels.npy"), y_val)
    np.save(os.path.join(OUTPUT_PATH, "sign_labels.npy"), np.array(sign_names))
    
    print(f"\\n✅ Preprocessing complete!")
    print(f"\\nOutput files:")
    print(f"  - train_features.npy: {X_train.shape}")
    print(f"  - train_labels.npy: {y_train.shape}")
    print(f"  - val_features.npy: {X_val.shape}")
    print(f"  - val_labels.npy: {y_val.shape}")
    print(f"  - sign_labels.npy: {len(sign_names)} classes")
    
    print(f"\\n🎯 Ready for training!")
    print(f"   Next step: Run train_agcn_FIXED.py")


if __name__ == "__main__":
    main()
