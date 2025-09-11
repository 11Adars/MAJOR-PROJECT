#!/usr/bin/env python3
"""
Fixed Advanced Training Script for Video-Based Training
Handles both original gesture_data and video-processed data
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import json
from pathlib import Path
import time
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
import ast
warnings.filterwarnings('ignore')

class FixedAdvancedGestureTrainer:
    """Fixed Advanced trainer for gesture recognition with video and landmark data"""
    
    def __init__(self, data_folder="gesture_data", model_output_folder="models"):
        # Check multiple possible data folders
        possible_folders = [
            data_folder,
            "your_videos_gesture_data", 
            "gesture_data",
            "your_videos_processed"
        ]
        
        self.data_folder = None
        for folder in possible_folders:
            folder_path = Path(folder)
            if folder_path.exists() and list(folder_path.glob("*.csv")):
                self.data_folder = folder_path
                print(f"📂 Using data folder: {self.data_folder}")
                break
        
        if not self.data_folder:
            # Use default
            self.data_folder = Path(data_folder)
        
        self.model_output_folder = Path(model_output_folder)
        self.model_output_folder.mkdir(exist_ok=True)
        
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        
        # Model configurations (simplified for reliability)
        self.models = {
            'RandomForest': {
                'model': RandomForestClassifier(random_state=42, n_jobs=-1),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2]
                }
            },
            'GradientBoosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'max_depth': [5, 10],
                    'learning_rate': [0.01, 0.1, 0.2]
                }
            }
        }
    
    def load_data(self, csv_file=None):
        """Load and prepare data from CSV files with landmark parsing"""
        print("📂 Loading gesture data...")
        
        if csv_file:
            # Load specific CSV file
            csv_path = Path(csv_file)
            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded data from {csv_path.name}: {len(df)} samples")
        else:
            # Load all CSV files in the data folder
            csv_files = list(self.data_folder.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {self.data_folder}")
            
            dataframes = []
            for csv_file in csv_files:
                try:
                    df_temp = pd.read_csv(csv_file)
                    dataframes.append(df_temp)
                    print(f"✅ Loaded {csv_file.name}: {len(df_temp)} samples")
                except Exception as e:
                    print(f"❌ Error loading {csv_file.name}: {e}")
            
            if not dataframes:
                raise ValueError("No data loaded successfully")
            
            df = pd.concat(dataframes, ignore_index=True)
            print(f"📊 Total combined data: {len(df)} samples")
        
        # Display gesture distribution
        if 'sign' in df.columns:
            gesture_col = 'sign'
        elif 'gesture' in df.columns:
            gesture_col = 'gesture'
        else:
            raise ValueError("No gesture column found (expected 'sign' or 'gesture')")
        
        print(f"\n📈 Gesture distribution:")
        gesture_counts = df[gesture_col].value_counts()
        for gesture, count in gesture_counts.items():
            print(f"   {gesture}: {count} samples")
        
        return df
    
    def parse_landmarks_string(self, landmarks_str):
        """Parse landmarks from string format to numeric array"""
        if pd.isna(landmarks_str):
            return [0.0] * 1659  # Default MediaPipe landmark count
        
        try:
            # Handle different string formats
            if isinstance(landmarks_str, str):
                # Try to parse as literal
                landmarks_list = ast.literal_eval(landmarks_str)
                return landmarks_list
            elif isinstance(landmarks_str, (list, np.ndarray)):
                return list(landmarks_str)
            else:
                return [0.0] * 1659
        except:
            # If parsing fails, return zeros
            return [0.0] * 1659
    
    def prepare_features(self, df):
        """Prepare features from the dataframe with proper landmark parsing"""
        print("🔧 Preparing features...")
        
        # Determine gesture column
        if 'sign' in df.columns:
            gesture_col = 'sign'
        elif 'gesture' in df.columns:
            gesture_col = 'gesture'
        else:
            raise ValueError("No gesture column found")
        
        # Check if landmarks need parsing
        if 'landmarks' in df.columns:
            print("🔍 Parsing landmarks from string format...")
            # Parse landmarks from string format
            landmark_data = []
            for idx, row in df.iterrows():
                parsed_landmarks = self.parse_landmarks_string(row['landmarks'])
                landmark_data.append(parsed_landmarks)
            
            # Create feature matrix from parsed landmarks
            X = np.array(landmark_data)
            y = df[gesture_col].values
            
            print(f"📊 Feature dimensions: {X.shape[1]} features")
            
        else:
            # Use existing numeric columns as features
            metadata_cols = [gesture_col, 'frame', 'video_source', 'sequence_id', 'Unnamed: 0']
            feature_cols = [col for col in df.columns if col not in metadata_cols]
            
            if not feature_cols:
                raise ValueError("No feature columns found in the data")
            
            print(f"📊 Feature dimensions: {len(feature_cols)} features")
            
            X = df[feature_cols].values
            y = df[gesture_col].values
        
        # Handle missing values
        if np.isnan(X).any():
            print("🔧 Filling missing values with zeros...")
            X = np.nan_to_num(X, nan=0.0)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Create gesture mapping
        self.gesture_mapping = {
            idx: label for idx, label in enumerate(self.label_encoder.classes_)
        }
        
        print(f"🎯 Gesture classes: {list(self.gesture_mapping.values())}")
        
        return X, y_encoded
    
    def train_model(self, model_name, model_config, X_train, X_test, y_train, y_test):
        """Train a single model with hyperparameter tuning"""
        print(f"\n🚀 Training {model_name}...")
        start_time = time.time()
        
        # Perform randomized search
        random_search = RandomizedSearchCV(
            model_config['model'], 
            model_config['params'],
            n_iter=10,  # Reduced for faster training
            cv=3,       # Reduced for faster training
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        
        random_search.fit(X_train, y_train)
        
        # Get best model
        best_model = random_search.best_estimator_
        
        # Predictions
        y_pred = best_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        training_time = time.time() - start_time
        
        print(f"✅ {model_name} completed in {training_time:.2f}s")
        print(f"📊 Best parameters: {random_search.best_params_}")
        print(f"🎯 Accuracy: {accuracy:.4f}")
        
        return {
            'model': best_model,
            'accuracy': accuracy,
            'best_params': random_search.best_params_,
            'training_time': training_time,
            'predictions': y_pred
        }
    
    def train_complete_pipeline(self, test_size=0.2, random_state=42):
        """Train complete pipeline with multiple models"""
        print("🚀 Starting complete training pipeline...")
        print("=" * 60)
        
        # Load data
        df = self.load_data()
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Split data
        print(f"\n🔄 Splitting data (test_size={test_size})...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"📊 Training samples: {len(X_train)}")
        print(f"📊 Testing samples: {len(X_test)}")
        
        # Scale features
        print("📏 Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        results = {}
        for model_name, model_config in self.models.items():
            try:
                result = self.train_model(
                    model_name, model_config, 
                    X_train_scaled, X_test_scaled, 
                    y_train, y_test
                )
                results[model_name] = result
            except Exception as e:
                print(f"❌ Error training {model_name}: {e}")
                continue
        
        if not results:
            raise ValueError("No models trained successfully")
        
        # Find best model
        best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        best_result = results[best_model_name]
        
        print(f"\n🏆 Best model: {best_model_name}")
        print(f"🎯 Best accuracy: {best_result['accuracy']:.4f}")
        
        # Save best model
        self.save_models(best_result['model'], best_model_name)
        
        # Generate detailed report
        self.generate_report(results, y_test, best_model_name)
        
        return results
    
    def save_models(self, model, model_name):
        """Save the trained model and related components"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"advanced_{model_name.lower()}_{timestamp}"
        
        # Save model
        model_path = self.model_output_folder / f"{base_name}.pkl"
        joblib.dump(model, model_path)
        print(f"💾 Model saved: {model_path}")
        
        # Save scaler
        scaler_path = self.model_output_folder / f"{base_name}_scaler.pkl"
        joblib.dump(self.scaler, scaler_path)
        print(f"💾 Scaler saved: {scaler_path}")
        
        # Save label encoder
        encoder_path = self.model_output_folder / f"{base_name}_encoder.pkl"
        joblib.dump(self.label_encoder, encoder_path)
        print(f"💾 Encoder saved: {encoder_path}")
        
        # Save gesture mapping
        mapping_path = self.model_output_folder / f"{base_name}_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(self.gesture_mapping, f, indent=2)
        print(f"💾 Mapping saved: {mapping_path}")
    
    def generate_report(self, results, y_test, best_model_name):
        """Generate comprehensive training report"""
        print("\n" + "=" * 60)
        print("📊 TRAINING SUMMARY REPORT")
        print("=" * 60)
        
        for model_name, result in results.items():
            print(f"\n🤖 {model_name}:")
            print(f"   Accuracy: {result['accuracy']:.4f}")
            print(f"   Training time: {result['training_time']:.2f}s")
            
            if model_name == best_model_name:
                print("   🏆 BEST MODEL")
        
        # Detailed classification report for best model
        best_predictions = results[best_model_name]['predictions']
        
        print(f"\n📈 Detailed Classification Report ({best_model_name}):")
        print("-" * 50)
        
        # Convert encoded labels back to original names
        y_test_names = self.label_encoder.inverse_transform(y_test)
        y_pred_names = self.label_encoder.inverse_transform(best_predictions)
        
        report = classification_report(y_test_names, y_pred_names)
        print(report)
        
        # Save report to file
        report_path = self.model_output_folder / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write("ADVANCED TRAINING REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            for model_name, result in results.items():
                f.write(f"{model_name}:\n")
                f.write(f"  Accuracy: {result['accuracy']:.4f}\n")
                f.write(f"  Training time: {result['training_time']:.2f}s\n")
                if model_name == best_model_name:
                    f.write("  *** BEST MODEL ***\n")
                f.write("\n")
            
            f.write(f"\nDetailed Classification Report ({best_model_name}):\n")
            f.write("-" * 50 + "\n")
            f.write(report)
        
        print(f"💾 Report saved: {report_path}")

def main():
    """Main training function"""
    try:
        trainer = FixedAdvancedGestureTrainer()
        results = trainer.train_complete_pipeline()
        
        print("\n🎉 Training completed successfully!")
        print("🚀 Ready for deployment!")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
