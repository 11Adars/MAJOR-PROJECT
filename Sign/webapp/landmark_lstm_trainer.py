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

class LandmarkBasedLSTMTrainer:
    """
    Incremental LSTM trainer using MediaPipe landmarks instead of image features
    This ensures consistency between training and prediction
    """
    
    def __init__(self, cache_dir="training_cache_landmarks", sequence_length=30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.features_cache_dir = self.cache_dir / "features"
        self.models_cache_dir = self.cache_dir / "models"
        self.features_cache_dir.mkdir(exist_ok=True)
        self.models_cache_dir.mkdir(exist_ok=True)
        
        self.processed_files_log = self.cache_dir / "processed_files.json"
        self.processed_files = self.load_processed_files()
        
        self.sequence_length = sequence_length
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        print("🚀 Landmark-based LSTM Trainer initialized")
        print(f"📁 Cache directory: {self.cache_dir}")
        
    def load_processed_files(self):
        """Load the log of already processed files"""
        if self.processed_files_log.exists():
            with open(self.processed_files_log, 'r') as f:
                data = json.load(f)
            print(f"📋 Loaded {len(data)} previously processed files")
            return data
        return {}
    
    def save_processed_files(self):
        """Save the log of processed files"""
        with open(self.processed_files_log, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def get_file_hash(self, file_path):
        """Get MD5 hash of video file for change detection"""
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    
    def get_cached_features_path(self, gesture_name, video_file):
        """Get path for cached features file"""
        safe_filename = video_file.stem.replace(' ', '_')
        return self.features_cache_dir / f"{gesture_name}_{safe_filename}.pkl"
    
    def extract_landmarks_from_frame(self, frame):
        """Extract MediaPipe landmarks from a single frame"""
        with self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5
        ) as hands, self.mp_pose.Pose(
            static_image_mode=True,
            min_detection_confidence=0.5
        ) as pose:
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process hands
            hands_results = hands.process(rgb_frame)
            pose_results = pose.process(rgb_frame)
            
            # Initialize landmark arrays
            right_hand = np.zeros((21, 3))
            left_hand = np.zeros((21, 3))
            pose_landmarks = np.zeros((33, 3))
            
            # Extract hand landmarks
            if hands_results.multi_hand_landmarks:
                for idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
                    hand_label = hands_results.multi_handedness[idx].classification[0].label
                    landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
                    
                    if hand_label == "Right":
                        right_hand = landmarks
                    else:
                        left_hand = landmarks
            
            # Extract pose landmarks
            if pose_results.pose_landmarks:
                pose_landmarks = np.array([[lm.x, lm.y, lm.z] for lm in pose_results.pose_landmarks.landmark])
            
            return right_hand, left_hand, pose_landmarks
    
    def extract_features_from_landmarks(self, right_hand, left_hand, pose_landmarks):
        """Extract 200-dimensional features from landmarks (same as in model_enhanced.py)"""
        features = []
        
        # Combine all landmarks
        all_coords = np.vstack([right_hand, left_hand, pose_landmarks])  # (75, 3)
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
        
        # 9-region analysis (40 features)  
        regions = []
        for i in range(3):
            for j in range(3):
                start_row, end_row = i*5, (i+1)*5
                start_col, end_col = j*2, (j+1)*2 if j < 2 else 5
                region = coord_matrix[start_row:end_row, start_col:end_col, :].flatten()
                if len(region) > 0:
                    regions.extend([
                        np.mean(region), np.std(region), 
                        np.max(region), np.min(region)
                    ])
                else:
                    regions.extend([0, 0, 0, 0])
        
        # Ensure we have exactly 40 region features
        while len(regions) < 40:
            regions.append(0)
        features.extend(regions[:40])
        
        # Ensure exactly 200 features
        features = features[:200]
        while len(features) < 200:
            features.append(0)
        
        return np.array(features, dtype=np.float32)
    
    def extract_features_from_video(self, video_path):
        """Extract features from a single video file using MediaPipe landmarks"""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return None
        
        frames_features = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract landmarks
            right_hand, left_hand, pose_landmarks = self.extract_landmarks_from_frame(frame)
            
            # Extract features from landmarks
            features = self.extract_features_from_landmarks(right_hand, left_hand, pose_landmarks)
            frames_features.append(features)
            frame_count += 1
            
            # Limit frames to prevent memory issues
            if frame_count >= self.sequence_length * 3:  # Allow up to 90 frames
                break
        
        cap.release()
        
        if not frames_features:
            print(f"❌ No frames processed from {video_path}")
            return None
        
        return np.array(frames_features)
    
    def process_gesture_videos(self, gesture_name, force_reprocess=False):
        """Process all videos for a specific gesture"""
        gesture_dir = Path("custom_videos") / gesture_name
        if not gesture_dir.exists():
            print(f"📁 No directory found for gesture: {gesture_name}")
            return []
        
        video_files = list(gesture_dir.glob("*.mp4"))
        if not video_files:
            print(f"📹 No videos found for gesture: {gesture_name}")
            return []
        
        print(f"📁 Processing gesture: {gesture_name}")
        print(f"  📹 Found {len(video_files)} videos")
        
        all_sequences = []
        
        for video_file in video_files:
            video_key = f"{gesture_name}_{video_file.name}"
            cached_path = self.get_cached_features_path(gesture_name, video_file)
            
            # Check if we need to process this file
            current_hash = self.get_file_hash(video_file)
            
            if not force_reprocess and video_key in self.processed_files and cached_path.exists():
                stored_hash = self.processed_files[video_key].get('hash')
                if stored_hash == current_hash:
                    # Load from cache
                    print(f"    ✅ Loaded from cache: {video_file.name}")
                    features = joblib.load(cached_path)
                    if features is not None:
                        sequences = self.augment_sequence(features)
                        all_sequences.extend(sequences)
                    continue
            
            # Process video
            print(f"    🔄 Processing: {video_file.name}")
            features = self.extract_features_from_video(video_file)
            
            if features is not None:
                # Save to cache
                joblib.dump(features, cached_path)
                
                # Update processed files log
                self.processed_files[video_key] = {
                    'hash': current_hash,
                    'features_path': str(cached_path),
                    'processed_at': datetime.datetime.now().isoformat()
                }
                
                # Generate augmented sequences
                sequences = self.augment_sequence(features)
                all_sequences.extend(sequences)
            else:
                print(f"    ❌ Failed to process: {video_file.name}")
        
        return all_sequences
    
    def augment_sequence(self, features):
        """Generate augmented sequences from video features"""
        if len(features) < self.sequence_length:
            # If video is too short, repeat frames
            repetitions = (self.sequence_length // len(features)) + 1
            features = np.tile(features, (repetitions, 1))
        
        sequences = []
        step_size = max(1, len(features) // 6)  # Generate 6 sequences per video
        
        for start_idx in range(0, len(features) - self.sequence_length + 1, step_size):
            if len(sequences) >= 6:  # Limit augmentations
                break
            sequence = features[start_idx:start_idx + self.sequence_length]
            sequences.append(sequence)
        
        return sequences
    
    def backup_current_model(self):
        """Backup existing model files with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_files = [
            "simple_custom_lstm.h5",
            "simple_custom_labels.pkl", 
            "simple_custom_mapping.json"
        ]
        
        for model_file in model_files:
            if Path(model_file).exists():
                backup_name = f"{timestamp}_{model_file}"
                backup_path = self.models_cache_dir / backup_name
                Path(model_file).rename(backup_path)
                print(f"💾 Backed up: {model_file} -> {backup_path}")
    
    def create_lstm_model(self, num_classes):
        """Create enhanced LSTM model"""
        model = keras.Sequential([
            # Input normalization
            layers.BatchNormalization(input_shape=(self.sequence_length, 200)),
            layers.GaussianNoise(0.1),
            
            # LSTM layers
            layers.LSTM(128, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            layers.BatchNormalization(),
            layers.LSTM(64, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            layers.BatchNormalization(),
            layers.LSTM(32, dropout=0.3, recurrent_dropout=0.3),
            
            # Dense layers
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.4),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(16, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        return model
    
    def train_incremental_model(self):
        """Train the LSTM model incrementally"""
        print("🚀 Starting landmark-based incremental training...")
        print("🔍 Scanning for videos...")
        
        # Find all gesture directories
        training_dir = Path("custom_videos")
        if not training_dir.exists():
            print("❌ custom_videos directory not found!")
            return False
        
        gesture_dirs = [d for d in training_dir.iterdir() if d.is_dir()]
        if not gesture_dirs:
            print("❌ No gesture directories found!")
            return False
        
        # Process all gestures
        all_sequences = []
        all_labels = []
        gesture_names = []
        
        newly_processed_videos = 0
        cached_videos = 0
        
        for gesture_dir in gesture_dirs:
            gesture_name = gesture_dir.name
            gesture_names.append(gesture_name)
            
            sequences = self.process_gesture_videos(gesture_name)
            
            if sequences:
                all_sequences.extend(sequences)
                all_labels.extend([gesture_name] * len(sequences))
                print(f"  ✅ Generated {len(sequences)} sequences for '{gesture_name}'")
        
        if not all_sequences:
            print("❌ No sequences generated!")
            return False
        
        # Save processed files log
        self.save_processed_files()
        
        print(f"\\n📊 Processing Summary:")
        print(f"  🔄 Newly processed: {newly_processed_videos} videos")
        print(f"  💾 Loaded from cache: {cached_videos} videos")
        print(f"  📈 Total sequences: {len(all_sequences)}")
        
        # Prepare training data
        X = np.array(all_sequences)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(all_labels)
        num_classes = len(label_encoder.classes_)
        
        # One-hot encode for categorical crossentropy
        y = keras.utils.to_categorical(y_encoded, num_classes=num_classes)
        
        print(f"\\n🔢 Training data shape: {X.shape}")
        print(f"🏷️ Gestures: {list(label_encoder.classes_)}")
        for i, gesture in enumerate(label_encoder.classes_):
            count = np.sum(y_encoded == i)
            print(f"  {gesture}: {count} sequences")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y_encoded
        )
        print(f"🔀 Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Backup existing model
        self.backup_current_model()
        
        # Create and compile model
        model = self.create_lstm_model(num_classes)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print(f"\\n🏗️ Model architecture:")
        model.summary()
        
        # Train model
        print("\\n🚀 Training model...")
        history = model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, y_test),
            callbacks=[
                keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.5),
                keras.callbacks.ModelCheckpoint('simple_custom_lstm.h5', save_best_only=True)
            ],
            verbose=1
        )
        
        # Evaluate model
        test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
        print(f"\\n📊 Final test accuracy: {test_accuracy*100:.1f}%")
        
        # Save model and encoders
        model.save('simple_custom_lstm.h5')
        joblib.dump(label_encoder, 'simple_custom_labels.pkl')
        
        # Save gesture mapping
        gesture_mapping = {gesture: int(idx) for idx, gesture in enumerate(label_encoder.classes_)}
        with open('simple_custom_mapping.json', 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        
        print("\\n✅ Training complete!")
        print("📂 Model saved: simple_custom_lstm.h5")
        print("📂 Labels saved: simple_custom_labels.pkl")
        print("📂 Mapping saved: simple_custom_mapping.json")
        print(f"💾 Cache directory: {self.cache_dir}")
        
        return True

def main():
    trainer = LandmarkBasedLSTMTrainer()
    trainer.train_incremental_model()

if __name__ == "__main__":
    main()
