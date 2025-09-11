#!/usr/bin/env python3
"""
Simple Custom Gesture Trainer
Trains a RandomForest classifier for your custom gestures
"""
import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

class CustomGestureTrainer:
    def __init__(self):
        self.base_path = Path(".")
        self.gesture_data_path = self.base_path / "gesture_data"
        self.classifier = None
        self.scaler = None
        self.gesture_mapping = {}
        
    def load_gesture_data(self):
        """Load all gesture data from CSV files"""
        print("🔄 Loading gesture data...")
        
        all_data = []
        gesture_names = []
        
        if not self.gesture_data_path.exists():
            print("❌ No gesture_data directory found!")
            return None, None
        
        # Find all CSV files in gesture_data directory
        csv_files = list(self.gesture_data_path.glob("*_landmarks.csv"))
        
        if not csv_files:
            print("❌ No landmark CSV files found in gesture_data/")
            return None, None
        
        gesture_id = 0
        for csv_file in csv_files:
            # Extract gesture name from filename
            gesture_name = csv_file.stem.replace("_landmarks", "")
            self.gesture_mapping[gesture_name] = gesture_id
            
            print(f"📂 Loading {gesture_name} from {csv_file.name}")
            
            try:
                df = pd.read_csv(csv_file)
                sequences = self.process_gesture_data(df, gesture_name)
                
                for sequence in sequences:
                    features = self.extract_sequence_features(sequence)
                    if features is not None:
                        all_data.append(features)
                        gesture_names.append(gesture_id)
                
                print(f"✅ Loaded {len(sequences)} sequences for {gesture_name}")
                gesture_id += 1
                
            except Exception as e:
                print(f"❌ Error loading {csv_file}: {e}")
                continue
        
        if not all_data:
            print("❌ No valid data loaded!")
            return None, None
        
        print(f"📊 Total: {len(all_data)} samples, {len(self.gesture_mapping)} gestures")
        return np.array(all_data), np.array(gesture_names)
    
    def process_gesture_data(self, df, gesture_name):
        """Process CSV data into sequences"""
        sequences = []
        
        # Group by sequence_id if available, otherwise treat as one sequence
        if 'sequence_id' in df.columns:
            for seq_id in df['sequence_id'].unique():
                seq_data = df[df['sequence_id'] == seq_id]
                sequences.append(seq_data)
        else:
            sequences.append(df)
        
        return sequences
    
    def extract_sequence_features(self, sequence_data):
        """Extract features from a gesture sequence"""
        try:
            if 'landmarks' in sequence_data.columns:
                # Parse landmarks from string format
                landmarks_list = []
                for landmarks_str in sequence_data['landmarks']:
                    try:
                        # Handle different formats
                        if isinstance(landmarks_str, str):
                            import ast
                            landmarks = ast.literal_eval(landmarks_str)
                        else:
                            landmarks = landmarks_str
                        landmarks_list.append(landmarks)
                    except:
                        continue
                
                if not landmarks_list:
                    return None
                
                landmarks_array = np.array(landmarks_list)
            else:
                # Assume all columns except metadata are landmark coordinates
                coord_columns = [col for col in sequence_data.columns 
                               if col not in ['sequence_id', 'frame', 'sign']]
                landmarks_array = sequence_data[coord_columns].values
            
            if landmarks_array.size == 0:
                return None
            
            # Extract sequence-level features
            features = []
            
            # Statistical features
            features.extend([
                np.mean(landmarks_array),
                np.std(landmarks_array),
                np.min(landmarks_array),
                np.max(landmarks_array),
                np.median(landmarks_array)
            ])
            
            # Motion features
            if len(landmarks_array) > 1:
                diffs = np.diff(landmarks_array, axis=0)
                features.extend([
                    np.mean(np.abs(diffs)),
                    np.std(diffs),
                    np.max(np.abs(diffs))
                ])
            else:
                features.extend([0] * 3)
            
            # Hand movement features (assuming landmarks include hand data)
            if landmarks_array.shape[1] > 10:
                # Take a subset for hand analysis
                hand_subset = landmarks_array[:, :min(42, landmarks_array.shape[1])]
                
                features.extend([
                    np.mean(hand_subset[:, ::3]),  # X coordinates
                    np.std(hand_subset[:, ::3]),
                    np.mean(hand_subset[:, 1::3]),  # Y coordinates  
                    np.std(hand_subset[:, 1::3]),
                    np.ptp(hand_subset[:, ::3]),  # X range
                    np.ptp(hand_subset[:, 1::3])  # Y range
                ])
            else:
                features.extend([0] * 6)
            
            # Sample key frames
            sample_indices = [0, len(landmarks_array)//2, -1] if len(landmarks_array) > 2 else [0]
            
            for idx in sample_indices:
                if idx < len(landmarks_array):
                    sample_frame = landmarks_array[idx]
                    # Take first 20 coordinates
                    sample_coords = sample_frame[:20] if len(sample_frame) >= 20 else sample_frame
                    features.extend(sample_coords.tolist())
                    
                    # Pad if needed
                    if len(sample_coords) < 20:
                        features.extend([0] * (20 - len(sample_coords)))
            
            # Ensure we have exactly 3 sample frames
            while len(sample_indices) < 3:
                features.extend([0] * 20)
                sample_indices.append(-1)
            
            return np.array(features)
            
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return None
    
    def train_classifier(self, X, y):
        """Train the RandomForest classifier"""
        print("🚀 Training classifier...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train classifier
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Training completed!")
        print(f"📊 Accuracy: {accuracy:.3f}")
        print("\n📋 Classification Report:")
        
        # Create gesture name mapping for report
        gesture_names = list(self.gesture_mapping.keys())
        print(classification_report(y_test, y_pred, target_names=gesture_names))
        
        return accuracy
    
    def save_model(self):
        """Save the trained model and mappings"""
        print("💾 Saving model...")
        
        # Save classifier
        joblib.dump(self.classifier, "custom_gesture_classifier.pkl")
        
        # Save scaler
        joblib.dump(self.scaler, "custom_gesture_scaler.pkl")
        
        # Save mapping
        with open("custom_gesture_mapping.json", "w") as f:
            json.dump(self.gesture_mapping, f, indent=2)
        
        print("✅ Model saved successfully!")
        print(f"📁 Files created:")
        print(f"   - custom_gesture_classifier.pkl")
        print(f"   - custom_gesture_scaler.pkl") 
        print(f"   - custom_gesture_mapping.json")

def main():
    print("🎯 Custom Gesture Trainer")
    print("=" * 50)
    
    trainer = CustomGestureTrainer()
    
    # Load data
    X, y = trainer.load_gesture_data()
    
    if X is None or len(X) == 0:
        print("❌ No training data found!")
        print("\n💡 To add gesture data:")
        print("   1. Put CSV files in gesture_data/ directory")
        print("   2. Name files like: gesture_name_landmarks.csv")
        print("   3. Ensure landmarks column contains coordinate data")
        return
    
    print(f"\n📊 Dataset Info:")
    print(f"   - Samples: {len(X)}")
    print(f"   - Features: {X.shape[1]}")
    print(f"   - Gestures: {list(trainer.gesture_mapping.keys())}")
    
    # Train
    accuracy = trainer.train_classifier(X, y)
    
    if accuracy > 0.7:
        trainer.save_model()
        print(f"\n🎉 Training successful! Accuracy: {accuracy:.3f}")
        print("🚀 You can now use the trained model in the webapp!")
    else:
        print(f"\n⚠️  Low accuracy ({accuracy:.3f}). Consider:")
        print("   - Adding more training samples")
        print("   - Checking data quality")
        print("   - Recording more varied examples")

if __name__ == "__main__":
    main()
