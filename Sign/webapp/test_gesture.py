"""
Test script for newly added custom gestures
"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

class GestureTester:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=2,
            refine_face_landmarks=True
        )
        
        # Load gesture dictionary
        self.load_gesture_dict()
        
    def load_gesture_dict(self):
        """Load the gesture dictionary"""
        dict_file = "module/islr/dict_sign.csv"
        if os.path.exists(dict_file):
            self.gesture_dict = pd.read_csv(dict_file)
            print(f"Loaded {len(self.gesture_dict)} gestures from dictionary")
            
            # Create mapping from ID to gesture name
            self.id_to_gesture = dict(zip(self.gesture_dict['sign_ord'], self.gesture_dict['sign']))
            self.gesture_to_id = dict(zip(self.gesture_dict['sign'], self.gesture_dict['sign_ord']))
        else:
            print("Gesture dictionary not found!")
            self.gesture_dict = pd.DataFrame()
    
    def test_data_collection(self, gesture_name):
        """Test if gesture data was collected properly"""
        print(f"\n=== Testing Data Collection for '{gesture_name}' ===")
        
        # Check if gesture exists in dictionary
        if gesture_name not in self.gesture_to_id:
            print(f"❌ Gesture '{gesture_name}' not found in dictionary!")
            return False
        
        gesture_id = self.gesture_to_id[gesture_name]
        print(f"✅ Gesture '{gesture_name}' found with ID: {gesture_id}")
        
        # Check raw data file
        csv_files = [f for f in os.listdir("custom_gestures") if f.startswith(gesture_name)]
        if not csv_files:
            print(f"❌ No raw data files found for '{gesture_name}'")
            return False
        
        raw_file = os.path.join("custom_gestures", csv_files[-1])
        raw_df = pd.read_csv(raw_file)
        
        sequences = raw_df['sequence_id'].nunique()
        frames = len(raw_df['frame'].unique())
        landmarks = len(raw_df)
        
        print(f"✅ Raw data: {sequences} sequences, {frames} unique frames, {landmarks} landmark points")
        
        # Check processed data file
        processed_file = f"processed_data/{gesture_name}_training_data.csv"
        if os.path.exists(processed_file):
            processed_df = pd.read_csv(processed_file)
            print(f"✅ Processed data: {len(processed_df)} training samples")
        else:
            print(f"❌ No processed data file found: {processed_file}")
            return False
        
        return True
    
    def simulate_gesture_recognition(self, gesture_name):
        """Simulate gesture recognition using collected data"""
        print(f"\n=== Simulating Recognition for '{gesture_name}' ===")
        
        # Load processed training data
        processed_file = f"processed_data/{gesture_name}_training_data.csv"
        if not os.path.exists(processed_file):
            print(f"❌ Processed data not found: {processed_file}")
            return
        
        df = pd.read_csv(processed_file)
        print(f"✅ Loaded {len(df)} training samples")
        
        # Analyze data quality
        sequences = df['sequence_id'].nunique()
        avg_frames = len(df) / sequences
        
        print(f"📊 Data Analysis:")
        print(f"   - Sequences: {sequences}")
        print(f"   - Average frames per sequence: {avg_frames:.1f}")
        print(f"   - Total samples: {len(df)}")
        
        # Check for data consistency
        landmark_sizes = df['landmarks'].apply(lambda x: len(eval(x)) if isinstance(x, str) else 0)
        expected_size = 543 * 3  # 543 landmarks * 3 coordinates (x,y,z)
        
        correct_size_count = (landmark_sizes == expected_size).sum()
        print(f"   - Correct landmark format: {correct_size_count}/{len(df)} samples")
        
        if correct_size_count < len(df) * 0.8:
            print("⚠️  Warning: Many samples have incorrect landmark format")
        else:
            print("✅ Data format looks good!")
    
    def test_live_gesture_recognition(self, gesture_name):
        """Test live gesture recognition from webcam"""
        print(f"\n=== Live Testing for '{gesture_name}' ===")
        print("Press 'q' to quit, 'r' to record test sequence")
        
        cap = cv2.VideoCapture(0)
        recording = False
        recorded_frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.holistic.process(rgb_frame)
            
            # Draw landmarks
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS)
            if results.left_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)
            if results.right_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)
            
            # Recording indicator
            if recording:
                cv2.putText(frame, f"RECORDING {gesture_name.upper()}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"Frame: {len(recorded_frames)}", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Extract landmarks for comparison
                landmarks = self.extract_landmarks_for_comparison(results)
                if landmarks:
                    recorded_frames.append(landmarks)
                
                # Stop recording after 30 frames
                if len(recorded_frames) >= 30:
                    recording = False
                    similarity = self.compare_with_training_data(recorded_frames, gesture_name)
                    print(f"Recorded sequence similarity: {similarity:.2f}%")
                    recorded_frames = []
            
            # Instructions
            cv2.putText(frame, f"Testing: {gesture_name}", (10, frame.shape[0] - 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'r' to record, 'q' to quit", (10, frame.shape[0] - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Gesture Testing', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r') and not recording:
                recording = True
                recorded_frames = []
                print(f"Recording {gesture_name}...")
        
        cap.release()
        cv2.destroyAllWindows()
    
    def extract_landmarks_for_comparison(self, results):
        """Extract landmarks in same format as training data"""
        landmarks = []
        
        # Extract different types of landmarks
        landmark_types = {
            'pose': results.pose_landmarks,
            'left_hand': results.left_hand_landmarks,
            'right_hand': results.right_hand_landmarks,
            'face': results.face_landmarks
        }
        
        for lm_type, lm_results in landmark_types.items():
            if lm_results:
                for landmark in lm_results.landmark:
                    landmarks.extend([landmark.x, landmark.y, landmark.z])
            else:
                # Add zeros for missing landmarks
                expected_counts = {'pose': 33, 'left_hand': 21, 'right_hand': 21, 'face': 468}
                landmarks.extend([0.0] * (expected_counts[lm_type] * 3))
        
        return landmarks if len(landmarks) == 543 * 3 else None
    
    def compare_with_training_data(self, recorded_sequence, gesture_name):
        """Compare recorded sequence with training data"""
        processed_file = f"processed_data/{gesture_name}_training_data.csv"
        if not os.path.exists(processed_file):
            return 0.0
        
        df = pd.read_csv(processed_file)
        
        # Get first training sequence for comparison
        first_sequence = df[df['sequence_id'] == 0]['landmarks'].apply(eval).tolist()
        
        if len(first_sequence) == 0 or len(recorded_sequence) == 0:
            return 0.0
        
        # Simple similarity calculation (this is very basic)
        min_length = min(len(first_sequence), len(recorded_sequence))
        similarity_scores = []
        
        for i in range(min_length):
            if len(first_sequence[i]) == len(recorded_sequence[i]):
                # Calculate cosine similarity
                a = np.array(first_sequence[i])
                b = np.array(recorded_sequence[i])
                similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                similarity_scores.append(max(0, similarity))
        
        return np.mean(similarity_scores) * 100 if similarity_scores else 0.0
    
    def show_gesture_statistics(self):
        """Show statistics about all gestures"""
        print(f"\n=== Gesture Statistics ===")
        print(f"Total gestures in dictionary: {len(self.gesture_dict)}")
        
        # Show recently added gestures (last 10)
        recent_gestures = self.gesture_dict.tail(10)
        print(f"\nRecently added gestures:")
        for _, row in recent_gestures.iterrows():
            print(f"  {row['sign_ord']}: {row['sign']}")
        
        # Check which gestures have training data
        custom_gestures = []
        if os.path.exists("processed_data"):
            for file in os.listdir("processed_data"):
                if file.endswith("_training_data.csv"):
                    gesture_name = file.replace("_training_data.csv", "")
                    custom_gestures.append(gesture_name)
        
        print(f"\nCustom gestures with training data: {len(custom_gestures)}")
        for gesture in custom_gestures:
            print(f"  - {gesture}")

def main():
    """Main testing interface"""
    tester = GestureTester()
    
    while True:
        print("\n=== Gesture Testing Menu ===")
        print("1. Test data collection for a gesture")
        print("2. Simulate gesture recognition")
        print("3. Live gesture testing (webcam)")
        print("4. Show gesture statistics")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            gesture_name = input("Enter gesture name to test: ").strip()
            if gesture_name:
                tester.test_data_collection(gesture_name)
            
        elif choice == '2':
            gesture_name = input("Enter gesture name to simulate: ").strip()
            if gesture_name:
                tester.simulate_gesture_recognition(gesture_name)
            
        elif choice == '3':
            gesture_name = input("Enter gesture name for live testing: ").strip()
            if gesture_name:
                tester.test_live_gesture_recognition(gesture_name)
            
        elif choice == '4':
            tester.show_gesture_statistics()
            
        elif choice == '5':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice! Please enter 1-5.")

if __name__ == "__main__":
    main()
