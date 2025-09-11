#!/usr/bin/env python3
"""
Smart Gesture Management System
Manage both original 250 gestures and custom gestures
"""
import json
import pandas as pd
from pathlib import Path
import os

class SmartGestureManager:
    def __init__(self):
        self.base_path = Path(".")
        self.webapp_path = self.base_path / "webapp"
        
    def show_status(self):
        """Show current system status"""
        print("🎯 Sign Language Recognition System Status")
        print("=" * 60)
        
        # Check original 250 gestures
        original_model_path = self.webapp_path / "module" / "islr" / "model.tflite"
        original_dict_path = self.webapp_path / "module" / "islr" / "dict_sign.csv"
        
        print("\n📊 Original 250 Gestures System:")
        if original_model_path.exists() and original_dict_path.exists():
            try:
                dict_df = pd.read_csv(original_dict_path)
                gestures = dict_df['sign'].tolist()
                print(f"   ✅ Status: ACTIVE")
                print(f"   📁 Model: {original_model_path}")
                print(f"   🎭 Gestures: {len(gestures)} available")
                print(f"   📝 Examples: {', '.join(gestures[:10])}...")
            except Exception as e:
                print(f"   ❌ Status: ERROR - {e}")
        else:
            print(f"   ❌ Status: MISSING FILES")
            print(f"   📁 Model path: {original_model_path}")
            print(f"   📄 Dict path: {original_dict_path}")
        
        # Check custom gestures
        print("\n🎨 Custom Gestures System:")
        
        # Trained gestures
        classifier_path = self.base_path / "custom_gesture_classifier.pkl"
        mapping_path = self.base_path / "custom_gesture_mapping.json"
        
        trained_gestures = []
        if classifier_path.exists() and mapping_path.exists():
            try:
                with open(mapping_path, 'r') as f:
                    mapping = json.load(f)
                trained_gestures = list(mapping.keys())
                print(f"   ✅ Trained gestures: {len(trained_gestures)}")
                print(f"   🎭 Available: {', '.join(trained_gestures)}")
            except Exception as e:
                print(f"   ❌ Trained gestures: ERROR - {e}")
        else:
            print(f"   ⚠️  Trained gestures: NONE")
        
        # Pattern-based gestures
        pattern_mapping_path = self.base_path / "simple_custom_mapping.json"
        pattern_gestures = []
        if pattern_mapping_path.exists():
            try:
                with open(pattern_mapping_path, 'r') as f:
                    mapping = json.load(f)
                pattern_gestures = list(mapping.keys())
                print(f"   ✅ Pattern gestures: {len(pattern_gestures)}")
                print(f"   🎭 Available: {', '.join(pattern_gestures)}")
            except Exception as e:
                print(f"   ❌ Pattern gestures: ERROR - {e}")
        else:
            print(f"   ⚠️  Pattern gestures: NONE")
        
        # Training data
        gesture_data_path = self.base_path / "gesture_data"
        training_files = []
        if gesture_data_path.exists():
            training_files = list(gesture_data_path.glob("*_landmarks.csv"))
            print(f"   📂 Training data: {len(training_files)} files")
            for file in training_files[:5]:
                gesture_name = file.stem.replace("_landmarks", "")
                print(f"      - {gesture_name}")
            if len(training_files) > 5:
                print(f"      ... and {len(training_files) - 5} more")
        else:
            print(f"   📂 Training data: NO DATA FOLDER")
        
        # System recommendations
        print("\n💡 System Recommendations:")
        
        total_custom = len(trained_gestures) + len(pattern_gestures)
        if total_custom == 0:
            print("   🚀 Get started: Run 'python record_new_gesture.py' to add your first custom gesture")
        elif len(trained_gestures) == 0 and len(training_files) > 0:
            print("   🎯 Train model: Run 'python train_custom_gestures.py' to train your recorded data")
        elif len(trained_gestures) > 0:
            print("   ✅ System ready: Both original and custom gestures available")
            print("   🌐 Start webapp: 'cd webapp/app && python main.py'")
        
        if not original_model_path.exists():
            print("   ⚠️  Missing original model - some features may not work")
        
        return {
            'original_gestures': len(gestures) if 'gestures' in locals() else 0,
            'trained_custom': len(trained_gestures),
            'pattern_custom': len(pattern_gestures),
            'training_files': len(training_files)
        }
    
    def list_gestures(self):
        """List all available gestures"""
        print("🎭 Available Gestures")
        print("=" * 40)
        
        # Original gestures
        original_dict_path = self.webapp_path / "module" / "islr" / "dict_sign.csv"
        if original_dict_path.exists():
            try:
                dict_df = pd.read_csv(original_dict_path)
                gestures = dict_df['sign'].tolist()
                print(f"\n📚 Original 250 Gestures ({len(gestures)} total):")
                
                # Show in columns
                for i in range(0, min(50, len(gestures)), 5):
                    row_gestures = gestures[i:i+5]
                    print("   " + "  ".join(f"{g:<12}" for g in row_gestures))
                
                if len(gestures) > 50:
                    print(f"   ... and {len(gestures) - 50} more")
                
            except Exception as e:
                print(f"❌ Error reading original gestures: {e}")
        
        # Custom trained gestures
        mapping_path = self.base_path / "custom_gesture_mapping.json"
        if mapping_path.exists():
            try:
                with open(mapping_path, 'r') as f:
                    mapping = json.load(f)
                trained_gestures = list(mapping.keys())
                print(f"\n🎨 Custom Trained Gestures ({len(trained_gestures)} total):")
                for gesture in trained_gestures:
                    print(f"   ✅ {gesture}")
            except Exception as e:
                print(f"❌ Error reading trained gestures: {e}")
        
        # Pattern-based gestures
        pattern_mapping_path = self.base_path / "simple_custom_mapping.json"
        if pattern_mapping_path.exists():
            try:
                with open(pattern_mapping_path, 'r') as f:
                    mapping = json.load(f)
                pattern_gestures = list(mapping.keys())
                print(f"\n🎯 Pattern-Based Gestures ({len(pattern_gestures)} total):")
                for gesture in pattern_gestures:
                    print(f"   🎪 {gesture}")
            except Exception as e:
                print(f"❌ Error reading pattern gestures: {e}")
    
    def quick_train(self):
        """Quick training of available data"""
        print("🚀 Quick Training")
        print("=" * 30)
        
        gesture_data_path = self.base_path / "gesture_data"
        if not gesture_data_path.exists():
            print("❌ No gesture_data directory found!")
            print("💡 Run 'python record_new_gesture.py' first")
            return
        
        training_files = list(gesture_data_path.glob("*_landmarks.csv"))
        if not training_files:
            print("❌ No training data found!")
            print("💡 Run 'python record_new_gesture.py' to record gestures")
            return
        
        print(f"📂 Found {len(training_files)} training files")
        for file in training_files:
            gesture_name = file.stem.replace("_landmarks", "")
            print(f"   - {gesture_name}")
        
        print("\n🎯 Starting training...")
        
        # Import and run training
        try:
            import train_custom_gestures
            print("✅ Training completed!")
        except Exception as e:
            print(f"❌ Training failed: {e}")
            print("💡 Try running: python train_custom_gestures.py")
    
    def start_webapp(self):
        """Start the web application"""
        print("🌐 Starting Web Application")
        print("=" * 40)
        
        webapp_main = self.webapp_path / "app" / "main.py"
        if not webapp_main.exists():
            print(f"❌ Web app not found at: {webapp_main}")
            return
        
        print("🚀 Starting server...")
        print("📍 URL: http://127.0.0.1:8001")
        print("⏹️  Press Ctrl+C to stop")
        
        try:
            os.chdir(webapp_main.parent)
            os.system("python main.py")
        except KeyboardInterrupt:
            print("\n⏹️  Server stopped")
        except Exception as e:
            print(f"❌ Error starting webapp: {e}")

def main():
    print("🎯 Smart Gesture Management System")
    print("=" * 50)
    
    manager = SmartGestureManager()
    
    while True:
        print("\n📋 Available Commands:")
        print("   1. Show system status")
        print("   2. List all gestures")
        print("   3. Quick train models")
        print("   4. Start web application")
        print("   5. Exit")
        
        try:
            choice = input("\n👉 Choose option (1-5): ").strip()
            
            if choice == "1":
                manager.show_status()
            elif choice == "2":
                manager.list_gestures()
            elif choice == "3":
                manager.quick_train()
            elif choice == "4":
                manager.start_webapp()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
