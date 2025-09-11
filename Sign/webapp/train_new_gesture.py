#!/usr/bin/env python3
"""
Script to train a new custom gesture with optimal parameters
"""

import cv2
import os
import json
import time
from pathlib import Path

class NewGestureTrainer:
    def __init__(self, gesture_name):
        self.gesture_name = gesture_name
        self.base_path = Path("custom_gestures")
        self.gesture_path = self.base_path / gesture_name
        self.video_count = 0
        
        # Create directories
        self.gesture_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🎯 Training new gesture: {gesture_name}")
        print(f"📁 Saving to: {self.gesture_path}")
    
    def record_training_videos(self, num_videos=15):
        """Record training videos with optimal parameters"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Error: Cannot open camera")
            return False
        
        print(f"\n📹 Recording {num_videos} training videos")
        print("📋 Guidelines:")
        print("  • Each video will be 3 seconds")
        print("  • Perform gesture clearly and consistently")
        print("  • Vary hand position slightly between videos")
        print("  • Keep good lighting")
        print("  • Press SPACE to start recording, ESC to quit")
        
        for i in range(num_videos):
            print(f"\n🎬 Preparing video {i+1}/{num_videos}")
            print("Press SPACE when ready...")
            
            # Wait for user to be ready
            while True:
                ret, frame = cap.read()
                if ret:
                    # Flip frame horizontally for mirror effect
                    frame = cv2.flip(frame, 1)
                    
                    # Add text overlay
                    cv2.putText(frame, f"Video {i+1}/{num_videos} - Press SPACE to start", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Gesture: {self.gesture_name}", 
                              (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    cv2.imshow('Gesture Training', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 32:  # Space key
                    break
                elif key == 27:  # Escape key
                    cap.release()
                    cv2.destroyAllWindows()
                    return False
            
            # Record video
            video_path = self.gesture_path / f"{self.gesture_name}_{i+1:02d}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (640, 480))
            
            print(f"🔴 Recording... (3 seconds)")
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < 3.0:  # 3 seconds
                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    
                    # Add recording indicator
                    remaining = 3.0 - (time.time() - start_time)
                    cv2.putText(frame, f"RECORDING: {remaining:.1f}s", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, f"Gesture: {self.gesture_name}", 
                              (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    cv2.imshow('Gesture Training', frame)
                    out.write(frame)
                    frame_count += 1
                
                if cv2.waitKey(1) & 0xFF == 27:  # Escape to quit
                    break
            
            out.release()
            print(f"✅ Video {i+1} saved: {frame_count} frames")
            time.sleep(1)  # Brief pause between videos
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"\n🎉 Training complete! {num_videos} videos recorded.")
        return True
    
    def get_training_stats(self):
        """Get statistics about recorded training data"""
        if not self.gesture_path.exists():
            return None
        
        videos = list(self.gesture_path.glob("*.mp4"))
        total_videos = len(videos)
        
        if total_videos == 0:
            return None
        
        total_frames = 0
        for video_path in videos:
            cap = cv2.VideoCapture(str(video_path))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            total_frames += frame_count
            cap.release()
        
        avg_frames = total_frames / total_videos
        
        stats = {
            'gesture_name': self.gesture_name,
            'total_videos': total_videos,
            'total_frames': total_frames,
            'avg_frames_per_video': avg_frames,
            'recommended_min_videos': 15,
            'recommended_frames_per_video': '25-35'
        }
        
        return stats

def main():
    print("🎯 New Gesture Training Tool")
    print("=" * 50)
    
    # Get gesture name from user
    while True:
        gesture_name = input("\n📝 Enter new gesture name (e.g., 'money', 'pay', 'card'): ").strip().lower()
        if gesture_name and gesture_name.isalpha():
            break
        print("❌ Please enter a valid gesture name (letters only)")
    
    # Check if gesture already exists
    existing_gestures = ["welcome", "bank", "block"]
    if gesture_name in existing_gestures:
        print(f"⚠️  Gesture '{gesture_name}' already exists in: {existing_gestures}")
        overwrite = input("Do you want to overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Training cancelled.")
            return
    
    # Create trainer
    trainer = NewGestureTrainer(gesture_name)
    
    # Get number of videos
    try:
        num_videos = int(input(f"\n📹 Number of training videos (recommended: 15-20): ") or "15")
        if num_videos < 10:
            print("⚠️  Warning: Less than 10 videos may result in poor accuracy")
        elif num_videos > 25:
            print("⚠️  Warning: More than 25 videos may not improve accuracy significantly")
    except ValueError:
        num_videos = 15
        print(f"Using default: {num_videos} videos")
    
    print(f"\n🎬 Instructions for '{gesture_name}' gesture:")
    print("1. Perform the gesture clearly and consistently")
    print("2. Vary hand position slightly between videos")
    print("3. Maintain good lighting")
    print("4. Each video will be 3 seconds (≈30 frames)")
    print("5. Press SPACE to start each recording")
    print("6. Press ESC to quit anytime")
    
    input("\nPress ENTER when ready to start training...")
    
    # Record training videos
    success = trainer.record_training_videos(num_videos)
    
    if success:
        # Show statistics
        stats = trainer.get_training_stats()
        if stats:
            print(f"\n📊 Training Statistics:")
            print(f"  • Gesture: {stats['gesture_name']}")
            print(f"  • Videos recorded: {stats['total_videos']}")
            print(f"  • Total frames: {stats['total_frames']}")
            print(f"  • Average frames per video: {stats['avg_frames_per_video']:.1f}")
            print(f"  • Quality: {'✅ Good' if stats['avg_frames_per_video'] >= 25 else '⚠️  Low frames'}")
        
        print(f"\n🎯 Next Steps:")
        print(f"1. Run the training script to add '{gesture_name}' to your model")
        print(f"2. Test the gesture in the web application")
        print(f"3. Retrain if accuracy is low")
        
        # Save training info
        info_file = trainer.gesture_path / "training_info.json"
        with open(info_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n✅ Training data saved to: {trainer.gesture_path}")
    else:
        print("\n❌ Training cancelled or failed")

if __name__ == "__main__":
    main()
