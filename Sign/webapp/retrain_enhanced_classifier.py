#!/usr/bin/env python3
"""
Updated script to retrain custom gesture classifier with new gesture
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

class EnhancedGestureRetrainer:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            refine_face_landmarks=False
        )
        
        self.processed_data = []
        self.labels = []
        
        # Load existing gesture mapping
        self.load_existing_mapping()
    
    def load_existing_mapping(self):
        """Load existing gesture mapping if it exists"""
        mapping_file = Path("custom_gesture_mapping.json")
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                self.gesture_mapping = json.load(f)
            print(f"📋 Loaded existing gestures: {list(self.gesture_mapping.keys())}")
        else:
            self.gesture_mapping = {}
            print("📋 Starting with new gesture mapping")
    
    def extract_landmarks(self, image):
        """Extract MediaPipe landmarks from image"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(rgb_image)
        
        landmarks = []
        
        # Face landmarks (first 10 for efficiency)
        if results.face_landmarks:
            for i, landmark in enumerate(results.face_landmarks.landmark[:10]):
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0] * 30)  # 10 landmarks * 3 coordinates
        
        # Pose landmarks
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0] * 99)  # 33 landmarks * 3 coordinates
        
        # Left hand landmarks
        if results.left_hand_landmarks:
            for landmark in results.left_hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0] * 63)  # 21 landmarks * 3 coordinates
        
        # Right hand landmarks
        if results.right_hand_landmarks:
            for landmark in results.right_hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0] * 63)  # 21 landmarks * 3 coordinates
        
        return landmarks
    
    def extract_features_from_landmarks(self, landmarks_sequence):
        """Extract statistical features from landmark sequence"""
        if len(landmarks_sequence) == 0:
            return np.zeros(1020)  # Return zero features if no landmarks
        
        landmarks_array = np.array(landmarks_sequence)
        
        # Statistical features
        features = []
        features.extend(np.mean(landmarks_array, axis=0))      # Mean
        features.extend(np.std(landmarks_array, axis=0))       # Standard deviation
        features.extend(np.max(landmarks_array, axis=0))       # Maximum
        features.extend(np.min(landmarks_array, axis=0))       # Minimum
        
        # Add first and last frame features
        features.extend(landmarks_array[0])                    # First frame
        features.extend(landmarks_array[-1])                   # Last frame
        
        return np.array(features)
    
    def process_video(self, video_path, gesture_name):
        """Process a single video and extract features"""
        cap = cv2.VideoCapture(str(video_path))
        landmarks_sequence = []
        
        print(f"  📹 Processing: {video_path.name}")
        
        frame_count = 0
        while cap.read()[0] and frame_count < 35:  # Limit to 35 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            landmarks = self.extract_landmarks(frame)
            if landmarks:
                landmarks_sequence.append(landmarks)
            frame_count += 1
        
        cap.release()
        
        if len(landmarks_sequence) < 10:  # Need minimum frames
            print(f"    ⚠️  Skipping {video_path.name}: Only {len(landmarks_sequence)} frames")
            return False
        
        # Extract features from the sequence
        features = self.extract_features_from_landmarks(landmarks_sequence)
        
        # Add to processed data
        self.processed_data.append(features)
        self.labels.append(gesture_name)
        
        print(f"    ✅ Extracted {len(landmarks_sequence)} frames, {len(features)} features")
        return True
    
    def load_existing_data(self):
        """Load existing processed data if available"""
        data_file = Path("processed_data/custom_gesture_data.pkl")
        if data_file.exists():
            print("📂 Loading existing training data...")
            try:
                with open(data_file, 'rb') as f:
                    existing_data = joblib.load(f)
                
                self.processed_data.extend(existing_data['features'])
                self.labels.extend(existing_data['labels'])
                
                print(f"✅ Loaded {len(existing_data['features'])} existing samples")
                return True
            except Exception as e:
                print(f"⚠️  Could not load existing data: {e}")
        
        return False
    
    def process_gesture_folder(self, gesture_name):
        """Process all videos for a specific gesture"""
        gesture_path = Path("custom_gestures") / gesture_name
        
        if not gesture_path.exists():
            print(f"❌ Gesture folder not found: {gesture_path}")
            return 0
        
        video_files = list(gesture_path.glob("*.mp4"))
        if not video_files:
            print(f"❌ No video files found in: {gesture_path}")
            return 0
        
        print(f"🎯 Processing gesture: {gesture_name}")
        print(f"📁 Found {len(video_files)} videos")
        
        processed_count = 0
        for video_file in video_files:
            if self.process_video(video_file, gesture_name):
                processed_count += 1
        
        print(f"✅ Processed {processed_count}/{len(video_files)} videos for '{gesture_name}'")
        return processed_count
    
    def update_gesture_mapping(self):
        """Update gesture to ID mapping"""
        unique_gestures = list(set(self.labels))
        
        # Add new gestures to mapping
        for gesture in unique_gestures:
            if gesture not in self.gesture_mapping:
                new_id = len(self.gesture_mapping)
                self.gesture_mapping[gesture] = new_id
                print(f"➕ Added new gesture: {gesture} -> ID {new_id}")
        
        # Save updated mapping
        with open("custom_gesture_mapping.json", 'w') as f:
            json.dump(self.gesture_mapping, f, indent=2)
        
        print(f"💾 Updated gesture mapping: {self.gesture_mapping}")
    
    def train_classifier(self):
        """Train the custom gesture classifier"""
        if len(self.processed_data) < 10:
            print("❌ Not enough training data. Need at least 10 samples.")
            return False
        
        # Convert to numpy arrays
        X = np.array(self.processed_data)
        
        # Convert labels to IDs
        y = [self.gesture_mapping[label] for label in self.labels]
        y = np.array(y)
        
        print(f"🔢 Training data shape: {X.shape}")
        print(f"🏷️  Labels distribution:")
        unique, counts = np.unique(y, return_counts=True)
        for gesture_id, count in zip(unique, counts):
            gesture_name = [k for k, v in self.gesture_mapping.items() if v == gesture_id][0]
            print(f"   {gesture_name}: {count} samples")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train classifier with optimized parameters
        classifier = RandomForestClassifier(
            n_estimators=150,
            max_depth=15,
            min_samples_split=3,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        print("🚀 Training Random Forest classifier...")
        classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n📊 Training Results:")
        print(f"✅ Accuracy: {accuracy:.1%}")
        
        # Detailed classification report
        gesture_names = [k for k, v in sorted(self.gesture_mapping.items(), key=lambda x: x[1])]
        print(f"\n📋 Detailed Results:")
        print(classification_report(y_test, y_pred, target_names=gesture_names))
        
        # Save models
        joblib.dump(classifier, 'custom_gesture_classifier.pkl')
        joblib.dump(scaler, 'custom_gesture_scaler.pkl')
        
        # Save processed data for future use
        processed_data_dir = Path("processed_data")
        processed_data_dir.mkdir(exist_ok=True)
        
        training_data = {
            'features': self.processed_data,
            'labels': self.labels,
            'gesture_mapping': self.gesture_mapping
        }
        
        with open(processed_data_dir / "custom_gesture_data.pkl", 'wb') as f:
            joblib.dump(training_data, f)
        
        print(f"\n💾 Saved files:")
        print(f"  • custom_gesture_classifier.pkl")
        print(f"  • custom_gesture_scaler.pkl")
        print(f"  • custom_gesture_mapping.json")
        print(f"  • processed_data/custom_gesture_data.pkl")
        
        return True

def main():
    print("🎯 Enhanced Custom Gesture Retrainer")
    print("=" * 50)
    
    trainer = EnhancedGestureRetrainer()
    
    # Check for available gestures
    gestures_dir = Path("custom_gestures")
    if not gestures_dir.exists():
        print("❌ No custom_gestures directory found!")
        print("Run train_new_gesture.py first to record gesture data.")
        return
    
    available_gestures = [d.name for d in gestures_dir.iterdir() if d.is_dir()]
    
    if not available_gestures:
        print("❌ No gesture folders found!")
        print("Run train_new_gesture.py first to record gesture data.")
        return
    
    print(f"📁 Available gestures: {available_gestures}")
    
    # Load existing data
    trainer.load_existing_data()
    
    # Ask which gestures to include
    print(f"\n🎯 Select gestures to include in training:")
    gestures_to_train = []
    
    for gesture in available_gestures:
        include = input(f"Include '{gesture}'? (y/n): ").lower().strip()
        if include in ['y', 'yes', '']:
            gestures_to_train.append(gesture)
    
    if not gestures_to_train:
        print("❌ No gestures selected for training.")
        return
    
    print(f"\n🎯 Training gestures: {gestures_to_train}")
    
    # Process each selected gesture
    total_processed = 0
    for gesture in gestures_to_train:
        count = trainer.process_gesture_folder(gesture)
        total_processed += count
    
    if total_processed == 0:
        print("❌ No videos processed successfully.")
        return
    
    print(f"\n📊 Total processed videos: {total_processed}")
    
    # Update gesture mapping
    trainer.update_gesture_mapping()
    
    # Train classifier
    success = trainer.train_classifier()
    
    if success:
        print(f"\n🎉 Training completed successfully!")
        print(f"✅ Custom gesture classifier updated with {len(trainer.gesture_mapping)} gestures")
        print(f"\n🔄 Restart the server to use the updated classifier.")
    else:
        print(f"\n❌ Training failed!")

if __name__ == "__main__":
    main()
