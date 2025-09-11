import tensorflow as tf
import pandas as pd
import numpy as np
from typing import Optional, List
import joblib
import json
import ast
from pathlib import Path

class CompatibleIsolatedASLRecognition:
    def __init__(self, model_path: str):
        # API state variables
        self.all_landmarks = None
        self.unique_signs = []
        self.sign_name = ""
        self.pred_sentence = ""

        # Initialize TensorFlow Lite model for original gestures
        try:
            self.interpreter = tf.lite.Interpreter(model_path=model_path + "/model.tflite")
            self.interpreter.allocate_tensors()
            self.model = self.interpreter.get_signature_runner("serving_default")

            # Load dictionary of signs
            dict_sign = pd.read_csv(model_path + "/dict_sign.csv")
            self.ORD2SIGN = dict_sign.set_index('sign_ord')['sign'].to_dict()
        except Exception as e:
            print(f"⚠️  Original model loading failed: {e}")
            self.interpreter = None
            self.model = None
            self.ORD2SIGN = {}
        
        # Initialize custom gesture classifier
        self.custom_classifier = None
        self.custom_mapping = {}
        self.load_custom_classifier()

        # Landmark counts and types
        self.landmark_counts = {"face": 478, "pose": 33, "left_hand": 21, "right_hand": 21}
        self.landmark_types = {
            "faceLandmarks": "face",
            "poseLandmarks": "pose",
            "leftHandLandmarks": "left_hand",
            "rightHandLandmarks": "right_hand",
        }

    def load_custom_classifier(self):
        """Load the custom gesture classifier"""
        try:
            # Look for custom LSTM files
            base_path = Path("../")
            
            lstm_model_path = base_path / "simple_custom_lstm.h5"
            labels_path = base_path / "simple_custom_labels.pkl"
            mapping_path = base_path / "simple_custom_mapping.json"
            
            if lstm_model_path.exists() and labels_path.exists() and mapping_path.exists():
                # Load LSTM model with compatible loading
                self.custom_lstm_model = tf.keras.models.load_model(
                    lstm_model_path, 
                    compile=True
                )
                
                # Load label encoder
                self.custom_label_encoder = joblib.load(labels_path)
                
                # Load mapping
                with open(mapping_path, 'r') as f:
                    self.custom_mapping = json.load(f)
                
                print(f"✅ Custom LSTM classifier loaded: {list(self.custom_mapping.keys())}")
                self.custom_classifier = "lstm"
            else:
                print("⚠️  Custom gesture files not found")
                self.custom_classifier = None
                
        except Exception as e:
            print(f"❌ Error loading custom classifier: {e}")
            import traceback
            traceback.print_exc()
            self.custom_classifier = None

    def _is_no_action(self, all_landmarks):
        """Detect no action state"""
        try:
            if not all_landmarks or len(all_landmarks) < 3:
                return True
            
            # Get hand positions from recent frames
            recent_frames = all_landmarks[-10:]
            hand_positions = []
            
            for frame_data in recent_frames:
                frame_df = pd.DataFrame(frame_data)
                if frame_df.empty:
                    continue
                
                right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y']].values
                left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y']].values
                
                if len(right_hand) > 0 or len(left_hand) > 0:
                    all_hand_coords = []
                    if len(right_hand) > 0:
                        all_hand_coords.extend(right_hand)
                    if len(left_hand) > 0:
                        all_hand_coords.extend(left_hand)
                    
                    if all_hand_coords:
                        center = np.mean(all_hand_coords, axis=0)
                        hand_positions.append(center)
            
            if len(hand_positions) < 3:
                return True
            
            # Calculate movement
            positions_array = np.array(hand_positions)
            movement_variance = np.var(positions_array, axis=0)
            total_variance = np.sum(movement_variance)
            
            differences = []
            for i in range(1, len(positions_array)):
                diff = np.linalg.norm(positions_array[i] - positions_array[i-1])
                differences.append(diff)
            
            avg_movement = np.mean(differences) if differences else 0
            
            # Thresholds
            variance_threshold = 0.005
            movement_threshold = 0.008
            
            is_static = total_variance < variance_threshold and avg_movement < movement_threshold
            return is_static
            
        except Exception as e:
            print(f"Error in no-action detection: {e}")
            return False

    def predict_custom_gesture(self, all_landmarks):
        """Predict using custom LSTM classifier"""
        if self.custom_classifier != "lstm":
            return None, 0.0
        
        try:
            # Check for no-action
            if self._is_no_action(all_landmarks):
                return "no_action", 0.95
            
            def extract_frame_features(frame_df):
                """Extract features from single frame - matching training"""
                if frame_df.empty:
                    return np.zeros(100)
                
                features = []
                
                # Get landmark data
                right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y', 'z']].values
                left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y', 'z']].values
                pose = frame_df[frame_df['type'] == 'pose'][['x', 'y', 'z']].values
                
                # Ensure consistent sizes
                if len(right_hand) == 0: right_hand = np.zeros((21, 3))
                if len(left_hand) == 0: left_hand = np.zeros((21, 3))
                if len(pose) == 0: pose = np.zeros((11, 3))
                
                # Pad or truncate
                right_hand = np.pad(right_hand, ((0, max(0, 21-len(right_hand))), (0, 0)), 'constant')[:21]
                left_hand = np.pad(left_hand, ((0, max(0, 21-len(left_hand))), (0, 0)), 'constant')[:21]
                pose = np.pad(pose, ((0, max(0, 11-len(pose))), (0, 0)), 'constant')[:11]
                
                # Flatten coordinates
                right_flat = right_hand.flatten()
                left_flat = left_hand.flatten()
                pose_flat = pose.flatten()
                
                # Basic statistics (25 features)
                all_coords = np.concatenate([right_flat, left_flat, pose_flat])
                features.extend([
                    np.mean(all_coords), np.std(all_coords), np.min(all_coords), np.max(all_coords),
                    np.median(all_coords), np.var(all_coords),
                    np.mean(np.abs(all_coords)), np.std(np.abs(all_coords)),
                    np.sum(all_coords > 0), np.sum(all_coords < 0),
                    np.mean(right_flat), np.std(right_flat), np.mean(left_flat), np.std(left_flat),
                    np.mean(pose_flat), np.std(pose_flat),
                    np.mean(right_hand[:, 0]), np.mean(right_hand[:, 1]), np.mean(right_hand[:, 2]),
                    np.mean(left_hand[:, 0]), np.mean(left_hand[:, 1]), np.mean(left_hand[:, 2]),
                    np.mean(pose[:, 0]), np.mean(pose[:, 1]), np.mean(pose[:, 2])
                ])
                
                # Hand distance features (10 features)
                if len(right_hand) > 0 and len(left_hand) > 0:
                    hand_distance = np.linalg.norm(np.mean(right_hand, axis=0) - np.mean(left_hand, axis=0))
                    features.append(hand_distance)
                    
                    right_center = np.mean(right_hand, axis=0)
                    left_center = np.mean(left_hand, axis=0)
                    right_spread = np.mean(np.linalg.norm(right_hand - right_center, axis=1))
                    left_spread = np.mean(np.linalg.norm(left_hand - left_center, axis=1))
                    features.extend([right_spread, left_spread])
                    
                    if len(pose) > 0:
                        pose_center = np.mean(pose, axis=0)
                        right_to_pose = np.linalg.norm(right_center - pose_center)
                        left_to_pose = np.linalg.norm(left_center - pose_center)
                        features.extend([right_to_pose, left_to_pose])
                    else:
                        features.extend([0, 0])
                    
                    features.extend([
                        np.ptp(right_hand[:, 0]), np.ptp(right_hand[:, 1]),
                        np.ptp(left_hand[:, 0]), np.ptp(left_hand[:, 1]),
                        np.max(right_hand[:, 2]), np.max(left_hand[:, 2])
                    ])
                else:
                    features.extend([0] * 10)
                
                # Coordinate distribution features (65 features)
                key_coords = []
                if len(right_hand) >= 5:
                    key_coords.extend(right_hand[[4, 8, 12, 16, 20]].flatten())
                else:
                    key_coords.extend([0] * 15)
                    
                if len(left_hand) >= 5:
                    key_coords.extend(left_hand[[4, 8, 12, 16, 20]].flatten())
                else:
                    key_coords.extend([0] * 15)
                    
                if len(pose) >= 5:
                    key_coords.extend(pose[:5].flatten())
                else:
                    key_coords.extend([0] * 15)
                
                remaining_coords = all_coords[:20]
                key_coords.extend(remaining_coords.tolist())
                
                while len(key_coords) < 65:
                    key_coords.append(0)
                features.extend(key_coords[:65])
                
                # Ensure exactly 100 features
                while len(features) < 100:
                    features.append(0)
                
                return np.array(features[:100])
            
            # Process landmark sequence
            if not all_landmarks:
                return None, 0.0
            
            # Extract features for each frame
            frame_features = []
            for frame_data in all_landmarks:
                frame_df = pd.DataFrame(frame_data)
                features = extract_frame_features(frame_df)
                frame_features.append(features)
            
            # Handle sequence length
            frame_features = np.array(frame_features)
            sequence_length = 30
            
            if len(frame_features) >= sequence_length:
                start_idx = (len(frame_features) - sequence_length) // 2
                frame_features = frame_features[start_idx:start_idx + sequence_length]
            else:
                padding_needed = sequence_length - len(frame_features)
                padding = np.zeros((padding_needed, 100))
                frame_features = np.vstack([frame_features, padding])
            
            # Reshape for prediction
            X = frame_features.reshape(1, sequence_length, 100)
            
            # Make prediction
            predictions = self.custom_lstm_model.predict(X, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            # Get gesture name
            gesture_name = self.custom_label_encoder.inverse_transform([predicted_class])[0]
            
            print(f"🔮 Prediction: {gesture_name} (confidence: {confidence:.3f})")
            
            # Apply confidence threshold
            if confidence < 0.25:
                return "no_action", confidence
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0

    def format_df(self, results):
        """Format landmark results into DataFrame"""
        data = []
        for frame_data in results:
            frame_number = frame_data.get("frameNumber", 0)
            
            for landmark_type, landmarks in frame_data.items():
                if landmark_type in self.landmark_types and landmarks:
                    for landmark_index, landmark in enumerate(landmarks):
                        row = {
                            'type': self.landmark_types[landmark_type],
                            'landmark_index': landmark_index,
                            'x': landmark['x'],
                            'y': landmark['y'],
                            'z': landmark.get('z', 0),
                            'frame': frame_number
                        }
                        data.append(row)
        
        return pd.DataFrame(data)

    def predict(self, results):
        """Main prediction function"""
        # Try custom gesture recognition first
        if self.custom_classifier:
            gesture, confidence = self.predict_custom_gesture(results)
            if gesture and gesture != "no_action":
                self.sign_name = gesture
                self.pred_sentence += f" {gesture}"
                return {
                    'sign': gesture,
                    'sentence': self.pred_sentence.strip(),
                    'confidence': confidence,
                    'type': 'custom'
                }
            elif gesture == "no_action":
                return {
                    'sign': "no_action",
                    'sentence': self.pred_sentence.strip(),
                    'confidence': confidence,
                    'type': 'custom'
                }
        
        # Fall back to original model if available
        if self.model:
            all_landmarks = self.format_df(results)
            if len(all_landmarks) == 0:
                return {
                    'sign': "no_action",
                    'sentence': self.pred_sentence.strip(),
                    'confidence': 0.0,
                    'type': 'fallback'
                }
            
            prediction = self.model(
                inputs=tf.constant(all_landmarks[["x", "y", "z"]].values, dtype=tf.float32)
            )
            
            sign_prediction = prediction["outputs"].numpy()
            sign_prediction_index = np.argmax(sign_prediction)
            sign_prediction_prob = np.max(sign_prediction)
            
            self.sign_name = self.ORD2SIGN[sign_prediction_index]
            self.pred_sentence += f" {self.sign_name}"
            
            return {
                'sign': self.sign_name,
                'sentence': self.pred_sentence.strip(),
                'confidence': float(sign_prediction_prob),
                'type': 'original'
            }
        
        # Default response
        return {
            'sign': "no_action",
            'sentence': self.pred_sentence.strip(),
            'confidence': 0.0,
            'type': 'default'
        }
