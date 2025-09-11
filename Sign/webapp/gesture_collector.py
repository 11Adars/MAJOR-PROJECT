import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import os
from datetime import datetime

class GestureCollector:
    def __init__(self, gesture_name, output_dir="custom_gestures"):
        self.gesture_name = gesture_name
        self.output_dir = output_dir
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=2,
            refine_face_landmarks=True
        )
        
        os.makedirs(output_dir, exist_ok=True)
        
    def collect_gesture_data(self, num_sequences=50, frames_per_sequence=30):
        """Collect gesture data from webcam"""
        cap = cv2.VideoCapture(0)
        sequences = []
        
        print(f"Collecting data for gesture: {self.gesture_name}")
        print(f"Press SPACE to start recording, ESC to exit")
        
        sequence_count = 0
        
        while sequence_count < num_sequences:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Display instructions
            cv2.putText(frame, f"Gesture: {self.gesture_name}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Sequence: {sequence_count + 1}/{num_sequences}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to record", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            cv2.imshow('Gesture Collection', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                sequence_data = self.record_sequence(cap, frames_per_sequence)
                if sequence_data:
                    sequences.append(sequence_data)
                    sequence_count += 1
                    print(f"Recorded sequence {sequence_count}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save collected data
        self.save_sequences(sequences)
        return sequences
    
    def record_sequence(self, cap, num_frames):
        """Record a single sequence of the gesture"""
        sequence_landmarks = []
        frame_count = 0
        
        print("Recording... Perform your gesture now!")
        
        while frame_count < num_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.holistic.process(rgb_frame)
            
            # Extract landmarks
            landmarks = self.extract_landmarks(results, frame_count)
            if landmarks is not None:
                sequence_landmarks.extend(landmarks)  # Changed from append to extend
            
            # Show recording progress
            cv2.putText(frame, f"Recording: {frame_count + 1}/{num_frames}", 
                       (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Gesture Collection', frame)
            cv2.waitKey(50)  # Small delay between frames
            
            frame_count += 1
        
        return sequence_landmarks if sequence_landmarks else None
    
    def extract_landmarks(self, results, frame_num):
        """Extract landmarks similar to your existing format"""
        landmarks_data = []
        
        # Extract different types of landmarks
        landmark_types = {
            'pose': results.pose_landmarks,
            'left_hand': results.left_hand_landmarks,
            'right_hand': results.right_hand_landmarks,
            'face': results.face_landmarks
        }
        
        for lm_type, landmarks in landmark_types.items():
            if landmarks:
                for idx, landmark in enumerate(landmarks.landmark):
                    landmarks_data.append({
                        'frame': frame_num,
                        'type': lm_type,
                        'landmark_index': idx,
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'sign': self.gesture_name
                    })
        
        return landmarks_data if landmarks_data else None
    
    def save_sequences(self, sequences):
        """Save collected sequences to CSV"""
        all_data = []
        for seq_idx, sequence in enumerate(sequences):
            for landmark in sequence:
                landmark['sequence_id'] = seq_idx
                all_data.append(landmark)
        
        if all_data:
            df = pd.DataFrame(all_data)
            filename = f"{self.output_dir}/{self.gesture_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            print(f"Saved gesture data to {filename}")
            return filename
        return None

# Usage example
if __name__ == "__main__":
    # Example usage
    gesture_name = input("Enter gesture name: ")
    num_sequences = int(input("Enter number of sequences (default 30): ") or "30")
    frames_per_sequence = int(input("Enter frames per sequence (default 50): ") or "50")
    
    collector = GestureCollector(gesture_name)
    collector.collect_gesture_data(num_sequences=num_sequences, frames_per_sequence=frames_per_sequence)
