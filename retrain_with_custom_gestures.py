#!/usr/bin/env python3
"""
Custom Gesture Model Retraining Script
Converts custom gesture data to TFRecord format and retrains the model
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import json
import os
from pathlib import Path
import shutil
from tqdm import tqdm

class CustomGestureRetrainer:
    def __init__(self):
        self.base_dir = Path("d:/MAJOR-PROJECT")
        self.sign_dir = self.base_dir / "Sign"
        self.gesture_data_dir = Path("gesture_data")
        self.output_dir = Path("tfrecord_data")
        self.model_dir = self.base_dir / "webapp" / "app" / "module" / "islr"
        
        # Constants
        self.ROWS_PER_FRAME = 543
        self.SEQUENCE_LENGTH = 30
        
    def load_gesture_dictionary(self):
        """Load the gesture dictionary"""
        dict_path = self.model_dir / "dict_sign.csv"
        if dict_path.exists():
            df = pd.read_csv(dict_path)
            print(f"✅ Loaded dictionary with {len(df)} gestures")
            return {row['sign']: row['sign_ord'] for _, row in df.iterrows()}
        else:
            print("❌ Dictionary not found")
            return {}
    
    def load_custom_gesture_data(self, gesture_name):
        """Load landmark data for a custom gesture"""
        data_file = self.gesture_data_dir / f"{gesture_name}_landmarks.csv"
        
        if not data_file.exists():
            print(f"❌ Data file not found: {data_file}")
            return None
            
        try:
            df = pd.read_csv(data_file)
            print(f"✅ Loaded {gesture_name}: {len(df)} frames")
            
            # Group by sequence and extract landmarks
            sequences = []
            for seq_id in df['sequence'].unique():
                seq_data = df[df['sequence'] == seq_id].copy()
                seq_data = seq_data.sort_values('frame')
                
                # Extract landmark coordinates (x, y, z)
                landmarks = []
                for _, row in seq_data.iterrows():
                    frame_landmarks = []
                    # Extract coordinates from landmark columns
                    for i in range(0, self.ROWS_PER_FRAME):
                        try:
                            x = row.get(f'landmark_{i}_x', 0.0)
                            y = row.get(f'landmark_{i}_y', 0.0) 
                            z = row.get(f'landmark_{i}_z', 0.0)
                            frame_landmarks.extend([x, y, z])
                        except:
                            # If landmark columns not found, try alternative format
                            landmark_cols = [col for col in df.columns if 'landmark' in col.lower()]
                            if landmark_cols:
                                # Use available landmark data
                                x = row.get(landmark_cols[min(i*3, len(landmark_cols)-1)], 0.0)
                                y = row.get(landmark_cols[min(i*3+1, len(landmark_cols)-1)], 0.0)
                                z = row.get(landmark_cols[min(i*3+2, len(landmark_cols)-1)], 0.0)
                                frame_landmarks.extend([x, y, z])
                            else:
                                frame_landmarks.extend([0.0, 0.0, 0.0])
                    
                    landmarks.append(frame_landmarks)
                
                if len(landmarks) > 0:
                    # Convert to numpy array and ensure correct shape
                    seq_array = np.array(landmarks, dtype=np.float32)
                    if seq_array.shape[1] != self.ROWS_PER_FRAME * 3:
                        # Reshape or pad if necessary
                        target_size = self.ROWS_PER_FRAME * 3
                        if seq_array.shape[1] < target_size:
                            # Pad with zeros
                            padding = np.zeros((seq_array.shape[0], target_size - seq_array.shape[1]))
                            seq_array = np.concatenate([seq_array, padding], axis=1)
                        else:
                            # Truncate
                            seq_array = seq_array[:, :target_size]
                    
                    # Reshape to (frames, landmarks, 3)
                    seq_array = seq_array.reshape(-1, self.ROWS_PER_FRAME, 3)
                    sequences.append(seq_array)
            
            return sequences
            
        except Exception as e:
            print(f"❌ Error loading {gesture_name}: {e}")
            return None
    
    def create_tfrecord_from_custom_data(self, gesture_name, gesture_id, sequences):
        """Convert custom gesture sequences to TFRecord format"""
        self.output_dir.mkdir(exist_ok=True)
        tfrecord_path = self.output_dir / f"custom_{gesture_name}.tfrecords"
        
        print(f"📝 Creating TFRecord for {gesture_name} (ID: {gesture_id})")
        
        options = tf.io.TFRecordOptions(compression_type='GZIP', compression_level=9)
        
        with tf.io.TFRecordWriter(str(tfrecord_path), options=options) as writer:
            for seq_idx, sequence in enumerate(tqdm(sequences, desc=f"Processing {gesture_name}")):
                # Ensure sequence has the right shape
                if len(sequence.shape) == 3:
                    coordinates_encoded = sequence.tobytes()
                    
                    # Create TFRecord example
                    record = tf.train.Example(features=tf.train.Features(feature={
                        'coordinates': tf.train.Feature(bytes_list=tf.train.BytesList(value=[coordinates_encoded])),
                        'participant_id': tf.train.Feature(int64_list=tf.train.Int64List(value=[999])),  # Custom participant ID
                        'sequence_id': tf.train.Feature(int64_list=tf.train.Int64List(value=[seq_idx])),
                        'sign': tf.train.Feature(int64_list=tf.train.Int64List(value=[gesture_id]))
                    }))
                    
                    writer.write(record.SerializeToString())
        
        print(f"✅ Created TFRecord: {tfrecord_path}")
        return tfrecord_path
    
    def prepare_training_data(self):
        """Prepare all custom gesture data for training"""
        print("🔄 Preparing custom gesture training data...")
        
        # Load gesture dictionary
        gesture_dict = self.load_gesture_dictionary()
        
        # Find custom gestures (IDs >= 250)
        custom_gestures = {name: id for name, id in gesture_dict.items() if id >= 250}
        
        if not custom_gestures:
            print("❌ No custom gestures found in dictionary")
            return False
        
        print(f"📋 Found custom gestures: {custom_gestures}")
        
        # Process each custom gesture
        tfrecord_files = []
        for gesture_name, gesture_id in custom_gestures.items():
            sequences = self.load_custom_gesture_data(gesture_name)
            if sequences and len(sequences) > 0:
                tfrecord_path = self.create_tfrecord_from_custom_data(gesture_name, gesture_id, sequences)
                tfrecord_files.append(tfrecord_path)
            else:
                print(f"⚠️  No valid sequences found for {gesture_name}")
        
        if tfrecord_files:
            print(f"✅ Created {len(tfrecord_files)} TFRecord files")
            return True
        else:
            print("❌ No TFRecord files created")
            return False
    
    def update_training_notebook(self):
        """Update the training notebook configuration"""
        notebook_path = self.sign_dir / "code" / "model_training.ipynb"
        
        print(f"📝 Updating training notebook: {notebook_path}")
        
        if not notebook_path.exists():
            print("❌ Training notebook not found")
            return False
        
        try:
            # Read the notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_content = f.read()
            
            # Update NUM_CLASSES if needed
            if 'NUM_CLASSES = 250' in notebook_content:
                notebook_content = notebook_content.replace('NUM_CLASSES = 250', 'NUM_CLASSES = 253')
                print("✅ Updated NUM_CLASSES to 253")
            elif 'NUM_CLASSES = 251' in notebook_content:
                notebook_content = notebook_content.replace('NUM_CLASSES = 251', 'NUM_CLASSES = 253')
                print("✅ Updated NUM_CLASSES to 253")
            
            # Write back
            with open(notebook_path, 'w', encoding='utf-8') as f:
                f.write(notebook_content)
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating notebook: {e}")
            return False
    
    def create_training_script(self):
        """Create a simplified training script"""
        script_content = '''
import tensorflow as tf
import numpy as np
import pandas as pd
from pathlib import Path

# Load custom TFRecord data
def load_tfrecord_data(tfrecord_files):
    """Load data from TFRecord files"""
    dataset = tf.data.TFRecordDataset(tfrecord_files, compression_type='GZIP')
    
    def parse_tfrecord(example):
        feature_description = {
            'coordinates': tf.io.FixedLenFeature([], tf.string),
            'participant_id': tf.io.FixedLenFeature([], tf.int64),
            'sequence_id': tf.io.FixedLenFeature([], tf.int64),
            'sign': tf.io.FixedLenFeature([], tf.int64),
        }
        
        parsed = tf.io.parse_single_example(example, feature_description)
        
        # Decode coordinates
        coordinates = tf.io.decode_raw(parsed['coordinates'], tf.float32)
        coordinates = tf.reshape(coordinates, [-1, 543, 3])
        
        return coordinates, parsed['sign']
    
    return dataset.map(parse_tfrecord)

# Simple fine-tuning approach
def create_fine_tuning_model(num_classes=253):
    """Create a model for fine-tuning with custom gestures"""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(None, 543, 3)),
        tf.keras.layers.Conv1D(128, 3, activation='relu'),
        tf.keras.layers.GlobalMaxPooling1D(),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

# Training function
def train_custom_gestures():
    print("🚀 Starting custom gesture training...")
    
    # Load custom TFRecord files
    tfrecord_files = list(Path("tfrecord_data").glob("*.tfrecords"))
    
    if not tfrecord_files:
        print("❌ No TFRecord files found")
        return
    
    print(f"📁 Found {len(tfrecord_files)} TFRecord files")
    
    # Load dataset
    dataset = load_tfrecord_data([str(f) for f in tfrecord_files])
    dataset = dataset.batch(16).prefetch(tf.data.AUTOTUNE)
    
    # Create model
    model = create_fine_tuning_model(253)
    
    # Train model
    print("🔄 Training model...")
    model.fit(dataset, epochs=10, verbose=1)
    
    # Convert to TFLite
    print("🔄 Converting to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    
    # Save model
    model_path = Path("webapp/app/module/islr/model.tflite")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(model_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"✅ Model saved: {model_path}")

if __name__ == "__main__":
    train_custom_gestures()
'''
        
        script_path = Path("custom_gesture_training.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print(f"✅ Created training script: {script_path}")
        return script_path

def main():
    """Main execution function"""
    print("🎯 Custom Gesture Model Retraining")
    print("=" * 50)
    
    retrainer = CustomGestureRetrainer()
    
    # Step 1: Prepare training data
    print("\n📋 Step 1: Preparing training data...")
    if retrainer.prepare_training_data():
        print("✅ Training data prepared successfully")
    else:
        print("❌ Failed to prepare training data")
        return
    
    # Step 2: Update training notebook
    print("\n📋 Step 2: Updating training configuration...")
    if retrainer.update_training_notebook():
        print("✅ Training notebook updated")
    else:
        print("⚠️  Could not update training notebook")
    
    # Step 3: Create training script
    print("\n📋 Step 3: Creating training script...")
    script_path = retrainer.create_training_script()
    
    print("\n🎯 NEXT STEPS:")
    print("=" * 30)
    print("1. Run the training script:")
    print(f"   python {script_path}")
    print("\n2. Or use the Jupyter notebook:")
    print("   Open Sign/code/model_training.ipynb")
    print("   Update data paths to include your TFRecord files")
    print("   Run all cells")
    print("\n3. Test your custom gestures after training!")
    
    # Check if gesture data exists
    gesture_data_dir = Path("gesture_data")
    if gesture_data_dir.exists():
        csv_files = list(gesture_data_dir.glob("*_landmarks.csv"))
        print(f"\n📊 Found {len(csv_files)} gesture data files:")
        for file in csv_files:
            print(f"   - {file.name}")
    else:
        print("\n⚠️  Gesture data directory not found")
        print("   Make sure you've recorded your custom gestures first")

if __name__ == "__main__":
    main()
