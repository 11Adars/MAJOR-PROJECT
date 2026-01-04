"""
Custom Sign Language Dataset Preprocessing for NS-AGF
=====================================================

This script preprocesses YOUR CUSTOM dataset where videos are organized
by sign folders (no pre-split train/val structure).

Expected Dataset Structure:
    your-dataset/
      ├── sign1/
      │   ├── video1.mp4
      │   ├── video2.mp4
      │   └── video3.mp4
      ├── sign2/
      │   ├── video1.mp4
      │   └── video2.mp4

The script will:
1. Extract 75 MediaPipe landmarks from each video
2. Automatically split into train (80%) and val (20%)
3. Save processed numpy arrays ready for training

Usage in Kaggle:
    %run preprocess_wlasl.py

Output:
    - processed_data/features_train.npy
    - processed_data/labels_train.npy
    - processed_data/features_val.npy
    - processed_data/labels_val.npy
    - processed_data/sign_labels.npy
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from tqdm import tqdm
from pathlib import Path
from sklearn.model_selection import train_test_split


# ==================== CONFIGURATION ====================
# ⚠️ CHANGE THIS TO YOUR DATASET PATH IN KAGGLE
DATASET_PATH = "/kaggle/input/your-custom-dataset"  # ← UPDATE THIS!
OUTPUT_PATH = "/kaggle/working/processed_data/"

# Processing parameters
SEQUENCE_LENGTH = 30  # Number of frames per video
NUM_NODES = 75  # MediaPipe Holistic subgraph
NUM_FEATURES = 3  # x, y, z coordinates

# Train/Val split ratio
TRAIN_RATIO = 0.8
VAL_RATIO = 0.2

# Video formats to search for
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.MP4', '.AVI', '.MOV']


# ==================== MEDIAPIPE SETUP ====================
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=2,
    enable_segmentation=False,
    refine_face_landmarks=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def extract_75_landmarks(results):
    """
    Extract 75 landmarks from MediaPipe Holistic results.
    
    Returns:
        numpy array of shape (75, 3) with x, y, z coordinates
    """
    landmarks = np.zeros((NUM_NODES, NUM_FEATURES), dtype=np.float32)
    
    # Extract pose landmarks (0-32)
    if results.pose_landmarks:
        for i, lm in enumerate(results.pose_landmarks.landmark):
            if i < 33:  # We use all 33 pose landmarks
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


def process_video(video_path, target_frames=SEQUENCE_LENGTH):
    """
    Process a single video file to extract landmarks.
    
    Args:
        video_path: Path to video file
        target_frames: Number of frames to extract (will interpolate/sample)
    
    Returns:
        numpy array of shape (target_frames, 75, 3) or None if processing fails
    """
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        return None
    
    frames_landmarks = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = holistic.process(frame_rgb)
        
        # Extract 75 landmarks
        landmarks = extract_75_landmarks(results)
        frames_landmarks.append(landmarks)
    
    cap.release()
    
    if len(frames_landmarks) == 0:
        return None
    
    # Convert to numpy array
    frames_landmarks = np.array(frames_landmarks)  # (T, 75, 3)
    
    # Handle sequence length adjustment
    current_length = frames_landmarks.shape[0]
    
    if current_length < target_frames:
        # Pad with zeros if too short
        padding = np.zeros((target_frames - current_length, NUM_NODES, NUM_FEATURES))
        frames_landmarks = np.vstack([frames_landmarks, padding])
    elif current_length > target_frames:
        # Sample uniformly if too long
        indices = np.linspace(0, current_length - 1, target_frames, dtype=int)
        frames_landmarks = frames_landmarks[indices]
    
    return frames_landmarks  # (30, 75, 3)


def process_custom_dataset(dataset_root):
    """
    Process custom dataset with automatic train/val split.
    
    Args:
        dataset_root: Path to dataset root (contains sign folders)
    
    Returns:
        X_train, y_train, X_val, y_val, sign_names
    """
    dataset_path = Path(dataset_root)
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_root}")
    
    all_features = []
    all_labels = []
    sign_names = []
    
    # Get all sign folders
    sign_folders = sorted([f for f in dataset_path.iterdir() if f.is_dir()])
    
    if len(sign_folders) == 0:
        raise ValueError(f"No sign folders found in {dataset_root}")
    
    print("=" * 60)
    print(f"🎯 Processing Custom Dataset")
    print("=" * 60)
    print(f"Dataset Root: {dataset_root}")
    print(f"Found {len(sign_folders)} sign classes")
    print(f"Train/Val Split: {TRAIN_RATIO*100:.0f}% / {VAL_RATIO*100:.0f}%\n")
    
    # Preview sign names
    print(f"Sign Classes Preview: {[f.name for f in sign_folders[:5]]}")
    if len(sign_folders) > 5:
        print(f"... and {len(sign_folders) - 5} more\n")
    
    # Process each sign folder
    for sign_idx, sign_folder in enumerate(tqdm(sign_folders, desc="Processing signs")):
        sign_name = sign_folder.name
        sign_names.append(sign_name)
        
        # Get all video files (support multiple formats)
        video_files = []
        for ext in VIDEO_EXTENSIONS:
            video_files.extend(list(sign_folder.glob(f"*{ext}")))
        
        if len(video_files) == 0:
            print(f"\n⚠️  Warning: No videos found in {sign_folder.name}, skipping...")
            continue
        
        print(f"\n📁 {sign_name}: Processing {len(video_files)} videos")
        
        successful = 0
        failed = 0
        
        # Process all videos in this sign folder
        for video_path in tqdm(video_files, desc=f"  Extracting landmarks", leave=False):
            sequence = process_video(video_path)
            
            if sequence is not None:
                all_features.append(sequence)
                all_labels.append(sign_idx)
                successful += 1
            else:
                failed += 1
        
        print(f"   ✅ Success: {successful} | ❌ Failed: {failed}")
    
    # Convert to numpy arrays
    all_features = np.array(all_features, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=np.int64)
    
    print("\n" + "=" * 60)
    print(f"📊 TOTAL Dataset Statistics")
    print("=" * 60)
    print(f"Total samples: {len(all_features)}")
    print(f"Feature shape: {all_features.shape}")
    print(f"Classes: {len(sign_names)}")
    
    # Create train/val split using stratification (ensures balanced classes)
    print(f"\n🔀 Splitting dataset...")
    X_train, X_val, y_train, y_val = train_test_split(
        all_features, 
        all_labels, 
        test_size=VAL_RATIO,
        train_size=TRAIN_RATIO,
        stratify=all_labels,
        random_state=42
    )
    
    print(f"\n" + "=" * 60)
    print(f"✅ TRAIN Set")
    print("=" * 60)
    print(f"Samples: {len(X_train)}")
    print(f"Shape: {X_train.shape}")
    
    print(f"\n" + "=" * 60)
    print(f"✅ VALIDATION Set")
    print("=" * 60)
    print(f"Samples: {len(X_val)}")
    print(f"Shape: {X_val.shape}")
    
    # Print class distribution
    print(f"\n" + "=" * 60)
    print(f"📈 Class Distribution (Training)")
    print("=" * 60)
    unique, counts = np.unique(y_train, return_counts=True)
    for idx, (cls, count) in enumerate(zip(unique, counts)):
        if idx < 5:  # Show first 5 classes
            print(f"  {sign_names[cls]}: {count} samples")
        elif idx == 5:
            print(f"  ... ({len(sign_names) - 5} more classes)")
            break
    
    return X_train, y_train, X_val, y_val, sign_names
    



def main():
    """Main preprocessing pipeline"""
    print("\n" + "=" * 60)
    print("🚀 NS-AGF Custom Dataset Preprocessing")
    print("=" * 60)
    print(f"Dataset: {DATASET_PATH}")
    print(f"Output: {OUTPUT_PATH}\n")
    
    # Create output directory
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Process custom dataset with automatic train/val split
    try:
        X_train, y_train, X_val, y_val, sign_names = process_custom_dataset(DATASET_PATH)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"\n⚠️  Please check your dataset structure:")
        print(f"Expected:")
        print(f"{DATASET_PATH}/")
        print(f"  ├── sign1/")
        print(f"  │   ├── video1.mp4")
        print(f"  │   └── video2.mp4")
        print(f"  ├── sign2/")
        print(f"  │   ├── video1.mp4")
        print(f"  │   └── video2.mp4")
        return
    
    # Save processed data
    print(f"\n" + "=" * 60)
    print(f"💾 Saving processed data...")
    print("=" * 60)
    
    np.save(os.path.join(OUTPUT_PATH, "features_train.npy"), X_train)
    np.save(os.path.join(OUTPUT_PATH, "labels_train.npy"), y_train)
    np.save(os.path.join(OUTPUT_PATH, "features_val.npy"), X_val)
    np.save(os.path.join(OUTPUT_PATH, "labels_val.npy"), y_val)
    np.save(os.path.join(OUTPUT_PATH, "sign_labels.npy"), np.array(sign_names))
    
    print(f"✅ Saved to: {OUTPUT_PATH}")
    print(f"  - features_train.npy ({X_train.nbytes / 1024 / 1024:.2f} MB)")
    print(f"  - labels_train.npy")
    print(f"  - features_val.npy ({X_val.nbytes / 1024 / 1024:.2f} MB)")
    print(f"  - labels_val.npy")
    print(f"  - sign_labels.npy")
    
    print("\n" + "=" * 60)
    print("✨ Preprocessing Complete!")
    print("=" * 60)
    print(f"\n📦 Dataset Summary:")
    print(f"  Total Classes: {len(sign_names)}")
    print(f"  Training Samples: {len(X_train)}")
    print(f"  Validation Samples: {len(X_val)}")
    print(f"  Feature Shape: {X_train.shape}")
    print(f"\n🎯 Next Step: Run train_agcn.py to train the model")
    
    # Cleanup
    holistic.close()


if __name__ == "__main__":
    main()
