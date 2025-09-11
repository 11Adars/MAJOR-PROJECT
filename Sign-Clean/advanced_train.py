#!/usr/bin/env python3
"""
Advanced Training Script for Augmented Video Data
Handles large datasets with augmented videos and provides better model performance
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
warnings.filterwarnings('ignore')

class AdvancedGestureTrainer:
    """Advanced trainer for gesture recognition with augmented data"""
    
    def __init__(self, data_folder="gesture_data", model_output_folder="models"):
        self.data_folder = Path(data_folder)
        self.model_output_folder = Path(model_output_folder)
        self.model_output_folder.mkdir(exist_ok=True)
        
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        
        # Model configurations
        self.models = {
            'RandomForest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            },
            'GradientBoosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.05, 0.1, 0.15],
                    'max_depth': [3, 5, 7]
                }
            },
            'SVM': {
                'model': SVC(random_state=42, probability=True),
                'params': {
                    'C': [1, 10, 100],
                    'gamma': ['scale', 'auto'],
                    'kernel': ['rbf', 'poly']
                }
            },
            'NeuralNetwork': {
                'model': MLPClassifier(random_state=42, max_iter=1000),
                'params': {
                    'hidden_layer_sizes': [(100,), (200,), (100, 50)],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate': ['constant', 'adaptive']
                }
            }
        }
    
    def load_data(self, csv_file=None):
        """Load and prepare data from CSV files"""
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
                raise ValueError("No valid CSV files could be loaded")
            
            df = pd.concat(dataframes, ignore_index=True)
            print(f"📊 Total combined data: {len(df)} samples")
        
        # Analyze data
        gesture_counts = df['sign'].value_counts()
        print(f"\n📈 Gesture distribution:")
        for gesture, count in gesture_counts.items():
            print(f"   {gesture}: {count} samples")
        
        # Check for class imbalance
        min_samples = gesture_counts.min()
        max_samples = gesture_counts.max()
        imbalance_ratio = max_samples / min_samples
        
        if imbalance_ratio > 3:
            print(f"⚠️  Warning: Class imbalance detected (ratio: {imbalance_ratio:.1f})")
            print("   Consider collecting more data for underrepresented gestures")
        
        self.raw_data = df
        return df
    
    def prepare_features(self, df):
        """Prepare feature matrix and labels"""
        print("🔧 Preparing features...")
        
        # Get feature columns (exclude metadata columns)
        metadata_cols = ['sign', 'frame', 'video_source', 'sequence_id']
        self.feature_columns = [col for col in df.columns if col not in metadata_cols]
        
        print(f"📊 Feature dimensions: {len(self.feature_columns)} features")
        
        # Prepare feature matrix
        X = df[self.feature_columns].values
        y = df['sign'].values
        
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
        
        print(f"✅ Prepared {X.shape[0]} samples with {X.shape[1]} features")
        print(f"🎯 Gesture classes: {list(self.gesture_mapping.values())}")
        
        return X, y_encoded
    
    def create_balanced_dataset(self, X, y, method='undersample'):
        """Create balanced dataset"""
        print(f"⚖️  Balancing dataset using {method}...")
        
        from collections import Counter
        original_distribution = Counter(y)
        print(f"Original distribution: {dict(original_distribution)}")
        
        if method == 'undersample':
            # Undersample to match smallest class
            min_samples = min(original_distribution.values())
            
            balanced_indices = []
            for class_idx in np.unique(y):
                class_indices = np.where(y == class_idx)[0]
                selected_indices = np.random.choice(class_indices, min_samples, replace=False)
                balanced_indices.extend(selected_indices)
            
            balanced_indices = np.array(balanced_indices)
            np.random.shuffle(balanced_indices)
            
            X_balanced = X[balanced_indices]
            y_balanced = y[balanced_indices]
            
        elif method == 'oversample':
            # Oversample to match largest class (using SMOTE if available)
            try:
                from imblearn.over_sampling import SMOTE
                smote = SMOTE(random_state=42)
                X_balanced, y_balanced = smote.fit_resample(X, y)
                print("✅ Applied SMOTE for oversampling")
            except ImportError:
                print("⚠️  SMOTE not available, using simple oversampling")
                max_samples = max(original_distribution.values())
                
                balanced_indices = []
                for class_idx in np.unique(y):
                    class_indices = np.where(y == class_idx)[0]
                    if len(class_indices) < max_samples:
                        # Oversample with replacement
                        selected_indices = np.random.choice(class_indices, max_samples, replace=True)
                    else:
                        selected_indices = class_indices
                    balanced_indices.extend(selected_indices)
                
                balanced_indices = np.array(balanced_indices)
                np.random.shuffle(balanced_indices)
                
                X_balanced = X[balanced_indices]
                y_balanced = y[balanced_indices]
        else:
            return X, y
        
        balanced_distribution = Counter(y_balanced)
        print(f"Balanced distribution: {dict(balanced_distribution)}")
        print(f"✅ Balanced dataset: {X_balanced.shape[0]} samples")
        
        return X_balanced, y_balanced
    
    def train_and_evaluate_models(self, X, y, balance_data=True, use_cross_validation=True):
        """Train and evaluate multiple models"""
        print("\n🤖 Training and evaluating models...")
        
        # Balance dataset if requested
        if balance_data:
            X, y = self.create_balanced_dataset(X, y, method='undersample')
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        print("📏 Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {}
        best_model = None
        best_score = 0
        
        for model_name, model_config in self.models.items():
            print(f"\n🔄 Training {model_name}...")
            start_time = time.time()
            
            try:
                # Hyperparameter tuning with RandomizedSearchCV
                random_search = RandomizedSearchCV(
                    model_config['model'],
                    model_config['params'],
                    n_iter=20,
                    cv=3,
                    random_state=42,
                    n_jobs=-1,
                    scoring='accuracy'
                )
                
                random_search.fit(X_train_scaled, y_train)
                best_model_instance = random_search.best_estimator_
                
                # Predictions
                y_pred = best_model_instance.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                # Cross-validation if requested
                if use_cross_validation and model_name != 'SVM':  # SVM can be slow
                    cv_scores = cross_val_score(best_model_instance, X_train_scaled, y_train, cv=5)
                    cv_mean = cv_scores.mean()
                    cv_std = cv_scores.std()
                else:
                    cv_mean = cv_std = None
                
                training_time = time.time() - start_time
                
                results[model_name] = {
                    'model': best_model_instance,
                    'best_params': random_search.best_params_,
                    'test_accuracy': accuracy,
                    'cv_mean': cv_mean,
                    'cv_std': cv_std,
                    'training_time': training_time,
                    'y_pred': y_pred
                }
                
                print(f"✅ {model_name} - Test Accuracy: {accuracy:.4f}")
                if cv_mean is not None:
                    print(f"   CV Accuracy: {cv_mean:.4f} ± {cv_std:.4f}")
                print(f"   Training time: {training_time:.2f}s")
                print(f"   Best params: {random_search.best_params_}")
                
                # Track best model
                if accuracy > best_score:
                    best_score = accuracy
                    best_model = (model_name, best_model_instance)
                
            except Exception as e:
                print(f"❌ Error training {model_name}: {e}")
                continue
        
        # Print comparison
        print(f"\n📊 Model Comparison:")
        print("-" * 80)
        print(f"{'Model':<15} {'Test Acc':<10} {'CV Acc':<15} {'Time (s)':<10}")
        print("-" * 80)
        
        for name, result in results.items():
            cv_str = f"{result['cv_mean']:.4f}±{result['cv_std']:.4f}" if result['cv_mean'] else "N/A"
            print(f"{name:<15} {result['test_accuracy']:<10.4f} {cv_str:<15} {result['training_time']:<10.1f}")
        
        if best_model:
            model_name, model_instance = best_model
            print(f"\n🏆 Best model: {model_name} (Accuracy: {best_score:.4f})")
            
            # Detailed evaluation of best model
            self._detailed_evaluation(model_instance, X_test_scaled, y_test, model_name)
            
            return model_instance, results, (X_test_scaled, y_test)
        else:
            raise ValueError("No models were successfully trained")
    
    def _detailed_evaluation(self, model, X_test, y_test, model_name):
        """Detailed evaluation of the best model"""
        print(f"\n🔍 Detailed evaluation of {model_name}:")
        
        y_pred = model.predict(X_test)
        
        # Classification report
        report = classification_report(y_test, y_pred, 
                                     target_names=self.label_encoder.classes_,
                                     output_dict=True)
        
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Plot confusion matrix
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=self.label_encoder.classes_,
                   yticklabels=self.label_encoder.classes_)
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        # Save plot
        plot_path = self.model_output_folder / f'confusion_matrix_{model_name.lower()}.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"💾 Confusion matrix saved to: {plot_path}")
        plt.close()
        
        # Per-class accuracy
        print(f"\n🎯 Per-class accuracy:")
        for i, class_name in enumerate(self.label_encoder.classes_):
            class_accuracy = report[class_name]['precision']
            print(f"   {class_name}: {class_accuracy:.4f}")
    
    def save_model(self, model, model_name="custom_gesture_classifier"):
        """Save the trained model and associated files"""
        print(f"\n💾 Saving model...")
        
        # Save model
        model_path = self.model_output_folder / f"{model_name}.pkl"
        joblib.dump(model, model_path)
        print(f"✅ Model saved to: {model_path}")
        
        # Save scaler
        scaler_path = self.model_output_folder / f"{model_name}_scaler.pkl"
        joblib.dump(self.scaler, scaler_path)
        print(f"✅ Scaler saved to: {scaler_path}")
        
        # Save gesture mapping
        mapping_path = self.model_output_folder / f"{model_name}_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(self.gesture_mapping, f, indent=2)
        print(f"✅ Gesture mapping saved to: {mapping_path}")
        
        # Save feature columns
        features_path = self.model_output_folder / f"{model_name}_features.json"
        with open(features_path, 'w') as f:
            json.dump(self.feature_columns, f, indent=2)
        print(f"✅ Feature columns saved to: {features_path}")
        
        # Save training metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'num_features': len(self.feature_columns),
            'num_classes': len(self.gesture_mapping),
            'gestures': list(self.gesture_mapping.values()),
            'total_samples': len(self.raw_data) if hasattr(self, 'raw_data') else 'Unknown'
        }
        
        metadata_path = self.model_output_folder / f"{model_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✅ Metadata saved to: {metadata_path}")
        
        return {
            'model_path': model_path,
            'scaler_path': scaler_path,
            'mapping_path': mapping_path,
            'features_path': features_path,
            'metadata_path': metadata_path
        }
    
    def train_complete_pipeline(self, csv_file=None, balance_data=True, 
                              use_cross_validation=True, model_name="custom_gesture_classifier"):
        """Complete training pipeline"""
        print("🚀 Starting complete training pipeline...")
        print("=" * 60)
        
        try:
            # Load data
            df = self.load_data(csv_file)
            
            # Prepare features
            X, y = self.prepare_features(df)
            
            # Train models
            best_model, results, test_data = self.train_and_evaluate_models(
                X, y, balance_data, use_cross_validation
            )
            
            # Save best model
            saved_files = self.save_model(best_model, model_name)
            
            print(f"\n🎉 Training completed successfully!")
            print(f"📁 Model files saved to: {self.model_output_folder}")
            
            return best_model, results, saved_files
            
        except Exception as e:
            print(f"\n❌ Training failed: {e}")
            raise

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Gesture Recognition Training")
    parser.add_argument("--data-folder", "-d", default="gesture_data",
                       help="Folder containing CSV files (default: gesture_data)")
    parser.add_argument("--csv-file", "-c", help="Specific CSV file to train on")
    parser.add_argument("--output-folder", "-o", default="models",
                       help="Output folder for models (default: models)")
    parser.add_argument("--model-name", "-n", default="custom_gesture_classifier",
                       help="Name for the saved model (default: custom_gesture_classifier)")
    parser.add_argument("--no-balance", action="store_true",
                       help="Skip dataset balancing")
    parser.add_argument("--no-cv", action="store_true",
                       help="Skip cross-validation")
    
    args = parser.parse_args()
    
    # Create trainer
    trainer = AdvancedGestureTrainer(
        data_folder=args.data_folder,
        model_output_folder=args.output_folder
    )
    
    # Train
    trainer.train_complete_pipeline(
        csv_file=args.csv_file,
        balance_data=not args.no_balance,
        use_cross_validation=not args.no_cv,
        model_name=args.model_name
    )

if __name__ == "__main__":
    main()
