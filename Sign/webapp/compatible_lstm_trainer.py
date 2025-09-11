import os
import json
import numpy as np
import pandas as pd
import cv2
import mediapipe as mp
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import datetime

# Import TensorFlow with error handling
try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    print(f"✅ TensorFlow {tf.__version__} loaded successfully")
except ImportError as e:
    print(f"❌ TensorFlow import error: {e}")
    exit(1)

class CompatibleLSTMTrainer:
    """
    Compatible LSTM trainer that works with TensorFlow 2.12+
    """
    
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        
        print("🚀 Compatible LSTM Trainer initialized")
        
    def extract_landmarks_from_video(self, video_path):
        """Extract MediaPipe landmarks from video"""
        print(f"📹 Processing: {Path(video_path).name}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"❌ Could not open: {video_path}")
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
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
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
                
                # Pose landmarks (only upper body)
                if pose_results.pose_landmarks:
                    # Only use upper body landmarks (0-10)
                    for j in range(11):  # Reduce to key pose points
                        landmark = pose_results.pose_landmarks.landmark[j]
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
                    landmarks_sequence.append(pd.DataFrame())
        
        cap.release()
        return landmarks_sequence
    
    def extract_features_from_sequence(self, landmarks_sequence):
        """Extract simplified but consistent features"""
        def extract_frame_features(frame_df):
            """Extract features from a single frame"""
            if frame_df.empty:
                return np.zeros(100)  # Reduced feature size
            
            features = []
            
            # Get landmark data
            right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y', 'z']].values
            left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y', 'z']].values
            pose = frame_df[frame_df['type'] == 'pose'][['x', 'y', 'z']].values
            
            # Ensure consistent sizes
            if len(right_hand) == 0: right_hand = np.zeros((21, 3))
            if len(left_hand) == 0: left_hand = np.zeros((21, 3))
            if len(pose) == 0: pose = np.zeros((11, 3))
            
            # Pad or truncate
            right_hand = np.pad(right_hand, ((0, max(0, 21-len(right_hand))), (0, 0)), 'constant')[:21]
            left_hand = np.pad(left_hand, ((0, max(0, 21-len(left_hand))), (0, 0)), 'constant')[:21]
            pose = np.pad(pose, ((0, max(0, 11-len(pose))), (0, 0)), 'constant')[:11]
            
            # Flatten coordinates
            right_flat = right_hand.flatten()  # 63 features
            left_flat = left_hand.flatten()    # 63 features
            pose_flat = pose.flatten()         # 33 features
            
            # Basic statistics (25 features)
            all_coords = np.concatenate([right_flat, left_flat, pose_flat])
            features.extend([
                np.mean(all_coords), np.std(all_coords), np.min(all_coords), np.max(all_coords),
                np.median(all_coords), np.var(all_coords),
                np.mean(np.abs(all_coords)), np.std(np.abs(all_coords)),
                np.sum(all_coords > 0), np.sum(all_coords < 0),
                np.mean(right_flat), np.std(right_flat), np.mean(left_flat), np.std(left_flat),
                np.mean(pose_flat), np.std(pose_flat),
                np.mean(right_hand[:, 0]), np.mean(right_hand[:, 1]), np.mean(right_hand[:, 2]),
                np.mean(left_hand[:, 0]), np.mean(left_hand[:, 1]), np.mean(left_hand[:, 2]),
                np.mean(pose[:, 0]), np.mean(pose[:, 1]), np.mean(pose[:, 2])
            ])
            
            # Hand distance features (10 features)
            if len(right_hand) > 0 and len(left_hand) > 0:
                hand_distance = np.linalg.norm(np.mean(right_hand, axis=0) - np.mean(left_hand, axis=0))
                features.append(hand_distance)
                
                # Individual hand spreads
                right_center = np.mean(right_hand, axis=0)
                left_center = np.mean(left_hand, axis=0)
                right_spread = np.mean(np.linalg.norm(right_hand - right_center, axis=1))
                left_spread = np.mean(np.linalg.norm(left_hand - left_center, axis=1))
                features.extend([right_spread, left_spread])
                
                # Hand positions relative to pose
                if len(pose) > 0:
                    pose_center = np.mean(pose, axis=0)
                    right_to_pose = np.linalg.norm(right_center - pose_center)
                    left_to_pose = np.linalg.norm(left_center - pose_center)
                    features.extend([right_to_pose, left_to_pose])
                else:
                    features.extend([0, 0])
                
                # Additional hand features
                features.extend([
                    np.ptp(right_hand[:, 0]), np.ptp(right_hand[:, 1]),  # Range of movement
                    np.ptp(left_hand[:, 0]), np.ptp(left_hand[:, 1]),
                    np.max(right_hand[:, 2]), np.max(left_hand[:, 2])    # Max z values
                ])
            else:
                features.extend([0] * 10)
            
            # Coordinate distribution features (65 features)
            # Sample key coordinates
            key_coords = []
            if len(right_hand) >= 5:  # Thumb, index, middle, ring, pinky tips
                key_coords.extend(right_hand[[4, 8, 12, 16, 20]].flatten())
            else:
                key_coords.extend([0] * 15)
                
            if len(left_hand) >= 5:
                key_coords.extend(left_hand[[4, 8, 12, 16, 20]].flatten())
            else:
                key_coords.extend([0] * 15)
                
            if len(pose) >= 5:  # Key pose points
                key_coords.extend(pose[:5].flatten())
            else:
                key_coords.extend([0] * 15)
            
            # Add remaining coordinates to reach 65
            remaining_coords = all_coords[:20]  # First 20 coordinates
            key_coords.extend(remaining_coords.tolist())
            
            # Ensure exactly 65 coordinate features
            while len(key_coords) < 65:
                key_coords.append(0)
            features.extend(key_coords[:65])
            
            # Ensure exactly 100 features total
            while len(features) < 100:
                features.append(0)
            
            return np.array(features[:100])
        
        # Process each frame
        frame_features = []
        for frame_df in landmarks_sequence:
            features = extract_frame_features(frame_df)
            frame_features.append(features)
        
        # Handle sequence length
        frame_features = np.array(frame_features)
        if len(frame_features) >= self.sequence_length:
            # Take middle section
            start_idx = (len(frame_features) - self.sequence_length) // 2
            frame_features = frame_features[start_idx:start_idx + self.sequence_length]
        else:
            # Pad with zeros
            padding_needed = self.sequence_length - len(frame_features)
            padding = np.zeros((padding_needed, 100))
            frame_features = np.vstack([frame_features, padding])
        
        return frame_features
    
    def process_gesture_videos(self, gesture_dir):
        """Process all videos for a gesture"""
        gesture_path = Path(gesture_dir)
        if not gesture_path.exists():
            return []
        
        video_files = list(gesture_path.glob("*.mp4"))
        print(f"📁 Found {len(video_files)} videos for {gesture_path.name}")
        
        gesture_features = []
        for i, video_file in enumerate(video_files):
            try:
                landmarks_sequence = self.extract_landmarks_from_video(video_file)
                if landmarks_sequence:
                    features = self.extract_features_from_sequence(landmarks_sequence)
                    gesture_features.append(features)
                    
                if (i + 1) % 10 == 0:
                    print(f"✅ Processed {i + 1}/{len(video_files)}")
                    
            except Exception as e:
                print(f"❌ Error processing {video_file.name}: {e}")
                continue
        
        return gesture_features
    
    def create_simple_lstm_model(self, num_classes):
        """Create a simple LSTM model"""
        model = keras.Sequential([
            layers.Input(shape=(self.sequence_length, 100)),
            layers.LSTM(64, return_sequences=True, dropout=0.3),
            layers.LSTM(32, dropout=0.3),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self, custom_videos_dir="custom_videos"):
        """Train the LSTM model"""
        print("🚀 Starting Compatible LSTM Training...")
        
        custom_videos_path = Path(custom_videos_dir)
        if not custom_videos_path.exists():
            print(f"❌ Directory not found: {custom_videos_dir}")
            return False
        
        gesture_dirs = [d for d in custom_videos_path.iterdir() if d.is_dir()]
        print(f"📁 Gesture directories: {[d.name for d in gesture_dirs]}")
        
        # Process gestures
        all_features = []
        all_labels = []
        
        for gesture_dir in gesture_dirs:
            gesture_features = self.process_gesture_videos(gesture_dir)
            if gesture_features:
                all_features.extend(gesture_features)
                all_labels.extend([gesture_dir.name] * len(gesture_features))
                print(f"✅ {gesture_dir.name}: {len(gesture_features)} samples")
        
        if not all_features:
            print("❌ No training data!")
            return False
        
        # Prepare data
        X = np.array(all_features)
        y = np.array(all_labels)
        
        print(f"📊 Training data: {X.shape}")
        print(f"📊 Gestures: {np.unique(y)}")
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Create model
        num_classes = len(label_encoder.classes_)
        model = self.create_simple_lstm_model(num_classes)
        
        print("🤖 Model summary:")
        model.summary()
        
        # Training callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=8, min_lr=0.00001)
        ]
        
        # Train
        print("🚀 Training model...")
        history = model.fit(
            X_train, y_train,
            epochs=100,
            batch_size=8,
            validation_data=(X_test, y_test),
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
        print(f"📊 Final accuracy: {test_accuracy:.4f}")
        
        # Save files
        gesture_mapping = {gesture: idx for idx, gesture in enumerate(label_encoder.classes_)}
        
        # Save model
        model.save("simple_custom_lstm.h5", save_format='h5')
        print("💾 Model saved: simple_custom_lstm.h5")
        
        # Save label encoder
        joblib.dump(label_encoder, "simple_custom_labels.pkl")
        print("💾 Labels saved: simple_custom_labels.pkl")
        
        # Save mapping
        with open("simple_custom_mapping.json", 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        print("💾 Mapping saved: simple_custom_mapping.json")
        
        print(f"✅ Training completed! Accuracy: {test_accuracy:.4f}")
        return True

if __name__ == "__main__":
    trainer = CompatibleLSTMTrainer()
    success = trainer.train_model()
    
    if success:
        print("🎉 Training successful!")
    else:
        print("❌ Training failed!")
