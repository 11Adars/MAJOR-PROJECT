#!/usr/bin/env python3
"""
Fixed Training Script for Custom Gesture Data
Handles the actual CSV format from record_new_gesture.py
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class FixedTrainer:
    def __init__(self):
        self.base_path = Path(".")
        self.gesture_data_path = self.base_path / "gesture_data"
        self.classifier = None
        self.scaler = None
        self.gesture_mapping = {}
        
    def load_gesture_data(self):
        """Load gesture data from the actual CSV format"""
        print("🔄 Loading gesture data...")
        
        all_data = []
        gesture_names = []
        
        if not self.gesture_data_path.exists():
            print("❌ No gesture_data directory found!")
            return None, None
        
        csv_files = list(self.gesture_data_path.glob("*_landmarks.csv"))
        
        if not csv_files:
            print("❌ No landmark CSV files found in gesture_data/")
            return None, None
        
        gesture_id = 0
        for csv_file in csv_files:
            gesture_name = csv_file.stem.replace("_landmarks", "")
            self.gesture_mapping[gesture_name] = gesture_id
            
            print(f"📂 Loading {gesture_name} from {csv_file.name}")
            
            try:
                # Read CSV without headers since format is different
                df = pd.read_csv(csv_file, header=None)
                valid_samples = 0
                
                for _, row in df.iterrows():
                    row_data = row.values
                    
                    # Find the gesture label and landmarks JSON
                    for i, val in enumerate(row_data):
                        if isinstance(val, str) and val == gesture_name:
                            # Found gesture label, get landmarks from next column
                            if i + 1 < len(row_data):
                                try:
                                    landmarks_str = str(row_data[i + 1])
                                    landmarks_data = json.loads(landmarks_str)
                                    
                                    # Add to dataset
                                    all_data.append(landmarks_data)
                                    gesture_names.append(gesture_id)
                                    valid_samples += 1
                                    break
                                except json.JSONDecodeError:
                                    continue
                
                print(f"✅ Loaded {valid_samples} frames for {gesture_name}")
                gesture_id += 1
                
            except Exception as e:
                print(f"❌ Error loading {csv_file}: {e}")
                continue
        
        if not all_data:
            print("❌ No valid data loaded!")
            return None, None
            
        X = np.array(all_data)
        y = np.array(gesture_names)
        
        print(f"📊 Total: {len(X)} samples, {len(np.unique(y))} gestures")
        print(f"📊 Feature dimensions: {X.shape}")
        
        # Print gesture distribution
        unique_gestures, counts = np.unique(y, return_counts=True)
        for gesture_id, count in zip(unique_gestures, counts):
            gesture_name = [k for k, v in self.gesture_mapping.items() if v == gesture_id][0]
            print(f"📊 {gesture_name}: {count} samples")
        
        return X, y
    
    def train_simple_classifier(self, X, y):
        """Train without train/test split for small datasets"""
        print("🚀 Training simple classifier...")
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train classifier on all data
        self.classifier = RandomForestClassifier(
            n_estimators=50,
            random_state=42,
            max_depth=10
        )
        
        self.classifier.fit(X_scaled, y)
        
        # Calculate training accuracy
        train_accuracy = self.classifier.score(X_scaled, y)
        print(f"✅ Training accuracy: {train_accuracy:.3f}")
        
        return train_accuracy
    
    def save_models(self):
        """Save the trained models"""
        print("💾 Saving models...")
        
        # Save classifier
        classifier_path = self.base_path / "custom_gesture_classifier.pkl"
        joblib.dump(self.classifier, classifier_path)
        print(f"✅ Classifier saved to {classifier_path}")
        
        # Save scaler
        scaler_path = self.base_path / "custom_gesture_scaler.pkl"
        joblib.dump(self.scaler, scaler_path)
        print(f"✅ Scaler saved to {scaler_path}")
        
        # Save gesture mapping
        mapping_path = self.base_path / "custom_gesture_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(self.gesture_mapping, f, indent=2)
        print(f"✅ Gesture mapping saved to {mapping_path}")
    
    def run_training(self):
        """Main training pipeline"""
        print("🎯 Starting Custom Gesture Training")
        print("=" * 50)
        
        # Load data
        X, y = self.load_gesture_data()
        if X is None:
            return False
        
        # Check if we have enough data
        unique_gestures = np.unique(y)
        if len(unique_gestures) < 2:
            print("❌ Need at least 2 different gestures to train!")
            return False
        
        # Train classifier
        accuracy = self.train_simple_classifier(X, y)
        
        # Save models
        self.save_models()
        
        print("=" * 50)
        print("🎉 Training completed successfully!")
        print(f"📊 Final accuracy: {accuracy:.3f}")
        print("💡 Models are ready for use in the custom server!")
        
        return True

def main():
    trainer = FixedTrainer()
    success = trainer.run_training()
    
    if success:
        print("\n🚀 You can now use the trained models in your custom gesture server!")
    else:
        print("\n❌ Training failed. Please check your gesture data.")

if __name__ == "__main__":
    main()
