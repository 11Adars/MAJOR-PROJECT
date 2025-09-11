#!/usr/bin/env python3
"""
Simple Custom Gesture Trainer
Trains a classifier for your custom gestures
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

class CustomGestureTrainer:
    def __init__(self):
        self.gesture_data_dir = Path("gesture_data")
        self.scaler = StandardScaler()
        
    def load_gesture_data(self):
        """Load all recorded gesture data"""
        print("📊 Loading gesture data...")
        
        gesture_files = list(self.gesture_data_dir.glob("*_landmarks.csv"))
        
        if not gesture_files:
            print("❌ No gesture data files found!")
            print("   Please record gestures first using: python record_new_gesture.py")
            return None, None, None
        
        all_data = []
        all_labels = []
        gesture_mapping = {}
        
        for i, file_path in enumerate(gesture_files):
            gesture_name = file_path.stem.replace("_landmarks", "")
            gesture_mapping[gesture_name] = i
            
            print(f"📁 Loading {gesture_name}...")
            
            try:
                df = pd.read_csv(file_path)
                
                # Group by sequence
                for sequence_id in df['sequence'].unique():
                    sequence_data = df[df['sequence'] == sequence_id].copy()
                    sequence_data = sequence_data.sort_values('frame')
                    
                    # Extract landmark features for this sequence
                    features = self.extract_sequence_features(sequence_data)
                    
                    if features is not None:
                        all_data.append(features)
                        all_labels.append(i)
                
                print(f"✅ Loaded {len(df['sequence'].unique())} sequences for {gesture_name}")
                
            except Exception as e:
                print(f"❌ Error loading {gesture_name}: {e}")
        
        if all_data:
            return np.array(all_data), np.array(all_labels), gesture_mapping
        else:
            return None, None, None
    
    def extract_sequence_features(self, sequence_data):
        """Extract features from a sequence of landmarks"""
        try:
            # Get landmark columns
            landmark_cols = [col for col in sequence_data.columns if 'landmark' in col]
            
            if not landmark_cols:
                return None
            
            # Extract landmark data
            landmarks = sequence_data[landmark_cols].values
            
            # Calculate features
            features = []
            
            # Statistical features
            features.extend([
                np.mean(landmarks),
                np.std(landmarks),
                np.min(landmarks),
                np.max(landmarks),
                np.median(landmarks)
            ])
            
            # Hand movement features (if hand landmarks exist)
            # Look for hand landmark patterns
            hand_x_cols = [col for col in landmark_cols if '_x' in col and ('landmark_4' in col or 'landmark_5' in col)]
            hand_y_cols = [col for col in landmark_cols if '_y' in col and ('landmark_4' in col or 'landmark_5' in col)]
            
            if hand_x_cols and hand_y_cols:
                hand_x = sequence_data[hand_x_cols[:2]].values.flatten()
                hand_y = sequence_data[hand_y_cols[:2]].values.flatten()
                
                # Hand movement statistics
                features.extend([
                    np.mean(hand_x),
                    np.std(hand_x),
                    np.mean(hand_y),
                    np.std(hand_y),
                    np.max(hand_x) - np.min(hand_x),  # X range
                    np.max(hand_y) - np.min(hand_y)   # Y range
                ])
            else:
                features.extend([0] * 6)
            
            # Frame-by-frame differences (motion)
            if len(landmarks) > 1:
                diffs = np.diff(landmarks, axis=0)
                features.extend([
                    np.mean(np.abs(diffs)),
                    np.std(diffs),
                    np.max(np.abs(diffs))
                ])
            else:
                features.extend([0] * 3)
            
            # Sample key landmark positions
            if len(landmarks) > 0:
                # Sample first, middle, and last frames
                sample_indices = [0, len(landmarks)//2, -1] if len(landmarks) > 2 else [0]
                
                for idx in sample_indices:
                    if idx < len(landmarks):
                        sample_frame = landmarks[idx]
                        # Take first 20 landmark coordinates
                        sample_landmarks = sample_frame[:20] if len(sample_frame) >= 20 else sample_frame
                        features.extend(sample_landmarks.tolist())
                        
                        # Pad if necessary
                        if len(sample_landmarks) < 20:
                            features.extend([0] * (20 - len(sample_landmarks)))
                
                # Pad if we have fewer than 3 sample frames
                while len(sample_indices) < 3:
                    features.extend([0] * 20)
                    sample_indices.append(-1)
            
            return np.array(features)
            
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return None
    
    def train_classifier(self, X, y, gesture_mapping):
        """Train the gesture classifier"""
        print("🔄 Training gesture classifier...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest classifier
        classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Training complete!")
        print(f"📊 Accuracy: {accuracy:.2%}")
        
        # Detailed report
        gesture_names = list(gesture_mapping.keys())
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=gesture_names))
        
        return classifier
    
    def save_model(self, classifier, gesture_mapping):
        """Save the trained model and mappings"""
        print("💾 Saving model...")
        
        # Save classifier
        joblib.dump(classifier, "custom_gesture_classifier.pkl")
        print("✅ Saved: custom_gesture_classifier.pkl")
        
        # Save scaler
        joblib.dump(self.scaler, "custom_gesture_scaler.pkl")
        print("✅ Saved: custom_gesture_scaler.pkl")
        
        # Save gesture mapping
        with open("custom_gesture_mapping.json", 'w') as f:
            json.dump(gesture_mapping, f, indent=2)
        print("✅ Saved: custom_gesture_mapping.json")
        
        print(f"\n🎯 Custom gestures trained: {list(gesture_mapping.keys())}")
    
    def train(self):
        """Main training function"""
        print("🎯 Custom Gesture Training")
        print("=" * 30)
        
        # Load data
        X, y, gesture_mapping = self.load_gesture_data()
        
        if X is None:
            return False
        
        print(f"📊 Loaded {len(X)} sequences for {len(gesture_mapping)} gestures")
        
        # Check minimum data requirements
        unique_labels, counts = np.unique(y, return_counts=True)
        print(f"📋 Data distribution:")
        for label, count in zip(unique_labels, counts):
            gesture_name = list(gesture_mapping.keys())[list(gesture_mapping.values()).index(label)]
            print(f"   {gesture_name}: {count} sequences")
        
        if len(X) < 10:
            print("⚠️  Warning: Very little training data. Record more sequences for better accuracy.")
        
        # Train classifier
        classifier = self.train_classifier(X, y, gesture_mapping)
        
        # Save model
        self.save_model(classifier, gesture_mapping)
        
        print("\n🚀 Training complete!")
        print("\n📋 Next steps:")
        print("1. Test your gestures in the web application")
        print("2. The system will now recognize your custom gestures!")
        
        return True

def main():
    trainer = CustomGestureTrainer()
    
    if not trainer.gesture_data_dir.exists():
        print("❌ gesture_data directory not found!")
        print("Please record gestures first using: python record_new_gesture.py")
        return
    
    success = trainer.train()
    
    if success:
        print("\n✅ Success! Your custom gestures are ready to use.")
    else:
        print("\n❌ Training failed. Please check your data and try again.")

if __name__ == "__main__":
    main()
