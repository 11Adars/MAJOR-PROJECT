"""
Utility to prepare and format collected gesture data for training
"""
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

class GestureDataProcessor:
    def __init__(self, output_dir="processed_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def process_collected_data(self, csv_file, gesture_name):
        """Process the collected CSV data to match training format"""
        print(f"Processing {csv_file} for gesture: {gesture_name}")
        
        # Load the collected data
        df = pd.read_csv(csv_file)
        
        # Group by sequence_id and frame to get complete frames
        processed_sequences = []
        
        for seq_id in df['sequence_id'].unique():
            seq_data = df[df['sequence_id'] == seq_id]
            
            # Group by frame
            sequence_frames = []
            for frame_num in sorted(seq_data['frame'].unique()):
                frame_data = seq_data[seq_data['frame'] == frame_num]
                
                # Convert to the format expected by the model
                frame_landmarks = self.format_frame_landmarks(frame_data)
                if frame_landmarks is not None:
                    sequence_frames.append(frame_landmarks)
            
            if sequence_frames:
                processed_sequences.append({
                    'sequence_id': seq_id,
                    'sign': gesture_name,
                    'landmarks': sequence_frames
                })
        
        return processed_sequences
    
    def format_frame_landmarks(self, frame_data):
        """Format frame landmarks to match expected structure"""
        landmarks = {}
        
        # Group by landmark type
        for lm_type in ['pose', 'left_hand', 'right_hand', 'face']:
            type_data = frame_data[frame_data['type'] == lm_type]
            if not type_data.empty:
                landmarks[lm_type] = []
                for _, row in type_data.iterrows():
                    landmarks[lm_type].append({
                        'x': row['x'],
                        'y': row['y'],
                        'z': row['z']
                    })
        
        return landmarks if landmarks else None
    
    def convert_to_training_format(self, processed_sequences, max_frames=50):
        """Convert processed sequences to training format"""
        training_data = []
        
        for sequence in processed_sequences:
            landmarks_data = sequence['landmarks']
            
            # Pad or truncate to max_frames
            if len(landmarks_data) > max_frames:
                landmarks_data = landmarks_data[:max_frames]
            elif len(landmarks_data) < max_frames:
                # Pad with last frame
                last_frame = landmarks_data[-1] if landmarks_data else {}
                while len(landmarks_data) < max_frames:
                    landmarks_data.append(last_frame)
            
            # Flatten landmarks for each frame
            flattened_sequence = []
            for frame in landmarks_data:
                flattened_frame = self.flatten_frame_landmarks(frame)
                flattened_sequence.append(flattened_frame)
            
            training_data.append({
                'sequence_id': sequence['sequence_id'],
                'sign': sequence['sign'],
                'landmarks': flattened_sequence
            })
        
        return training_data
    
    def flatten_frame_landmarks(self, frame_landmarks):
        """Flatten frame landmarks to a single vector"""
        flattened = []
        
        # Expected order: pose, left_hand, right_hand, face
        landmark_types = ['pose', 'left_hand', 'right_hand', 'face']
        expected_counts = {
            'pose': 33,
            'left_hand': 21,
            'right_hand': 21,
            'face': 468
        }
        
        for lm_type in landmark_types:
            if lm_type in frame_landmarks:
                landmarks = frame_landmarks[lm_type]
                for landmark in landmarks:
                    flattened.extend([landmark['x'], landmark['y'], landmark['z']])
                
                # Pad if not enough landmarks
                current_count = len(landmarks)
                expected_count = expected_counts[lm_type]
                if current_count < expected_count:
                    padding = [0.0, 0.0, 0.0] * (expected_count - current_count)
                    flattened.extend(padding)
            else:
                # Add zeros if landmark type is missing
                padding = [0.0, 0.0, 0.0] * expected_counts[lm_type]
                flattened.extend(padding)
        
        return flattened
    
    def save_training_data(self, training_data, filename):
        """Save training data to file"""
        output_file = os.path.join(self.output_dir, filename)
        
        # Convert to DataFrame
        rows = []
        for item in training_data:
            for frame_idx, frame_landmarks in enumerate(item['landmarks']):
                rows.append({
                    'sequence_id': item['sequence_id'],
                    'frame': frame_idx,
                    'sign': item['sign'],
                    'landmarks': frame_landmarks
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"Saved training data to {output_file}")
        return output_file
    
    def combine_with_existing_data(self, new_data_file, existing_data_file=None):
        """Combine new gesture data with existing training data"""
        new_df = pd.read_csv(new_data_file)
        
        if existing_data_file and os.path.exists(existing_data_file):
            existing_df = pd.read_csv(existing_data_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        # Save combined data
        combined_file = os.path.join(self.output_dir, "combined_training_data.csv")
        combined_df.to_csv(combined_file, index=False)
        print(f"Combined data saved to {combined_file}")
        return combined_file

def process_gesture_data(csv_file, gesture_name):
    """Main function to process collected gesture data"""
    processor = GestureDataProcessor()
    
    # Process the collected data
    processed_sequences = processor.process_collected_data(csv_file, gesture_name)
    print(f"Processed {len(processed_sequences)} sequences")
    
    # Convert to training format
    training_data = processor.convert_to_training_format(processed_sequences)
    
    # Save training data
    filename = f"{gesture_name}_training_data.csv"
    output_file = processor.save_training_data(training_data, filename)
    
    return output_file

if __name__ == "__main__":
    # Example usage
    csv_file = input("Enter path to collected CSV file: ").strip()
    gesture_name = input("Enter gesture name: ").strip()
    
    if os.path.exists(csv_file):
        output_file = process_gesture_data(csv_file, gesture_name)
        print(f"Training data ready: {output_file}")
    else:
        print("CSV file not found!")
