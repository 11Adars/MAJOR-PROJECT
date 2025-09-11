#!/usr/bin/env python3
"""
Quick retrain script - automatically includes all available gestures
"""

import os
import cv2
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import mediapipe as mp
import time

def quick_retrain():
    """Quick retraining without user prompts"""
    start_time = time.time()
    
    print("🚀 Quick Custom Gesture Retrainer")
    print("=" * 50)
    
    # Check for available gestures
    gestures_dir = Path("custom_gestures")
    if not gestures_dir.exists():
        print("❌ No custom_gestures directory found!")
        return
    
    available_gestures = [d.name for d in gestures_dir.iterdir() if d.is_dir()]
    if not available_gestures:
        print("❌ No gesture folders found!")
        return
    
    print(f"📁 Found gestures: {available_gestures}")
    print(f"⏱️  Starting training at {time.strftime('%H:%M:%S')}")
    
    # Initialize MediaPipe
    print("🔧 Initializing MediaPipe...")
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        refine_face_landmarks=False
    )
    
    processed_data = []
    labels = []
    gesture_mapping = {}
    
    # Load existing mapping
    mapping_file = Path("custom_gesture_mapping.json")
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            gesture_mapping = json.load(f)
        print(f"📋 Loaded existing mapping: {list(gesture_mapping.keys())}")
    
    # Process each gesture
    total_videos = 0
    processed_videos = 0
    
    for gesture_name in available_gestures:
        gesture_path = Path("custom_gestures") / gesture_name
        video_files = list(gesture_path.glob("*.mp4"))
        total_videos += len(video_files)
        
        print(f"\n🎯 Processing {gesture_name}: {len(video_files)} videos")
        
        for i, video_file in enumerate(video_files):
            print(f"  📹 {i+1}/{len(video_files)}: {video_file.name}", end="")
            
            cap = cv2.VideoCapture(str(video_file))
            landmarks_sequence = []
            
            frame_count = 0
            while frame_count < 35:  # Limit frames
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract landmarks
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(rgb_image)
                
                landmarks = []
                
                # Face (reduced)
                if results.face_landmarks:
                    for landmark in results.face_landmarks.landmark[:10]:
                        landmarks.extend([landmark.x, landmark.y, landmark.z])
                else:
                    landmarks.extend([0] * 30)
                
                # Pose
                if results.pose_landmarks:
                    for landmark in results.pose_landmarks.landmark:
                        landmarks.extend([landmark.x, landmark.y, landmark.z])
                else:
                    landmarks.extend([0] * 99)
                
                # Hands
                for hand_landmarks in [results.left_hand_landmarks, results.right_hand_landmarks]:
                    if hand_landmarks:
                        for landmark in hand_landmarks.landmark:
                            landmarks.extend([landmark.x, landmark.y, landmark.z])
                    else:
                        landmarks.extend([0] * 63)
                
                landmarks_sequence.append(landmarks)
                frame_count += 1
            
            cap.release()
            
            if len(landmarks_sequence) >= 10:  # Minimum frames
                # Extract features
                landmarks_array = np.array(landmarks_sequence)
                features = []
                features.extend(np.mean(landmarks_array, axis=0))
                features.extend(np.std(landmarks_array, axis=0))
                features.extend(np.max(landmarks_array, axis=0))
                features.extend(np.min(landmarks_array, axis=0))
                features.extend(landmarks_array[0])
                features.extend(landmarks_array[-1])
                
                processed_data.append(features)
                labels.append(gesture_name)
                processed_videos += 1
                print(f" ✅ ({len(landmarks_sequence)} frames)")
            else:
                print(f" ❌ (only {len(landmarks_sequence)} frames)")
    
    print(f"\n📊 Processed {processed_videos}/{total_videos} videos")
    
    if processed_videos < 10:
        print("❌ Not enough data for training")
        return
    
    # Update mapping
    unique_gestures = list(set(labels))
    for gesture in unique_gestures:
        if gesture not in gesture_mapping:
            gesture_mapping[gesture] = len(gesture_mapping)
    
    print(f"🏷️  Final gesture mapping: {gesture_mapping}")
    
    # Prepare training data
    X = np.array(processed_data)
    y = [gesture_mapping[label] for label in labels]
    y = np.array(y)
    
    print(f"🔢 Training data: {X.shape}, Labels: {len(np.unique(y))} classes")
    
    # Train
    print("🚀 Training classifier...")
    train_start = time.time()
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=15,
        min_samples_split=3,
        random_state=42,
        class_weight='balanced'
    )
    
    classifier.fit(X_train_scaled, y_train)
    
    train_time = time.time() - train_start
    print(f"⚡ Training completed in {train_time:.1f} seconds")
    
    # Evaluate
    y_pred = classifier.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"📊 Accuracy: {accuracy:.1%}")
    
    # Save everything
    print("💾 Saving models...")
    joblib.dump(classifier, 'custom_gesture_classifier.pkl')
    joblib.dump(scaler, 'custom_gesture_scaler.pkl')
    
    with open("custom_gesture_mapping.json", 'w') as f:
        json.dump(gesture_mapping, f, indent=2)
    
    total_time = time.time() - start_time
    print(f"\n🎉 Complete! Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"✅ Ready to test {len(gesture_mapping)} custom gestures")

if __name__ == "__main__":
    quick_retrain()
