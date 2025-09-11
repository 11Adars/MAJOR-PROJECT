import os
import json
import numpy as np
import pandas as pd
import cv2
import mediapipe as mp
from pathlib import Path
import hashlib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import datetime

class CompleteLandmarkTrainer:
    """
    Complete landmark-based LSTM trainer with consistent feature extraction
    """
    
    def __init__(self, cache_dir="training_cache_complete", sequence_length=30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.features_cache_dir = self.cache_dir / "features"
        self.models_cache_dir = self.cache_dir / "models"
        self.features_cache_dir.mkdir(exist_ok=True)
        self.models_cache_dir.mkdir(exist_ok=True)
        
        self.sequence_length = sequence_length
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        print("🚀 Complete Landmark-based LSTM Trainer initialized")
        print(f"📁 Cache directory: {self.cache_dir}")
        
    def extract_landmarks_from_video(self, video_path):
        """Extract MediaPipe landmarks from video - EXACT same as prediction"""
        print(f"📹 Processing video: {video_path}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"❌ Error: Could not open video {video_path}")
            return []
        
        landmarks_sequence = []
        
        with self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as hands, self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process with MediaPipe
                hands_results = hands.process(rgb_frame)
                pose_results = pose.process(rgb_frame)
                
                # Extract landmark data
                frame_landmarks = []
                
                # Hand landmarks
                if hands_results.multi_hand_landmarks:
                    for i, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
                        hand_label = hands_results.multi_handedness[i].classification[0].label
                        hand_type = "right_hand" if hand_label == "Right" else "left_hand"
                        
                        for j, landmark in enumerate(hand_landmarks.landmark):
                            frame_landmarks.append({
                                'type': hand_type,
                                'landmark_index': j,
                                'x': landmark.x,
                                'y': landmark.y,
                                'z': landmark.z
                            })
                
                # Pose landmarks
                if pose_results.pose_landmarks:
                    for j, landmark in enumerate(pose_results.pose_landmarks.landmark):
                        frame_landmarks.append({
                            'type': 'pose',
                            'landmark_index': j,
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z
                        })
                
                # Convert to DataFrame
                if frame_landmarks:
                    frame_df = pd.DataFrame(frame_landmarks)
                    landmarks_sequence.append(frame_df)
                else:
                    # Add empty frame
                    landmarks_sequence.append(pd.DataFrame())
        
        cap.release()
        print(f"✅ Processed {frame_count} frames, extracted {len(landmarks_sequence)} landmark frames")
        return landmarks_sequence
    
    def extract_features_from_sequence(self, landmarks_sequence):
        """Extract features using EXACT same method as prediction"""
        def extract_simple_features(frame_df):
            """Extract 200-dimensional features from a single frame - SAME as prediction"""
            features = []
            
            if frame_df.empty:
                return np.zeros(200)
            
            # Get hand landmarks
            right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y', 'z']].values
            left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y', 'z']].values
            pose = frame_df[frame_df['type'] == 'pose'][['x', 'y', 'z']].values
            
            # Ensure we have data
            if len(right_hand) == 0: right_hand = np.zeros((21, 3))
            if len(left_hand) == 0: left_hand = np.zeros((21, 3))
            if len(pose) == 0: pose = np.zeros((33, 3))
            
            # Pad or truncate to expected sizes
            right_hand = np.pad(right_hand, ((0, max(0, 21-len(right_hand))), (0, 0)), 'constant')[:21]
            left_hand = np.pad(left_hand, ((0, max(0, 21-len(left_hand))), (0, 0)), 'constant')[:21]
            pose = np.pad(pose, ((0, max(0, 33-len(pose))), (0, 0)), 'constant')[:33]
            
            # Combine all landmarks
            all_coords = np.vstack([right_hand, left_hand, pose])  # (75, 3)
            coords_flat = all_coords.flatten()  # 225 values
            
            # Basic statistics (20 features)
            features.extend([
                np.mean(coords_flat), np.std(coords_flat), np.min(coords_flat), np.max(coords_flat),
                np.median(coords_flat), np.var(coords_flat), np.ptp(coords_flat),
                np.mean(coords_flat[coords_flat > 0]) if len(coords_flat[coords_flat > 0]) > 0 else 0,
                len(coords_flat[coords_flat > 0.5]) / len(coords_flat),
                len(coords_flat[coords_flat < -0.5]) / len(coords_flat),
                np.percentile(coords_flat, 25), np.percentile(coords_flat, 75),
                np.mean(np.abs(coords_flat)), np.std(np.abs(coords_flat)),
                np.sum(coords_flat > 0), np.sum(coords_flat < 0),
                np.mean(coords_flat**2), np.std(coords_flat**2),
                np.mean(np.sqrt(np.abs(coords_flat))), np.std(np.sqrt(np.abs(coords_flat)))
            ])
            
            # Hand-specific features (40 features)
            for hand_data, hand_name in [(right_hand, 'right'), (left_hand, 'left')]:
                hand_flat = hand_data.flatten()
                features.extend([
                    np.mean(hand_flat), np.std(hand_flat), np.min(hand_flat), np.max(hand_flat),
                    np.median(hand_flat), np.var(hand_flat), np.ptp(hand_flat),
                    np.mean(hand_data[:, 0]), np.mean(hand_data[:, 1]), np.mean(hand_data[:, 2]),
                    np.std(hand_data[:, 0]), np.std(hand_data[:, 1]), np.std(hand_data[:, 2]),
                    np.ptp(hand_data[:, 0]), np.ptp(hand_data[:, 1]), np.ptp(hand_data[:, 2]),
                    np.mean(np.linalg.norm(hand_data, axis=1)),
                    np.std(np.linalg.norm(hand_data, axis=1)),
                    np.sum(hand_flat > 0.1), np.sum(hand_flat < -0.1)
                ])
            
            # HSV and color histograms (30 features)
            x_coords = all_coords[:, 0]
            y_coords = all_coords[:, 1]
            z_coords = all_coords[:, 2]
            
            # Create pseudo-HSV values from coordinates
            hue_values = (x_coords + 1) * 180  # Map [-1,1] to [0,360]
            sat_values = (y_coords + 1) * 0.5  # Map [-1,1] to [0,1]
            val_values = (z_coords + 1) * 0.5  # Map [-1,1] to [0,1]
            
            h_hist, _ = np.histogram(hue_values, bins=10, range=(0, 360))
            s_hist, _ = np.histogram(sat_values, bins=10, range=(0, 1))
            v_hist, _ = np.histogram(val_values, bins=10, range=(0, 1))
            
            features.extend(h_hist.tolist())
            features.extend(s_hist.tolist())
            features.extend(v_hist.tolist())
            
            # Edge detection features (30 features)
            coord_matrix = all_coords.reshape(15, 5, 3)  # Reshape for edge detection
            edges_x = np.abs(np.diff(coord_matrix[:, :, 0], axis=0)).flatten()
            edges_y = np.abs(np.diff(coord_matrix[:, :, 1], axis=1)).flatten()
            
            edge_features = []
            for edge_data in [edges_x, edges_y]:
                if len(edge_data) > 0:
                    edge_features.extend([
                        np.mean(edge_data), np.std(edge_data), np.max(edge_data),
                        np.min(edge_data), np.sum(edge_data > np.mean(edge_data))
                    ])
                else:
                    edge_features.extend([0, 0, 0, 0, 0])
            
            # Add padding to reach 30
            while len(edge_features) < 30:
                edge_features.append(0)
            features.extend(edge_features[:30])
            
            # Texture and contour features (40 features)
            for i in range(3):  # For x, y, z coordinates
                coord_channel = all_coords[:, i].reshape(15, 5)
                
                # Texture features
                features.extend([
                    np.mean(coord_channel), np.std(coord_channel),
                    np.var(coord_channel), np.ptp(coord_channel),
                    np.mean(np.abs(np.gradient(coord_channel.flatten()))),
                    np.std(np.abs(np.gradient(coord_channel.flatten()))),
                    np.mean(coord_channel**2), np.std(coord_channel**2),
                    np.sum(coord_channel > np.mean(coord_channel)),
                    len(np.where(np.diff(np.sign(coord_channel.flatten())))[0])  # Zero crossings
                ])
            
            # Additional motion features (40 features) 
            motion_features = []
            
            # Global motion features
            center_of_mass = np.mean(all_coords, axis=0)
            distances_from_center = np.linalg.norm(all_coords - center_of_mass, axis=1)
            motion_features.extend([
                np.mean(distances_from_center), np.std(distances_from_center),
                np.max(distances_from_center), np.min(distances_from_center),
                np.median(distances_from_center)
            ])
            
            # Hand spread features
            for hand_data in [right_hand, left_hand]:
                if len(hand_data) > 0:
                    hand_center = np.mean(hand_data, axis=0)
                    hand_spread = np.linalg.norm(hand_data - hand_center, axis=1)
                    motion_features.extend([
                        np.mean(hand_spread), np.std(hand_spread), np.max(hand_spread),
                        np.sum(hand_spread > np.mean(hand_spread)),
                        np.ptp(hand_data[:, 0]) + np.ptp(hand_data[:, 1])  # Bounding box area
                    ])
                else:
                    motion_features.extend([0, 0, 0, 0, 0])
            
            # Velocity-like features (differences between coordinates)
            velocity_features = []
            for i in range(min(20, len(all_coords)-1)):
                diff = all_coords[i+1] - all_coords[i]
                velocity_features.extend([np.linalg.norm(diff), np.mean(diff), np.std(diff)])
            
            # Pad velocity features to 15
            while len(velocity_features) < 15:
                velocity_features.append(0)
            motion_features.extend(velocity_features[:15])
            
            # Ensure motion features total 40
            while len(motion_features) < 40:
                motion_features.append(0)
            features.extend(motion_features[:40])
            
            # Ensure exactly 200 features
            while len(features) < 200:
                features.append(0)
            
            return np.array(features[:200])
        
        # Process sequence
        if len(landmarks_sequence) == 0:
            return np.zeros((self.sequence_length, 200))
        
        # Extract features for each frame
        frame_features = []
        for frame_df in landmarks_sequence:
            features = extract_simple_features(frame_df)
            frame_features.append(features)
        
        # Convert to numpy array
        frame_features = np.array(frame_features)
        
        # Handle sequence length
        if len(frame_features) >= self.sequence_length:
            # Take middle frames if too long
            start_idx = (len(frame_features) - self.sequence_length) // 2
            frame_features = frame_features[start_idx:start_idx + self.sequence_length]
        else:
            # Pad if too short
            padding_needed = self.sequence_length - len(frame_features)
            padding = np.zeros((padding_needed, 200))
            frame_features = np.vstack([frame_features, padding])
        
        return frame_features
    
    def process_gesture_videos(self, gesture_dir):
        """Process all videos for a specific gesture"""
        gesture_path = Path(gesture_dir)
        if not gesture_path.exists():
            print(f"❌ Gesture directory not found: {gesture_dir}")
            return []
        
        video_files = list(gesture_path.glob("*.mp4"))
        print(f"📁 Found {len(video_files)} videos for gesture: {gesture_path.name}")
        
        gesture_features = []
        successful_processed = 0
        
        for video_file in video_files:
            try:
                # Extract landmarks
                landmarks_sequence = self.extract_landmarks_from_video(video_file)
                
                if len(landmarks_sequence) > 0:
                    # Extract features
                    features = self.extract_features_from_sequence(landmarks_sequence)
                    gesture_features.append(features)
                    successful_processed += 1
                    
                    if successful_processed % 10 == 0:
                        print(f"✅ Processed {successful_processed}/{len(video_files)} videos")
                
            except Exception as e:
                print(f"❌ Error processing {video_file}: {e}")
                continue
        
        print(f"✅ Successfully processed {successful_processed}/{len(video_files)} videos for {gesture_path.name}")
        return gesture_features
    
    def create_lstm_model(self, num_classes):
        """Create LSTM model architecture"""
        model = keras.Sequential([
            layers.LSTM(128, return_sequences=True, input_shape=(self.sequence_length, 200)),
            layers.Dropout(0.5),
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.5),
            layers.LSTM(32),
            layers.Dropout(0.5),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_lstm_model(self, custom_videos_dir="custom_videos"):
        """Train LSTM model with balanced data"""
        print("🚀 Starting Complete LSTM Training...")
        
        # Get gesture directories
        custom_videos_path = Path(custom_videos_dir)
        if not custom_videos_path.exists():
            print(f"❌ Custom videos directory not found: {custom_videos_dir}")
            return False
        
        gesture_dirs = [d for d in custom_videos_path.iterdir() if d.is_dir()]
        if len(gesture_dirs) == 0:
            print(f"❌ No gesture directories found in {custom_videos_dir}")
            return False
        
        print(f"📁 Found gesture directories: {[d.name for d in gesture_dirs]}")
        
        # Process each gesture
        all_features = []
        all_labels = []
        gesture_names = []
        
        for gesture_dir in gesture_dirs:
            gesture_name = gesture_dir.name
            gesture_names.append(gesture_name)
            
            print(f"\n🔄 Processing gesture: {gesture_name}")
            gesture_features = self.process_gesture_videos(gesture_dir)
            
            if len(gesture_features) == 0:
                print(f"⚠️  No valid features extracted for {gesture_name}")
                continue
            
            # Add to training data
            all_features.extend(gesture_features)
            all_labels.extend([gesture_name] * len(gesture_features))
            
            print(f"✅ Added {len(gesture_features)} samples for {gesture_name}")
        
        if len(all_features) == 0:
            print("❌ No training data collected!")
            return False
        
        # Convert to numpy arrays
        X = np.array(all_features)
        y = np.array(all_labels)
        
        print(f"\n📊 Training data shape: {X.shape}")
        print(f"📊 Labels shape: {y.shape}")
        print(f"📊 Unique gestures: {np.unique(y)}")
        
        # Create label encoder
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Create mapping
        gesture_mapping = {gesture: idx for idx, gesture in enumerate(label_encoder.classes_)}
        print(f"📋 Gesture mapping: {gesture_mapping}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print(f"🔄 Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # Create and train model
        num_classes = len(label_encoder.classes_)
        model = self.create_lstm_model(num_classes)
        
        print(f"\n🤖 Model architecture:")
        model.summary()
        
        # Training callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # Train model
        print(f"\n🚀 Starting training...")
        history = model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=16,
            validation_data=(X_test, y_test),
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate model
        test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
        print(f"\n📊 Final test accuracy: {test_accuracy:.4f}")
        
        # Save model and files
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save model
        model_path = f"simple_custom_lstm.h5"
        model.save(model_path)
        print(f"💾 Model saved: {model_path}")
        
        # Save label encoder
        labels_path = f"simple_custom_labels.pkl"
        joblib.dump(label_encoder, labels_path)
        print(f"💾 Labels saved: {labels_path}")
        
        # Save mapping
        mapping_path = f"simple_custom_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        print(f"💾 Mapping saved: {mapping_path}")
        
        # Also save to cache
        cache_model_path = self.models_cache_dir / f"{timestamp}_simple_custom_lstm.h5"
        cache_labels_path = self.models_cache_dir / f"{timestamp}_simple_custom_labels.pkl"
        cache_mapping_path = self.models_cache_dir / f"{timestamp}_simple_custom_mapping.json"
        
        model.save(cache_model_path)
        joblib.dump(label_encoder, cache_labels_path)
        with open(cache_mapping_path, 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        
        print(f"\n✅ Training completed successfully!")
        print(f"📁 Files created:")
        print(f"   - {model_path}")
        print(f"   - {labels_path}")
        print(f"   - {mapping_path}")
        
        return True

if __name__ == "__main__":
    # Initialize trainer
    trainer = CompleteLandmarkTrainer()
    
    # Train the model
    success = trainer.train_lstm_model()
    
    if success:
        print("\n🎉 Training completed successfully!")
    else:
        print("\n❌ Training failed!")
