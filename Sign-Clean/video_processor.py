#!/usr/bin/env python3
"""
Video Processing and Augmentation System
Processes videos from a folder, generates augmented versions, and extracts landmarks
"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from pathlib import Path
import time
from datetime import datetime
import os
import random
from typing import List, Tuple, Dict
import json
import argparse

class VideoAugmenter:
    """Handles video augmentation operations"""
    
    def __init__(self):
        self.augmentation_methods = {
            'brightness': self._adjust_brightness,
            'contrast': self._adjust_contrast,
            'rotation': self._rotate_frame,
            'zoom': self._zoom_frame,
            'noise': self._add_noise
        }
    
    def _adjust_brightness(self, frame: np.ndarray, factor: float = None) -> np.ndarray:
        """Adjust brightness of the frame"""
        if factor is None:
            factor = random.uniform(0.7, 1.3)  # 70% to 130% brightness
        
        # Convert to float to prevent overflow
        bright_frame = frame.astype(np.float32)
        bright_frame = bright_frame * factor
        bright_frame = np.clip(bright_frame, 0, 255)
        return bright_frame.astype(np.uint8)
    
    def _adjust_contrast(self, frame: np.ndarray, factor: float = None) -> np.ndarray:
        """Adjust contrast of the frame"""
        if factor is None:
            factor = random.uniform(0.8, 1.2)  # 80% to 120% contrast
        
        # Convert to float and adjust contrast
        contrast_frame = frame.astype(np.float32)
        contrast_frame = (contrast_frame - 128) * factor + 128
        contrast_frame = np.clip(contrast_frame, 0, 255)
        return contrast_frame.astype(np.uint8)
    
    def _rotate_frame(self, frame: np.ndarray, angle: float = None) -> np.ndarray:
        """Rotate frame by a small angle"""
        if angle is None:
            angle = random.uniform(-10, 10)  # -10 to +10 degrees
        
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply rotation
        rotated_frame = cv2.warpAffine(frame, rotation_matrix, (w, h), 
                                     borderMode=cv2.BORDER_REFLECT_101)
        return rotated_frame
    
    def _zoom_frame(self, frame: np.ndarray, zoom_factor: float = None) -> np.ndarray:
        """Apply zoom to the frame"""
        if zoom_factor is None:
            zoom_factor = random.uniform(0.9, 1.1)  # 90% to 110% zoom
        
        h, w = frame.shape[:2]
        
        # Calculate new dimensions
        new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
        
        # Resize frame
        resized = cv2.resize(frame, (new_w, new_h))
        
        if zoom_factor > 1.0:
            # Crop to original size (zoom in)
            start_x = (new_w - w) // 2
            start_y = (new_h - h) // 2
            cropped = resized[start_y:start_y + h, start_x:start_x + w]
            return cropped
        else:
            # Pad to original size (zoom out)
            pad_x = (w - new_w) // 2
            pad_y = (h - new_h) // 2
            padded = cv2.copyMakeBorder(resized, pad_y, h - new_h - pad_y, 
                                      pad_x, w - new_w - pad_x, 
                                      cv2.BORDER_REFLECT_101)
            return padded
    
    def _add_noise(self, frame: np.ndarray, noise_factor: float = None) -> np.ndarray:
        """Add random noise to the frame"""
        if noise_factor is None:
            noise_factor = random.uniform(0.02, 0.08)  # 2% to 8% noise
        
        # Generate noise
        noise = np.random.normal(0, noise_factor * 255, frame.shape)
        
        # Add noise to frame
        noisy_frame = frame.astype(np.float32) + noise
        noisy_frame = np.clip(noisy_frame, 0, 255)
        return noisy_frame.astype(np.uint8)
    
    def generate_augmented_versions(self, video_path: str, output_dir: str, 
                                  num_versions: int = 5) -> List[str]:
        """Generate augmented versions of a video"""
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Read all frames
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        if not frames:
            raise ValueError(f"No frames found in video: {video_path}")
        
        # Generate augmented versions
        augmented_paths = []
        base_name = video_path.stem
        
        for version_idx in range(num_versions):
            # Choose augmentation combination
            augmentation_types = random.sample(list(self.augmentation_methods.keys()), 
                                             random.randint(2, 4))
            
            version_name = f"{base_name}_aug_{version_idx + 1}_{'_'.join(augmentation_types)}.mp4"
            output_path = output_dir / version_name
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            # Process each frame
            for frame in frames:
                augmented_frame = frame.copy()
                
                # Apply selected augmentations
                for aug_type in augmentation_types:
                    augmented_frame = self.augmentation_methods[aug_type](augmented_frame)
                
                out.write(augmented_frame)
            
            out.release()
            augmented_paths.append(str(output_path))
            print(f"✅ Generated augmented video: {version_name}")
        
        return augmented_paths

class VideoLandmarkExtractor:
    """Extracts landmarks from videos using MediaPipe"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_mesh
        
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
    
    def extract_landmarks_from_frame(self, frame: np.ndarray) -> Dict:
        """Extract landmarks from a single frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        hand_results = self.hands.process(rgb_frame)
        pose_results = self.pose.process(rgb_frame)
        face_results = self.face_mesh.process(rgb_frame)
        
        landmarks = {}
        
        # Extract face landmarks (468 points)
        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]
            for i, landmark in enumerate(face_landmarks.landmark):
                landmarks[f'face_{i}_x'] = landmark.x
                landmarks[f'face_{i}_y'] = landmark.y
                landmarks[f'face_{i}_z'] = landmark.z
        else:
            # Fill with zeros if no face detected
            for i in range(468):
                landmarks[f'face_{i}_x'] = 0.0
                landmarks[f'face_{i}_y'] = 0.0
                landmarks[f'face_{i}_z'] = 0.0
        
        # Extract pose landmarks (33 points)
        if pose_results.pose_landmarks:
            for i, landmark in enumerate(pose_results.pose_landmarks.landmark):
                landmarks[f'pose_{i}_x'] = landmark.x
                landmarks[f'pose_{i}_y'] = landmark.y
                landmarks[f'pose_{i}_z'] = landmark.z
        else:
            # Fill with zeros if no pose detected
            for i in range(33):
                landmarks[f'pose_{i}_x'] = 0.0
                landmarks[f'pose_{i}_y'] = 0.0
                landmarks[f'pose_{i}_z'] = 0.0
        
        # Extract hand landmarks (21 points per hand, max 2 hands)
        hand_data = {}
        if hand_results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                if hand_idx < 2:  # Max 2 hands
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        hand_data[f'hand_{hand_idx}_{i}_x'] = landmark.x
                        hand_data[f'hand_{hand_idx}_{i}_y'] = landmark.y
                        hand_data[f'hand_{hand_idx}_{i}_z'] = landmark.z
        
        # Ensure consistent hand data (2 hands, 21 points each)
        for hand_idx in range(2):
            for point_idx in range(21):
                key_x = f'hand_{hand_idx}_{point_idx}_x'
                key_y = f'hand_{hand_idx}_{point_idx}_y'
                key_z = f'hand_{hand_idx}_{point_idx}_z'
                
                if key_x not in hand_data:
                    hand_data[key_x] = 0.0
                    hand_data[key_y] = 0.0
                    hand_data[key_z] = 0.0
        
        landmarks.update(hand_data)
        return landmarks
    
    def process_video(self, video_path: str, gesture_name: str) -> pd.DataFrame:
        """Process video and extract landmarks"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        frame_data = []
        frame_count = 0
        
        print(f"Processing video: {Path(video_path).name}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                landmarks = self.extract_landmarks_from_frame(frame)
                landmarks['gesture'] = gesture_name
                landmarks['frame'] = frame_count
                landmarks['video_source'] = Path(video_path).name
                frame_data.append(landmarks)
                frame_count += 1
                
                if frame_count % 30 == 0:  # Progress update every 30 frames
                    print(f"  Processed {frame_count} frames...")
                    
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
                continue
        
        cap.release()
        
        if frame_data:
            df = pd.DataFrame(frame_data)
            print(f"✅ Extracted landmarks from {len(df)} frames")
            return df
        else:
            print(f"❌ No landmarks extracted from {video_path}")
            return pd.DataFrame()
    
    def cleanup(self):
        """Cleanup MediaPipe resources"""
        self.hands.close()
        self.pose.close()
        self.face_mesh.close()

class VideoProcessor:
    """Main video processing class"""
    
    def __init__(self, input_folder: str, output_folder: str = "processed_videos", 
                 gesture_data_folder: str = "gesture_data"):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.gesture_data_folder = Path(gesture_data_folder)
        
        # Create output directories
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.gesture_data_folder.mkdir(parents=True, exist_ok=True)
        
        self.augmenter = VideoAugmenter()
        self.extractor = VideoLandmarkExtractor()
        
        # Supported video formats
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
    
    def find_videos(self) -> Dict[str, List[str]]:
        """Find all videos organized by gesture name (folder structure)"""
        videos_by_gesture = {}
        
        if not self.input_folder.exists():
            raise ValueError(f"Input folder does not exist: {self.input_folder}")
        
        # Check if input folder has subfolders (gesture names) or just videos
        subfolders = [item for item in self.input_folder.iterdir() if item.is_dir()]
        
        if subfolders:
            # Folder structure: input_folder/gesture_name/video_files
            for gesture_folder in subfolders:
                gesture_name = gesture_folder.name
                videos = []
                
                for video_file in gesture_folder.iterdir():
                    if video_file.suffix.lower() in self.video_extensions:
                        videos.append(str(video_file))
                
                if videos:
                    videos_by_gesture[gesture_name] = videos
                    print(f"Found {len(videos)} videos for gesture: {gesture_name}")
        else:
            # Flat structure: all videos in one folder, extract gesture name from filename
            print("Flat folder structure detected, extracting gesture names from filenames...")
            for video_file in self.input_folder.iterdir():
                if video_file.suffix.lower() in self.video_extensions:
                    # Try to extract gesture name from filename
                    # Assuming format: gesture_name_*.mp4 or just gesture_name.mp4
                    gesture_name = video_file.stem.split('_')[0]
                    
                    if gesture_name not in videos_by_gesture:
                        videos_by_gesture[gesture_name] = []
                    videos_by_gesture[gesture_name].append(str(video_file))
        
        return videos_by_gesture
    
    def process_all_videos(self, num_augmentations: int = 5, extract_landmarks: bool = True):
        """Process all videos with augmentation and landmark extraction"""
        videos_by_gesture = self.find_videos()
        
        if not videos_by_gesture:
            print("❌ No videos found in the input folder!")
            return
        
        total_videos = sum(len(videos) for videos in videos_by_gesture.values())
        print(f"\n🎯 Found {total_videos} videos across {len(videos_by_gesture)} gestures")
        print(f"📈 Will generate {num_augmentations} augmented versions per video")
        print(f"📊 Total videos after augmentation: {total_videos * (num_augmentations + 1)}")
        
        all_landmark_data = []
        
        for gesture_name, video_paths in videos_by_gesture.items():
            print(f"\n🔄 Processing gesture: {gesture_name}")
            print(f"   Original videos: {len(video_paths)}")
            
            gesture_output_dir = self.output_folder / gesture_name
            gesture_output_dir.mkdir(exist_ok=True)
            
            gesture_landmarks = []
            
            for video_idx, video_path in enumerate(video_paths):
                video_name = Path(video_path).name
                print(f"\n  📹 Processing video {video_idx + 1}/{len(video_paths)}: {video_name}")
                
                try:
                    # Extract landmarks from original video
                    if extract_landmarks:
                        print("    🔍 Extracting landmarks from original video...")
                        landmarks_df = self.extractor.process_video(video_path, gesture_name)
                        if not landmarks_df.empty:
                            gesture_landmarks.append(landmarks_df)
                    
                    # Generate augmented versions
                    print(f"    🎨 Generating {num_augmentations} augmented versions...")
                    augmented_paths = self.augmenter.generate_augmented_versions(
                        video_path, gesture_output_dir, num_augmentations
                    )
                    
                    # Extract landmarks from augmented videos
                    if extract_landmarks:
                        for aug_idx, aug_path in enumerate(augmented_paths):
                            print(f"    🔍 Extracting landmarks from augmented video {aug_idx + 1}/{len(augmented_paths)}...")
                            landmarks_df = self.extractor.process_video(aug_path, gesture_name)
                            if not landmarks_df.empty:
                                gesture_landmarks.append(landmarks_df)
                
                except Exception as e:
                    print(f"    ❌ Error processing {video_name}: {e}")
                    continue
            
            # Save gesture landmarks to CSV
            if gesture_landmarks and extract_landmarks:
                combined_df = pd.concat(gesture_landmarks, ignore_index=True)
                csv_path = self.gesture_data_folder / f"{gesture_name}_landmarks.csv"
                combined_df.to_csv(csv_path, index=False)
                all_landmark_data.append(combined_df)
                print(f"  ✅ Saved {len(combined_df)} landmark frames to {csv_path}")
        
        # Save combined landmarks
        if all_landmark_data and extract_landmarks:
            combined_all_df = pd.concat(all_landmark_data, ignore_index=True)
            combined_csv_path = self.gesture_data_folder / "all_gestures_landmarks.csv"
            combined_all_df.to_csv(combined_csv_path, index=False)
            print(f"\n🎉 Processing complete!")
            print(f"📊 Total landmark frames: {len(combined_all_df)}")
            print(f"💾 Combined data saved to: {combined_csv_path}")
            
            # Print summary
            gesture_counts = combined_all_df['gesture'].value_counts()
            print(f"\n📈 Gesture distribution:")
            for gesture, count in gesture_counts.items():
                print(f"   {gesture}: {count} frames")
        
        # Cleanup
        self.extractor.cleanup()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Video Processing and Augmentation System")
    parser.add_argument("input_folder", help="Path to folder containing videos")
    parser.add_argument("--output", "-o", default="processed_videos", 
                       help="Output folder for processed videos (default: processed_videos)")
    parser.add_argument("--gesture-data", "-g", default="gesture_data",
                       help="Output folder for landmark CSV files (default: gesture_data)")
    parser.add_argument("--augmentations", "-a", type=int, default=5,
                       help="Number of augmented versions per video (default: 5)")
    parser.add_argument("--no-landmarks", action="store_true",
                       help="Skip landmark extraction (only generate augmented videos)")
    
    args = parser.parse_args()
    
    processor = VideoProcessor(
        input_folder=args.input_folder,
        output_folder=args.output,
        gesture_data_folder=args.gesture_data
    )
    
    processor.process_all_videos(
        num_augmentations=args.augmentations,
        extract_landmarks=not args.no_landmarks
    )

if __name__ == "__main__":
    main()
