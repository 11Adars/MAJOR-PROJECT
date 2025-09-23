import tensorflow as tf
import pandas as pd
import numpy as np
import os
from typing import Optional, List

# Optional Gemini sentence generation support
try:
    from module.llm.asl_sentence_generator import generate_sentence as _gen_sent
except Exception:  # If dependency or key missing, fallback gracefully
    _gen_sent = None

class IsolatedASLRecognition:
    def __init__(self, model_path: str):
        # API state variables
        self.all_landmarks = None
        self.unique_signs = []
        self.sign_name = ""
        self.pred_sentence = ""
        self._last_sentence_signature = None  # for debouncing LLM calls

        # Initialize TensorFlow Lite model
        self.interpreter = tf.lite.Interpreter(model_path=model_path + "/model.tflite")
        self.interpreter.allocate_tensors()
        self.model = self.interpreter.get_signature_runner("serving_default")

        # Load dictionary of signs
        dict_sign = pd.read_csv(model_path + "/dict_sign.csv")
        self.ORD2SIGN = dict_sign.set_index('sign_ord')['sign'].to_dict()

        # Landmark counts and types
        self.landmark_counts = {"face": 478, "pose": 33, "left_hand": 21, "right_hand": 21}
        self.landmark_types = {
            "faceLandmarks": "face",
            "poseLandmarks": "pose",
            "leftHandLandmarks": "left_hand",
            "rightHandLandmarks": "right_hand",
        }

    def reset(self):
        """Reset accumulated signs and sentence generation state."""
        self.unique_signs.clear()
        self.pred_sentence = ""
        self.sign_name = ""
        self._last_sentence_signature = None

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
        Handle predictions based on the incoming landmark data.
        Uses TensorFlow Lite model for sign language recognition.
        """
        print(data)
        if data[0].timeInSeconds <= 4:
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

        # Prepare data for prediction
        data_columns = ["x", "y", "z"]
        frames_count = len(self.all_landmarks["frame"].unique())
        xyz_np = self.all_landmarks[data_columns].to_numpy().reshape(
            frames_count, 543, len(data_columns)
        ).astype(np.float32)

        # Run the model prediction
        prediction = self.model(inputs=xyz_np)
        sign_index = prediction['outputs'].argmax()
        self.sign_name = self.ORD2SIGN.get(sign_index, "Unknown Sign")

        # Reset state or update unique signs and sentence
        if self.sign_name in {"", "jeans"}:
            self.sign_name = "No Movement Detected"
            self.unique_signs.clear()
            self.pred_sentence = ""
        else:
            if self.sign_name not in self.unique_signs:
                self.unique_signs.append(self.sign_name)
            if len(self.unique_signs) > 1:
                # Decide whether to use Gemini sentence generation
                enable_llm = os.getenv("ENABLE_SENTENCE_GEN", "false").lower() == "true"
                have_key = bool(os.getenv("GOOGLE_API_KEY"))
                signature = "|".join(self.unique_signs)
                use_cached = signature == self._last_sentence_signature
                if enable_llm and have_key and _gen_sent and not use_cached:
                    try:
                        # Call Gemini to refine sentence
                        self.pred_sentence = _gen_sent(self.unique_signs)
                        self._last_sentence_signature = signature
                    except Exception:
                        # Fallback to simple concatenation if LLM fails
                        self.pred_sentence = " ".join(self.unique_signs)
                elif not use_cached and not enable_llm:
                    self.pred_sentence = " ".join(self.unique_signs)
                elif not use_cached and enable_llm and (not have_key or not _gen_sent):
                    # LLM requested but unavailable: fallback
                    self.pred_sentence = " ".join(self.unique_signs)

        # Clear landmarks for the next prediction cycle
        self.all_landmarks = None

        return {
            "status": 200,
            "sign": self.sign_name,
            "list_sign": self.unique_signs,
            "sentence": self.pred_sentence,
        }