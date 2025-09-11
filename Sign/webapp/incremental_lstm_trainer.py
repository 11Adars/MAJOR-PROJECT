#!/usr/bin/env python3
"""
Incremental LSTM Custom Gesture Trainer
- Saves processed features to avoid reprocessing
- Only processes new videos
- Supports adding new gestures without full retraining
- Smart caching and feature management
"""

import os
import cv2
import json
import numpy as np
import pandas as pd
import pickle
import hashlib
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import warnings
warnings.filterwarnings('ignore')

class IncrementalLSTMTrainer:
    def __init__(self, custom_videos_folder="custom_videos"):
        self.custom_videos_folder = Path(custom_videos_folder)
        self.sequence_length = 30
        self.feature_dim = 200
        
        # Cache directories
        self.cache_dir = Path("training_cache")
        self.features_cache_dir = self.cache_dir / "features"
        self.models_backup_dir = self.cache_dir / "models"
        
        # Create cache directories
        self.cache_dir.mkdir(exist_ok=True)
        self.features_cache_dir.mkdir(exist_ok=True)
        self.models_backup_dir.mkdir(exist_ok=True)
        
        # Training data
        self.sequences = []
        self.labels = []
        self.label_encoder = LabelEncoder()
        
        # File tracking
        self.processed_files_log = self.cache_dir / "processed_files.json"
        self.processed_files = self.load_processed_files()
        
        print("🚀 Incremental LSTM Trainer initialized")
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
    
    def extract_features_from_video(self, video_path):
        """Extract features from a single video file"""
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
            
            features = self.extract_simple_features(frame)
            frames_features.append(features)
            frame_count += 1
            
            # Limit frames to prevent memory issues
            if frame_count >= self.sequence_length * 3:  # Allow up to 90 frames
                break
        
        cap.release()
        
        if len(frames_features) == 0:
            return None
            
        # Convert to numpy array
        frames_array = np.array(frames_features, dtype=np.float32)
        
        # Apply augmentation to create multiple sequences
        augmented_sequences = self.augment_sequence(frames_array)
        
        return augmented_sequences
    
    def extract_simple_features(self, frame):
        """Extract 200-dimensional features from a single frame"""
        # Resize frame
        frame_resized = cv2.resize(frame, (128, 128))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
        
        features = []
        
        # Basic statistics (20 features)
        for channel in [gray, hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]]:
            flat = channel.flatten().astype(np.float32)
            features.extend([
                np.mean(flat), np.std(flat), np.min(flat), np.max(flat), np.median(flat)
            ])
        
        # Histograms (80 features)
        hist_gray = cv2.calcHist([gray], [0], None, [20], [0, 256])
        hist_h = cv2.calcHist([hsv], [0], None, [20], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [20], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [20], [0, 256])
        
        features.extend(hist_gray.flatten())
        features.extend(hist_h.flatten())
        features.extend(hist_s.flatten())
        features.extend(hist_v.flatten())
        
        # Edge detection features (30 features)
        edges = cv2.Canny(gray, 50, 150)
        edge_hist = cv2.calcHist([edges], [0], None, [10], [0, 256])
        features.extend(edge_hist.flatten())
        
        # Add edge statistics
        features.extend([
            np.sum(edges > 0) / edges.size,  # Edge density
            np.mean(edges), np.std(edges), np.max(edges),
            len(cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]),  # Contour count
            np.mean(gray**2), np.std(gray**2),  # Intensity moments
            np.sum(gray > 128) / gray.size,  # Brightness ratio
            np.sum(gray < 64) / gray.size,   # Darkness ratio
            np.ptp(gray),  # Intensity range
            np.var(gray),  # Variance
            cv2.Laplacian(gray, cv2.CV_64F).var(),  # Laplacian variance
            np.mean(np.gradient(gray.astype(float))),  # Gradient
            np.std(np.gradient(gray.astype(float))),
            np.sum(np.abs(np.diff(gray.flatten()))),  # Total variation
            np.mean(np.abs(np.diff(gray.flatten()))),
            np.std(np.abs(np.diff(gray.flatten()))),
            np.sum((gray[1:] - gray[:-1])**2),  # Energy
            np.mean((gray[1:] - gray[:-1])**2),
            np.correlate(gray.flatten()[:-1], gray.flatten()[1:])[0] / len(gray.flatten()),  # Autocorrelation
        ])
        
        # Texture features (30 features)
        # Local Binary Pattern approximation
        kernel_mean = cv2.blur(gray, (3,3))
        texture_features = []
        for kernel_size in [3, 5, 7]:
            blurred = cv2.blur(gray, (kernel_size, kernel_size))
            texture_features.extend([
                np.mean(blurred), np.std(blurred), np.var(blurred),
                np.sum(blurred > np.mean(blurred)),
                np.sum(blurred < np.mean(blurred))
            ])
        
        # Add remaining texture features
        gabor_real, _ = cv2.getGaborKernel((5, 5), 1, 0, 10, 0.5, 0, ktype=cv2.CV_32F), None
        gabor_img = cv2.filter2D(gray, cv2.CV_8UC3, gabor_real)
        texture_features.extend([
            np.mean(gabor_img), np.std(gabor_img), np.var(gabor_img),
            np.max(gabor_img), np.min(gabor_img),
            np.sum(gabor_img > np.mean(gabor_img)),
            np.sum(gabor_img < np.mean(gabor_img)),
            np.ptp(gabor_img), np.median(gabor_img), np.percentile(gabor_img, 25),
            np.percentile(gabor_img, 75), cv2.Laplacian(gabor_img, cv2.CV_64F).var(),
            np.mean(np.gradient(gabor_img.astype(float))), np.std(np.gradient(gabor_img.astype(float))),
            np.correlate(gabor_img.flatten()[:-1], gabor_img.flatten()[1:])[0] / len(gabor_img.flatten())
        ])
        
        features.extend(texture_features[:30])
        
        # Region-based features (40 features)
        h, w = gray.shape
        regions = [
            gray[0:h//2, 0:w//2],      # Top-left
            gray[0:h//2, w//2:],       # Top-right  
            gray[h//2:, 0:w//2],       # Bottom-left
            gray[h//2:, w//2:],        # Bottom-right
            gray[h//4:3*h//4, w//4:3*w//4],  # Center
        ]
        
        region_features = []
        for region in regions:
            if region.size > 0:
                region_features.extend([
                    np.mean(region), np.std(region), np.var(region),
                    np.max(region), np.min(region), np.median(region),
                    np.ptp(region), np.sum(region > np.mean(region))
                ])
            else:
                region_features.extend([0] * 8)
        
        features.extend(region_features)
        
        # Ensure exactly 200 features
        features = features[:200]
        while len(features) < 200:
            features.append(0.0)
        
        return np.array(features, dtype=np.float32)
    
    def augment_sequence(self, sequence):
        """Apply various augmentations to create multiple training sequences"""
        augmented = []
        
        # Original sequence (truncated/padded to sequence_length)
        orig_seq = self.normalize_sequence_length(sequence)
        augmented.append(orig_seq)
        
        # Apply augmentations
        augmentation_configs = [
            {'noise_level': 0.01, 'speed_factor': 1.0, 'intensity_scale': 1.0},
            {'noise_level': 0.02, 'speed_factor': 0.8, 'intensity_scale': 0.95},
            {'noise_level': 0.015, 'speed_factor': 1.2, 'intensity_scale': 1.05},
            {'noise_level': 0.005, 'speed_factor': 0.9, 'intensity_scale': 0.9},
            {'noise_level': 0.025, 'speed_factor': 1.1, 'intensity_scale': 1.1},
        ]
        
        for config in augmentation_configs:
            aug_seq = self.apply_augmentation(sequence, **config)
            aug_seq = self.normalize_sequence_length(aug_seq)
            augmented.append(aug_seq)
        
        return augmented
    
    def apply_augmentation(self, sequence, noise_level=0.01, speed_factor=1.0, intensity_scale=1.0):
        """Apply specific augmentation to sequence"""
        aug_seq = sequence.copy()
        
        # Add noise
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, aug_seq.shape)
            aug_seq = aug_seq + noise
        
        # Speed variation (temporal)
        if speed_factor != 1.0:
            original_length = len(aug_seq)
            new_length = int(original_length * speed_factor)
            indices = np.linspace(0, original_length-1, new_length).astype(int)
            aug_seq = aug_seq[indices]
        
        # Intensity scaling
        if intensity_scale != 1.0:
            aug_seq = aug_seq * intensity_scale
        
        return aug_seq
    
    def normalize_sequence_length(self, sequence):
        """Normalize sequence to fixed length"""
        if len(sequence) >= self.sequence_length:
            return sequence[:self.sequence_length]
        else:
            # Pad with last frame
            padding = np.tile(sequence[-1:], (self.sequence_length - len(sequence), 1))
            return np.vstack([sequence, padding])
    
    def load_and_process_videos(self):
        """Load videos with smart caching - only process new/changed files"""
        print("🔍 Scanning for videos...")
        
        new_sequences = []
        new_labels = []
        processed_count = 0
        cached_count = 0
        
        gesture_folders = [f for f in self.custom_videos_folder.iterdir() if f.is_dir()]
        
        for gesture_folder in gesture_folders:
            gesture_name = gesture_folder.name
            print(f"\n📁 Processing gesture: {gesture_name}")
            
            video_files = list(gesture_folder.glob("*.mp4"))
            print(f"  📹 Found {len(video_files)} videos")
            
            for video_file in video_files:
                file_key = str(video_file.relative_to(self.custom_videos_folder))
                current_hash = self.get_file_hash(video_file)
                cached_features_path = self.get_cached_features_path(gesture_name, video_file)
                
                # Check if we need to process this file
                if (file_key in self.processed_files and 
                    self.processed_files[file_key]['hash'] == current_hash and
                    cached_features_path.exists()):
                    
                    # Load from cache
                    try:
                        with open(cached_features_path, 'rb') as f:
                            cached_sequences = pickle.load(f)
                        
                        new_sequences.extend(cached_sequences)
                        new_labels.extend([gesture_name] * len(cached_sequences))
                        cached_count += 1
                        print(f"    ✅ Loaded from cache: {video_file.name}")
                        continue
                    except Exception as e:
                        print(f"    ⚠️ Cache load failed: {e}")
                
                # Process video
                print(f"    🔄 Processing: {video_file.name}")
                sequences = self.extract_features_from_video(video_file)
                
                if sequences is not None and len(sequences) > 0:
                    # Save to cache
                    try:
                        with open(cached_features_path, 'wb') as f:
                            pickle.dump(sequences, f)
                        
                        # Update processed files log
                        self.processed_files[file_key] = {
                            'hash': current_hash,
                            'gesture': gesture_name,
                            'sequences_count': len(sequences),
                            'processed_at': pd.Timestamp.now().isoformat()
                        }
                        
                        new_sequences.extend(sequences)
                        new_labels.extend([gesture_name] * len(sequences))
                        processed_count += 1
                        print(f"      📈 Generated {len(sequences)} sequences")
                    except Exception as e:
                        print(f"      ❌ Caching failed: {e}")
                else:
                    print(f"      ❌ Failed to process")
        
        print(f"\n📊 Processing Summary:")
        print(f"  🔄 Newly processed: {processed_count} videos")
        print(f"  💾 Loaded from cache: {cached_count} videos")
        print(f"  📈 Total sequences: {len(new_sequences)}")
        
        # Save updated processed files log
        self.save_processed_files()
        
        return new_sequences, new_labels
    
    def build_lstm_model(self, num_classes):
        """Build enhanced LSTM model"""
        model = keras.Sequential([
            # Input normalization
            keras.layers.BatchNormalization(input_shape=(self.sequence_length, self.feature_dim)),
            keras.layers.GaussianNoise(0.1),
            
            # LSTM layers
            keras.layers.LSTM(128, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            keras.layers.BatchNormalization(),
            keras.layers.LSTM(64, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            keras.layers.BatchNormalization(),
            keras.layers.LSTM(32, dropout=0.3, recurrent_dropout=0.3),
            
            # Dense layers
            keras.layers.Dense(64, activation='relu'),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dropout(0.2),
            
            # Output layer - handle single vs multi-class
            keras.layers.Dense(1 if num_classes == 1 else num_classes, 
                             activation='sigmoid' if num_classes == 1 else 'softmax')
        ])
        
        # Compile with advanced optimizer
        optimizer = keras.optimizers.Adam(
            learning_rate=0.001,
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-07,
            clipnorm=1.0
        )
        
        # Choose metrics and loss based on number of classes
        if num_classes == 1:
            # For single class, use binary classification
            metrics = ['accuracy']
            loss = 'binary_crossentropy'
        else:
            # For multiple classes, use categorical (one-hot) crossentropy
            metrics = ['accuracy']
            loss = 'categorical_crossentropy'
        
        model.compile(
            optimizer=optimizer,
            loss=loss,
            metrics=metrics
        )
        
        return model
    
    def backup_current_model(self):
        """Backup current model before training"""
        backup_timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        for file_path in ["simple_custom_lstm.h5", "simple_custom_labels.pkl", "simple_custom_mapping.json"]:
            if Path(file_path).exists():
                backup_path = self.models_backup_dir / f"{backup_timestamp}_{file_path}"
                Path(file_path).rename(backup_path)
                print(f"💾 Backed up: {file_path} -> {backup_path}")
    
    def train_model(self):
        """Train the LSTM model with incremental learning support"""
        print("🚀 Starting incremental training...")
        
        # Load and process videos
        sequences, labels = self.load_and_process_videos()
        
        if len(sequences) == 0:
            print("❌ No training data found!")
            return
        
        print(f"\n🔢 Training data shape: {np.array(sequences).shape}")
        
        # Encode labels
        unique_labels = sorted(list(set(labels)))
        self.label_encoder.fit(unique_labels)
        encoded_labels = self.label_encoder.transform(labels)
        
        num_classes = len(unique_labels)
        print(f"🏷️ Gestures: {unique_labels}")
        for i, gesture in enumerate(unique_labels):
            count = labels.count(gesture)
            print(f"  {gesture}: {count} sequences")
        
        # Convert to arrays
        X = np.array(sequences, dtype=np.float32)
        
        # Handle single vs multi-class labels
        if num_classes == 1:
            y = np.ones(len(sequences))  # Binary: all samples are positive for single class
        else:
            # Convert to categorical (one-hot encoding) for multi-class
            y = keras.utils.to_categorical(encoded_labels, num_classes=num_classes)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"🔀 Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")
        
        # Backup existing model
        self.backup_current_model()
        
        # Build model
        num_classes = len(unique_labels)
        model = self.build_lstm_model(num_classes)
        
        print(f"\n🏗️ Model architecture:")
        model.summary()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            ),
            keras.callbacks.ModelCheckpoint(
                'best_incremental_lstm.h5',
                save_best_only=True,
                monitor='val_accuracy',
                mode='max'
            )
        ]
        
        # Train
        print(f"\n🚀 Training model...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,
            batch_size=8,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        try:
            test_results = model.evaluate(X_test, y_test, verbose=0)
            test_accuracy = test_results[1] if len(test_results) > 1 else test_results[0]
            print(f"\n📊 Final test accuracy: {test_accuracy:.1%}")
        except Exception as e:
            print(f"⚠️ Evaluation error: {e}")
        
        # Save model and metadata
        model.save('simple_custom_lstm.h5')
        
        # Save label encoder
        import joblib
        joblib.dump(self.label_encoder, 'simple_custom_labels.pkl')
        
        # Save mapping
        gesture_mapping = {gesture: i for i, gesture in enumerate(unique_labels)}
        with open('simple_custom_mapping.json', 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        
        print(f"\n✅ Training complete!")
        print(f"📂 Model saved: simple_custom_lstm.h5")
        print(f"📂 Labels saved: simple_custom_labels.pkl") 
        print(f"📂 Mapping saved: simple_custom_mapping.json")
        print(f"💾 Cache directory: {self.cache_dir}")
        
        return model, history

def main():
    trainer = IncrementalLSTMTrainer()
    trainer.train_model()

if __name__ == "__main__":
    main()
