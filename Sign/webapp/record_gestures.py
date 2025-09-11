#!/usr/bin/env python3
"""
Webcam Video Recorder for Custom Gestures
Records gesture videos directly from your laptop camera
"""

import cv2
import os
import time
from pathlib import Path

class GestureRecorder:
    def __init__(self, output_dir="custom_videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def record_gesture_videos(self, gesture_name, num_videos=8, video_duration=3):
        """Record multiple videos for a gesture"""
        
        gesture_folder = self.output_dir / gesture_name
        gesture_folder.mkdir(exist_ok=True)
        
        print(f"\n🎯 Recording {num_videos} videos for gesture: '{gesture_name}'")
        print(f"📁 Saving to: {gesture_folder}")
        print(f"⏱️  Each video: {video_duration} seconds")
        print("\n" + "="*50)
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Could not open camera")
            return False
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("📸 Camera initialized. Position yourself in the frame.")
        print("👋 Show the gesture clearly with hands and face visible.")
        print("\nPress 'q' to quit, 's' to skip current video\n")
        
        for video_num in range(1, num_videos + 1):
            print(f"\n🎬 Preparing to record video {video_num}/{num_videos}")
            print("Get ready... Press SPACE when ready to record!")
            
            # Wait for user to get ready
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Mirror the frame
                frame = cv2.flip(frame, 1)
                
                # Add text overlay
                cv2.putText(frame, f"Video {video_num}/{num_videos} - Press SPACE to start", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Gesture: {gesture_name}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(frame, "Position hands and face clearly in frame", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                cv2.imshow('Gesture Recorder', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):  # Space to start recording
                    break
                elif key == ord('q'):  # Quit
                    cap.release()
                    cv2.destroyAllWindows()
                    return False
                elif key == ord('s'):  # Skip this video
                    print(f"⏭️  Skipping video {video_num}")
                    break
            
            if key == ord('s'):
                continue
            
            # Start recording
            timestamp = int(time.time())
            video_filename = gesture_folder / f"{gesture_name}_{video_num}_{timestamp}.mp4"
            
            # Video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(video_filename), fourcc, 30.0, (640, 480))
            
            print(f"🔴 RECORDING... {video_duration} seconds")
            
            start_time = time.time()
            frames_recorded = 0
            
            while time.time() - start_time < video_duration:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Mirror the frame
                frame = cv2.flip(frame, 1)
                
                # Add recording indicator
                remaining_time = video_duration - (time.time() - start_time)
                cv2.putText(frame, f"RECORDING: {remaining_time:.1f}s", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"Gesture: {gesture_name}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # Draw recording circle
                cv2.circle(frame, (600, 40), 15, (0, 0, 255), -1)
                
                out.write(frame)
                cv2.imshow('Gesture Recorder', frame)
                frames_recorded += 1
                
                # Allow quitting during recording
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            out.release()
            print(f"✅ Saved: {video_filename.name} ({frames_recorded} frames)")
            
            # Brief pause between videos
            if video_num < num_videos:
                print("💤 2-second break before next video...")
                time.sleep(2)
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n🎉 Completed recording {num_videos} videos for '{gesture_name}'!")
        return True

def main():
    print("🎥 Custom Gesture Video Recorder")
    print("=" * 40)
    
    recorder = GestureRecorder()
    
    while True:
        print(f"\n📋 Current gesture folders:")
        folders = [d.name for d in recorder.output_dir.iterdir() if d.is_dir()]
        if folders:
            for i, folder in enumerate(folders, 1):
                video_count = len(list((recorder.output_dir / folder).glob("*.mp4")))
                print(f"  {i}. {folder} ({video_count} videos)")
        else:
            print("  (No gesture folders yet)")
        
        print(f"\n🎯 Options:")
        print(f"  1. Record new gesture")
        print(f"  2. Add videos to existing gesture")
        print(f"  3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            gesture_name = input("\nEnter gesture name (e.g., 'welcome', 'hello'): ").strip().lower()
            if not gesture_name:
                print("❌ Invalid gesture name")
                continue
            
            num_videos = input(f"Number of videos to record (default 8): ").strip()
            num_videos = int(num_videos) if num_videos.isdigit() else 8
            
            duration = input(f"Video duration in seconds (default 3): ").strip()
            duration = int(duration) if duration.isdigit() else 3
            
            success = recorder.record_gesture_videos(gesture_name, num_videos, duration)
            
            if success:
                print(f"\n🚀 Ready to train? Run: python custom_gesture_trainer.py")
            
        elif choice == '2':
            if not folders:
                print("❌ No existing gestures. Choose option 1 first.")
                continue
            
            print(f"\nExisting gestures:")
            for i, folder in enumerate(folders, 1):
                print(f"  {i}. {folder}")
            
            try:
                idx = int(input(f"Select gesture (1-{len(folders)}): ")) - 1
                if 0 <= idx < len(folders):
                    gesture_name = folders[idx]
                    
                    num_videos = input(f"Additional videos to record (default 4): ").strip()
                    num_videos = int(num_videos) if num_videos.isdigit() else 4
                    
                    success = recorder.record_gesture_videos(gesture_name, num_videos)
                    
                    if success:
                        total_videos = len(list((recorder.output_dir / gesture_name).glob("*.mp4")))
                        print(f"\n📊 Total videos for '{gesture_name}': {total_videos}")
                        print(f"🚀 Ready to train? Run: python custom_gesture_trainer.py")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
        
        elif choice == '3':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
