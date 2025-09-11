#!/usr/bin/env python3
"""
Quick Custom Gesture Solution
Creates a hybrid recognition system using existing model + custom gesture classifier
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from pathlib import Path
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

class HybridGestureRecognizer:
    def __init__(self):
        self.base_dir = Path("d:/MAJOR-PROJECT")
        self.gesture_data_dir = self.base_dir / "Sign" / "webapp" / "processed_data"
        self.model_dir = self.base_dir / "webapp" / "app" / "module" / "islr"
        self.ROWS_PER_FRAME = 543
        
    def load_custom_gesture_data(self):
        """Load all custom gesture data for training"""
        print("📊 Loading custom gesture data...")
        
        # Load gesture dictionary
        dict_path = self.model_dir / "dict_sign.csv"
        gesture_dict = {}
        if dict_path.exists():
            df = pd.read_csv(dict_path)
            gesture_dict = {row['sign']: row['sign_ord'] for _, row in df.iterrows()}
        
        # Find custom gestures (IDs >= 250)
        custom_gestures = {name: id for name, id in gesture_dict.items() if id >= 250}
        print(f"🎯 Custom gestures: {custom_gestures}")
        
        all_data = []
        all_labels = []
        
        for gesture_name, gesture_id in custom_gestures.items():
            data_file = self.gesture_data_dir / f"{gesture_name}_training_data.csv"
            
            if data_file.exists():
                try:
                    df = pd.read_csv(data_file)
                    print(f"✅ Loading {gesture_name}: {len(df)} frames")
                    
                    # Group by sequence
                    for seq_id in df['sequence'].unique():
                        seq_data = df[df['sequence'] == seq_id].copy()
                        seq_data = seq_data.sort_values('frame')
                        
                        # Extract landmark features
                        features = []
                        for _, row in seq_data.iterrows():
                            # Extract landmark coordinates
                            landmark_features = []
                            for col in df.columns:
                                if 'landmark' in col.lower() and ('_x' in col or '_y' in col or '_z' in col):
                                    landmark_features.append(row[col])
                            
                            if landmark_features:
                                features.extend(landmark_features)
                        
                        if features:
                            # Pad or truncate to fixed size
                            target_size = 1000  # Adjust based on your data
                            if len(features) < target_size:
                                features.extend([0.0] * (target_size - len(features)))
                            else:
                                features = features[:target_size]
                            
                            all_data.append(features)
                            all_labels.append(gesture_id)
                
                except Exception as e:
                    print(f"❌ Error loading {gesture_name}: {e}")
        
        if all_data:
            print(f"✅ Loaded {len(all_data)} sequences for {len(custom_gestures)} custom gestures")
            return np.array(all_data), np.array(all_labels), custom_gestures
        else:
            print("❌ No data loaded")
            return None, None, None
    
    def train_custom_gesture_classifier(self):
        """Train a classifier for custom gestures only"""
        print("🔄 Training custom gesture classifier...")
        
        X, y, custom_gestures = self.load_custom_gesture_data()
        
        if X is None:
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest classifier
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        
        # Test accuracy
        accuracy = clf.score(X_test, y_test)
        print(f"✅ Custom gesture classifier accuracy: {accuracy:.2%}")
        
        # Save the classifier
        model_path = Path("custom_gesture_classifier.pkl")
        joblib.dump(clf, model_path)
        print(f"✅ Saved classifier: {model_path}")
        
        # Save gesture mapping
        mapping_path = Path("custom_gesture_mapping.json")
        with open(mapping_path, 'w') as f:
            json.dump(custom_gestures, f, indent=2)
        print(f"✅ Saved gesture mapping: {mapping_path}")
        
        return True
    
    def create_hybrid_prediction_module(self):
        """Create a new prediction module that combines both models"""
        
        hybrid_code = '''
import numpy as np
import tensorflow as tf
import pandas as pd
import joblib
import json
from pathlib import Path
import mediapipe as mp
import cv2

class HybridIsolatedASLRecognition:
    def __init__(self):
        # Load original model for 250 gestures
        self.original_model = tf.lite.Interpreter(model_path="model.tflite")
        self.original_model.allocate_tensors()
        
        # Load custom gesture classifier
        try:
            self.custom_classifier = joblib.load("../../../custom_gesture_classifier.pkl")
            with open("../../../custom_gesture_mapping.json", 'r') as f:
                self.custom_gesture_mapping = json.load(f)
            self.has_custom_classifier = True
            print("✅ Loaded custom gesture classifier")
        except:
            self.has_custom_classifier = False
            print("⚠️  Custom gesture classifier not found")
        
        # Load gesture dictionary
        df = pd.read_csv("dict_sign.csv")
        self.gesture_dict = {row['sign_ord']: row['sign'] for _, row in df.iterrows()}
        
        # MediaPipe setup
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            refine_face_landmarks=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
    
    def extract_landmarks(self, frame):
        """Extract landmarks from frame"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(frame_rgb)
        
        landmarks = []
        
        # Face landmarks (468 points)
        if results.face_landmarks:
            for landmark in results.face_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * (468 * 3))
        
        # Pose landmarks (33 points)
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * (33 * 3))
        
        # Left hand landmarks (21 points)
        if results.left_hand_landmarks:
            for landmark in results.left_hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * (21 * 3))
        
        # Right hand landmarks (21 points)
        if results.right_hand_landmarks:
            for landmark in results.right_hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * (21 * 3))
        
        return np.array(landmarks, dtype=np.float32)
    
    def predict_original_gestures(self, sequence):
        """Predict using original model (250 gestures)"""
        try:
            # Prepare input
            input_details = self.original_model.get_input_details()
            output_details = self.original_model.get_output_details()
            
            # Set input
            self.original_model.set_tensor(input_details[0]['index'], sequence)
            
            # Run inference
            self.original_model.invoke()
            
            # Get output
            output = self.original_model.get_tensor(output_details[0]['index'])
            
            # Get prediction
            prediction_id = np.argmax(output[0])
            confidence = float(np.max(output[0]))
            
            return prediction_id, confidence
            
        except Exception as e:
            print(f"Error in original prediction: {e}")
            return None, 0.0
    
    def predict_custom_gestures(self, sequence):
        """Predict using custom gesture classifier"""
        if not self.has_custom_classifier:
            return None, 0.0
        
        try:
            # Flatten sequence for custom classifier
            features = sequence.flatten()
            
            # Pad or truncate to match training data
            target_size = 1000  # Match training data size
            if len(features) < target_size:
                features = np.pad(features, (0, target_size - len(features)))
            else:
                features = features[:target_size]
            
            # Predict
            prediction = self.custom_classifier.predict([features])[0]
            probabilities = self.custom_classifier.predict_proba([features])[0]
            confidence = float(np.max(probabilities))
            
            return prediction, confidence
            
        except Exception as e:
            print(f"Error in custom prediction: {e}")
            return None, 0.0
    
    def predict(self, sequence):
        """Hybrid prediction using both models"""
        # Try original model first
        original_pred, original_conf = self.predict_original_gestures(sequence)
        
        # Try custom model
        custom_pred, custom_conf = self.predict_custom_gestures(sequence)
        
        # Decide which prediction to use
        if custom_pred is not None and custom_conf > 0.7:
            # High confidence custom gesture
            gesture_name = self.gesture_dict.get(custom_pred, f"custom_{custom_pred}")
            return {
                "prediction": gesture_name,
                "confidence": custom_conf,
                "type": "custom"
            }
        elif original_pred is not None and original_conf > 0.5:
            # Original gesture
            gesture_name = self.gesture_dict.get(original_pred, f"gesture_{original_pred}")
            return {
                "prediction": gesture_name,
                "confidence": original_conf,
                "type": "original"
            }
        else:
            # No confident prediction
            return {
                "prediction": "unknown",
                "confidence": 0.0,
                "type": "none"
            }
    
    def predict_from_frames(self, frames):
        """Predict gesture from a sequence of frames"""
        landmarks_sequence = []
        
        for frame in frames:
            landmarks = self.extract_landmarks(frame)
            landmarks_sequence.append(landmarks)
        
        if landmarks_sequence:
            sequence = np.array(landmarks_sequence).reshape(1, len(landmarks_sequence), -1)
            return self.predict(sequence)
        else:
            return {"prediction": "no_landmarks", "confidence": 0.0, "type": "error"}
