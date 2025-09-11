import pandas as pd
import numpy as np
from typing import Optional, List
import json
from pathlib import Path
import joblib
import ast

class SimpleIsolatedASLRecognition:
    def __init__(self, model_path: str):
        # API state variables
        self.all_landmarks = None
        self.unique_signs = []
        self.sign_name = ""
        self.pred_sentence = ""

        # Initialize simple gesture classifier
        self.custom_mapping = {}
        self.load_custom_mapping()
        
        # Load trained custom gesture classifier
        self.custom_classifier = None
        self.custom_scaler = None
        self.trained_gesture_mapping = {}
        self.load_trained_classifier()

        # Landmark types
        self.landmark_types = {
            "faceLandmarks": "face",
            "poseLandmarks": "pose",
            "leftHandLandmarks": "left_hand",
            "rightHandLandmarks": "right_hand",
        }

    def load_custom_mapping(self):
        """Load the gesture mapping"""
        try:
            base_path = Path("../../../")  # Go to project root
            mapping_path = base_path / "simple_custom_mapping.json"
            
            if mapping_path.exists():
                with open(mapping_path, 'r') as f:
                    self.custom_mapping = json.load(f)
                print(f"✅ Custom gesture mapping loaded: {list(self.custom_mapping.keys())}")
            else:
                # Default mapping
                self.custom_mapping = {
                    "block_mad": 0,
                    "hello": 1,
                    "thank_you": 2
                }
                print("⚠️  Using default gesture mapping")
                
        except Exception as e:
            print(f"❌ Error loading mapping: {e}")
            self.custom_mapping = {"hello": 0, "thank_you": 1, "block_mad": 2}

    def load_trained_classifier(self):
        """Load the trained custom gesture classifier"""
        try:
            base_path = Path("../../../")  # Go to project root
            
            classifier_path = base_path / "custom_gesture_classifier.pkl"
            scaler_path = base_path / "custom_gesture_scaler.pkl"
            mapping_path = base_path / "custom_gesture_mapping.json"
            
            if classifier_path.exists() and scaler_path.exists() and mapping_path.exists():
                self.custom_classifier = joblib.load(classifier_path)
                self.custom_scaler = joblib.load(scaler_path)
                
                with open(mapping_path, 'r') as f:
                    self.trained_gesture_mapping = json.load(f)
                
                # Create reverse mapping for predictions
                self.id_to_trained_gesture = {v: k for k, v in self.trained_gesture_mapping.items()}
                
                print(f"✅ Trained gesture classifier loaded: {list(self.trained_gesture_mapping.keys())}")
                return True
            else:
                print("⚠️  Trained gesture classifier not found")
                return False
                
        except Exception as e:
            print(f"❌ Error loading trained classifier: {e}")
            self.custom_classifier = None
            return False

    def extract_features_from_landmarks(self, landmarks_sequence):
        """Extract features from landmarks sequence for trained classifier"""
        try:
            # Convert landmarks to feature vector
            sequence_features = []
            
            for frame_data in landmarks_sequence:
                # Collect all landmark coordinates
                all_coords = []
                
                # Face landmarks
                if hasattr(frame_data, 'faceLandmarks') and frame_data.faceLandmarks:
                    for landmark in frame_data.faceLandmarks:
                        all_coords.extend([landmark.x, landmark.y, getattr(landmark, 'z', 0)])
                else:
                    all_coords.extend([0.0] * (468 * 3))  # 468 face landmarks
                
                # Pose landmarks  
                if hasattr(frame_data, 'poseLandmarks') and frame_data.poseLandmarks:
                    for landmark in frame_data.poseLandmarks:
                        all_coords.extend([landmark.x, landmark.y, getattr(landmark, 'z', 0)])
                else:
                    all_coords.extend([0.0] * (33 * 3))  # 33 pose landmarks
                
                # Hand landmarks (21 landmarks x 2 hands = 42 total)
                hand_coords = [0.0] * (42 * 3)
                hand_idx = 0
                
                if hasattr(frame_data, 'rightHandLandmarks') and frame_data.rightHandLandmarks:
                    for landmark in frame_data.rightHandLandmarks:
                        if hand_idx < 21:
                            idx = hand_idx * 3
                            hand_coords[idx:idx+3] = [landmark.x, landmark.y, getattr(landmark, 'z', 0)]
                            hand_idx += 1
                
                if hasattr(frame_data, 'leftHandLandmarks') and frame_data.leftHandLandmarks:
                    for landmark in frame_data.leftHandLandmarks:
                        if hand_idx < 42:
                            idx = hand_idx * 3
                            hand_coords[idx:idx+3] = [landmark.x, landmark.y, getattr(landmark, 'z', 0)]
                            hand_idx += 1
                
                all_coords.extend(hand_coords)
                sequence_features.append(all_coords)
            
            if not sequence_features:
                return None
            
            # Convert to numpy array
            landmarks_array = np.array(sequence_features)
            
            # Extract sequence-level features (same as training)
            features = []
            
            # Statistical features
            features.extend([
                np.mean(landmarks_array),
                np.std(landmarks_array),
                np.min(landmarks_array),
                np.max(landmarks_array),
                np.median(landmarks_array)
            ])
            
            # Hand movement features
            if landmarks_array.shape[1] > 500:
                hand_data = landmarks_array[:, 500:540]  # Approximate hand region
                
                features.extend([
                    np.mean(hand_data[:, ::3]),  # X coordinates
                    np.std(hand_data[:, ::3]),
                    np.mean(hand_data[:, 1::3]),  # Y coordinates
                    np.std(hand_data[:, 1::3]),
                    np.max(hand_data[:, ::3]) - np.min(hand_data[:, ::3]),  # X range
                    np.max(hand_data[:, 1::3]) - np.min(hand_data[:, 1::3])  # Y range
                ])
            else:
                features.extend([0] * 6)
            
            # Motion features
            if len(landmarks_array) > 1:
                diffs = np.diff(landmarks_array, axis=0)
                features.extend([
                    np.mean(np.abs(diffs)),
                    np.std(diffs),
                    np.max(np.abs(diffs))
                ])
            else:
                features.extend([0] * 3)
            
            # Sample key frames
            sample_indices = [0, len(landmarks_array)//2, -1] if len(landmarks_array) > 2 else [0]
            
            for idx in sample_indices:
                if idx < len(landmarks_array):
                    sample_frame = landmarks_array[idx]
                    sample_landmarks = sample_frame[:20] if len(sample_frame) >= 20 else sample_frame
                    features.extend(sample_landmarks.tolist())
                    
                    if len(sample_landmarks) < 20:
                        features.extend([0] * (20 - len(sample_landmarks)))
            
            # Pad if fewer than 3 sample frames
            while len(sample_indices) < 3:
                features.extend([0] * 20)
                sample_indices.append(-1)
            
            return np.array(features)
            
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return None

    def predict_with_trained_classifier(self, landmarks_sequence):
        """Predict using the trained custom gesture classifier"""
        if not self.custom_classifier:
            return None, 0.0
        
        try:
            # Extract features
            features = self.extract_features_from_landmarks(landmarks_sequence)
            
            if features is None:
                return None, 0.0
            
            # Scale features
            features_scaled = self.custom_scaler.transform([features])
            
            # Predict
            prediction = self.custom_classifier.predict(features_scaled)[0]
            confidence = np.max(self.custom_classifier.predict_proba(features_scaled))
            
            # Get gesture name
            gesture_name = self.id_to_trained_gesture.get(prediction, "unknown")
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"❌ Trained classifier prediction error: {e}")
            return None, 0.0

    def _is_no_action(self, all_landmarks):
        """Detect no action state"""
        try:
            if not all_landmarks or len(all_landmarks) < 3:
                return True
            
            # Get hand positions from recent frames
            recent_frames = all_landmarks[-10:]
            hand_positions = []
            
            for frame_data in recent_frames:
                # Handle the actual data structure from LandmarkData
                all_hand_coords = []
                
                # Extract right hand landmarks
                if hasattr(frame_data, 'rightHandLandmarks') and frame_data.rightHandLandmarks:
                    for landmark in frame_data.rightHandLandmarks:
                        all_hand_coords.append([landmark.x, landmark.y])
                
                # Extract left hand landmarks  
                if hasattr(frame_data, 'leftHandLandmarks') and frame_data.leftHandLandmarks:
                    for landmark in frame_data.leftHandLandmarks:
                        all_hand_coords.append([landmark.x, landmark.y])
                
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
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

    def predict_custom_gesture(self, all_landmarks):
        """Simple pattern-based gesture prediction"""
        try:
            # Check for no-action
            is_no_action = self._is_no_action(all_landmarks)
            if is_no_action:
                return "no_action", 0.95
            
            # Extract hand movement patterns
            hand_positions = []
            for frame_data in all_landmarks:
                # Handle the actual data structure from LandmarkData
                right_hand_coords = []
                left_hand_coords = []
                
                # Extract right hand landmarks
                if hasattr(frame_data, 'rightHandLandmarks') and frame_data.rightHandLandmarks:
                    right_hand_coords = [[landmark.x, landmark.y, landmark.z if hasattr(landmark, 'z') else 0] 
                                       for landmark in frame_data.rightHandLandmarks]
                
                # Extract left hand landmarks
                if hasattr(frame_data, 'leftHandLandmarks') and frame_data.leftHandLandmarks:
                    left_hand_coords = [[landmark.x, landmark.y, landmark.z if hasattr(landmark, 'z') else 0] 
                                      for landmark in frame_data.leftHandLandmarks]
                
                if right_hand_coords or left_hand_coords:
                    position_data = {}
                    
                    if right_hand_coords:
                        right_hand = np.array(right_hand_coords)
                        position_data['right'] = np.mean(right_hand, axis=0)
                        position_data['right_spread'] = np.std(right_hand, axis=0)
                    
                    if left_hand_coords:
                        left_hand = np.array(left_hand_coords)
                        position_data['left'] = np.mean(left_hand, axis=0)
                        position_data['left_spread'] = np.std(left_hand, axis=0)
                    
                    hand_positions.append(position_data)
            
            if len(hand_positions) < 3:
                return "no_action", 0.85
            
            # Analyze movement patterns
            right_positions = []
            left_positions = []
            
            for pos in hand_positions:
                if 'right' in pos:
                    right_positions.append(pos['right'])
                if 'left' in pos:
                    left_positions.append(pos['left'])
            
            # Pattern classification
            confidence = 0.6
            
            if len(right_positions) >= 3:
                right_array = np.array(right_positions)
                y_movement = np.ptp(right_array[:, 1])  # Y-axis range
                x_movement = np.ptp(right_array[:, 0])  # X-axis range
                z_movement = np.ptp(right_array[:, 2])  # Z-axis range
                
                # Gesture classification based on movement patterns
                if y_movement > 0.15:  # Significant vertical movement
                    if np.mean(right_array[:, 1]) < 0.5:  # Upper area
                        # Hello gesture - hand waving up
                        return "hello", min(0.85, 0.6 + y_movement * 2)
                    else:
                        # Thank you gesture - hand moving down
                        return "thank_you", min(0.80, 0.6 + y_movement * 1.5)
                
                elif x_movement > 0.2:  # Horizontal movement
                    # Block mad gesture - horizontal blocking motion
                    return "block_mad", min(0.75, 0.6 + x_movement * 1.8)
                
                elif z_movement > 0.1:  # Forward/backward movement
                    # Could be any gesture with depth
                    if y_movement > 0.05:
                        return "hello", 0.70
                    else:
                        return "block_mad", 0.65
            
            # If no clear pattern, check for basic hand presence
            if len(right_positions) > 0 or len(left_positions) > 0:
                return "hello", 0.50  # Default to hello with low confidence
            
            return "no_action", 0.90
            
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return "no_action", 0.50

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
        # First try trained classifier if available
        if self.custom_classifier:
            trained_gesture, trained_confidence = self.predict_with_trained_classifier(results)
            
            if trained_gesture and trained_confidence > 0.6:  # Good confidence threshold
                self.sign_name = trained_gesture
                self.pred_sentence += f" {trained_gesture}"
                result = {
                    'sign': trained_gesture,
                    'sentence': self.pred_sentence.strip(),
                    'confidence': trained_confidence,
                    'type': 'trained_classifier'
                }
                return result
        
        # Fall back to pattern-based recognition
        gesture, confidence = self.predict_custom_gesture(results)
        
        if gesture and gesture != "no_action":
            self.sign_name = gesture
            self.pred_sentence += f" {gesture}"
            result = {
                'sign': gesture,
                'sentence': self.pred_sentence.strip(),
                'confidence': confidence,
                'type': 'simple_pattern'
            }
            return result
        elif gesture == "no_action":
            result = {
                'sign': "no_action",
                'sentence': self.pred_sentence.strip(),
                'confidence': confidence,
                'type': 'simple_pattern'
            }
            return result
        
        # Default response
        result = {
            'sign': "no_action",
            'sentence': self.pred_sentence.strip(),
            'confidence': 0.0,
            'type': 'default'
        }
        return result
