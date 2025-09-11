"""
Script to add gestures from existing video files
"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import os
from datetime import datetime
from gesture_manager import GestureManager
from data_processor import GestureDataProcessor

class VideoGestureProcessor:
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
    
    def process_video_file(self, video_path, start_time=0, end_time=None, segment_duration=3):
        """
        Process a video file to extract gesture sequences
        
        Args:
            video_path: Path to the video file
            start_time: Start time in seconds (default: 0)
            end_time: End time in seconds (default: entire video)
            segment_duration: Duration of each gesture sequence in seconds
        """
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Cannot open video: {video_path}")
            return None
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video info: {duration:.2f}s, {fps:.2f} FPS, {total_frames} frames")
        
        # Calculate frame ranges
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps) if end_time else total_frames
        frames_per_sequence = int(segment_duration * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        sequences = []
        sequence_count = 0
        
        print(f"Processing video from {start_time}s to {end_time or duration}s")
        print(f"Extracting {segment_duration}s sequences ({frames_per_sequence} frames each)")
        
        while cap.get(cv2.CAP_PROP_POS_FRAMES) < end_frame:
            sequence_data = self.extract_sequence_from_video(cap, frames_per_sequence, sequence_count)
            
            if sequence_data:
                sequences.append(sequence_data)
                sequence_count += 1
                print(f"Extracted sequence {sequence_count}")
            else:
                break
        
        cap.release()
        
        if sequences:
            self.save_sequences(sequences)
            print(f"Extracted {len(sequences)} sequences from video")
        
        return sequences
    
    def extract_sequence_from_video(self, cap, num_frames, sequence_id):
        """Extract a single sequence from video"""
        sequence_landmarks = []
        frame_count = 0
        
        while frame_count < num_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.holistic.process(rgb_frame)
            
            # Extract landmarks
            landmarks = self.extract_landmarks(results, frame_count, sequence_id)
            if landmarks:
                sequence_landmarks.extend(landmarks)
            
            frame_count += 1
        
        return sequence_landmarks if sequence_landmarks else None
    
    def extract_landmarks(self, results, frame_num, sequence_id):
        """Extract landmarks similar to the gesture collector format"""
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
                        'sign': self.gesture_name,
                        'sequence_id': sequence_id
                    })
        
        return landmarks_data if landmarks_data else None
    
    def save_sequences(self, sequences):
        """Save extracted sequences to CSV"""
        all_data = []
        for sequence in sequences:
            all_data.extend(sequence)
        
        if all_data:
            df = pd.DataFrame(all_data)
            filename = f"{self.output_dir}/{self.gesture_name}_from_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            print(f"Saved gesture data to {filename}")
            return filename
        return None
    
    def process_multiple_videos(self, video_list, segment_duration=3):
        """Process multiple video files for the same gesture"""
        all_sequences = []
        
        for video_info in video_list:
            if isinstance(video_info, str):
                # Just video path
                video_path = video_info
                start_time = 0
                end_time = None
            else:
                # Dictionary with video path and timing
                video_path = video_info['path']
                start_time = video_info.get('start_time', 0)
                end_time = video_info.get('end_time', None)
            
            print(f"\n--- Processing: {video_path} ---")
            sequences = self.process_video_file(video_path, start_time, end_time, segment_duration)
            
            if sequences:
                all_sequences.extend(sequences)
        
        if all_sequences:
            self.save_sequences(all_sequences)
        
        return all_sequences

def add_gesture_from_video():
    """Interactive function to add gesture from video"""
    print("=== Add Gesture from Video ===\n")
    
    # Get gesture information
    gesture_name = input("Enter gesture name: ").strip()
    if not gesture_name:
        print("Invalid gesture name!")
        return
    
    video_path = input("Enter video file path: ").strip()
    if not os.path.exists(video_path):
        print("Video file not found!")
        return
    
    # Optional timing parameters
    start_time = input("Start time in seconds (default 0): ").strip()
    start_time = float(start_time) if start_time else 0
    
    end_time = input("End time in seconds (default: full video): ").strip()
    end_time = float(end_time) if end_time else None
    
    segment_duration = input("Segment duration in seconds (default 3): ").strip()
    segment_duration = float(segment_duration) if segment_duration else 3
    
    # Process video
    processor = VideoGestureProcessor(gesture_name)
    sequences = processor.process_video_file(video_path, start_time, end_time, segment_duration)
    
    if not sequences:
        print("No data extracted from video!")
        return
    
    # Find the created CSV file
    csv_files = [f for f in os.listdir("custom_gestures") if f.startswith(gesture_name) and "from_video" in f]
    if not csv_files:
        print("No CSV file created!")
        return
    
    csv_file = os.path.join("custom_gestures", csv_files[-1])
    
    # Process the data
    data_processor = GestureDataProcessor()
    processed_sequences = data_processor.process_collected_data(csv_file, gesture_name)
    training_data = data_processor.convert_to_training_format(processed_sequences)
    training_file = data_processor.save_training_data(training_data, f"{gesture_name}_training_data.csv")
    
    # Update gesture dictionary
    manager = GestureManager()
    gesture_id = manager.add_new_gesture(gesture_name)
    num_classes = manager.update_model_classes()
    
    print(f"\n=== Video Processing Complete ===")
    print(f"Gesture '{gesture_name}' added with ID: {gesture_id}")
    print(f"Extracted {len(sequences)} sequences from video")
    print(f"Training data saved: {training_file}")
    print(f"Model updated with {num_classes} classes")

if __name__ == "__main__":
    # Example usage
    choice = input("1. Single video\n2. Multiple videos\nChoice: ").strip()
    
    if choice == "1":
        add_gesture_from_video()
    elif choice == "2":
        gesture_name = input("Enter gesture name: ").strip()
        
        # Example for multiple videos
        video_list = [
            {"path": "video1.mp4", "start_time": 5, "end_time": 20},
            {"path": "video2.mp4", "start_time": 0, "end_time": 15},
            "video3.mp4"  # Full video
        ]
        
        processor = VideoGestureProcessor(gesture_name)
        sequences = processor.process_multiple_videos(video_list)
        print(f"Processed {len(sequences)} total sequences")
    else:
        print("Invalid choice!")
