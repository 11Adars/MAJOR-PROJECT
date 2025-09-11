#!/usr/bin/env python3
"""
Simple Gesture Recording Script
Records landmark data for a new gesture using MediaPipe
"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from pathlib import Path
import time
from datetime import datetime

class GestureRecorder:
    def __init__(self, gesture_name):
        self.gesture_name = gesture_name
        self.output_dir = Path("gesture_data")
        self.output_dir.mkdir(exist_ok=True)
        
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
        
        self.face_mesh = self.mp_face.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.recorded_data = []
        
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
        
        # Hand landmarks (21 points per hand, 2 hands = 42 points)
        hand_landmarks = [0.0] * (42 * 3)
        hand_count = 0
        
        if results_hands.multi_hand_landmarks:
            for hand_landmarks_mp in results_hands.multi_hand_landmarks:
                if hand_count < 2:  # Max 2 hands
                    start_idx = hand_count * 21 * 3
                    for i, landmark in enumerate(hand_landmarks_mp.landmark):
                        if i < 21:  # Max 21 landmarks per hand
                            idx = start_idx + i * 3
                            hand_landmarks[idx:idx+3] = [landmark.x, landmark.y, landmark.z]
                    hand_count += 1
        
        landmarks.extend(hand_landmarks)
        return landmarks
    
    def save_data(self):
        """Save recorded data to CSV"""
        if not self.recorded_data:
            print("❌ No data to save!")
            return
        
        # Create DataFrame
        df = pd.DataFrame(self.recorded_data)
        
        # Save to CSV
        filename = f"{self.gesture_name}_landmarks.csv"
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False)
        
        print(f"✅ Data saved to: {filepath}")
        print(f"📊 Recorded {len(self.recorded_data)} frames")
    
    def record_gesture(self):
        """Record gesture data from webcam"""
        print(f"🎥 Recording gesture: {self.gesture_name}")
        print("=" * 50)
        print("Instructions:")
        print("📹 Position yourself in front of camera")
        print("🎬 Press SPACE to start/stop recording")
        print("⏹️  Press 'q' to quit")
        print("🔄 Press 'r' to reset current recording")
        
        cap = cv2.VideoCapture(0)
        recording = False
        sequence_id = 0
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results_hands = self.hands.process(frame_rgb)
            results_pose = self.pose.process(frame_rgb)
            results_face = self.face_mesh.process(frame_rgb)
            
            # Draw landmarks
            if results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            if results_pose.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, results_pose.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Recording indicator
            if recording:
                cv2.circle(frame, (30, 30), 15, (0, 0, 255), -1)  # Red circle
                cv2.putText(frame, "RECORDING", (60, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Extract and save landmarks
                landmarks = self.extract_landmarks(results_hands, results_pose, results_face)
                
                self.recorded_data.append({
                    'sequence_id': sequence_id,
                    'frame': frame_count,
                    'sign': self.gesture_name,
                    'landmarks': landmarks
                })
                
                frame_count += 1
            else:
                cv2.putText(frame, "Press SPACE to record", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display frame info
            cv2.putText(frame, f"Gesture: {self.gesture_name}", (10, frame.shape[0] - 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Sequences: {sequence_id}", (10, frame.shape[0] - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Gesture Recording', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Space to start/stop recording
                if recording:
                    print(f"⏹️  Stopped recording sequence {sequence_id} ({frame_count} frames)")
                    sequence_id += 1
                    frame_count = 0
                    recording = False
                else:
                    print(f"🎬 Started recording sequence {sequence_id}")
                    recording = True
            
            elif key == ord('r'):  # Reset
                self.recorded_data = []
                sequence_id = 0
                frame_count = 0
                recording = False
                print("🔄 Reset - cleared all data")
            
            elif key == ord('q'):  # Quit
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save data if any was recorded
        if self.recorded_data:
            print(f"\n💾 Saving {len(self.recorded_data)} frames...")
            self.save_data()
        else:
            print("❌ No data recorded!")

def main():
    print("🎯 Gesture Recording Tool")
    print("=" * 30)
    
    gesture_name = input("Enter gesture name (e.g., 'wave', 'thumbs_up'): ").strip()
    
    if not gesture_name:
        print("❌ Invalid gesture name!")
        return
    
    if not gesture_name.replace('_', '').isalnum():
        print("❌ Gesture name should contain only letters, numbers, and underscores!")
        return
    
    print(f"🎪 Ready to record gesture: '{gesture_name}'")
    input("Press Enter to start camera...")
    
    try:
        recorder = GestureRecorder(gesture_name)
        recorder.record_gesture()
        
        print("\n🎉 Recording session completed!")
        print("💡 Next steps:")
        print("   1. Record multiple variations of your gesture")
        print("   2. Run train_custom_gestures.py to train the model")
        print("   3. Test in the webapp!")
        
    except Exception as e:
        print(f"❌ Error during recording: {e}")
        print("💡 Make sure you have:")
        print("   - A working webcam")
        print("   - MediaPipe installed: pip install mediapipe")
        print("   - OpenCV installed: pip install opencv-python")

if __name__ == "__main__":
    main()
