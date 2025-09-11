#!/usr/bin/env python3
"""
Simple Training Script for Small Datasets
Handles cases where you have limited training data and variable-length features
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

class SimpleTrainer:
    def __init__(self):
        self.base_path = Path(".")
        self.gesture_data_path = self.base_path / "gesture_data"
        self.classifier = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.gesture_mapping = {}
        
    def load_gesture_data(self):
        """Load all gesture data from CSV files with proper feature handling"""
        print("🔄 Loading gesture data...")
        
        all_data = []
        gesture_labels = []
        
        if not self.gesture_data_path.exists():
            print("❌ No gesture_data directory found!")
            return None, None
        
        csv_files = list(self.gesture_data_path.glob("*_landmarks.csv"))
        
        if not csv_files:
            print("❌ No landmark CSV files found in gesture_data/")
            return None, None
        
        for csv_file in csv_files:
            gesture_name = csv_file.stem.replace("_landmarks", "")
            
            print(f"📂 Loading {gesture_name} from {csv_file.name}")
            
            try:
                df = pd.read_csv(csv_file)
                valid_samples = 0
                
                for _, row in df.iterrows():
                    try:
                        # Parse landmarks JSON
                        landmarks_str = row['landmarks']
                        landmarks_data = json.loads(landmarks_str)
                        
                        # Convert to numpy array
                        landmarks_array = np.array(landmarks_data)
                        
                        # Remove zero padding at the end
                        non_zero_indices = np.nonzero(landmarks_array)[0]
                        if len(non_zero_indices) > 0:
                            last_nonzero = non_zero_indices[-1]
                            landmarks_clean = landmarks_array[:last_nonzero + 1]
                        else:
                            continue  # Skip if all zeros
                        
                        # Ensure minimum feature count
                        if len(landmarks_clean) >= 100:
                            # Standardize to fixed length (1500 features max)
                            max_features = 1500
                            if len(landmarks_clean) > max_features:
                                landmarks_clean = landmarks_clean[:max_features]
                            else:
                                # Pad with zeros if needed
                                padded = np.zeros(max_features)
                                padded[:len(landmarks_clean)] = landmarks_clean
                                landmarks_clean = padded
                            
                            all_data.append(landmarks_clean)
                            gesture_labels.append(gesture_name)
                            valid_samples += 1
                            
                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue
                
                print(f"✅ Loaded {valid_samples} valid frames for {gesture_name}")
                
            except Exception as e:
                print(f"❌ Error loading {csv_file}: {e}")
                continue
                
                # Add gesture labels
                for _, row in df.iterrows():
                    features = row.drop(['timeInSeconds', 'frameNumber']).values
                    all_data.append(features)
                    gesture_names.append(gesture_id)
                    
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
        joblib.dump(self.classifier, 'simple_rf_model.pkl')
        print("✅ Saved: simple_rf_model.pkl")
        
        # Save scaler
        joblib.dump(self.scaler, 'simple_scaler.pkl')
        print("✅ Saved: simple_scaler.pkl")
        
        # Save gesture mapping
        with open('simple_custom_mapping.json', 'w') as f:
            json.dump(self.gesture_mapping, f, indent=2)
        print("✅ Saved: simple_custom_mapping.json")
        
        # Save labels mapping (reverse mapping)
        reverse_mapping = {v: k for k, v in self.gesture_mapping.items()}
        joblib.dump(reverse_mapping, 'simple_custom_labels.pkl')
        print("✅ Saved: simple_custom_labels.pkl")

def main():
    print("🎯 Simple Custom Gesture Trainer")
    print("=" * 50)
    
    trainer = SimpleTrainer()
    
    # Load data
    X, y = trainer.load_gesture_data()
    if X is None:
        print("❌ No data to train on!")
        return
    
    print(f"📊 Dataset shape: {X.shape}")
    print(f"🎯 Gesture mapping: {trainer.gesture_mapping}")
    
    # Train
    accuracy = trainer.train_simple_classifier(X, y)
    
    # Save models
    trainer.save_models()
    
    print("\n🎉 Training completed!")
    print(f"📊 Final accuracy: {accuracy:.3f}")
    print("\n💡 Next steps:")
    print("   1. Copy model files to custom-server/")
    print("   2. Restart custom server")
    print("   3. Test your new gestures!")

if __name__ == "__main__":
    main()
