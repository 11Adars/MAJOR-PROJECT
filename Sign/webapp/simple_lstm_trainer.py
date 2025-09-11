#!/usr/bin/env python3
"""
Simple LSTM Custom Gesture Trainer (No MediaPipe conflicts)
Uses OpenCV and basic feature extraction for compatibility
"""

import os
import cv2
import json
import numpy as np
import pandas as pd
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class SimpleLSTMTrainer:
    def __init__(self, custom_videos_folder="custom_videos"):
        self.custom_videos_folder = Path(custom_videos_folder)
        self.sequence_length = 30
        self.feature_dim = 200  # Increased feature dimensions
        
        self.sequences = []
        self.labels = []
        self.label_encoder = LabelEncoder()
        
    def extract_simple_features(self, frame):
        """Extract enhanced visual features without MediaPipe"""
        # Resize frame to standard size
        frame_resized = cv2.resize(frame, (128, 128))  # Increased resolution
        
        # Convert to multiple color spaces
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
        
        features = []
        
        # 1. Enhanced histogram features (multiple color channels)
        # Grayscale histogram
        hist_gray = cv2.calcHist([gray], [0], None, [32], [0, 256])
        features.extend(hist_gray.flatten())
        
        # HSV histograms
        hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [16], [0, 256])
        features.extend(hist_h.flatten())
        features.extend(hist_s.flatten())
        
        # 2. Multiple edge detection methods
        # Canny edges
        edges_canny = cv2.Canny(gray, 30, 100)
        edge_density_canny = np.sum(edges_canny > 0) / (128 * 128)
        features.append(edge_density_canny)
        
        # Sobel edges
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        edge_density_sobel = np.sum(sobel_magnitude > 50) / (128 * 128)
        features.append(edge_density_sobel)
        
        # 3. Enhanced intensity statistics
        features.extend([
            np.mean(gray), np.std(gray), np.min(gray), np.max(gray),
            np.median(gray), np.percentile(gray, 25), np.percentile(gray, 75),
            np.var(gray), np.sum(gray > 128) / (128*128)  # Brightness ratio
        ])
        
        # 4. Enhanced motion/gradient features
        features.extend([
            np.mean(np.abs(sobel_x)), np.mean(np.abs(sobel_y)),
            np.std(sobel_x), np.std(sobel_y),
            np.max(sobel_magnitude), np.mean(sobel_magnitude)
        ])
        
        # 5. Enhanced contour features
        contours, _ = cv2.findContours(edges_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # Largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            # Contour moments
            moments = cv2.moments(largest_contour)
            if moments['m00'] != 0:
                cx = moments['m10'] / moments['m00']
                cy = moments['m01'] / moments['m00']
            else:
                cx = cy = 64  # Center
            
            # Bounding rectangle
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = w / h if h > 0 else 1
            
            features.extend([
                area / (128*128), perimeter / (128*4),
                cx / 128, cy / 128, aspect_ratio,
                len(contours), w / 128, h / 128
            ])
        else:
            features.extend([0] * 8)
        
        # 6. Enhanced regional features (9 regions - 3x3 grid)
        h, w = gray.shape
        for i in range(3):
            for j in range(3):
                region = gray[i*h//3:(i+1)*h//3, j*w//3:(j+1)*w//3]
                if region.size > 0:
                    features.extend([
                        np.mean(region), np.std(region),
                        np.max(region) - np.min(region),  # Range
                        np.sum(region > np.mean(region)) / region.size  # Above-mean ratio
                    ])
                else:
                    features.extend([0, 0, 0, 0])
        
        # 7. Texture features (Local Binary Pattern approximation)
        # Simple texture analysis using standard deviation in small windows
        texture_features = []
        for window_size in [5, 10]:
            texture_map = np.zeros_like(gray, dtype=float)
            half_window = window_size // 2
            for i in range(half_window, gray.shape[0] - half_window):
                for j in range(half_window, gray.shape[1] - half_window):
                    window = gray[i-half_window:i+half_window+1, j-half_window:j+half_window+1]
                    texture_map[i, j] = np.std(window)
            
            texture_features.extend([
                np.mean(texture_map), np.std(texture_map), np.max(texture_map)
            ])
        
        features.extend(texture_features)
        
        # 8. Color distribution features
        for channel in range(3):  # B, G, R channels
            channel_data = frame_resized[:, :, channel].flatten()
            features.extend([
                np.mean(channel_data), np.std(channel_data),
                np.percentile(channel_data, 90) - np.percentile(channel_data, 10)
            ])
        
        # Ensure exactly 200 features (increased from 100)
        while len(features) < 200:
            features.append(0)
        
        return np.array(features[:200])
    
    def augment_sequence(self, sequence):
        """Apply aggressive data augmentation"""
        augmented = [sequence]  # Original
        
        # 1. Multiple noise levels
        for noise_level in [0.005, 0.01, 0.02]:
            noisy = sequence + np.random.normal(0, noise_level, sequence.shape)
            augmented.append(noisy)
        
        # 2. Multiple intensity scaling
        for scale in [0.8, 0.9, 1.1, 1.2]:
            scaled = sequence * scale
            augmented.append(scaled)
        
        # 3. Temporal augmentation - speed variations
        if len(sequence) >= 20:
            # Speed up (sample every 2nd frame, then interpolate)
            speed_indices = np.linspace(0, len(sequence)-1, len(sequence)//2, dtype=int)
            speed_up = sequence[speed_indices]
            # Repeat frames to get back to original length
            speed_up_full = np.repeat(speed_up, 2, axis=0)[:len(sequence)]
            augmented.append(speed_up_full)
            
            # Slow down (interpolate between frames)
            slow_indices = np.linspace(0, len(sequence)-1, min(len(sequence)*2, 40), dtype=int)
            slow_down = sequence[slow_indices[:len(sequence)]]
            augmented.append(slow_down)
        
        # 4. Feature shifting (simulate camera movement)
        for shift in [0.05, -0.05, 0.1, -0.1]:
            shifted = sequence + shift
            augmented.append(shifted)
        
        # 5. Random feature dropout (simulate occlusion)
        for dropout_rate in [0.1, 0.2]:
            dropout_mask = np.random.random(sequence.shape) > dropout_rate
            dropped = sequence * dropout_mask
            augmented.append(dropped)
        
        # 6. Smooth filtering (simulate motion blur)
        from scipy import ndimage
        try:
            smoothed = ndimage.gaussian_filter1d(sequence, sigma=0.5, axis=0)
            augmented.append(smoothed)
        except:
            pass  # Skip if scipy not available
        
        # 7. Elastic deformation in feature space
        for elastic_strength in [0.02, 0.05]:
            elastic = sequence.copy()
            for i in range(elastic.shape[1]):
                if np.random.random() > 0.5:
                    displacement = np.random.normal(0, elastic_strength, elastic.shape[0])
                    elastic[:, i] += displacement
            augmented.append(elastic)
        
        print(f"    📈 Augmented {len(augmented)} sequences from 1 original")
        return augmented
    
    def process_video(self, video_path, gesture_label):
        """Process video and extract sequences"""
        cap = cv2.VideoCapture(str(video_path))
        frames_features = []
        
        print(f"  📹 Processing: {video_path.name}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            features = self.extract_simple_features(frame)
            frames_features.append(features)
            
            if len(frames_features) >= self.sequence_length * 2:
                break
        
        cap.release()
        
        if len(frames_features) < 15:
            print(f"    ⚠️ Skipping {video_path.name}: Only {len(frames_features)} frames")
            return 0
        
        # Create sequences
        sequences_count = 0
        
        if len(frames_features) >= self.sequence_length:
            # Multiple overlapping sequences from one video (more aggressive sampling)
            step = max(1, len(frames_features) // 6)  # Get 6 sequences per video
            for start_idx in range(0, len(frames_features) - self.sequence_length + 1, step):
                sequence = np.array(frames_features[start_idx:start_idx + self.sequence_length])
                
                # Apply aggressive augmentation
                augmented_seqs = self.augment_sequence(sequence)
                for aug_seq in augmented_seqs:
                    self.sequences.append(aug_seq)
                    self.labels.append(gesture_label)
                    sequences_count += 1
                    
            # Also create sequences with different lengths (temporal variation)
            for seq_len in [20, 25, 35]:  # Different sequence lengths
                if len(frames_features) >= seq_len:
                    sequence = np.array(frames_features[:seq_len])
                    # Pad or truncate to standard length
                    if len(sequence) < self.sequence_length:
                        padding = np.repeat(sequence[-1:], self.sequence_length - len(sequence), axis=0)
                        sequence = np.vstack([sequence, padding])
                    else:
                        sequence = sequence[:self.sequence_length]
                    
                    # Light augmentation for temporal variants
                    for noise in [0.005, 0.01]:
                        noisy_seq = sequence + np.random.normal(0, noise, sequence.shape)
                        self.sequences.append(noisy_seq)
                        self.labels.append(gesture_label)
                        sequences_count += 1
        else:
            # Pad short sequences
            sequence = np.array(frames_features)
            padding_needed = self.sequence_length - len(sequence)
            padding = np.repeat(sequence[-1:], padding_needed, axis=0)
            sequence = np.vstack([sequence, padding])
            
            augmented_seqs = self.augment_sequence(sequence)
            for aug_seq in augmented_seqs:
                self.sequences.append(aug_seq)
                self.labels.append(gesture_label)
                sequences_count += 1
        
        print(f"    ✅ Generated {sequences_count} sequences")
        return sequences_count
    
    def load_custom_videos(self):
        """Load all custom videos"""
        if not self.custom_videos_folder.exists():
            print(f"❌ Custom videos folder not found: {self.custom_videos_folder}")
            return False
        
        gesture_folders = [d for d in self.custom_videos_folder.iterdir() if d.is_dir()]
        
        if not gesture_folders:
            print("❌ No gesture folders found!")
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
        """Build enhanced LSTM model with more capacity"""
        model = keras.Sequential([
            keras.layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            # Enhanced normalization and preprocessing
            keras.layers.BatchNormalization(),
            keras.layers.GaussianNoise(0.01),  # Add noise for regularization
            
            # Deeper LSTM architecture
            keras.layers.LSTM(128, return_sequences=True, dropout=0.3, recurrent_dropout=0.2),
            keras.layers.BatchNormalization(),
            keras.layers.LSTM(64, return_sequences=True, dropout=0.3, recurrent_dropout=0.2),
            keras.layers.BatchNormalization(),
            keras.layers.LSTM(32, dropout=0.3, recurrent_dropout=0.2),
            
            # Enhanced dense layers
            keras.layers.Dense(64, activation='relu'),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(num_classes, activation='softmax')
        ])
        
        # Enhanced optimizer with learning rate scheduling
        optimizer = keras.optimizers.Adam(
            learning_rate=0.001,
            beta_1=0.9,
            beta_2=0.999,
            clipnorm=1.0  # Gradient clipping
        )
        
        model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )
        
        return model
    
    def train_model(self):
        """Train the LSTM model"""
        if len(self.sequences) < 10:
            print("❌ Not enough sequences. Need at least 10.")
            return False
        
        X = np.array(self.sequences)
        y_encoded = self.label_encoder.fit_transform(self.labels)
        y_categorical = keras.utils.to_categorical(y_encoded)
        
        print(f"\n🔢 Training data shape: {X.shape}")
        print(f"🏷️ Number of classes: {len(self.label_encoder.classes_)}")
        print(f"📋 Classes: {list(self.label_encoder.classes_)}")
        
        # Class distribution
        unique, counts = np.unique(y_encoded, return_counts=True)
        for class_idx, count in zip(unique, counts):
            class_name = self.label_encoder.classes_[class_idx]
            print(f"   {class_name}: {count} sequences")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_categorical, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Build and train model
        num_classes = len(self.label_encoder.classes_)
        model = self.build_lstm_model(num_classes)
        
        print(f"\n🏗️ Model architecture:")
        model.summary()
        
        # Enhanced callbacks for better training
        callbacks = [
            keras.callbacks.EarlyStopping(
                patience=15, 
                restore_best_weights=True,
                monitor='val_accuracy',
                min_delta=0.001
            ),
            keras.callbacks.ReduceLROnPlateau(
                factor=0.5, 
                patience=8,
                monitor='val_loss',
                min_lr=1e-6
            ),
            keras.callbacks.ModelCheckpoint(
                'best_simple_lstm.h5',
                save_best_only=True,
                monitor='val_accuracy',
                mode='max'
            )
        ]
        
        print(f"\n🚀 Training enhanced model...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,  # More epochs
            batch_size=8,   # Smaller batch size for better gradients
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
        print(f"\n📊 Final Results:")
        print(f"✅ Test Accuracy: {test_accuracy:.1%}")
        
        # Save model and encoder
        model.save('simple_custom_lstm.h5')
        
        import joblib
        joblib.dump(self.label_encoder, 'simple_custom_labels.pkl')
        
        # Save mapping
        gesture_mapping = {gesture: idx for idx, gesture in enumerate(self.label_encoder.classes_)}
        with open('simple_custom_mapping.json', 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        
        print(f"\n💾 Saved files:")
        print(f"  • simple_custom_lstm.h5")
        print(f"  • simple_custom_labels.pkl")
        print(f"  • simple_custom_mapping.json")
        
        return True

def main():
    print("🎯 Simple LSTM Custom Gesture Trainer")
    print("=" * 50)
    
    trainer = SimpleLSTMTrainer()
    
    # Check for custom videos
    if not trainer.custom_videos_folder.exists():
        print(f"📁 Creating custom_videos folder...")
        trainer.custom_videos_folder.mkdir(exist_ok=True)
        
        for gesture in ['welcome', 'thank_you', 'hello']:
            (trainer.custom_videos_folder / gesture).mkdir(exist_ok=True)
        
        print(f"\n📋 Folder structure created!")
        print(f"📹 Use record_gestures.py to record videos or add manually.")
        return
    
    # Load and train
    if trainer.load_custom_videos():
        trainer.train_model()
        print(f"\n🎉 Training completed!")
    else:
        print(f"\n❌ No videos to train on!")

if __name__ == "__main__":
    main()
