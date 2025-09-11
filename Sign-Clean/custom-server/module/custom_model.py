import pandas as pd
import numpy as np
from typing import Optional, List
import json
from pathlib import Path
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
import warnings
import time
import math
warnings.filterwarnings('ignore')

class CustomGestureRecognition:
    def __init__(self, model_path: str = "."):
        # API state variables
        self.all_landmarks = None
        self.sign_name = ""
        self.pred_sentence = ""

        # Initialize custom gesture system
        self.custom_classifier = None
        self.custom_scaler = None
        self.lstm_model = None
        self.gesture_mapping = {}
        self.id_to_gesture = {}
        
        # Motion detection and timing variables
        self.last_prediction_time = 0
        self.min_prediction_interval = 3.0  # Minimum 3 seconds between predictions
        self.motion_threshold = 0.05  # Higher threshold for detecting significant motion
        self.previous_landmarks = None
        self.gesture_start_time = None
        self.min_gesture_duration = 2.0  # Minimum 2 seconds to complete gesture
        self.max_gesture_duration = 6.0  # Maximum 6 seconds for gesture
        self.stable_frames_count = 0
        self.required_stable_frames = 15  # More frames needed to confirm gesture completion
        self.motion_history = []  # Track motion over time
        self.max_motion_history = 30  # Keep 30 frames of motion history
        self.rest_threshold = 0.01  # Very low motion = rest state
        self.consecutive_rest_frames = 0
        self.required_rest_frames = 20  # Need 20 consecutive rest frames before allowing new prediction
        self.in_rest_state = True  # Start in rest state
        self.significant_motion_detected = False
        
        # Load custom models
        self.load_custom_models()

    def load_custom_models(self):
        """Load custom gesture recognition models"""
        base_path = Path("../")
        
        # Try to load LSTM model first (preferred)
        lstm_model_path = base_path / "training_cache" / "models"
        if lstm_model_path.exists():
            lstm_files = list(lstm_model_path.glob("*_lstm.h5"))
            if lstm_files:
                try:
                    self.lstm_model = load_model(lstm_files[0])
                    
                    # Load corresponding mapping
                    mapping_file = lstm_files[0].with_suffix('.json').name.replace('_lstm', '_mapping')
                    mapping_path = lstm_model_path / mapping_file
                    
                    if mapping_path.exists():
                        with open(mapping_path, 'r') as f:
                            self.gesture_mapping = json.load(f)
                        self.id_to_gesture = {v: k for k, v in self.gesture_mapping.items()}
                        print(f"✅ LSTM model loaded with gestures: {list(self.gesture_mapping.keys())}")
                        return
                except Exception as e:
                    print(f"⚠️  LSTM model load failed: {e}")
        
        # Fallback to RandomForest classifier
        classifier_path = base_path / "custom_gesture_classifier.pkl"
        scaler_path = base_path / "custom_gesture_scaler.pkl"
        mapping_path = base_path / "custom_gesture_mapping.json"
        
        if classifier_path.exists() and scaler_path.exists() and mapping_path.exists():
            try:
                self.custom_classifier = joblib.load(classifier_path)
                self.custom_scaler = joblib.load(scaler_path)
                
                with open(mapping_path, 'r') as f:
                    self.gesture_mapping = json.load(f)
                self.id_to_gesture = {v: k for k, v in self.gesture_mapping.items()}
                
                print(f"✅ RandomForest classifier loaded with gestures: {list(self.gesture_mapping.keys())}")
            except Exception as e:
                print(f"❌ Error loading custom models: {e}")
        else:
            print("❌ No custom models found!")

    def calculate_motion_score(self, current_landmarks):
        """Calculate motion score between current and previous landmarks with enhanced detection"""
        if self.previous_landmarks is None:
            self.previous_landmarks = current_landmarks
            return 0.0
        
        try:
            motion_score = 0.0
            comparison_points = 0
            
            # Focus primarily on hand landmarks for gesture detection
            for hand_attr in ['leftHandLandmarks', 'rightHandLandmarks']:
                curr_hand = getattr(current_landmarks, hand_attr, None)
                prev_hand = getattr(self.previous_landmarks, hand_attr, None)
                
                if curr_hand and prev_hand and len(curr_hand) > 0 and len(prev_hand) > 0:
                    # Calculate motion for key hand landmarks (fingertips and wrist)
                    key_indices = [0, 4, 8, 12, 16, 20]  # Wrist, thumb tip, index tip, middle tip, ring tip, pinky tip
                    
                    for idx in key_indices:
                        if idx < len(curr_hand) and idx < len(prev_hand):
                            curr = curr_hand[idx]
                            prev = prev_hand[idx]
                            dx = curr.x - prev.x
                            dy = curr.y - prev.y
                            # Weight hand motion heavily for gesture detection
                            motion_score += math.sqrt(dx*dx + dy*dy) * 3.0
                            comparison_points += 1
            
            # Add some pose motion but with lower weight
            if (hasattr(current_landmarks, 'poseLandmarks') and current_landmarks.poseLandmarks and
                hasattr(self.previous_landmarks, 'poseLandmarks') and self.previous_landmarks.poseLandmarks):
                
                # Only check shoulder and elbow motion
                key_pose_indices = [11, 12, 13, 14, 15, 16]  # Shoulders and elbows
                for idx in key_pose_indices:
                    if idx < len(current_landmarks.poseLandmarks) and idx < len(self.previous_landmarks.poseLandmarks):
                        curr = current_landmarks.poseLandmarks[idx]
                        prev = self.previous_landmarks.poseLandmarks[idx]
                        dx = curr.x - prev.x
                        dy = curr.y - prev.y
                        motion_score += math.sqrt(dx*dx + dy*dy) * 0.5  # Lower weight for pose
                        comparison_points += 1
            
            self.previous_landmarks = current_landmarks
            
            if comparison_points > 0:
                final_score = motion_score / comparison_points
                
                # Add to motion history
                self.motion_history.append(final_score)
                if len(self.motion_history) > self.max_motion_history:
                    self.motion_history.pop(0)
                
                return final_score
            else:
                return 0.0
            
        except Exception as e:
            print(f"⚠️ Motion calculation error: {e}")
            self.previous_landmarks = current_landmarks
            return 0.0

    def analyze_motion_pattern(self):
        """Analyze motion pattern to detect if user is in rest state or performing gesture"""
        if len(self.motion_history) < 10:
            return "insufficient_data", 0.0
        
        # Calculate recent motion statistics
        recent_motion = self.motion_history[-10:]  # Last 10 frames
        avg_motion = sum(recent_motion) / len(recent_motion)
        max_motion = max(recent_motion)
        
        # Check if in rest state (very low motion for extended period)
        if avg_motion < self.rest_threshold and max_motion < self.motion_threshold:
            self.consecutive_rest_frames += 1
            if self.consecutive_rest_frames >= self.required_rest_frames:
                self.in_rest_state = True
                self.significant_motion_detected = False
            return "rest_state", avg_motion
        else:
            self.consecutive_rest_frames = 0
            
            # Check for significant motion indicating start of gesture
            if avg_motion > self.motion_threshold and max_motion > self.motion_threshold * 1.5:
                if self.in_rest_state:
                    # Transitioning from rest to motion
                    self.in_rest_state = False
                    self.significant_motion_detected = True
                    self.gesture_start_time = time.time()
                    return "gesture_starting", avg_motion
                elif self.significant_motion_detected:
                    return "gesture_active", avg_motion
                else:
                    return "minor_motion", avg_motion
            else:
                return "settling", avg_motion

    def should_predict(self, landmarks_sequence):
        """Determine if we should make a prediction based on comprehensive motion analysis"""
        current_time = time.time()
        
        # Always return early if rate limited
        if current_time - self.last_prediction_time < self.min_prediction_interval:
            return False, "rate_limited"
        
        # Need sufficient data
        if len(landmarks_sequence) < 20:
            return False, "insufficient_data"
        
        # Calculate current motion and analyze pattern
        if len(landmarks_sequence) >= 2:
            motion_score = self.calculate_motion_score(landmarks_sequence[-1])
            motion_state, avg_motion = self.analyze_motion_pattern()
            
            # Debug info (optional - can be removed)
            if len(self.motion_history) % 30 == 0:  # Print every 30 frames to reduce spam
                print(f"🎯 Motion Analysis: State={motion_state}, Avg={avg_motion:.4f}, Current={motion_score:.4f}")
            
            # If in rest state, absolutely no prediction
            if motion_state == "rest_state":
                return False, "in_rest_state"
            
            # If just minor motion or settling, don't predict
            if motion_state in ["minor_motion", "settling", "insufficient_data"]:
                return False, motion_state
            
            # Only predict if we have significant gesture activity
            if motion_state not in ["gesture_starting", "gesture_active"]:
                return False, "waiting_for_significant_motion"
            
            # Check if gesture has been active long enough
            if self.gesture_start_time is not None:
                gesture_duration = current_time - self.gesture_start_time
                
                # Gesture too short
                if gesture_duration < self.min_gesture_duration:
                    return False, "gesture_too_short"
                
                # Gesture too long - reset and require new gesture
                if gesture_duration > self.max_gesture_duration:
                    print("⏰ Gesture timeout - resetting")
                    self.gesture_start_time = None
                    self.in_rest_state = True
                    self.significant_motion_detected = False
                    return False, "gesture_timeout"
            else:
                # No gesture timing started yet
                return False, "no_gesture_timing"
        
        # All conditions met for prediction
        print(f"✅ Prediction conditions met - gesture active for {current_time - self.gesture_start_time:.1f}s")
        self.last_prediction_time = current_time
        
        # Reset gesture state after prediction
        self.gesture_start_time = None
        self.in_rest_state = True
        self.significant_motion_detected = False
        
        return True, "ready_to_predict"

    def extract_sequence_features_for_lstm(self, landmarks_sequence):
        """Extract features for LSTM model (sequence-based)"""
        try:
            sequence_features = []
            
            for frame_data in landmarks_sequence:
                frame_landmarks = []
                
                # Extract all landmark coordinates in a consistent order
                # Face landmarks (first 468 * 3 = 1404 features)
                if hasattr(frame_data, 'faceLandmarks') and frame_data.faceLandmarks:
                    for landmark in frame_data.faceLandmarks[:468]:  # Limit to 468
                        frame_landmarks.extend([landmark.x, landmark.y, getattr(landmark, 'z', 0)])
                else:
                    frame_landmarks.extend([0.0] * (468 * 3))
                
                # Pose landmarks (33 * 3 = 99 features)
                if hasattr(frame_data, 'poseLandmarks') and frame_data.poseLandmarks:
                    for landmark in frame_data.poseLandmarks:
                        frame_landmarks.extend([landmark.x, landmark.y, getattr(landmark, 'z', 0)])
                else:
                    frame_landmarks.extend([0.0] * (33 * 3))
                
                # Hand landmarks (42 * 3 = 126 features)
                hand_landmarks = [0.0] * (42 * 3)
                hand_idx = 0
                
                # Right hand
                if hasattr(frame_data, 'rightHandLandmarks') and frame_data.rightHandLandmarks:
                    for landmark in frame_data.rightHandLandmarks:
                        if hand_idx < 21:
                            idx = hand_idx * 3
                            hand_landmarks[idx:idx+3] = [landmark.x, landmark.y, getattr(landmark, 'z', 0)]
                            hand_idx += 1
                
                # Left hand
                if hasattr(frame_data, 'leftHandLandmarks') and frame_data.leftHandLandmarks:
                    for landmark in frame_data.leftHandLandmarks:
                        if hand_idx < 42:
                            idx = hand_idx * 3
                            hand_landmarks[idx:idx+3] = [landmark.x, landmark.y, getattr(landmark, 'z', 0)]
                            hand_idx += 1
                
                frame_landmarks.extend(hand_landmarks)
                sequence_features.append(frame_landmarks)
            
            # Pad or trim sequence to fixed length (e.g., 30 frames)
            target_length = 30
            if len(sequence_features) > target_length:
                # Take middle portion
                start = (len(sequence_features) - target_length) // 2
                sequence_features = sequence_features[start:start + target_length]
            elif len(sequence_features) < target_length:
                # Pad with last frame
                while len(sequence_features) < target_length:
                    sequence_features.append(sequence_features[-1] if sequence_features else [0.0] * (468*3 + 33*3 + 42*3))
            
            return np.array(sequence_features, dtype=np.float32)
            
        except Exception as e:
            print(f"❌ LSTM feature extraction error: {e}")
            return None

    def extract_statistical_features(self, landmarks_sequence):
        """Extract raw landmark features matching training data format"""
        try:
            # Extract raw landmarks from the latest frame (like training data)
            if not landmarks_sequence:
                return None
            
            # Use the most recent frame for prediction
            frame_data = landmarks_sequence[-1]
            all_coords = []
            
            # Face landmarks (468 landmarks * 3 coordinates = 1404 features)
            if hasattr(frame_data, 'faceLandmarks') and frame_data.faceLandmarks:
                for landmark in frame_data.faceLandmarks:
                    all_coords.extend([landmark.x, landmark.y, getattr(landmark, 'z', 0)])
            else:
                all_coords.extend([0.0] * (468 * 3))
            
            # Pose landmarks (33 landmarks * 3 coordinates = 99 features)
            if hasattr(frame_data, 'poseLandmarks') and frame_data.poseLandmarks:
                for landmark in frame_data.poseLandmarks:
                    all_coords.extend([landmark.x, landmark.y, getattr(landmark, 'z', 0)])
            else:
                all_coords.extend([0.0] * (33 * 3))
            
            # Hand landmarks (42 landmarks * 3 coordinates = 126 features)
            hand_coords = [0.0] * (42 * 3)
            hand_idx = 0
            
            # Right hand (21 landmarks)
            if hasattr(frame_data, 'rightHandLandmarks') and frame_data.rightHandLandmarks:
                for landmark in frame_data.rightHandLandmarks:
                    if hand_idx < 21:
                        idx = hand_idx * 3
                        hand_coords[idx:idx+3] = [landmark.x, landmark.y, getattr(landmark, 'z', 0)]
                        hand_idx += 1
            
            # Left hand (21 landmarks)
            if hasattr(frame_data, 'leftHandLandmarks') and frame_data.leftHandLandmarks:
                for landmark in frame_data.leftHandLandmarks:
                    if hand_idx < 42:
                        idx = hand_idx * 3
                        hand_coords[idx:idx+3] = [landmark.x, landmark.y, getattr(landmark, 'z', 0)]
                        hand_idx += 1
            
            all_coords.extend(hand_coords)
            
            # Pad to match training data length (1500 features)
            max_features = 1500
            if len(all_coords) > max_features:
                all_coords = all_coords[:max_features]
            else:
                # Pad with zeros to reach expected length
                while len(all_coords) < max_features:
                    all_coords.append(0.0)
            
            return np.array(all_coords)
            
        except Exception as e:
            print(f"❌ Statistical feature extraction error: {e}")
            return None

    def predict_with_lstm(self, landmarks_sequence):
        """Predict using LSTM model"""
        if not self.lstm_model:
            return None, 0.0
        
        try:
            features = self.extract_sequence_features_for_lstm(landmarks_sequence)
            if features is None:
                return None, 0.0
            
            # Add batch dimension
            features = np.expand_dims(features, axis=0)
            
            # Predict
            prediction = self.lstm_model.predict(features, verbose=0)
            predicted_class = np.argmax(prediction)
            confidence = np.max(prediction)
            
            gesture_name = self.id_to_gesture.get(predicted_class, "unknown")
            return gesture_name, float(confidence)
            
        except Exception as e:
            print(f"❌ LSTM prediction error: {e}")
            return None, 0.0

    def predict_with_classifier(self, landmarks_sequence):
        """Predict using RandomForest classifier"""
        if not self.custom_classifier:
            return None, 0.0
        
        try:
            features = self.extract_statistical_features(landmarks_sequence)
            if features is None:
                return None, 0.0
            
            # Scale features
            features_scaled = self.custom_scaler.transform([features])
            
            # Predict
            prediction = self.custom_classifier.predict(features_scaled)[0]
            confidence = np.max(self.custom_classifier.predict_proba(features_scaled))
            
            gesture_name = self.id_to_gesture.get(prediction, "unknown")
            return gesture_name, float(confidence)
            
        except Exception as e:
            print(f"❌ Classifier prediction error: {e}")
            return None, 0.0

    def predict(self, data):
        """Main prediction function for custom gestures with comprehensive motion detection"""
        current_time = time.time()
        
        # Check if we should make a prediction
        should_predict, reason = self.should_predict(data)
        
        if not should_predict:
            # Only print debug info occasionally to reduce spam
            if reason == "rate_limited" and len(self.motion_history) % 60 == 0:
                print(f"⏸️ Rate limited - {self.min_prediction_interval}s cooldown")
            
            # Return silent status - no prediction being made
            return {
                "status": 200,
                "sign_name": "no_gesture_detected",
                "pred_sentence": "",
                "model_type": "custom_gestures",
                "confidence": 0.0,
                "reason": reason,
                "timestamp": current_time,
                "silent": True  # Flag to indicate this shouldn't be displayed
            }
        
        print(f"🔍 Custom Model: Processing {len(data)} frames for ACTIVE GESTURE prediction")
        
        if len(data) == 0:
            return {
                "status": 400,
                "sign_name": "No data",
                "pred_sentence": "",
                "model_type": "custom_gestures",
                "confidence": 0.0
            }
        
        # Try LSTM first, then fallback to classifier
        gesture_name = None
        confidence = 0.0
        model_used = "none"
        
        if self.lstm_model:
            gesture_name, confidence = self.predict_with_lstm(data)
            model_used = "lstm"
            if gesture_name and confidence > 0.7:  # Higher confidence threshold
                print(f"🧠 LSTM prediction: {gesture_name} (confidence: {confidence:.3f})")
        
        if (not gesture_name or confidence < 0.7) and self.custom_classifier:
            gesture_name, confidence = self.predict_with_classifier(data)
            model_used = "random_forest"
            if gesture_name and confidence > 0.6:  # Higher confidence threshold
                print(f"🌳 RandomForest prediction: {gesture_name} (confidence: {confidence:.3f})")
        
        # Higher confidence thresholds for final prediction
        confidence_threshold = 0.7 if model_used == "lstm" else 0.6
        
        if gesture_name and gesture_name != "unknown" and confidence > confidence_threshold:
            self.sign_name = gesture_name
            self.pred_sentence = gesture_name
            print(f"✅ CONFIDENT GESTURE DETECTED: {gesture_name} (confidence: {confidence:.3f})")
            
            return {
                "status": 200,
                "sign_name": gesture_name,
                "pred_sentence": gesture_name,
                "gesture": gesture_name,  # For frontend compatibility
                "confidence": confidence,
                "model_type": "custom_gestures",
                "model_used": model_used,
                "timestamp": current_time
            }
        else:
            print(f"❌ Gesture detected but low confidence: {gesture_name or 'none'} ({confidence:.3f})")
            return {
                "status": 200,
                "sign_name": "no_gesture_detected",
                "pred_sentence": "",
                "gesture": "no_gesture_detected",  # For frontend compatibility
                "confidence": confidence,
                "model_type": "custom_gestures",
                "model_used": model_used,
                "timestamp": current_time,
                "reason": "low_confidence"
            }
