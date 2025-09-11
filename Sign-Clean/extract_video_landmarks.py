#!/usr/bin/env python3
"""
Video to CSV Landmark Extractor
Processes videos and generates CSV files with MediaPipe landmarks for training
"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm
import os

class VideoLandmarkExtractor:
    """Extract MediaPipe landmarks from videos and save as CSV"""
    
    def __init__(self, input_folder="your_videos", output_folder="gesture_data"):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        
        # Initialize MediaPipe
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            refine_face_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def extract_landmarks_from_frame(self, frame):
        """Extract landmarks from a single frame"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.holistic.process(rgb_frame)
        
        # Initialize landmarks array (1659 features for MediaPipe holistic)
        landmarks = []
        
        # Face landmarks (468 points * 3 = 1404 features)
        if results.face_landmarks:
            for landmark in results.face_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * 1404)
        
        # Pose landmarks (33 points * 3 = 99 features) 
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * 99)
        
        # Left hand landmarks (21 points * 3 = 63 features)
        if results.left_hand_landmarks:
            for landmark in results.left_hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * 63)
        
        # Right hand landmarks (21 points * 3 = 63 features)
        if results.right_hand_landmarks:
            for landmark in results.right_hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
        else:
            landmarks.extend([0.0] * 63)
        
        # Add padding to reach 1659 if needed
        while len(landmarks) < 1659:
            landmarks.append(0.0)
        
        # Truncate if too long
        landmarks = landmarks[:1659]
        
        return landmarks
    
    def process_video(self, video_path, gesture_name):
        """Process a single video and extract landmarks"""
        print(f"  🎬 Processing: {video_path.name}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"    ❌ Could not open video: {video_path}")
            return None
        
        frames_data = []
        frame_count = 0
        sequence_id = video_path.stem  # Use filename as sequence ID
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract landmarks
            landmarks = self.extract_landmarks_from_frame(frame)
            
            # Create frame data
            frame_data = {
                'sequence_id': sequence_id,
                'frame': frame_count,
                'sign': gesture_name,
                'landmarks': str(landmarks)  # Store as string like original format
            }
            
            frames_data.append(frame_data)
            frame_count += 1
        
        cap.release()
        
        if frames_data:
            df = pd.DataFrame(frames_data)
            print(f"    ✅ Extracted {len(df)} frames")
            return df
        else:
            print(f"    ❌ No frames extracted")
            return None
    
    def process_all_videos(self):
        """Process all videos in gesture folders"""
        print("🚀 Starting Video Landmark Extraction")
        print("=" * 50)
        
        if not self.input_folder.exists():
            print(f"❌ Input folder not found: {self.input_folder}")
            return
        
        # Find gesture folders
        gesture_folders = [d for d in self.input_folder.iterdir() if d.is_dir()]
        
        if not gesture_folders:
            print(f"❌ No gesture folders found in {self.input_folder}")
            return
        
        print(f"📂 Found {len(gesture_folders)} gesture folders:")
        for folder in gesture_folders:
            videos = list(folder.glob("*.mp4"))
            print(f"   {folder.name}: {len(videos)} videos")
        
        all_data = []
        
        # Process each gesture folder
        for gesture_folder in gesture_folders:
            gesture_name = gesture_folder.name
            video_files = list(gesture_folder.glob("*.mp4"))
            
            if not video_files:
                print(f"\n⚠️  No videos found in {gesture_folder}")
                continue
            
            print(f"\n🎯 Processing gesture: {gesture_name}")
            print(f"   📹 Videos to process: {len(video_files)}")
            
            gesture_data = []
            
            # Process each video with progress bar
            for video_file in tqdm(video_files, desc=f"Processing {gesture_name}"):
                df = self.process_video(video_file, gesture_name)
                if df is not None:
                    gesture_data.append(df)
            
            # Combine all videos for this gesture
            if gesture_data:
                combined_gesture_df = pd.concat(gesture_data, ignore_index=True)
                
                # Save gesture-specific CSV
                csv_path = self.output_folder / f"{gesture_name}_landmarks.csv"
                combined_gesture_df.to_csv(csv_path, index=False)
                
                print(f"   ✅ Saved {len(combined_gesture_df)} frames to {csv_path}")
                all_data.append(combined_gesture_df)
            else:
                print(f"   ❌ No data extracted for {gesture_name}")
        
        # Save combined CSV
        if all_data:
            combined_all_df = pd.concat(all_data, ignore_index=True)
            combined_csv_path = self.output_folder / "all_gestures_landmarks.csv"
            combined_all_df.to_csv(combined_csv_path, index=False)
            
            print(f"\n🎉 Processing complete!")
            print(f"📊 Total frames extracted: {len(combined_all_df)}")
            print(f"💾 Combined data saved to: {combined_csv_path}")
            
            # Print summary by gesture
            print(f"\n📈 Gesture distribution:")
            gesture_counts = combined_all_df['sign'].value_counts()
            for gesture, count in gesture_counts.items():
                print(f"   {gesture}: {count} frames")
        
        else:
            print("\n❌ No data extracted from any videos!")
        
        # Cleanup
        self.holistic.close()

def main():
    """Main function"""
    print("🎬 Video to CSV Landmark Extractor")
    print("This will process your videos and create CSV files for training")
    print("=" * 60)
    
    # Check if input folder exists
    input_folder = Path("your_videos")
    if not input_folder.exists():
        print(f"❌ Input folder not found: {input_folder}")
        print("💡 Please make sure your videos are in the 'your_videos' folder")
        return
    
    # Create extractor and process
    extractor = VideoLandmarkExtractor()
    extractor.process_all_videos()
    
    print(f"\n✅ Next steps:")
    print(f"   1. Check the 'your_videos_gesture_data' folder for CSV files")
    print(f"   2. Run training: python train_video_data.py")
    print(f"   3. Or use the universal trainer: python universal_train.py")

if __name__ == "__main__":
    main()
