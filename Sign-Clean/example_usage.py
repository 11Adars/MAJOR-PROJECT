#!/usr/bin/env python3
"""
Example Usage Script
Demonstrates how to use the video processing system
"""
import os
from pathlib import Path
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from video_processor import VideoProcessor
from advanced_train import AdvancedGestureTrainer

def example_usage():
    """Example of how to use the video processing system"""
    
    print("🎬 Video Processing System - Example Usage")
    print("=" * 50)
    
    # Example 1: Process videos from a folder
    print("\n📁 Example 1: Processing videos from folder")
    print("-" * 40)
    
    # Assume you have videos in a folder called "my_gesture_videos"
    input_folder = "my_gesture_videos"  # Change this to your actual folder
    
    if Path(input_folder).exists():
        processor = VideoProcessor(
            input_folder=input_folder,
            output_folder="processed_gestures",
            gesture_data_folder="training_data"
        )
        
        # Process all videos with 3 augmentations per video
        processor.process_all_videos(
            num_augmentations=3,
            extract_landmarks=True
        )
        
        print("✅ Video processing completed!")
    else:
        print(f"❌ Folder '{input_folder}' does not exist")
        print("   Create this folder and add your gesture videos")
    
    # Example 2: Train models on the processed data
    print("\n🤖 Example 2: Training gesture recognition model")
    print("-" * 40)
    
    if Path("training_data").exists():
        trainer = AdvancedGestureTrainer(
            data_folder="training_data",
            model_output_folder="gesture_models"
        )
        
        # Train using all available data
        best_model, results, saved_files = trainer.train_complete_pipeline(
            balance_data=True,
            use_cross_validation=True,
            model_name="my_gesture_classifier"
        )
        
        print("✅ Model training completed!")
        print(f"📁 Models saved in: gesture_models/")
        
    else:
        print("❌ No training data found")
        print("   Run video processing first to generate training data")

def create_example_folder_structure():
    """Create an example folder structure for demonstration"""
    
    print("\n📂 Creating example folder structure...")
    
    # Create example folder structure
    example_folder = Path("example_gesture_videos")
    
    # Create gesture folders
    gestures = ["hello", "goodbye", "thumbs_up", "peace", "stop"]
    
    for gesture in gestures:
        gesture_folder = example_folder / gesture
        gesture_folder.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder info file
        info_file = gesture_folder / "README.txt"
        with open(info_file, 'w') as f:
            f.write(f"Place your '{gesture}' gesture videos in this folder.\n")
            f.write(f"Supported formats: .mp4, .avi, .mov, .mkv, .wmv, .flv\n")
            f.write(f"\nExample filenames:\n")
            f.write(f"- {gesture}_video1.mp4\n")
            f.write(f"- {gesture}_recording2.avi\n")
            f.write(f"- {gesture}_sample3.mov\n")
    
    print(f"✅ Example folder structure created at: {example_folder}")
    print(f"   Add your gesture videos to the appropriate subfolders")
    
    return example_folder

def quick_test():
    """Quick test with minimal setup"""
    
    print("\n⚡ Quick Test Mode")
    print("-" * 20)
    
    # Check if we have any existing gesture data
    gesture_data_folder = Path("gesture_data")
    if gesture_data_folder.exists():
        csv_files = list(gesture_data_folder.glob("*.csv"))
        if csv_files:
            print(f"Found {len(csv_files)} CSV files in gesture_data/")
            
            # Quick training test
            trainer = AdvancedGestureTrainer(
                data_folder="gesture_data",
                model_output_folder="test_models"
            )
            
            try:
                # Load data from first CSV file
                df = trainer.load_data(str(csv_files[0]))
                X, y = trainer.prepare_features(df)
                
                print(f"📊 Data shape: {X.shape}")
                print(f"🎯 Gestures: {list(trainer.gesture_mapping.values())}")
                
                # Quick training (no cross-validation for speed)
                best_model, results, _ = trainer.train_and_evaluate_models(
                    X, y, 
                    balance_data=True, 
                    use_cross_validation=False
                )
                
                print("✅ Quick test completed successfully!")
                
            except Exception as e:
                print(f"❌ Quick test failed: {e}")
        else:
            print("❌ No CSV files found in gesture_data/")
    else:
        print("❌ No gesture_data folder found")
        print("   Run video processing first or use existing gesture data")

if __name__ == "__main__":
    print("🎯 Choose an option:")
    print("1. Create example folder structure")
    print("2. Run full example (requires videos)")
    print("3. Quick test with existing data")
    print("4. Show usage instructions")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        create_example_folder_structure()
    elif choice == "2":
        example_usage()
    elif choice == "3":
        quick_test()
    elif choice == "4":
        print("\n📖 Usage Instructions:")
        print("=" * 30)
        print("1. Create folder structure with gesture videos")
        print("2. Run: python process_videos.py")
        print("3. Run: python advanced_train.py")
        print("4. Use trained models in your application")
        print("\nFor detailed guide, see: VIDEO_PROCESSING_GUIDE.md")
    else:
        print("❌ Invalid choice")
    
    input("\nPress Enter to exit...")