'''
        
        # Save the hybrid module
        hybrid_path = self.model_dir / "hybrid_model.py"
        with open(hybrid_path, 'w') as f:
            f.write(hybrid_code)
        
        print(f"✅ Created hybrid prediction module: {hybrid_path}")
        return hybrid_path

def main():
    """Main execution"""
    print("🎯 Quick Custom Gesture Solution")
    print("=" * 40)
    
    recognizer = HybridGestureRecognizer()
    
    # Step 1: Train custom gesture classifier
    print("\n📋 Step 1: Training custom gesture classifier...")
    if recognizer.train_custom_gesture_classifier():
        print("✅ Custom gesture classifier trained successfully")
    else:
        print("❌ Failed to train custom gesture classifier")
        print("Make sure you have recorded custom gesture data")
        return
    
    # Step 2: Create hybrid prediction module
    print("\n📋 Step 2: Creating hybrid prediction system...")
    hybrid_path = recognizer.create_hybrid_prediction_module()
    
    print("\n🎯 SOLUTION READY!")
    print("=" * 30)
    print("✅ Custom gesture classifier trained")
    print("✅ Hybrid prediction system created")
    print("\n📋 Next Steps:")
    print("1. Update your web application to use the hybrid model")
    print("2. Replace 'from model import IsolatedASLRecognition'")
    print("   with 'from hybrid_model import HybridIsolatedASLRecognition'")
    print("3. Test your custom gestures!")
    
    print("\n💡 This solution combines:")
    print("  - Original model for 250 existing gestures")
    print("  - New classifier for your 3 custom gestures")
    print("  - Smart decision making between both models")

if __name__ == "__main__":
    main()
