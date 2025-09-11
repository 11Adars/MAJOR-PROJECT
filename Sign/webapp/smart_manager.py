#!/usr/bin/env python3
"""
Smart Gesture Training Manager
- Add new gestures without retraining existing ones
- Manage training cache
- Quick gesture addition workflow
"""

import os
import json
from pathlib import Path
import subprocess
import sys

class SmartGestureManager:
    def __init__(self):
        self.custom_videos_folder = Path("custom_videos")
        self.cache_dir = Path("training_cache")
        self.processed_files_log = self.cache_dir / "processed_files.json"
        
    def list_gestures(self):
        """List all available gestures"""
        if not self.custom_videos_folder.exists():
            print("❌ No custom_videos folder found")
            return []
        
        gestures = []
        for folder in self.custom_videos_folder.iterdir():
            if folder.is_dir():
                video_count = len(list(folder.glob("*.mp4")))
                gestures.append({
                    'name': folder.name,
                    'videos': video_count,
                    'folder': folder
                })
        
        return gestures
    
    def show_status(self):
        """Show current training status"""
        print("🎯 Smart Gesture Training Status")
        print("=" * 50)
        
        gestures = self.list_gestures()
        if not gestures:
            print("❌ No gestures found")
            return
        
        # Load processed files info
        processed_info = {}
        if self.processed_files_log.exists():
            with open(self.processed_files_log, 'r') as f:
                processed_data = json.load(f)
            
            for file_path, info in processed_data.items():
                gesture = info.get('gesture', 'unknown')
                if gesture not in processed_info:
                    processed_info[gesture] = {'videos': 0, 'sequences': 0}
                processed_info[gesture]['videos'] += 1
                processed_info[gesture]['sequences'] += info.get('sequences_count', 0)
        
        print(f"📁 Found {len(gestures)} gesture types:")
        for gesture in gestures:
            name = gesture['name']
            videos = gesture['videos']
            
            if name in processed_info:
                processed_videos = processed_info[name]['videos']
                sequences = processed_info[name]['sequences']
                status = f"✅ Trained ({processed_videos}/{videos} videos, {sequences} sequences)"
                if processed_videos < videos:
                    status += f" - {videos - processed_videos} new videos need training"
            else:
                status = "❌ Not trained"
            
            print(f"  🎭 {name:15} | {videos:2} videos | {status}")
        
        # Check if models exist
        print(f"\n📂 Model files:")
        model_files = [
            "simple_custom_lstm.h5",
            "simple_custom_labels.pkl", 
            "simple_custom_mapping.json"
        ]
        
        for file_name in model_files:
            exists = "✅" if Path(file_name).exists() else "❌"
            print(f"  {exists} {file_name}")
    
    def add_new_gesture(self, gesture_name):
        """Add a new gesture"""
        print(f"🎭 Adding new gesture: {gesture_name}")
        
        # Create gesture folder
        gesture_folder = self.custom_videos_folder / gesture_name
        gesture_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Created folder: {gesture_folder}")
        print(f"📹 Now record videos for '{gesture_name}' gesture")
        
        return gesture_folder
    
    def quick_train(self, gesture_name=None):
        """Quick training for specific gesture or all new gestures"""
        print("🚀 Starting incremental training...")
        
        if gesture_name:
            gesture_folder = self.custom_videos_folder / gesture_name
            if not gesture_folder.exists():
                print(f"❌ Gesture '{gesture_name}' not found")
                return False
            
            video_count = len(list(gesture_folder.glob("*.mp4")))
            if video_count == 0:
                print(f"❌ No videos found for '{gesture_name}'")
                print(f"   Record videos first using the recorder")
                return False
            
            print(f"📹 Found {video_count} videos for '{gesture_name}'")
        
        # Run incremental trainer
        try:
            cmd = [sys.executable, "incremental_lstm_trainer.py"]
            print(f"🔄 Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, cwd=Path.cwd())
            
            if result.returncode == 0:
                print("✅ Training completed successfully!")
                return True
            else:
                print(f"❌ Training failed with exit code: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ Training error: {e}")
            return False
    
    def clear_cache(self, gesture_name=None):
        """Clear training cache"""
        if gesture_name:
            print(f"🧹 Clearing cache for: {gesture_name}")
            # Remove specific gesture cache files
            if self.cache_dir.exists():
                cache_files = list(self.cache_dir.glob(f"**/*{gesture_name}*"))
                for cache_file in cache_files:
                    try:
                        cache_file.unlink()
                        print(f"  🗑️ Removed: {cache_file}")
                    except Exception as e:
                        print(f"  ❌ Could not remove {cache_file}: {e}")
        else:
            print("🧹 Clearing all training cache...")
            if self.cache_dir.exists():
                import shutil
                shutil.rmtree(self.cache_dir)
                print("  🗑️ Cache cleared")
    
    def interactive_menu(self):
        """Interactive menu for gesture management"""
        while True:
            print("\n" + "="*60)
            print("🎭 SMART GESTURE TRAINING MANAGER")
            print("="*60)
            print("1. 📊 Show training status")
            print("2. ➕ Add new gesture")
            print("3. 🚀 Quick train (all new)")
            print("4. 🎯 Train specific gesture")
            print("5. 📹 Record videos")
            print("6. 🧹 Clear cache")
            print("0. 🚪 Exit")
            print("-"*60)
            
            choice = input("Choose option: ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            
            elif choice == "1":
                self.show_status()
            
            elif choice == "2":
                gesture_name = input("🎭 Enter gesture name: ").strip()
                if gesture_name:
                    self.add_new_gesture(gesture_name)
                    
                    print("\n📋 Next steps:")
                    print(f"1. Record videos: python record_gestures.py")
                    print(f"2. Choose option 1 and enter: {gesture_name}")
                    print(f"3. Train model: python smart_manager.py (option 3)")
            
            elif choice == "3":
                self.quick_train()
            
            elif choice == "4":
                gestures = self.list_gestures()
                if not gestures:
                    print("❌ No gestures found")
                    continue
                
                print("Available gestures:")
                for i, gesture in enumerate(gestures, 1):
                    print(f"  {i}. {gesture['name']} ({gesture['videos']} videos)")
                
                try:
                    idx = int(input("Select gesture number: ")) - 1
                    if 0 <= idx < len(gestures):
                        self.quick_train(gestures[idx]['name'])
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Please enter a number")
            
            elif choice == "5":
                self.launch_recorder()
            
            elif choice == "6":
                clear_all = input("🧹 Clear all cache? (y/n): ").strip().lower()
                if clear_all == 'y':
                    self.clear_cache()
                else:
                    gesture_name = input("🎭 Enter gesture name to clear (or empty for cancel): ").strip()
                    if gesture_name:
                        self.clear_cache(gesture_name)
            
            else:
                print("❌ Invalid option")
    
    def launch_recorder(self):
        """Launch video recorder"""
        try:
            print("📹 Launching recorder...")
            subprocess.run([sys.executable, "record_gestures.py"])
        except Exception as e:
            print(f"❌ Failed to launch recorder: {e}")

def main():
    manager = SmartGestureManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            manager.show_status()
        elif command == "train":
            gesture = sys.argv[2] if len(sys.argv) > 2 else None
            manager.quick_train(gesture)
        elif command == "add":
            if len(sys.argv) > 2:
                manager.add_new_gesture(sys.argv[2])
            else:
                print("❌ Usage: python smart_manager.py add <gesture_name>")
        elif command == "clear":
            gesture = sys.argv[2] if len(sys.argv) > 2 else None
            manager.clear_cache(gesture)
        else:
            print("❌ Unknown command. Available: status, train, add, clear")
    else:
        manager.interactive_menu()

if __name__ == "__main__":
    main()
