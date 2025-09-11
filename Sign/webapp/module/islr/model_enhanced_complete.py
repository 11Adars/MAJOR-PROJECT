import tensorflow as tf
import pandas as pd
import numpy as np
from typing import Optional, List
import joblib
import json
import ast
from pathlib import Path

class IsolatedASLRecognition:
    def __init__(self, model_path: str):
        # API state variables
        self.all_landmarks = None
        self.unique_signs = []
        self.sign_name = ""
        self.pred_sentence = ""

        # Initialize TensorFlow Lite model for original gestures
        self.interpreter = tf.lite.Interpreter(model_path=model_path + "/model.tflite")
        self.interpreter.allocate_tensors()
        self.model = self.interpreter.get_signature_runner("serving_default")

        # Load dictionary of signs
        dict_sign = pd.read_csv(model_path + "/dict_sign.csv")
        self.ORD2SIGN = dict_sign.set_index('sign_ord')['sign'].to_dict()
        
        # Initialize custom gesture classifier
        self.custom_classifier = None
        self.custom_scaler = None
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
            # Look for custom LSTM files in the webapp directory
            base_path = Path("../")
            
            lstm_model_path = base_path / "simple_custom_lstm.h5"
            labels_path = base_path / "simple_custom_labels.pkl"
            mapping_path = base_path / "simple_custom_mapping.json"
            
            if lstm_model_path.exists() and labels_path.exists() and mapping_path.exists():
                # Load LSTM model
                import tensorflow as tf
                self.custom_lstm_model = tf.keras.models.load_model(lstm_model_path)
                
                # Load label encoder
                self.custom_label_encoder = joblib.load(labels_path)
                
                # Load mapping
                with open(mapping_path, 'r') as f:
                    self.custom_mapping = json.load(f)
                
                print(f"✅ Custom LSTM classifier loaded: {list(self.custom_mapping.keys())}")
                self.custom_classifier = "lstm"  # Flag to indicate LSTM is loaded
            else:
                print("⚠️  Custom gesture classifier not found")
                self.custom_classifier = None
                
        except Exception as e:
            print(f"❌ Error loading custom classifier: {e}")
            self.custom_classifier = None

    def _is_no_action(self, all_landmarks):
        """Detect if there's meaningful hand movement or if it's just idle state"""
        try:
            if not all_landmarks or len(all_landmarks) < 3:
                return True
            
            # Get hand coordinates for recent frames
            recent_frames = all_landmarks[-10:]  # Last 10 frames
            
            hand_positions = []
            for frame_data in recent_frames:
                frame_df = pd.DataFrame(frame_data)
                if frame_df.empty:
                    continue
                
                # Get hand landmarks
                right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y']].values
                left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y']].values
                
                if len(right_hand) > 0 or len(left_hand) > 0:
                    # Calculate center of hands
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
            
            # Calculate movement variance
            positions_array = np.array(hand_positions)
            movement_variance = np.var(positions_array, axis=0)
            total_variance = np.sum(movement_variance)
            
            # Calculate frame-to-frame differences
            differences = []
            for i in range(1, len(positions_array)):
                diff = np.linalg.norm(positions_array[i] - positions_array[i-1])
                differences.append(diff)
            
            avg_movement = np.mean(differences) if differences else 0
            
            # Thresholds for no-action detection
            variance_threshold = 0.005  # Low variance indicates minimal movement
            movement_threshold = 0.008  # Low average movement indicates static pose
            
            is_static = total_variance < variance_threshold and avg_movement < movement_threshold
            
            return is_static
            
        except Exception as e:
            print(f"Error in no-action detection: {e}")
            return False

    def predict_custom_gesture(self, all_landmarks):
        """Predict using custom LSTM gesture classifier with landmark features"""
        if self.custom_classifier != "lstm":
            return None, 0.0
        
        try:
            # Check for no-action first
            if self._is_no_action(all_landmarks):
                return "no_action", 0.95
            
            # Extract features using EXACT same method as training
            def extract_simple_features(frame_df):
                """Extract 200-dimensional features from a single frame - EXACT match with training"""
                features = []
                
                if frame_df.empty:
                    return np.zeros(200)
                
                # Get hand landmarks
                right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y', 'z']].values
                left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y', 'z']].values
                pose = frame_df[frame_df['type'] == 'pose'][['x', 'y', 'z']].values
                
                # Ensure we have data
                if len(right_hand) == 0: right_hand = np.zeros((21, 3))
                if len(left_hand) == 0: left_hand = np.zeros((21, 3))
                if len(pose) == 0: pose = np.zeros((33, 3))
                
                # Pad or truncate to expected sizes
                right_hand = np.pad(right_hand, ((0, max(0, 21-len(right_hand))), (0, 0)), 'constant')[:21]
                left_hand = np.pad(left_hand, ((0, max(0, 21-len(left_hand))), (0, 0)), 'constant')[:21]
                pose = np.pad(pose, ((0, max(0, 33-len(pose))), (0, 0)), 'constant')[:33]
                
                # Combine all landmarks
                all_coords = np.vstack([right_hand, left_hand, pose])  # (75, 3)
                coords_flat = all_coords.flatten()  # 225 values
                
                # Basic statistics (20 features)
                features.extend([
                    np.mean(coords_flat), np.std(coords_flat), np.min(coords_flat), np.max(coords_flat),
                    np.median(coords_flat), np.var(coords_flat), np.ptp(coords_flat),
                    np.mean(coords_flat[coords_flat > 0]) if len(coords_flat[coords_flat > 0]) > 0 else 0,
                    len(coords_flat[coords_flat > 0.5]) / len(coords_flat),
                    len(coords_flat[coords_flat < -0.5]) / len(coords_flat),
                    np.percentile(coords_flat, 25), np.percentile(coords_flat, 75),
                    np.mean(np.abs(coords_flat)), np.std(np.abs(coords_flat)),
                    np.sum(coords_flat > 0), np.sum(coords_flat < 0),
                    np.mean(coords_flat**2), np.std(coords_flat**2),
                    np.mean(np.sqrt(np.abs(coords_flat))), np.std(np.sqrt(np.abs(coords_flat)))
                ])
                
                # Hand-specific features (40 features)
                for hand_data, hand_name in [(right_hand, 'right'), (left_hand, 'left')]:
                    hand_flat = hand_data.flatten()
                    features.extend([
                        np.mean(hand_flat), np.std(hand_flat), np.min(hand_flat), np.max(hand_flat),
                        np.median(hand_flat), np.var(hand_flat), np.ptp(hand_flat),
                        np.mean(hand_data[:, 0]), np.mean(hand_data[:, 1]), np.mean(hand_data[:, 2]),
                        np.std(hand_data[:, 0]), np.std(hand_data[:, 1]), np.std(hand_data[:, 2]),
                        np.ptp(hand_data[:, 0]), np.ptp(hand_data[:, 1]), np.ptp(hand_data[:, 2]),
                        np.mean(np.linalg.norm(hand_data, axis=1)),
                        np.std(np.linalg.norm(hand_data, axis=1)),
                        np.sum(hand_flat > 0.1), np.sum(hand_flat < -0.1)
                    ])
                
                # HSV and color histograms (30 features)
                x_coords = all_coords[:, 0]
                y_coords = all_coords[:, 1]
                z_coords = all_coords[:, 2]
                
                # Create pseudo-HSV values from coordinates
                hue_values = (x_coords + 1) * 180  # Map [-1,1] to [0,360]
                sat_values = (y_coords + 1) * 0.5  # Map [-1,1] to [0,1]
                val_values = (z_coords + 1) * 0.5  # Map [-1,1] to [0,1]
                
                h_hist, _ = np.histogram(hue_values, bins=10, range=(0, 360))
                s_hist, _ = np.histogram(sat_values, bins=10, range=(0, 1))
                v_hist, _ = np.histogram(val_values, bins=10, range=(0, 1))
                
                features.extend(h_hist.tolist())
                features.extend(s_hist.tolist())
                features.extend(v_hist.tolist())
                
                # Edge detection features (30 features)
                coord_matrix = all_coords.reshape(15, 5, 3)  # Reshape for edge detection
                edges_x = np.abs(np.diff(coord_matrix[:, :, 0], axis=0)).flatten()
                edges_y = np.abs(np.diff(coord_matrix[:, :, 1], axis=1)).flatten()
                
                edge_features = []
                for edge_data in [edges_x, edges_y]:
                    if len(edge_data) > 0:
                        edge_features.extend([
                            np.mean(edge_data), np.std(edge_data), np.max(edge_data),
                            np.min(edge_data), np.sum(edge_data > np.mean(edge_data))
                        ])
                    else:
                        edge_features.extend([0, 0, 0, 0, 0])
                
                # Add padding to reach 30
                while len(edge_features) < 30:
                    edge_features.append(0)
                features.extend(edge_features[:30])
                
                # Texture and contour features (40 features)
                for i in range(3):  # For x, y, z coordinates
                    coord_channel = all_coords[:, i].reshape(15, 5)
                    
                    # Texture features
                    features.extend([
                        np.mean(coord_channel), np.std(coord_channel),
                        np.var(coord_channel), np.ptp(coord_channel),
                        np.mean(np.abs(np.gradient(coord_channel.flatten()))),
                        np.std(np.abs(np.gradient(coord_channel.flatten()))),
                        np.mean(coord_channel**2), np.std(coord_channel**2),
                        np.sum(coord_channel > np.mean(coord_channel)),
                        len(np.where(np.diff(np.sign(coord_channel.flatten())))[0])  # Zero crossings
                    ])
                
                # Additional motion features (40 features) 
                motion_features = []
                
                # Global motion features
                center_of_mass = np.mean(all_coords, axis=0)
                distances_from_center = np.linalg.norm(all_coords - center_of_mass, axis=1)
                motion_features.extend([
                    np.mean(distances_from_center), np.std(distances_from_center),
                    np.max(distances_from_center), np.min(distances_from_center),
                    np.median(distances_from_center)
                ])
                
                # Hand spread features
                for hand_data in [right_hand, left_hand]:
                    if len(hand_data) > 0:
                        hand_center = np.mean(hand_data, axis=0)
                        hand_spread = np.linalg.norm(hand_data - hand_center, axis=1)
                        motion_features.extend([
                            np.mean(hand_spread), np.std(hand_spread), np.max(hand_spread),
                            np.sum(hand_spread > np.mean(hand_spread)),
                            np.ptp(hand_data[:, 0]) + np.ptp(hand_data[:, 1])  # Bounding box area
                        ])
                    else:
                        motion_features.extend([0, 0, 0, 0, 0])
                
                # Velocity-like features (differences between coordinates)
                velocity_features = []
                for i in range(min(20, len(all_coords)-1)):
                    diff = all_coords[i+1] - all_coords[i]
                    velocity_features.extend([np.linalg.norm(diff), np.mean(diff), np.std(diff)])
                
                # Pad velocity features to 15
                while len(velocity_features) < 15:
                    velocity_features.append(0)
                motion_features.extend(velocity_features[:15])
                
                # Ensure motion features total 40
                while len(motion_features) < 40:
                    motion_features.append(0)
                features.extend(motion_features[:40])
                
                # Ensure exactly 200 features
                while len(features) < 200:
                    features.append(0)
                
                return np.array(features[:200])
            
            # Process landmark sequence to extract features
            if not all_landmarks:
                return None, 0.0
            
            # Extract features for each frame
            frame_features = []
            for frame_data in all_landmarks:
                frame_df = pd.DataFrame(frame_data)
                features = extract_simple_features(frame_df)
                frame_features.append(features)
            
            # Convert to numpy array
            frame_features = np.array(frame_features)
            
            # Handle sequence length (30 frames)
            sequence_length = 30
            if len(frame_features) >= sequence_length:
                # Take middle frames if too long
                start_idx = (len(frame_features) - sequence_length) // 2
                frame_features = frame_features[start_idx:start_idx + sequence_length]
            else:
                # Pad if too short
                padding_needed = sequence_length - len(frame_features)
                padding = np.zeros((padding_needed, 200))
                frame_features = np.vstack([frame_features, padding])
            
            # Reshape for LSTM prediction (1, sequence_length, features)
            X = frame_features.reshape(1, sequence_length, 200)
            
            # Make prediction
            predictions = self.custom_lstm_model.predict(X, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            # Get gesture name from label encoder
            gesture_name = self.custom_label_encoder.inverse_transform([predicted_class])[0]
            
            print(f"🔮 LSTM Prediction: {gesture_name} (confidence: {confidence:.3f})")
            
            # Apply confidence threshold
            if confidence < 0.3:  # Lower threshold for better detection
                return "no_action", confidence
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"❌ Error in custom gesture prediction: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0

    def extract_features_from_landmarks_df(self, landmarks_df):
        """Extract features from processed landmarks DataFrame (for backward compatibility)"""
        try:
            if landmarks_df.empty:
                return np.zeros(63)
            
            # Convert to array format
            data_columns = ["x", "y", "z"]
            coords = landmarks_df[data_columns].values.flatten()
            
            features = []
            
            # Basic statistics
            features.extend([
                np.mean(coords),
                np.std(coords),
                np.min(coords),
                np.max(coords),
                np.median(coords)
            ])
            
            # Hand-specific features
            try:
                # Right hand landmarks (indices for processed DataFrame)
                right_hand_data = landmarks_df[landmarks_df['type'] == 'right_hand'][data_columns].values
                left_hand_data = landmarks_df[landmarks_df['type'] == 'left_hand'][data_columns].values
                
                if len(right_hand_data) > 0:
                    features.extend([
                        np.mean(right_hand_data[:, 0]),  # x coords
                        np.mean(right_hand_data[:, 1]),  # y coords
                        np.std(right_hand_data[:, 0]),
                        np.std(right_hand_data[:, 1])
                    ])
                else:
                    features.extend([0] * 4)
                
                if len(left_hand_data) > 0:
                    features.extend([
                        np.mean(left_hand_data[:, 0]),   # x coords
                        np.mean(left_hand_data[:, 1]),   # y coords
                        np.std(left_hand_data[:, 0]),
                        np.std(left_hand_data[:, 1])
                    ])
                else:
                    features.extend([0] * 4)
                    
            except:
                features.extend([0] * 8)
            
            # Sample coordinates
            sampled_coords = coords[::max(1, len(coords)//50)][:50]
            features.extend(sampled_coords.tolist())
            
            # Pad if needed
            while len(features) < 63:
                features.append(0)
            
            return np.array(features[:63])
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return np.zeros(63)

    def format_df(self, results):
        """Format landmark results into DataFrame"""
        data = []
        for frame_data in results:
            frame_number = frame_data.get("frameNumber", 0)
            
            # Process each landmark type
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
        # Format data
        all_landmarks = self.format_df(results)
        
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
        if len(all_landmarks) == 0:
            return {
                'sign': "no_action",
                'sentence': self.pred_sentence.strip(),
                'confidence': 0.0,
                'type': 'fallback'
            }
        
        # Use original prediction method
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
