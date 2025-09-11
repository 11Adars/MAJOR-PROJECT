#!/usr/bin/env python3
"""
Simple Advanced Training Script for Gesture Recognition
Works with the existing landmark CSV format
"""
import pandas as pd
import numpy as np
import ast
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
from pathlib import Path
import os

class SimpleGestureTrainer:
    """Simple trainer for gesture recognition with landmark data"""
    
    def __init__(self, data_folder="gesture_data", model_output_folder="models"):
        self.data_folder = Path(data_folder)
        self.model_output_folder = Path(model_output_folder)
        self.model_output_folder.mkdir(exist_ok=True)
        
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.model = None
        self.gesture_mapping = {}
        
    def load_and_parse_data(self):
        """Load CSV files and parse landmarks data"""
        print("📂 Loading gesture data...")
        
        all_data = []
        csv_files = list(self.data_folder.glob("*_landmarks.csv"))
        
        if not csv_files:
            raise ValueError(f"No landmark CSV files found in {self.data_folder}")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                print(f"✅ Loaded {csv_file.name}: {len(df)} samples")
                
                # Parse landmarks from string to list of numbers
                landmarks_data = []
                signs = []
                
                for _, row in df.iterrows():
                    try:
                        # Parse the landmarks string into a list of floats
                        landmarks_str = row['landmarks']
                        landmarks_list = ast.literal_eval(landmarks_str)
                        landmarks_data.append(landmarks_list)
                        signs.append(row['sign'])
                    except Exception as e:
                        print(f"⚠️ Error parsing row: {e}")
                        continue
                
                # Convert to DataFrame
                parsed_df = pd.DataFrame(landmarks_data)
                parsed_df['sign'] = signs
                all_data.append(parsed_df)
                
            except Exception as e:
                print(f"❌ Error loading {csv_file}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No data could be loaded successfully")
        
        # Combine all data
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"📊 Total combined data: {len(final_df)} samples")
        
        # Analyze gesture distribution
        gesture_counts = final_df['sign'].value_counts()
        print(f"\n📈 Gesture distribution:")
        for gesture, count in gesture_counts.items():
            print(f"   {gesture}: {count} samples")
        
        return final_df
    
    def prepare_features(self, df):
        """Prepare features and labels"""
        print("🔧 Preparing features...")
        
        # Separate features and labels
        feature_columns = [col for col in df.columns if col != 'sign']
        X = df[feature_columns].values
        y = df['sign'].values
        
        print(f"📊 Feature dimensions: {X.shape[1]} features")
        
        # Handle missing values
        if np.isnan(X).any():
            print("🔧 Filling missing values with zeros...")
            X = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Create gesture mapping
        self.gesture_mapping = {
            idx: label for idx, label in enumerate(self.label_encoder.classes_)
        }
        
        print(f"🎯 Gesture classes: {list(self.gesture_mapping.values())}")
        
        return X_scaled, y_encoded
    
    def train_model(self, X, y):
        """Train the RandomForest model"""
        print("🤖 Training RandomForest model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Training set: {X_train.shape[0]} samples")
        print(f"📊 Test set: {X_test.shape[0]} samples")
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n🎯 Model Performance:")
        print(f"Accuracy: {accuracy:.3f}")
        
        print(f"\n📊 Detailed Classification Report:")
        target_names = [self.gesture_mapping[i] for i in sorted(self.gesture_mapping.keys())]
        print(classification_report(y_test, y_pred, target_names=target_names))
        
        return accuracy
    
    def save_model(self, model_name="simple_gesture_classifier"):
        """Save the trained model and related files"""
        print(f"💾 Saving model as {model_name}...")
        
        # Save model
        model_path = self.model_output_folder / f"{model_name}.pkl"
        joblib.dump(self.model, model_path)
        
        # Save scaler
        scaler_path = self.model_output_folder / f"{model_name}_scaler.pkl"
        joblib.dump(self.scaler, scaler_path)
        
        # Save gesture mapping
        mapping_path = self.model_output_folder / f"{model_name}_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(self.gesture_mapping, f, indent=2)
        
        # Save label encoder
        encoder_path = self.model_output_folder / f"{model_name}_encoder.pkl"
        joblib.dump(self.label_encoder, encoder_path)
        
        print(f"✅ Model saved:")
        print(f"   Model: {model_path}")
        print(f"   Scaler: {scaler_path}")
        print(f"   Mapping: {mapping_path}")
        print(f"   Encoder: {encoder_path}")
    
    def train_complete_pipeline(self):
        """Run the complete training pipeline"""
        try:
            # Load data
            df = self.load_and_parse_data()
            
            # Prepare features
            X, y = self.prepare_features(df)
            
            # Train model
            accuracy = self.train_model(X, y)
            
            # Save model
            self.save_model()
            
            print(f"\n🎉 Training completed successfully!")
            print(f"Final accuracy: {accuracy:.3f}")
            
            return accuracy
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    print("🚀 Starting simple gesture recognition training...")
    print("=" * 60)
    
    trainer = SimpleGestureTrainer()
    accuracy = trainer.train_complete_pipeline()
    
    if accuracy:
        print(f"\n✅ Training successful! Final accuracy: {accuracy:.3f}")
    else:
        print(f"\n❌ Training failed!")

if __name__ == "__main__":
    main()
