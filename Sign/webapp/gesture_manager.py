import pandas as pd
import json
import os
from pathlib import Path

class GestureManager:
    def __init__(self, dict_file="module/islr/dict_sign.csv"):
        self.dict_file = dict_file
        
    def load_gesture_dict(self):
        """Load the gesture dictionary"""
        if os.path.exists(self.dict_file):
            return pd.read_csv(self.dict_file)
        else:
            # Create empty dictionary if it doesn't exist
            return pd.DataFrame(columns=['sign', 'sign_ord'])
    
    def add_new_gesture(self, gesture_name):
        """Add a new gesture to the dictionary"""
        df = self.load_gesture_dict()
        
        # Check if gesture already exists
        if gesture_name in df['sign'].values:
            print(f"Gesture '{gesture_name}' already exists!")
            return df[df['sign'] == gesture_name]['sign_ord'].iloc[0]
        
        # Get next sign_ord
        next_ord = df['sign_ord'].max() + 1 if len(df) > 0 else 0
        
        # Add new gesture
        new_row = pd.DataFrame({
            'sign': [gesture_name],
            'sign_ord': [next_ord]
        })
        
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.dict_file, index=False)
        print(f"Added gesture '{gesture_name}' with ID {next_ord}")
        
        return next_ord
    
    def remove_gesture(self, gesture_name):
        """Remove a gesture from the dictionary"""
        df = self.load_gesture_dict()
        
        if gesture_name not in df['sign'].values:
            print(f"Gesture '{gesture_name}' not found!")
            return False
        
        # Remove the gesture
        df = df[df['sign'] != gesture_name]
        
        # Reassign sign_ord to maintain continuity
        df = df.sort_values('sign_ord').reset_index(drop=True)
        df['sign_ord'] = range(len(df))
        
        df.to_csv(self.dict_file, index=False)
        print(f"Removed gesture '{gesture_name}'")
        return True
    
    def list_gestures(self):
        """List all gestures in the dictionary"""
        df = self.load_gesture_dict()
        print(f"\nTotal gestures: {len(df)}")
        print("Gestures:")
        for idx, row in df.iterrows():
            print(f"  {row['sign_ord']}: {row['sign']}")
        return df
    
    def update_model_classes(self, model_file="module/islr/model.py"):
        """Update the NUM_CLASSES in model.py"""
        df = self.load_gesture_dict()
        num_classes = len(df)
        
        if os.path.exists(model_file):
            with open(model_file, 'r') as f:
                content = f.read()
            
            # Replace NUM_CLASSES line
            import re
            content = re.sub(r'NUM_CLASSES\s*=\s*\d+', f'NUM_CLASSES = {num_classes}', content)
            
            with open(model_file, 'w') as f:
                f.write(content)
            
            print(f"Updated {model_file} with NUM_CLASSES = {num_classes}")
        else:
            print(f"Model file {model_file} not found!")
        
        return num_classes
    
    def batch_add_gestures(self, gesture_list):
        """Add multiple gestures at once"""
        added_gestures = []
        for gesture in gesture_list:
            gesture_id = self.add_new_gesture(gesture)
            added_gestures.append((gesture, gesture_id))
        return added_gestures
    
    def batch_remove_gestures(self, gesture_list):
        """Remove multiple gestures at once"""
        removed_gestures = []
        for gesture in gesture_list:
            if self.remove_gesture(gesture):
                removed_gestures.append(gesture)
        return removed_gestures

# CLI Interface
def main():
    manager = GestureManager()
    
    while True:
        print("\n=== Gesture Manager ===")
        print("1. List all gestures")
        print("2. Add new gesture")
        print("3. Remove gesture")
        print("4. Add multiple gestures")
        print("5. Remove multiple gestures")
        print("6. Update model classes")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            manager.list_gestures()
            
        elif choice == '2':
            gesture_name = input("Enter gesture name: ").strip()
            if gesture_name:
                manager.add_new_gesture(gesture_name)
            else:
                print("Invalid gesture name!")
                
        elif choice == '3':
            gesture_name = input("Enter gesture name to remove: ").strip()
            if gesture_name:
                manager.remove_gesture(gesture_name)
            else:
                print("Invalid gesture name!")
                
        elif choice == '4':
            gestures_input = input("Enter gesture names (comma-separated): ").strip()
            if gestures_input:
                gestures = [g.strip() for g in gestures_input.split(',')]
                added = manager.batch_add_gestures(gestures)
                print(f"Added {len(added)} gestures: {added}")
            else:
                print("No gestures provided!")
                
        elif choice == '5':
            gestures_input = input("Enter gesture names to remove (comma-separated): ").strip()
            if gestures_input:
                gestures = [g.strip() for g in gestures_input.split(',')]
                removed = manager.batch_remove_gestures(gestures)
                print(f"Removed {len(removed)} gestures: {removed}")
            else:
                print("No gestures provided!")
                
        elif choice == '6':
            num_classes = manager.update_model_classes()
            print(f"Model updated with {num_classes} classes")
            
        elif choice == '7':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice! Please enter 1-7.")

if __name__ == "__main__":
    main()
