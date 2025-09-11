#!/usr/bin/env python3
"""
Test Custom Gestures
Quick test to verify your trained custom gestures work
"""

import cv2
import mediapipe as mp
import numpy as np
import joblib
import json
from pathlib import Path

class CustomGestureTest:
    def __init__(self):
        # Load trained model
        try:
            self.classifier = joblib.load("custom_gesture_classifier.pkl")
            self.scaler = joblib.load("custom_gesture_scaler.pkl")
            
            with open("custom_gesture_mapping.json", 'r') as f:
                self.gesture_mapping = json.load(f)
            
            self.id_to_gesture = {v: k for k, v in self.gesture_mapping.items()}
            self.model_loaded = True
            print("✅ Custom gesture model loaded successfully")
            print(f"🎯 Available gestures: {list(self.gesture_mapping.keys())}")
            
        except Exception as e:
            print(f"❌ Could not load model: {e}")
            self.model_loaded = False
            return
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.face_mesh = self.mp_face.Face_Mesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # For sequence processing
        self.frame_buffer = []
        self.buffer_size = 30  # Process every 30 frames
    
    def extract_landmarks(self, results_hands, results_pose, results_face):
        """Extract landmarks from MediaPipe results"""
        landmarks = []
        
        # Face landmarks (468 points)
        if results_face.multi_face_landmarks:
            for face_landmarks in results_face.multi_face_landmarks:
                for landmark in face_landmarks.landmark:
                    landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * (468 * 3))
        
        # Pose landmarks (33 points)
        if results_pose.pose_landmarks:
            for landmark in results_pose.pose_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * (33 * 3))
        
        # Hand landmarks (42 points total for 2 hands)
        hand_data = [0.0] * (42 * 3)
        if results_hands.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results_hands.multi_hand_landmarks):
                if hand_idx < 2:
                    start_idx = hand_idx * 21 * 3
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        idx = start_idx + i * 3
                        hand_data[idx:idx+3] = [landmark.x, landmark.y, landmark.z]
        
        landmarks.extend(hand_data)
        return landmarks
    
    def extract_sequence_features(self, landmark_sequence):
        """Extract features from a sequence of landmarks (same as training)"""
        try:
            landmarks = np.array(landmark_sequence)
            
            # Calculate features (same as training script)
            features = []
            
            # Statistical features
            features.extend([
                np.mean(landmarks),
                np.std(landmarks),
                np.min(landmarks),
                np.max(landmarks),
                np.median(landmarks)
            ])
            
            # Hand movement features
            # Approximate hand positions (landmarks around index 500-540)
            if landmarks.shape[1] > 500:
                hand_data = landmarks[:, 500:540]  # Approximate hand region
                
                features.extend([
                    np.mean(hand_data[:, ::3]),  # X coordinates
                    np.std(hand_data[:, ::3]),
                    np.mean(hand_data[:, 1::3]), # Y coordinates
                    np.std(hand_data[:, 1::3]),
                    np.max(hand_data[:, ::3]) - np.min(hand_data[:, ::3]),  # X range
                    np.max(hand_data[:, 1::3]) - np.min(hand_data[:, 1::3])  # Y range
                ])
            else:
                features.extend([0] * 6)
            
            # Motion features
            if len(landmarks) > 1:
                diffs = np.diff(landmarks, axis=0)
                features.extend([
                    np.mean(np.abs(diffs)),
                    np.std(diffs),
                    np.max(np.abs(diffs))
                ])
            else:
                features.extend([0] * 3)
            
            # Sample key frames
            sample_indices = [0, len(landmarks)//2, -1] if len(landmarks) > 2 else [0]
            
            for idx in sample_indices:
                if idx < len(landmarks):
                    sample_frame = landmarks[idx]
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
            print(f"Feature extraction error: {e}")
            return None
    
    def predict_gesture(self):
        """Predict gesture from current frame buffer"""
        if len(self.frame_buffer) < 10:  # Need minimum frames
            return None, 0.0
        
        # Extract features
        features = self.extract_sequence_features(self.frame_buffer)
        
        if features is None:
            return None, 0.0
        
        try:
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict
            prediction = self.classifier.predict(features_scaled)[0]
            confidence = np.max(self.classifier.predict_proba(features_scaled))
            
            gesture_name = self.id_to_gesture.get(prediction, "unknown")
            
            return gesture_name, confidence
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return None, 0.0
    
    def test_gestures(self):
        """Main testing function"""
        if not self.model_loaded:
            print("❌ Model not loaded. Please train custom gestures first.")
            return
        
        cap = cv2.VideoCapture(0)
        
        print("🎥 Testing Custom Gestures")
        print("📋 Instructions:")
        print("  - Perform your trained gestures in front of the camera")
        print("  - Predictions will appear on screen")
        print("  - Press 'q' to quit")
        
        last_prediction = ""
        prediction_count = 0
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                continue
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            
            # Process with MediaPipe
            results_hands = self.hands.process(image_rgb)
            results_pose = self.pose.process(image_rgb)
            results_face = self.face_mesh.process(image_rgb)
            
            # Convert back to BGR
            image_rgb.flags.writeable = True
            image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            
            # Draw landmarks
            if results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            if results_pose.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    image, results_pose.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Extract landmarks and add to buffer
            landmarks = self.extract_landmarks(results_hands, results_pose, results_face)
            self.frame_buffer.append(landmarks)
            
            # Maintain buffer size
            if len(self.frame_buffer) > self.buffer_size:
                self.frame_buffer.pop(0)
            
            # Predict every few frames
            if len(self.frame_buffer) >= 20 and len(self.frame_buffer) % 10 == 0:
                gesture, confidence = self.predict_gesture()
                
                if gesture and confidence > 0.6:  # Confidence threshold
                    if gesture == last_prediction:
                        prediction_count += 1
                    else:
                        last_prediction = gesture
                        prediction_count = 1
                    
                    # Display prediction
                    if prediction_count >= 2:  # Stable prediction
                        cv2.putText(image, f"Gesture: {gesture}", 
                                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(image, f"Confidence: {confidence:.2%}", 
                                   (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(image, "No gesture detected", 
                               (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display available gestures
            y_pos = 120
            cv2.putText(image, "Available gestures:", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            for gesture_name in self.gesture_mapping.keys():
                y_pos += 20
                cv2.putText(image, f"- {gesture_name}", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Custom Gesture Test', image)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

def main():
    tester = CustomGestureTest()
    tester.test_gestures()

if __name__ == "__main__":
    main()
