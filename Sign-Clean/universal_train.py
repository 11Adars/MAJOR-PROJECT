#!/usr/bin/env python3
"""
Universal Training Script - Works with any data format
Automatically detects data format and trains the best model
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
from pathlib import Path
import time
from datetime import datetime
import ast
import warnings
warnings.filterwarnings('ignore')

def main():
    """Universal training that works with any data format"""
    print("🚀 Universal Gesture Training System")
    print("=" * 50)
    
    # Try different data folders
    data_folders = ["gesture_data", "your_videos_gesture_data"]
    data_folder = None
    
    for folder in data_folders:
        folder_path = Path(folder)
        if folder_path.exists() and list(folder_path.glob("*.csv")):
            data_folder = folder_path
            print(f"✅ Using data folder: {data_folder}")
            break
    
    if not data_folder:
        print("❌ No CSV data found in any folder!")
        print("💡 Recommendation: Use the working simple_advanced_train.py")
        return
    
    # Load data
    print("\n📂 Loading data...")
    csv_files = list(data_folder.glob("*.csv"))
    dataframes = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dataframes.append(df)
            print(f"✅ {csv_file.name}: {len(df)} samples")
        except Exception as e:
            print(f"❌ Error loading {csv_file.name}: {e}")
    
    if not dataframes:
        print("❌ No data loaded successfully!")
        print("💡 Recommendation: Use simple_advanced_train.py for the original data")
        return
    
    # Combine data
    df = pd.concat(dataframes, ignore_index=True)
    print(f"📊 Total samples: {len(df)}")
    
    # Detect data format and prepare features
    gesture_col = None
    if 'sign' in df.columns:
        gesture_col = 'sign'
    elif 'gesture' in df.columns:
        gesture_col = 'gesture'
    else:
        print("❌ No gesture column found!")
        return
    
    print(f"🎯 Using gesture column: {gesture_col}")
    
    # Check if we have a landmarks column (from video processing)
    if 'landmarks' in df.columns:
        print("🔍 Video processing format detected - parsing landmarks...")
        try:
            # Parse landmarks
            landmark_data = []
            for idx, row in df.iterrows():
                if pd.isna(row['landmarks']):
                    landmarks = [0.0] * 1659
                else:
                    try:
                        landmarks = ast.literal_eval(str(row['landmarks']))
                    except:
                        landmarks = [0.0] * 1659
                landmark_data.append(landmarks)
            
            X = np.array(landmark_data)
            y = df[gesture_col].values
            
        except Exception as e:
            print(f"❌ Error parsing landmarks: {e}")
            print("💡 Falling back to simple_advanced_train.py method...")
            return
    
    else:
        print("📊 Original format detected - using numeric columns...")
        # Use existing numeric columns
        exclude_cols = [gesture_col, 'frame', 'sequence_id', 'video_source', 'Unnamed: 0']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not feature_cols:
            print("❌ No feature columns found!")
            return
        
        print(f"📈 Using {len(feature_cols)} feature columns")
        X = df[feature_cols].values
        y = df[gesture_col].values
    
    # Handle missing values
    if np.isnan(X).any():
        print("🔧 Cleaning missing values...")
        X = np.nan_to_num(X, nan=0.0)
    
    print(f"✅ Feature matrix shape: {X.shape}")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Print class distribution
    print(f"\n📈 Gesture distribution:")
    unique, counts = np.unique(y, return_counts=True)
    for gesture, count in zip(unique, counts):
        print(f"   {gesture}: {count} samples")
    
    # Split data
    print(f"\n🔄 Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"📊 Training: {len(X_train)} samples")
    print(f"📊 Testing: {len(X_test)} samples")
    
    # Scale features
    print("📏 Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    print("\n🤖 Training RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        random_state=42,
        n_jobs=-1
    )
    
    start_time = time.time()
    model.fit(X_train_scaled, y_train)
    training_time = time.time() - start_time
    
    # Test model
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✅ Training completed in {training_time:.2f}s")
    print(f"🎯 Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Detailed report
    y_test_names = label_encoder.inverse_transform(y_test)
    y_pred_names = label_encoder.inverse_transform(y_pred)
    
    print(f"\n📈 Classification Report:")
    print("-" * 40)
    report = classification_report(y_test_names, y_pred_names)
    print(report)
    
    # Save model
    models_folder = Path("models")
    models_folder.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"universal_model_{timestamp}"
    
    # Save all components
    model_path = models_folder / f"{base_name}.pkl"
    scaler_path = models_folder / f"{base_name}_scaler.pkl"
    encoder_path = models_folder / f"{base_name}_encoder.pkl"
    mapping_path = models_folder / f"{base_name}_mapping.json"
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(label_encoder, encoder_path)
    
    # Create gesture mapping
    gesture_mapping = {
        idx: label for idx, label in enumerate(label_encoder.classes_)
    }
    
    with open(mapping_path, 'w') as f:
        json.dump(gesture_mapping, f, indent=2)
    
    print(f"\n💾 Model saved:")
    print(f"   📄 Model: {model_path}")
    print(f"   📄 Scaler: {scaler_path}")
    print(f"   📄 Encoder: {encoder_path}")
    print(f"   📄 Mapping: {mapping_path}")
    
    print(f"\n🎉 Training completed successfully!")
    print(f"🚀 Model ready for deployment!")
    
    # Save training report
    report_path = models_folder / f"training_report_{timestamp}.txt"
    with open(report_path, 'w') as f:
        f.write("UNIVERSAL TRAINING REPORT\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Data Format: {'Video Processing' if 'landmarks' in df.columns else 'Original'}\n")
        f.write(f"Total Samples: {len(df)}\n")
        f.write(f"Feature Dimensions: {X.shape[1]}\n")
        f.write(f"Training Time: {training_time:.2f}s\n")
        f.write(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)\n\n")
        f.write("Gesture Distribution:\n")
        for gesture, count in zip(unique, counts):
            f.write(f"  {gesture}: {count} samples\n")
        f.write(f"\nClassification Report:\n")
        f.write("-" * 40 + "\n")
        f.write(report)
    
    print(f"📊 Report saved: {report_path}")

if __name__ == "__main__":
    main()
