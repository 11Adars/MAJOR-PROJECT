#!/usr/bin/env python3
"""
Optimized Custom Gesture Solution
Fast solution that works with your exact data format
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import ast

class FastCustomGestureClassifier:
    def __init__(self):
        self.base_dir = Path("d:/MAJOR-PROJECT")
        self.gesture_data_dir = self.base_dir / "Sign" / "webapp" / "processed_data"
        self.model_dir = self.base_dir / "Sign" / "webapp" / "module" / "islr"
        
    def load_gesture_dictionary(self):
        """Load gesture dictionary"""
        dict_path = self.model_dir / "dict_sign.csv"
        if dict_path.exists():
            df = pd.read_csv(dict_path)
            gesture_dict = {row['sign']: row['sign_ord'] for _, row in df.iterrows()}
            print(f"✅ Loaded dictionary: {len(df)} gestures")
            return gesture_dict
        return {}
    
    def extract_features_from_landmarks(self, landmarks_str):
        """Extract features from landmarks string"""
        try:
            # Parse the landmarks string (it's stored as a JSON string)
            landmarks = ast.literal_eval(landmarks_str)
            landmarks = np.array(landmarks, dtype=np.float32)
            
            # Extract key features for gesture recognition
            features = []
            
            # Basic statistics
            features.extend([
                np.mean(landmarks),
                np.std(landmarks),
                np.min(landmarks),
                np.max(landmarks),
                np.median(landmarks)
            ])
            
            # Hand landmarks (assume they're in specific ranges)
            if len(landmarks) >= 126:  # At least hand landmarks
                # Right hand landmarks (indices based on MediaPipe)
                right_hand_start = 468 * 3 + 33 * 3  # face + pose
                left_hand_start = right_hand_start + 21 * 3
                
                if len(landmarks) > right_hand_start + 63:  # Full hand landmarks
                    right_hand = landmarks[right_hand_start:right_hand_start + 63]
                    left_hand = landmarks[left_hand_start:left_hand_start + 63]
                    
                    # Hand-specific features
                    features.extend([
                        np.mean(right_hand[::3]),  # x coordinates mean
                        np.mean(right_hand[1::3]), # y coordinates mean  
                        np.std(right_hand[::3]),   # x coordinates std
                        np.std(right_hand[1::3]),  # y coordinates std
                        np.mean(left_hand[::3]),   # left hand x mean
                        np.mean(left_hand[1::3]),  # left hand y mean
                        np.std(left_hand[::3]),    # left hand x std
                        np.std(left_hand[1::3])    # left hand y std
                    ])
                else:
                    features.extend([0] * 8)  # Pad with zeros
            else:
                features.extend([0] * 8)  # Pad with zeros
            
            # Reshape and take every nth element to reduce dimensionality
            if len(landmarks) > 50:
                sampled = landmarks[::max(1, len(landmarks)//50)]  # Sample ~50 points
                features.extend(sampled[:50].tolist())  # Take first 50
                if len(sampled) < 50:
                    features.extend([0] * (50 - len(sampled)))  # Pad if needed
            else:
                features.extend(landmarks.tolist())
                features.extend([0] * (50 - len(landmarks)))  # Pad to 50
            
            return np.array(features[:63])  # Fixed size: 5 + 8 + 50 = 63 features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return np.zeros(63)  # Return zero vector on error
    
    def load_and_process_gesture_data(self):
        """Load and process all custom gesture data"""
        print("📊 Loading custom gesture data...")
        
        gesture_dict = self.load_gesture_dictionary()
        custom_gestures = {name: id for name, id in gesture_dict.items() if id >= 250}
        
        if not custom_gestures:
            print("❌ No custom gestures found")
            return None, None, None
        
        print(f"🎯 Found custom gestures: {custom_gestures}")
        
        all_features = []
        all_labels = []
        
        for gesture_name, gesture_id in custom_gestures.items():
            data_file = self.gesture_data_dir / f"{gesture_name}_training_data.csv"
            
            if data_file.exists():
                try:
                    df = pd.read_csv(data_file)
                    print(f"📁 Processing {gesture_name}: {len(df)} frames")
                    
                    # Group by sequence and extract features
                    for seq_id in df['sequence_id'].unique():
                        seq_data = df[df['sequence_id'] == seq_id]
                        
                        # Extract features from each frame
                        sequence_features = []
                        for _, row in seq_data.iterrows():
                            frame_features = self.extract_features_from_landmarks(row['landmarks'])
                            sequence_features.append(frame_features)
                        
                        if sequence_features:
                            # Aggregate sequence features
                            seq_array = np.array(sequence_features)
                            
                            # Create sequence-level features
                            final_features = []
                            final_features.extend(np.mean(seq_array, axis=0))  # Mean across frames
                            final_features.extend(np.std(seq_array, axis=0))   # Std across frames
                            final_features.extend(seq_array[0])                # First frame
                            final_features.extend(seq_array[-1])               # Last frame
                            
                            all_features.append(final_features)
                            all_labels.append(gesture_id)
                
                except Exception as e:
                    print(f"❌ Error processing {gesture_name}: {e}")
        
        if all_features:
            X = np.array(all_features)
            y = np.array(all_labels)
            print(f"✅ Processed {len(X)} sequences, feature size: {X.shape[1]}")
            return X, y, custom_gestures
        
        return None, None, None
    
    def train_classifier(self):
        """Train the custom gesture classifier"""
        print("🔄 Training custom gesture classifier...")
        
        X, y, custom_gestures = self.load_and_process_gesture_data()
        
        if X is None:
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train classifier
        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        clf.fit(X_train_scaled, y_train)
        
        # Test accuracy
        train_accuracy = clf.score(X_train_scaled, y_train)
        test_accuracy = clf.score(X_test_scaled, y_test)
        
        print(f"✅ Training accuracy: {train_accuracy:.2%}")
        print(f"✅ Test accuracy: {test_accuracy:.2%}")
        
        # Save classifier and scaler
        model_path = Path("custom_gesture_classifier.pkl")
        scaler_path = Path("custom_gesture_scaler.pkl")
        mapping_path = Path("custom_gesture_mapping.json")
        
        joblib.dump(clf, model_path)
        joblib.dump(scaler, scaler_path)
        
        with open(mapping_path, 'w') as f:
            json.dump(custom_gestures, f, indent=2)
        
        print(f"✅ Saved classifier: {model_path}")
        print(f"✅ Saved scaler: {scaler_path}")
        print(f"✅ Saved mapping: {mapping_path}")
        
        return True
    
    def create_integration_code(self):
        """Create code to integrate with the web application"""
        
        integration_code = '''
# Add this to your web application's prediction module

import joblib
import json
import numpy as np
import ast
from pathlib import Path

class CustomGesturePredictor:
    def __init__(self):
        try:
            # Load the custom gesture classifier
            self.classifier = joblib.load("custom_gesture_classifier.pkl")
            self.scaler = joblib.load("custom_gesture_scaler.pkl")
            
            with open("custom_gesture_mapping.json", 'r') as f:
                self.gesture_mapping = json.load(f)
            
            # Reverse mapping for prediction results
            self.id_to_gesture = {v: k for k, v in self.gesture_mapping.items()}
            self.is_loaded = True
            print("✅ Custom gesture classifier loaded successfully")
            
        except Exception as e:
            print(f"⚠️ Could not load custom gesture classifier: {e}")
            self.is_loaded = False
    
    def extract_features_from_landmarks(self, landmarks_str):
        """Extract features from landmarks string"""
        try:
            landmarks = ast.literal_eval(landmarks_str) if isinstance(landmarks_str, str) else landmarks_str
            landmarks = np.array(landmarks, dtype=np.float32)
            
            features = []
            
            # Basic statistics
            features.extend([
                np.mean(landmarks),
                np.std(landmarks),
                np.min(landmarks),
                np.max(landmarks),
                np.median(landmarks)
            ])
            
            # Hand features (simplified)
            if len(landmarks) >= 126:
                right_hand_start = 468 * 3 + 33 * 3
                left_hand_start = right_hand_start + 21 * 3
                
                if len(landmarks) > right_hand_start + 63:
                    right_hand = landmarks[right_hand_start:right_hand_start + 63]
                    left_hand = landmarks[left_hand_start:left_hand_start + 63]
                    
                    features.extend([
                        np.mean(right_hand[::3]),
                        np.mean(right_hand[1::3]),
                        np.std(right_hand[::3]),
                        np.std(right_hand[1::3]),
                        np.mean(left_hand[::3]),
                        np.mean(left_hand[1::3]),
                        np.std(left_hand[::3]),
                        np.std(left_hand[1::3])
                    ])
                else:
                    features.extend([0] * 8)
            else:
                features.extend([0] * 8)
            
            # Sample landmarks
            if len(landmarks) > 50:
                sampled = landmarks[::max(1, len(landmarks)//50)]
                features.extend(sampled[:50].tolist())
                if len(sampled) < 50:
                    features.extend([0] * (50 - len(sampled)))
            else:
                features.extend(landmarks.tolist())
                features.extend([0] * (50 - len(landmarks)))
            
            return np.array(features[:63])
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return np.zeros(63)
    
    def predict_custom_gesture(self, landmarks_sequence):
        """Predict custom gesture from landmarks sequence"""
        if not self.is_loaded:
            return None, 0.0
        
        try:
            # Process sequence of landmarks
            sequence_features = []
            
            for landmarks in landmarks_sequence:
                if isinstance(landmarks, str):
                    frame_features = self.extract_features_from_landmarks(landmarks)
                else:
                    # Convert array to string format if needed
                    landmarks_str = str(landmarks.tolist()) if hasattr(landmarks, 'tolist') else str(landmarks)
                    frame_features = self.extract_features_from_landmarks(landmarks_str)
                
                sequence_features.append(frame_features)
            
            if not sequence_features:
                return None, 0.0
            
            # Create sequence-level features
            seq_array = np.array(sequence_features)
            final_features = []
            final_features.extend(np.mean(seq_array, axis=0))
            final_features.extend(np.std(seq_array, axis=0))
            final_features.extend(seq_array[0])
            final_features.extend(seq_array[-1])
            
            # Scale features
            features_scaled = self.scaler.transform([final_features])
            
            # Predict
            prediction = self.classifier.predict(features_scaled)[0]
            probabilities = self.classifier.predict_proba(features_scaled)[0]
            confidence = float(np.max(probabilities))
            
            gesture_name = self.id_to_gesture.get(prediction, f"gesture_{prediction}")
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return None, 0.0

# Usage example:
# predictor = CustomGesturePredictor()
# gesture, confidence = predictor.predict_custom_gesture(landmarks_sequence)
# if confidence > 0.7:
#     print(f"Detected: {gesture} (confidence: {confidence:.2%})")
'''
        
        integration_path = Path("custom_gesture_integration.py")
        with open(integration_path, 'w') as f:
            f.write(integration_code)
        
        print(f"✅ Created integration code: {integration_path}")
        return integration_path

def main():
    """Main execution function"""
    print("🚀 Fast Custom Gesture Solution")
    print("=" * 40)
    
    classifier = FastCustomGestureClassifier()
    
    # Train the classifier
    if classifier.train_classifier():
        print("\n✅ Classifier trained successfully!")
        
        # Create integration code
        integration_path = classifier.create_integration_code()
        
        print("\n🎯 SOLUTION READY!")
        print("=" * 30)
        print("✅ Custom gesture classifier trained")
        print("✅ Integration code created")
        print("\n📋 Next Steps:")
        print("1. Copy the files to your webapp directory:")
        print("   - custom_gesture_classifier.pkl")
        print("   - custom_gesture_scaler.pkl") 
        print("   - custom_gesture_mapping.json")
        print("   - custom_gesture_integration.py")
        print("\n2. Update your main prediction module to use CustomGesturePredictor")
        print("\n3. Test your gestures!")
        
        print("\n💡 This classifier can recognize:")
        gesture_dict = classifier.load_gesture_dictionary()
        custom_gestures = {name: id for name, id in gesture_dict.items() if id >= 250}
        for name, id in custom_gestures.items():
            print(f"   - {name} (ID: {id})")
    
    else:
        print("❌ Failed to train classifier")

if __name__ == "__main__":
    main()
