#!/usr/bin/env python3
"""
Video Data Training Script
Trains a gesture recognition model using CSV data extracted from videos
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
    """Train model using video-extracted landmark data"""
    print("🎬 Video Data Training System")
    print("=" * 50)
    
    # Check for video data
    video_data_folder = Path("gesture_data")
    if not video_data_folder.exists():
        print(f"❌ Video data folder not found: {video_data_folder}")
        print("💡 Run extract_video_landmarks.py first to generate CSV files")
        return
    
    # Load CSV files
    csv_files = list(video_data_folder.glob("*.csv"))
    if not csv_files:
        print(f"❌ No CSV files found in {video_data_folder}")
        print("💡 Run extract_video_landmarks.py first")
        return
    
    print(f"📂 Found {len(csv_files)} CSV files:")
    dataframes = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dataframes.append(df)
            print(f"✅ {csv_file.name}: {len(df)} frames")
        except Exception as e:
            print(f"❌ Error loading {csv_file.name}: {e}")
    
    if not dataframes:
        print("❌ No data loaded successfully!")
        return
    
    # Combine all data
    df = pd.concat(dataframes, ignore_index=True)
    print(f"\n📊 Total frames: {len(df)}")
    
    # Show gesture distribution
    print(f"\n📈 Gesture distribution:")
    gesture_counts = df['sign'].value_counts()
    for gesture, count in gesture_counts.items():
        print(f"   {gesture}: {count} frames")
    
    # Parse landmarks
    print(f"\n🔧 Parsing landmark data...")
    landmark_data = []
    failed_parses = 0
    
    for idx, row in df.iterrows():
        try:
            # Parse landmarks string to list
            landmarks_str = row['landmarks']
            landmarks = ast.literal_eval(landmarks_str)
            
            # Ensure consistent length (1659 features)
            if len(landmarks) > 1659:
                landmarks = landmarks[:1659]
            elif len(landmarks) < 1659:
                landmarks.extend([0.0] * (1659 - len(landmarks)))
            
            landmark_data.append(landmarks)
        except Exception as e:
            # If parsing fails, use zeros
            landmark_data.append([0.0] * 1659)
            failed_parses += 1
    
    print(f"✅ Parsed {len(landmark_data)} landmark sequences")
    if failed_parses > 0:
        print(f"⚠️  {failed_parses} failed parses (filled with zeros)")
    
    # Create feature matrix
    X = np.array(landmark_data)
    y = df['sign'].values
    
    print(f"📊 Feature matrix shape: {X.shape}")
    print(f"🎯 Gesture classes: {np.unique(y)}")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split data
    print(f"\n🔄 Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"📊 Training: {len(X_train)} frames")
    print(f"📊 Testing: {len(X_test)} frames")
    
    # Scale features
    print(f"\n📏 Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    print(f"\n🤖 Training RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
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
    print("-" * 50)
    report = classification_report(y_test_names, y_pred_names)
    print(report)
    
    # Save model
    models_folder = Path("models")
    models_folder.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"video_trained_model_{timestamp}"
    
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
    
    # Save training report
    report_path = models_folder / f"video_training_report_{timestamp}.txt"
    with open(report_path, 'w') as f:
        f.write("VIDEO DATA TRAINING REPORT\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total Frames: {len(df)}\n")
        f.write(f"Feature Dimensions: {X.shape[1]}\n")
        f.write(f"Training Time: {training_time:.2f}s\n")
        f.write(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)\n\n")
        f.write("Gesture Distribution:\n")
        for gesture, count in gesture_counts.items():
            f.write(f"  {gesture}: {count} frames\n")
        f.write(f"\nClassification Report:\n")
        f.write("-" * 40 + "\n")
        f.write(report)
    
    print(f"📊 Report saved: {report_path}")
    
    print(f"\n🎉 Video training completed successfully!")
    print(f"🚀 Model ready for deployment!")
    
    # Show next steps
    print(f"\n✅ Next steps:")
    print(f"   1. Test model: python test_trained_model.py")
    print(f"   2. Continue extraction: python extract_video_landmarks.py")
    print(f"   3. Deploy servers: start_servers.bat")

if __name__ == "__main__":
    main()
