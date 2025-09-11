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

    def extract_features_from_landmarks_df(self, landmarks_df):
        """Extract features from processed landmarks DataFrame"""
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
            
            # Extract features using the same method as in training
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
                
                # 9-region analysis (40 features)  
                regions = []
                for i in range(3):
                    for j in range(3):
                        start_row, end_row = i*5, (i+1)*5
                        start_col, end_col = j*2, (j+1)*2 if j < 2 else 5
                        region = coord_matrix[start_row:end_row, start_col:end_col, :].flatten()
                        if len(region) > 0:
                            regions.extend([
                                np.mean(region), np.std(region), 
                                np.max(region), np.min(region)
                            ])
                        else:
                            regions.extend([0, 0, 0, 0])
                
                # Ensure we have exactly 40 region features
                while len(regions) < 40:
                    regions.append(0)
                features.extend(regions[:40])
                
                # Ensure exactly 200 features
                features = features[:200]
                while len(features) < 200:
                    features.append(0)
                
                return np.array(features, dtype=np.float32)
            
            # Get frames and extract features for each
            frames = sorted(all_landmarks['frame'].unique().tolist())
            if not frames:
                return None, 0.0
            
            # Extract features for up to 30 frames (same as training)
            sequence_features = []
            for frame_num in frames[:30]:
                frame_df = all_landmarks[all_landmarks['frame'] == frame_num]
                features = extract_simple_features(frame_df)
                sequence_features.append(features)
            
            # Pad sequence to exactly 30 frames
            while len(sequence_features) < 30:
                sequence_features.append(np.zeros(200, dtype=np.float32))
            
            # Convert to numpy array and add batch dimension
            sequence_array = np.array(sequence_features[:30], dtype=np.float32)  # (30, 200)
            sequence_batch = np.expand_dims(sequence_array, axis=0)  # (1, 30, 200)
            
            # Predict using LSTM
            prediction = self.custom_lstm_model.predict(sequence_batch, verbose=0)
            
            # Apply softmax to get proper probabilities
            exp_scores = np.exp(prediction[0] - np.max(prediction[0]))  # Numerical stability
            probabilities = exp_scores / np.sum(exp_scores)
            
            confidence = float(np.max(probabilities))
            predicted_class = int(np.argmax(probabilities))
            
            # Debug output
            print(f"🔍 LSTM raw output: {prediction[0]}")
            print(f"🔍 LSTM probabilities: {probabilities}")
            print(f"🔍 LSTM confidence: {confidence:.3f}, predicted_class: {predicted_class}")
            
            # Check for no action using motion analysis
            if self._is_no_action(sequence_array):
                print("🚫 No action detected - insufficient motion")
                return "no_action", 1.0
            
            # Enhanced confidence threshold with no-action fallback
            confidence_threshold = 0.3  # Increased to 30% for better accuracy
            if confidence < confidence_threshold:
                print(f"⚠️ LSTM confidence too low: {confidence:.3f} - treating as no_action")
                return "no_action", 1.0
            
            # Convert class index back to gesture name
            gesture_name = self.custom_label_encoder.inverse_transform([predicted_class])[0]
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"Custom LSTM prediction error: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0

    def _is_no_action(self, sequence_array):
        """
        Detect if the sequence represents no meaningful action/gesture
        """
        try:
            # Calculate motion variance across the sequence
            if len(sequence_array) < 3:
                return True  # Too short sequence
            
            # Calculate frame-to-frame differences
            frame_diffs = np.diff(sequence_array, axis=0)
            
            # Calculate overall motion magnitude
            motion_magnitude = np.mean(np.sum(np.abs(frame_diffs), axis=1))
            
            # Calculate variance in landmark positions
            position_variance = np.mean(np.var(sequence_array, axis=0))
            
            # Thresholds for no action detection
            motion_threshold = 0.008  # Minimum motion required
            variance_threshold = 0.005  # Minimum variance required
            
            # Check if motion is below thresholds
            is_static = motion_magnitude < motion_threshold and position_variance < variance_threshold
            
            print(f"🔍 Motion analysis - Magnitude: {motion_magnitude:.6f}, Variance: {position_variance:.6f}, Static: {is_static}")
            
            return is_static
            
        except Exception as e:
            print(f"Error in no-action detection: {e}")
            return False

    def process_landmarks(self, landmarks: Optional[List], landmark_type: str) -> pd.DataFrame:
        """
        Convert a list of landmarks into a structured DataFrame.
        """
        if not landmarks:
            return pd.DataFrame()

        return pd.DataFrame(
            [(i, point.x, point.y, point.z) for i, point in enumerate(landmarks)],
            columns=["landmark_index", "x", "y", "z"]
        ).assign(type=landmark_type)

    def create_frame_landmark_df(self, data) -> pd.DataFrame:
        """
        Create a DataFrame for all landmarks from a LandmarkData object.
        """
        # Process each type of landmark into a DataFrame
        landmarks = pd.concat(
            [self.process_landmarks(getattr(data, key), value) for key, value in self.landmark_types.items()],
            ignore_index=True
        )
        landmarks["frame"] = data.frameNumber

        # Fill missing landmarks for types not detected
        for type_, count in self.landmark_counts.items():
            if landmarks[landmarks["type"] == type_].empty:
                missing_df = pd.DataFrame({
                    "landmark_index": range(count),
                    "x": np.nan,
                    "y": np.nan,
                    "z": np.nan,
                    "type": type_,
                    "frame": data.frameNumber
                })
                landmarks = pd.concat([landmarks, missing_df], ignore_index=True)

        # Drop unused landmark indices (e.g., Iris) and reset the index
        landmarks = landmarks[landmarks["landmark_index"] < 468].reset_index(drop=True)
        return landmarks

    def predict(self, data):
        """
        Enhanced prediction handling both original and custom gestures.
        """
        print(f"🔍 Received {len(data)} frames for prediction")
        
        if len(data) == 0:
            print("No data received!")
            return {
                "status": 400,
                "sign_name": "No data",
                "unique_signs": [],
                "pred_sentence": "",
            }
        
        if data[0].timeInSeconds <= 4:
            print("Resetting state - early frame detected")
            self.sign_name = "No Movement Detected"
            self.unique_signs.clear()
            self.pred_sentence = ""

        # Process the current frame's landmarks efficiently
        processed_landmarks = [
            self.create_frame_landmark_df(data_i) for data_i in data
        ]
        self.all_landmarks = pd.concat(
            processed_landmarks, ignore_index=True
        ).sort_values(by=["frame", "type", "landmark_index"]).reset_index(drop=True)

        print(f"Processed landmarks shape: {self.all_landmarks.shape}")
        
        # Try both predictions and compare confidences
        custom_gesture, custom_confidence = self.predict_custom_gesture(self.all_landmarks)
        
        # Always run original model prediction first
        print("🔄 Running original model prediction")
        
        # Prepare data for original prediction
        data_columns = ["x", "y", "z"]
        frames_count = len(self.all_landmarks["frame"].unique())
        
        if frames_count == 0:
            print("No frames to process!")
            return {
                "status": 400,
                "sign_name": "No frames",
                "unique_signs": [],
                "pred_sentence": "",
            }
        
        xyz_np = self.all_landmarks[data_columns].to_numpy().reshape(
            frames_count, 543, len(data_columns)
        ).astype(np.float32)
        
        print(f"Input tensor shape: {xyz_np.shape}")

        # Run the original model prediction
        prediction = self.model(inputs=xyz_np)
        # Some TFLite models return logits that are not normalized; convert to softmax probabilities
        logits = np.squeeze(prediction['outputs'])
        try:
            # Stable softmax
            logits_shifted = logits - np.max(logits)
            exp_vals = np.exp(logits_shifted)
            probs = exp_vals / np.sum(exp_vals)
        except Exception:
            # Fallback in case of unexpected shape
            probs = logits
            if probs.ndim > 1:
                probs = probs.ravel()
            # Normalize to [0,1]
            min_v, max_v = float(np.min(probs)), float(np.max(probs))
            if max_v > min_v:
                probs = (probs - min_v) / (max_v - min_v)

        sign_index = int(np.argmax(probs))
        original_confidence = float(np.max(probs))
        original_sign = self.ORD2SIGN.get(sign_index, "Unknown Sign")
        
        print(f"📊 Original model: {original_sign} (index: {sign_index}, confidence: {original_confidence:.1%})")
        if custom_gesture:
            print(f"🎯 Custom model: {custom_gesture} (confidence: {custom_confidence:.1%})")

        # Decision logic with LOWERED confidence thresholds for better detection:
        # - Prefer original unless: (a) custom is strong and original is weak, or (b) custom is very strong
        strong_custom = custom_gesture and (custom_confidence >= 0.5)  # Lowered from 0.8 to 0.5
        weak_original = original_confidence < 0.6
        good_custom = custom_gesture and (custom_confidence >= 0.3)    # Lowered from 0.7 to 0.3
        
        # More aggressive custom gesture preference
        use_custom = (custom_gesture and (strong_custom or (good_custom and weak_original) or custom_confidence >= 0.2))
        
        if use_custom:
            print(f"✅ Using custom gesture: {custom_gesture} (confidence: {custom_confidence:.1%})")
            self.sign_name = custom_gesture
            prediction_type = "custom"
            final_confidence = custom_confidence
        else:
            print(f"✅ Using original gesture: {original_sign} (confidence: {original_confidence:.1%})")
            self.sign_name = original_sign
            prediction_type = "original"
            final_confidence = original_confidence

        # Handle no_action and other special cases
        if self.sign_name == "no_action":
            # Don't add no_action to sentences or unique signs
            print("🚫 No action detected - not adding to sentence")
            # Keep existing sentence and unique signs unchanged
        elif self.sign_name in {"", "jeans"}:
            self.sign_name = "No Movement Detected"
            self.unique_signs.clear()
            self.pred_sentence = ""
        else:
            # Add valid gestures to unique signs and sentence
            if self.sign_name not in self.unique_signs:
                self.unique_signs.append(self.sign_name)
            if len(self.unique_signs) > 1:
                self.pred_sentence = " ".join(self.unique_signs)

        # Clear landmarks for the next prediction cycle
        self.all_landmarks = None

        return {
            "status": 200,
            "sign_name": self.sign_name,
            "unique_signs": self.unique_signs,
            "pred_sentence": self.pred_sentence,
            "prediction_type": prediction_type,
            "confidence": final_confidence
        }
