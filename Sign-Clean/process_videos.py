#!/usr/bin/env python3
"""
Simple Video Batch Processor
Easy-to-use script for processing video folders and generating training data
"""
import os
import sys
from pathlib import Path

# Add current directory to path to import video_processor
sys.path.append(str(Path(__file__).parent))

from video_processor import VideoProcessor

def process_video_folder():
    """Interactive script to process video folders"""
    
    print("🎬 Video Processing and Augmentation System")
    print("=" * 50)
    
    # Get input folder
    while True:
        input_folder = input("\n📁 Enter path to your video folder: ").strip().strip('"')
        if not input_folder:
            print("❌ Please enter a valid folder path")
            continue
        
        input_path = Path(input_folder)
        if not input_path.exists():
            print(f"❌ Folder does not exist: {input_path}")
            continue
        
        if not input_path.is_dir():
            print(f"❌ Path is not a directory: {input_path}")
            continue
        
        break
    
    print(f"✅ Input folder: {input_path}")
    
    # Check folder structure
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
    subfolders = [item for item in input_path.iterdir() if item.is_dir()]
    videos_in_root = [item for item in input_path.iterdir() 
                     if item.is_file() and item.suffix.lower() in video_extensions]
    
    if subfolders and not videos_in_root:
        print(f"📂 Detected folder structure with {len(subfolders)} gesture folders:")
        for folder in subfolders[:5]:  # Show first 5
            video_count = len([f for f in folder.iterdir() 
                             if f.suffix.lower() in video_extensions])
            print(f"   📁 {folder.name}: {video_count} videos")
        if len(subfolders) > 5:
            print(f"   ... and {len(subfolders) - 5} more folders")
    elif videos_in_root:
        print(f"📄 Detected flat structure with {len(videos_in_root)} videos in root folder")
        print("   Gesture names will be extracted from filenames")
    else:
        print("❌ No videos found in the specified folder!")
        return
    
    # Get number of augmentations
    while True:
        try:
            num_aug = input(f"\n🎨 Number of augmented versions per video (default: 5): ").strip()
            if not num_aug:
                num_aug = 5
            else:
                num_aug = int(num_aug)
            
            if num_aug < 1 or num_aug > 20:
                print("❌ Please enter a number between 1 and 20")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    print(f"✅ Will generate {num_aug} augmented versions per video")
    
    # Ask about landmark extraction
    while True:
        extract_choice = input(f"\n🔍 Extract landmarks for training? (y/n, default: y): ").strip().lower()
        if not extract_choice or extract_choice in ['y', 'yes']:
            extract_landmarks = True
            break
        elif extract_choice in ['n', 'no']:
            extract_landmarks = False
            break
        else:
            print("❌ Please enter 'y' or 'n'")
    
    # Set output folders
    output_folder = input_path.parent / f"{input_path.name}_processed"
    gesture_data_folder = input_path.parent / f"{input_path.name}_gesture_data"
    
    print(f"\n📤 Output locations:")
    print(f"   Videos: {output_folder}")
    if extract_landmarks:
        print(f"   CSV Data: {gesture_data_folder}")
    
    # Confirm processing
    print(f"\n🎯 Processing Summary:")
    print(f"   Input: {input_path}")
    print(f"   Augmentations: {num_aug} per video")
    print(f"   Extract landmarks: {'Yes' if extract_landmarks else 'No'}")
    
    confirm = input(f"\n▶️  Start processing? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Processing cancelled")
        return
    
    # Start processing
    print(f"\n🚀 Starting video processing...")
    print("=" * 50)
    
    try:
        processor = VideoProcessor(
            input_folder=str(input_path),
            output_folder=str(output_folder),
            gesture_data_folder=str(gesture_data_folder)
        )
        
        processor.process_all_videos(
            num_augmentations=num_aug,
            extract_landmarks=extract_landmarks
        )
        
        print(f"\n🎉 Processing completed successfully!")
        print(f"📁 Check your results in:")
        print(f"   {output_folder}")
        if extract_landmarks:
            print(f"   {gesture_data_folder}")
    
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        print("Please check your input and try again")

if __name__ == "__main__":
    try:
        process_video_folder()
    except KeyboardInterrupt:
        print(f"\n❌ Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    input(f"\nPress Enter to exit...")
