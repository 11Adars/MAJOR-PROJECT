#!/usr/bin/env python3
"""
LSTM-based Custom Gesture Trainer
Processes video files and trains an LSTM model for custom gesture recognition
"""

import os
import cv2
import json
import numpy as np
import pandas as pd
from pathlib import Path
import mediapipe as mp
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class LSTMGestureTrainer:
    def __init__(self, custom_videos_folder="custom_videos"):
        self.custom_videos_folder = Path(custom_videos_folder)
        self.sequence_length = 30  # Number of frames per sequence
        self.feature_dim = 258  # MediaPipe landmarks dimension (reduced)
        
        # Initialize MediaPipe
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=0,  # Faster processing
            enable_segmentation=False,
            refine_face_landmarks=False
        )
        
        self.sequences = []
        self.labels = []
        self.label_encoder = LabelEncoder()
        
    def extract_landmarks(self, frame):
        """Extract key landmarks from frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(rgb_frame)
        
        landmarks = []
        
        # Face landmarks (key points only - 10 points)
        if results.face_landmarks:
            face_key_points = [0, 10, 152, 234, 454, 267, 269, 270, 271, 272]
            for idx in face_key_points:
                if idx < len(results.face_landmarks.landmark):
                    lm = results.face_landmarks.landmark[idx]
                    landmarks.extend([lm.x, lm.y, lm.z])
                else:
                    landmarks.extend([0, 0, 0])
        else:
            landmarks.extend([0] * 30)  # 10 points * 3 coords
        
        # Pose landmarks (33 points)
        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([0] * 99)  # 33 points * 3 coords
        
        # Left hand landmarks (21 points)
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([0] * 63)  # 21 points * 3 coords
        
        # Right hand landmarks (21 points)
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([0] * 63)  # 21 points * 3 coords
        
        # Add motion features (velocity approximation)
        if len(landmarks) == 255:  # 85 points * 3 coords
            landmarks.extend([0, 0, 0])  # Placeholder for velocity features
        
        return np.array(landmarks[:self.feature_dim])
    
    def augment_sequence(self, sequence):
        """Apply data augmentation to sequence"""
        augmented_sequences = [sequence]  # Original
        
        # Time scaling (speed up/slow down)
        if len(sequence) > 15:
            # Speed up (skip frames)
            speed_up = sequence[::2][:self.sequence_length]
            if len(speed_up) == self.sequence_length:
                augmented_sequences.append(speed_up)
        
        # Add noise
        noise_factor = 0.02
        noisy_sequence = sequence + np.random.normal(0, noise_factor, sequence.shape)
        augmented_sequences.append(noisy_sequence)
        
        # Horizontal flip (flip x coordinates)
        flipped_sequence = sequence.copy()
        # Flip x coordinates (every 3rd element starting from 0)
        flipped_sequence[:, ::3] = 1 - flipped_sequence[:, ::3]
        augmented_sequences.append(flipped_sequence)
        
        return augmented_sequences
    
    def process_video(self, video_path, gesture_label):
        """Process single video and extract sequence"""
        cap = cv2.VideoCapture(str(video_path))
        frames_landmarks = []
        
        print(f"  📹 Processing: {video_path.name}")
        
        while cap.read()[0]:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize frame for faster processing
            frame = cv2.resize(frame, (640, 480))
            landmarks = self.extract_landmarks(frame)
            frames_landmarks.append(landmarks)
            
            if len(frames_landmarks) >= self.sequence_length * 2:  # Get enough frames
                break
        
        cap.release()
        
        if len(frames_landmarks) < 15:
            print(f"    ⚠️ Skipping {video_path.name}: Only {len(frames_landmarks)} frames")
            return 0
        
        # Create sequences of fixed length
        sequences_from_video = []
        
        if len(frames_landmarks) >= self.sequence_length:
            # Extract multiple overlapping sequences from one video
            step = max(1, len(frames_landmarks) // 4)  # Get 4 sequences per video
            for start_idx in range(0, len(frames_landmarks) - self.sequence_length + 1, step):
                sequence = np.array(frames_landmarks[start_idx:start_idx + self.sequence_length])
                sequences_from_video.append(sequence)
        else:
            # Pad short sequences
            sequence = np.array(frames_landmarks)
            padding_needed = self.sequence_length - len(sequence)
            # Repeat last frame for padding
            last_frame = sequence[-1:] if len(sequence) > 0 else np.zeros((1, self.feature_dim))
            padding = np.repeat(last_frame, padding_needed, axis=0)
            sequence = np.vstack([sequence, padding])
            sequences_from_video.append(sequence)
        
        # Apply augmentation
        augmented_count = 0
        for seq in sequences_from_video:
            augmented_seqs = self.augment_sequence(seq)
            for aug_seq in augmented_seqs:
                self.sequences.append(aug_seq)
                self.labels.append(gesture_label)
                augmented_count += 1
        
        print(f"    ✅ Generated {augmented_count} sequences from {len(frames_landmarks)} frames")
        return augmented_count
    
    def load_custom_videos(self):
        """Load all custom gesture videos"""
        if not self.custom_videos_folder.exists():
            print(f"❌ Custom videos folder not found: {self.custom_videos_folder}")
            print("Create the folder and add gesture videos organized by gesture name")
            return False
        
        gesture_folders = [d for d in self.custom_videos_folder.iterdir() if d.is_dir()]
        
        if not gesture_folders:
            print("❌ No gesture folders found in custom_videos")
            print("Organize videos like: custom_videos/welcome/video1.mp4")
            return False
        
        print(f"🎯 Found {len(gesture_folders)} gesture types:")
        
        total_sequences = 0
        for gesture_folder in gesture_folders:
            gesture_name = gesture_folder.name
            video_files = list(gesture_folder.glob("*.mp4")) + list(gesture_folder.glob("*.avi"))
            
            if not video_files:
                print(f"  ⚠️ No videos in {gesture_name}")
                continue
            
            print(f"\n📁 Processing gesture: {gesture_name} ({len(video_files)} videos)")
            
            gesture_sequences = 0
            for video_file in video_files:
                sequences_added = self.process_video(video_file, gesture_name)
                gesture_sequences += sequences_added
            
            print(f"  ✅ Total sequences for {gesture_name}: {gesture_sequences}")
            total_sequences += gesture_sequences
        
        print(f"\n📊 Total sequences loaded: {total_sequences}")
        return total_sequences > 0
    
    def build_lstm_model(self, num_classes):
        """Build LSTM model for gesture classification"""
        model = keras.Sequential([
            keras.layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            # Normalization
            keras.layers.BatchNormalization(),
            
            # LSTM layers with dropout
            keras.layers.LSTM(128, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            keras.layers.LSTM(64, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            keras.layers.LSTM(32, dropout=0.3, recurrent_dropout=0.3),
            
            # Dense layers
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self):
        """Train the LSTM model"""
        if len(self.sequences) < 10:
            print("❌ Not enough sequences. Need at least 10 sequences.")
            return False
        
        # Convert to numpy arrays
        X = np.array(self.sequences)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(self.labels)
        y_categorical = keras.utils.to_categorical(y_encoded)
        
        print(f"\n🔢 Training data shape: {X.shape}")
        print(f"🏷️ Number of classes: {len(self.label_encoder.classes_)}")
        print(f"📋 Classes: {list(self.label_encoder.classes_)}")
        
        # Check class distribution
        unique, counts = np.unique(y_encoded, return_counts=True)
        for class_idx, count in zip(unique, counts):
            class_name = self.label_encoder.classes_[class_idx]
            print(f"   {class_name}: {count} sequences")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_categorical, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Build model
        num_classes = len(self.label_encoder.classes_)
        model = self.build_lstm_model(num_classes)
        
        print(f"\n🏗️ Model architecture:")
        model.summary()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5),
            keras.callbacks.ModelCheckpoint('best_custom_model.h5', save_best_only=True)
        ]
        
        # Train model
        print(f"\n🚀 Training model...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
        print(f"\n📊 Final Results:")
        print(f"✅ Test Accuracy: {test_accuracy:.1%}")
        print(f"📉 Test Loss: {test_loss:.4f}")
        
        # Save model and label encoder
        model.save('custom_gesture_lstm.h5')
        
        # Save label encoder
        import joblib
        joblib.dump(self.label_encoder, 'custom_gesture_labels.pkl')
        
        # Save gesture mapping
        gesture_mapping = {gesture: idx for idx, gesture in enumerate(self.label_encoder.classes_)}
        with open('custom_gesture_mapping.json', 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        
        print(f"\n💾 Saved files:")
        print(f"  • custom_gesture_lstm.h5 (LSTM model)")
        print(f"  • custom_gesture_labels.pkl (label encoder)")
        print(f"  • custom_gesture_mapping.json (gesture mapping)")
        
        return True

def main():
    print("🎯 LSTM Custom Gesture Trainer")
    print("=" * 50)
    
    # Create trainer
    trainer = LSTMGestureTrainer()
    
    # Check for custom videos folder
    if not trainer.custom_videos_folder.exists():
        print(f"📁 Creating custom_videos folder...")
        trainer.custom_videos_folder.mkdir(exist_ok=True)
        
        # Create example structure
        for gesture in ['welcome', 'thank_you', 'hello']:
            (trainer.custom_videos_folder / gesture).mkdir(exist_ok=True)
        
        print(f"\n📋 Folder structure created:")
        print(f"  custom_videos/")
        print(f"    ├── welcome/     # Put welcome gesture videos here")
        print(f"    ├── thank_you/   # Put thank_you gesture videos here")
        print(f"    └── hello/       # Put hello gesture videos here")
        print(f"\n💡 Add your gesture videos and run this script again.")
        return
    
    # Load and process videos
    if not trainer.load_custom_videos():
        return
    
    # Train model
    success = trainer.train_model()
    
    if success:
        print(f"\n🎉 Training completed successfully!")
        print(f"🔄 Now you can use the custom gesture recognition in your main app.")
    else:
        print(f"\n❌ Training failed!")

if __name__ == "__main__":
    main()
