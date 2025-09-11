import tensorflow as tf
import pandas as pd
import numpy as np
from typing import Optional, List
import joblib
import json
from pathlib import Path
import mediapipe as mp

class OptimizedASLRecognition:
    def __init__(self, model_path: str):
        # API state variables
        self.all_landmarks = None
        self.unique_signs = []
        self.sign_name = ""
        self.pred_sentence = ""

        # Initialize TensorFlow Lite model for original 250 gestures
        self.interpreter = tf.lite.Interpreter(model_path=model_path + "/model.tflite")
        self.interpreter.allocate_tensors()
        self.model = self.interpreter.get_signature_runner("serving_default")

        # Load dictionary of signs
        dict_sign = pd.read_csv(model_path + "/dict_sign.csv")
        self.ORD2SIGN = dict_sign.set_index('sign_ord')['sign'].to_dict()
        
        # Initialize MediaPipe for custom gesture processing
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=0,
            enable_segmentation=False,
            refine_face_landmarks=False
        )
        
        # Custom LSTM model variables
        self.custom_model = None
        self.custom_labels = None
        self.custom_mapping = {}
        self.custom_sequence = []
        self.sequence_length = 30
        self.feature_dim = 258
        
        self.load_custom_model()

        # Landmark configuration
        self.landmark_counts = {"face": 478, "pose": 33, "left_hand": 21, "right_hand": 21}
        self.landmark_types = {
            "faceLandmarks": "face",
            "poseLandmarks": "pose",
            "leftHandLandmarks": "left_hand",
            "rightHandLandmarks": "right_hand",
        }

    def load_custom_model(self):
        """Load the custom LSTM model and associated files"""
        try:
            model_path = Path("custom_gesture_lstm.h5")
            labels_path = Path("custom_gesture_labels.pkl")
            mapping_path = Path("custom_gesture_mapping.json")
            
            if model_path.exists() and labels_path.exists() and mapping_path.exists():
                # Load LSTM model
                self.custom_model = tf.keras.models.load_model(model_path)
                
                # Load label encoder
                self.custom_labels = joblib.load(labels_path)
                
                # Load gesture mapping
                with open(mapping_path, 'r') as f:
                    self.custom_mapping = json.load(f)
                
                print(f"✅ Custom LSTM model loaded: {list(self.custom_mapping.keys())}")
                print(f"📊 Model expects sequences of shape: ({self.sequence_length}, {self.feature_dim})")
            else:
                print("⚠️  Custom LSTM model not found. Train using custom_gesture_trainer.py first.")
                
        except Exception as e:
            print(f"❌ Error loading custom model: {e}")

    def extract_custom_landmarks(self, landmarks_df):
        """Extract landmarks in the same format as training"""
        try:
            landmarks = []
            
            # Face landmarks (key points only - 10 points)
            face_data = landmarks_df[landmarks_df['type'] == 'face'].sort_values('landmark_index')
            face_key_points = [0, 10, 152, 234, 454, 267, 269, 270, 271, 272]
            
            for idx in face_key_points:
                face_point = face_data[face_data['landmark_index'] == idx]
                if not face_point.empty:
                    landmarks.extend([face_point.iloc[0]['x'], face_point.iloc[0]['y'], face_point.iloc[0]['z']])
                else:
                    landmarks.extend([0, 0, 0])
            
            # Pose landmarks (33 points)
            pose_data = landmarks_df[landmarks_df['type'] == 'pose'].sort_values('landmark_index')
            for i in range(33):
                pose_point = pose_data[pose_data['landmark_index'] == i]
                if not pose_point.empty:
                    landmarks.extend([pose_point.iloc[0]['x'], pose_point.iloc[0]['y'], pose_point.iloc[0]['z']])
                else:
                    landmarks.extend([0, 0, 0])
            
            # Left hand landmarks (21 points)
            left_data = landmarks_df[landmarks_df['type'] == 'left_hand'].sort_values('landmark_index')
            for i in range(21):
                left_point = left_data[left_data['landmark_index'] == i]
                if not left_point.empty:
                    landmarks.extend([left_point.iloc[0]['x'], left_point.iloc[0]['y'], left_point.iloc[0]['z']])
                else:
                    landmarks.extend([0, 0, 0])
            
            # Right hand landmarks (21 points)
            right_data = landmarks_df[landmarks_df['type'] == 'right_hand'].sort_values('landmark_index')
            for i in range(21):
                right_point = right_data[right_data['landmark_index'] == i]
                if not right_point.empty:
                    landmarks.extend([right_point.iloc[0]['x'], right_point.iloc[0]['y'], right_point.iloc[0]['z']])
                else:
                    landmarks.extend([0, 0, 0])
            
            # Add motion features placeholder
            landmarks.extend([0, 0, 0])
            
            return np.array(landmarks[:self.feature_dim])
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return np.zeros(self.feature_dim)

    def predict_custom_gesture(self, all_landmarks):
        """Predict using custom LSTM model"""
        if self.custom_model is None:
            return None, 0.0
        
        try:
            # Extract landmarks for current frame
            current_landmarks = self.extract_custom_landmarks(all_landmarks)
            
            # Add to sequence
            self.custom_sequence.append(current_landmarks)
            
            # Keep only the last sequence_length frames
            if len(self.custom_sequence) > self.sequence_length:
                self.custom_sequence = self.custom_sequence[-self.sequence_length:]
            
            # Need full sequence for prediction
            if len(self.custom_sequence) < self.sequence_length:
                return None, 0.0
            
            # Prepare sequence for prediction
            sequence = np.array(self.custom_sequence)
            sequence = sequence.reshape(1, self.sequence_length, self.feature_dim)
            
            # Predict
            predictions = self.custom_model.predict(sequence, verbose=0)
            confidence = float(np.max(predictions))
            predicted_class = np.argmax(predictions)
            
            # Get gesture name
            gesture_name = self.custom_labels.classes_[predicted_class]
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"Custom LSTM prediction error: {e}")
            return None, 0.0

    def process_landmarks(self, landmarks: Optional[List], landmark_type: str) -> pd.DataFrame:
        """Convert a list of landmarks into a structured DataFrame."""
        if not landmarks:
            return pd.DataFrame()

        return pd.DataFrame(
            [(i, point.x, point.y, point.z) for i, point in enumerate(landmarks)],
            columns=["landmark_index", "x", "y", "z"]
        ).assign(type=landmark_type)

    def create_frame_landmark_df(self, data) -> pd.DataFrame:
        """Create a DataFrame for all landmarks from a LandmarkData object."""
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

        # Drop unused landmark indices and reset the index
        landmarks = landmarks[landmarks["landmark_index"] < 468].reset_index(drop=True)
        return landmarks

    def predict(self, data):
        """
        Optimized prediction handling both original and custom gestures.
        """
        print(f"🔍 Received {len(data)} frames for prediction")
        
        if len(data) == 0:
            return {
                "status": 400,
                "sign_name": "No data",
                "unique_signs": [],
                "pred_sentence": "",
                "prediction_type": "error",
                "confidence": 0.0
            }
        
        # Reset on early frames
        if data[0].timeInSeconds <= 4:
            print("Resetting state - early frame detected")
            self.sign_name = "No Movement Detected"
            self.unique_signs.clear()
            self.pred_sentence = ""
            self.custom_sequence.clear()

        # Process the current frame's landmarks
        processed_landmarks = [
            self.create_frame_landmark_df(data_i) for data_i in data
        ]
        self.all_landmarks = pd.concat(
            processed_landmarks, ignore_index=True
        ).sort_values(by=["frame", "type", "landmark_index"]).reset_index(drop=True)

        print(f"Processed landmarks shape: {self.all_landmarks.shape}")
        
        # Try custom gesture prediction first (LSTM)
        custom_gesture, custom_confidence = self.predict_custom_gesture(self.all_landmarks)
        
        # Original model prediction
        print("🔄 Running original model prediction")
        
        # Prepare data for original prediction
        data_columns = ["x", "y", "z"]
        frames_count = len(self.all_landmarks["frame"].unique())
        
        if frames_count == 0:
            return {
                "status": 400,
                "sign_name": "No frames",
                "unique_signs": [],
                "pred_sentence": "",
                "prediction_type": "error",
                "confidence": 0.0
            }
        
        xyz_np = self.all_landmarks[data_columns].to_numpy().reshape(
            frames_count, 543, len(data_columns)
        ).astype(np.float32)
        
        # Run the original model prediction
        prediction = self.model(inputs=xyz_np)
        logits = np.squeeze(prediction['outputs'])
        
        # Apply softmax
        try:
            logits_shifted = logits - np.max(logits)
            exp_vals = np.exp(logits_shifted)
            probs = exp_vals / np.sum(exp_vals)
        except Exception:
            probs = logits
            if probs.ndim > 1:
                probs = probs.ravel()
            min_v, max_v = float(np.min(probs)), float(np.max(probs))
            if max_v > min_v:
                probs = (probs - min_v) / (max_v - min_v)

        sign_index = int(np.argmax(probs))
        original_confidence = float(np.max(probs))
        original_sign = self.ORD2SIGN.get(sign_index, "Unknown Sign")
        
        print(f"📊 Original model: {original_sign} (confidence: {original_confidence:.1%})")
        if custom_gesture:
            print(f"🎯 Custom LSTM: {custom_gesture} (confidence: {custom_confidence:.1%})")

        # Decision logic: Prefer custom if confidence is high and significantly better
        use_custom = False
        if custom_gesture and custom_confidence > 0.7:  # High confidence threshold
            if custom_confidence > original_confidence + 0.2:  # Significantly better
                use_custom = True
            elif custom_confidence > 0.85:  # Very high confidence
                use_custom = True
        
        if use_custom:
            print(f"✅ Using custom gesture: {custom_gesture}")
            self.sign_name = custom_gesture
            prediction_type = "custom"
            final_confidence = custom_confidence
        else:
            print(f"✅ Using original gesture: {original_sign}")
            self.sign_name = original_sign
            prediction_type = "original"
            final_confidence = original_confidence

        # Update state
        if self.sign_name in {"", "jeans"}:
            self.sign_name = "No Movement Detected"
            self.unique_signs.clear()
            self.pred_sentence = ""
        else:
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
