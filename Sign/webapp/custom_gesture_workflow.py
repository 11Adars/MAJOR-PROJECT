"""
Complete workflow script for adding custom gestures
"""
from gesture_collector import GestureCollector
from gesture_manager import GestureManager
from data_processor import GestureDataProcessor
import os

def add_custom_gesture_workflow():
    """Complete workflow to add a new gesture"""
    print("=== Custom Gesture Addition Workflow ===\n")
    
    # Step 1: Get gesture information
    gesture_name = input("Enter the name of your gesture: ").strip()
    if not gesture_name:
        print("Invalid gesture name!")
        return
    
    num_sequences = int(input("Enter number of sequences to collect (default 30): ") or "30")
    frames_per_sequence = int(input("Enter frames per sequence (default 50): ") or "50")
    
    print(f"\nAdding gesture: {gesture_name}")
    print(f"Sequences: {num_sequences}")
    print(f"Frames per sequence: {frames_per_sequence}")
    
    # Step 2: Collect gesture data
    print("\n--- Step 1: Collecting Gesture Data ---")
    collector = GestureCollector(gesture_name)
    sequences = collector.collect_gesture_data(num_sequences, frames_per_sequence)
    
    if not sequences:
        print("No data collected. Exiting...")
        return
    
    # Find the collected CSV file
    csv_files = [f for f in os.listdir("custom_gestures") if f.startswith(gesture_name) and f.endswith(".csv")]
    if not csv_files:
        print("No CSV file found. Exiting...")
        return
    
    csv_file = os.path.join("custom_gestures", csv_files[-1])  # Get the latest file
    print(f"Data collected: {csv_file}")
    
    # Step 3: Process the data
    print("\n--- Step 2: Processing Data ---")
    processor = GestureDataProcessor()
    processed_sequences = processor.process_collected_data(csv_file, gesture_name)
    training_data = processor.convert_to_training_format(processed_sequences)
    
    training_file = processor.save_training_data(training_data, f"{gesture_name}_training_data.csv")
    
    # Step 4: Update gesture dictionary
    print("\n--- Step 3: Updating Gesture Dictionary ---")
    manager = GestureManager()
    gesture_id = manager.add_new_gesture(gesture_name)
    
    # Step 5: Update model configuration
    print("\n--- Step 4: Updating Model Configuration ---")
    num_classes = manager.update_model_classes()
    
    print(f"\n=== Workflow Complete ===")
    print(f"Gesture '{gesture_name}' added with ID: {gesture_id}")
    print(f"Training data saved: {training_file}")
    print(f"Model updated with {num_classes} classes")
    print(f"\nNext steps:")
    print(f"1. Review the collected data in: {csv_file}")
    print(f"2. Add more sequences if needed")
    print(f"3. Retrain the model with the new data")

def remove_gesture_workflow():
    """Workflow to remove unwanted gestures"""
    print("=== Remove Gesture Workflow ===\n")
    
    manager = GestureManager()
    
    # Show current gestures
    print("Current gestures:")
    df = manager.list_gestures()
    
    if len(df) == 0:
        print("No gestures found!")
        return
    
    # Get gestures to remove
    print("\nEnter gesture names to remove (comma-separated):")
    gestures_input = input().strip()
    
    if not gestures_input:
        print("No gestures specified!")
        return
    
    gestures_to_remove = [g.strip() for g in gestures_input.split(',')]
    
    # Confirm removal
    print(f"\nGestures to remove: {gestures_to_remove}")
    confirm = input("Are you sure? (y/N): ").strip().lower()
    
    if confirm == 'y':
        removed = manager.batch_remove_gestures(gestures_to_remove)
        num_classes = manager.update_model_classes()
        
        print(f"\nRemoved {len(removed)} gestures: {removed}")
        print(f"Model updated with {num_classes} classes")
        print("\nNext step: Retrain the model")
    else:
        print("Operation cancelled.")

def main():
    """Main menu"""
    while True:
        print("\n=== Custom Gesture System ===")
        print("1. Add new gesture (webcam)")
        print("2. Add gesture from video file")
        print("3. Remove gestures")
        print("4. List all gestures")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            add_custom_gesture_workflow()
        elif choice == '2':
            try:
                from video_gesture_processor import add_gesture_from_video
                add_gesture_from_video()
            except ImportError:
                print("Video processor not available!")
        elif choice == '3':
            remove_gesture_workflow()
        elif choice == '4':
            manager = GestureManager()
            manager.list_gestures()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please enter 1-5.")

if __name__ == "__main__":
    main()
