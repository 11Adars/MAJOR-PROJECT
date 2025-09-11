#!/usr/bin/env python3
"""
Simple Gesture Recording Script
Records landmark data for a new gesture
"""

import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from pathlib import Path
import time

class GestureRecorder:
    def __init__(self, gesture_name):
        self.gesture_name = gesture_name
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe
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
        
        # Data storage
        self.recorded_data = []
        self.recording = False
        self.sequence_id = 0
        self.frame_count = 0
        
    def extract_landmarks(self, results_hands, results_pose, results_face):
        """Extract all landmarks from MediaPipe results"""
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
        
        # Hand landmarks (21 points each, max 2 hands = 42 points)
        hand_data = [0.0] * (42 * 3)  # Initialize for 2 hands
        if results_hands.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results_hands.multi_hand_landmarks):
                if hand_idx < 2:  # Only process first 2 hands
                    start_idx = hand_idx * 21 * 3
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        idx = start_idx + i * 3
                        hand_data[idx:idx+3] = [landmark.x, landmark.y, landmark.z]
        
        landmarks.extend(hand_data)
        
        return landmarks
    
    def save_data(self):
        """Save recorded data to CSV"""
        if not self.recorded_data:
            print("❌ No data recorded!")
            return
        
        # Create gesture_data directory if it doesn't exist
        data_dir = Path("gesture_data")
        data_dir.mkdir(exist_ok=True)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.recorded_data)
        
        # Create landmark column names
        columns = ['sequence', 'frame']
        for i in range(543):  # Total landmarks: 468 + 33 + 42 = 543
            columns.extend([f'landmark_{i}_x', f'landmark_{i}_y', f'landmark_{i}_z'])
        
        df.columns = columns[:len(df.columns)]
        
        # Save to CSV
        filename = data_dir / f"{self.gesture_name}_landmarks.csv"
        df.to_csv(filename, index=False)
        
        print(f"✅ Saved {len(self.recorded_data)} frames to {filename}")
        print(f"📊 Total sequences recorded: {self.sequence_id + 1}")
    
    def record_gesture(self):
        """Main recording function"""
        cap = cv2.VideoCapture(0)
        
        print(f"🎥 Recording gesture: {self.gesture_name}")
        print("📋 Instructions:")
        print("  - Press SPACE to start/stop recording a sequence")
        print("  - Press 'n' to start a new sequence")
        print("  - Press 'q' to quit and save")
        print("  - Record 5-10 different sequences of your gesture")
        
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
            
            # Convert back to BGR for display
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
            
            # Record landmarks if recording
            if self.recording:
                landmarks = self.extract_landmarks(results_hands, results_pose, results_face)
                
                # Create row: [sequence, frame, ...landmarks]
                row = [self.sequence_id, self.frame_count] + landmarks
                self.recorded_data.append(row)
                self.frame_count += 1
                
                # Visual feedback
                cv2.putText(image, f"RECORDING - Seq: {self.sequence_id}, Frame: {self.frame_count}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(image, "Press SPACE to start recording", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(image, f"Gesture: {self.gesture_name}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(image, f"Total sequences: {self.sequence_id}", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            cv2.imshow('Gesture Recording', image)
            
            key = cv2.waitKey(5) & 0xFF
            if key == ord(' '):  # Space to toggle recording
                if self.recording:
                    print(f"⏹️ Stopped recording sequence {self.sequence_id} ({self.frame_count} frames)")
                    self.recording = False
                else:
                    print(f"▶️ Started recording sequence {self.sequence_id}")
                    self.recording = True
                    self.frame_count = 0
            
            elif key == ord('n'):  # New sequence
                if self.recording:
                    print("⏹️ Stopped current recording")
                    self.recording = False
                self.sequence_id += 1
                self.frame_count = 0
                print(f"🆕 Ready for new sequence {self.sequence_id}")
            
            elif key == ord('q'):  # Quit
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save data
        self.save_data()

def main():
    print("🎯 Gesture Recording Tool")
    print("=" * 30)
    
    gesture_name = input("Enter gesture name (e.g., 'wave', 'thumbs_up'): ").strip()
    
    if not gesture_name:
        print("❌ Please enter a valid gesture name")
        return
    
    recorder = GestureRecorder(gesture_name)
    recorder.record_gesture()
    
    print(f"\n✅ Recording complete for '{gesture_name}'!")
    print("\n🔄 Next steps:")
    print("1. Train the classifier:")
    print("   python quick_custom_gesture_solution.py")
    print("2. Test your new gesture in the web app!")

if __name__ == "__main__":
    main()
