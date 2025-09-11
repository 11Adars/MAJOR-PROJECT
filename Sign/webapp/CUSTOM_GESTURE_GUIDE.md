# Custom Gesture Addition Guide

This guide helps you add your own custom gestures to the existing ASL recognition model.

## Quick Start

### 1. Setup (First Time Only)
```bash
cd D:\MAJOR-PROJECT\Sign\webapp
python setup_custom_gestures.py
```

### 2. Add New Gesture
```bash
python custom_gesture_workflow.py
```
Select option 1 and follow the prompts.

## Detailed Steps

### Step 1: Collect Gesture Data
1. Run the gesture collector
2. Position yourself in front of the camera
3. Press SPACE to start recording each sequence
4. Perform your gesture clearly during recording
5. Repeat for the specified number of sequences

**Tips for good data collection:**
- Use good lighting
- Keep consistent hand positions
- Perform the gesture at normal speed
- Include slight variations in each sequence
- Make sure the gesture is clearly visible

### Step 2: Process and Add to Model
The workflow automatically:
- Processes your collected landmarks
- Adds the gesture to the dictionary
- Updates the model configuration
- Prepares data for training

### Step 3: Remove Unwanted Gestures
```bash
python custom_gesture_workflow.py
```
Select option 2 to remove gestures you don't need.

## File Structure

```
Sign/webapp/
├── custom_gestures/          # Collected raw data
├── processed_data/           # Processed training data
├── backup/                   # Backup of original files
├── gesture_collector.py      # Data collection script
├── gesture_manager.py        # Gesture dictionary management
├── data_processor.py         # Data processing utilities
├── custom_gesture_workflow.py # Main workflow script
└── setup_custom_gestures.py  # Setup script
```

## Individual Components

### Gesture Collector (`gesture_collector.py`)
Collects gesture data using your webcam:
```python
from gesture_collector import GestureCollector

collector = GestureCollector("my_gesture")
collector.collect_gesture_data(num_sequences=30, frames_per_sequence=50)
```

### Gesture Manager (`gesture_manager.py`)
Manages the gesture dictionary:
```python
from gesture_manager import GestureManager

manager = GestureManager()
manager.add_new_gesture("my_gesture")
manager.remove_gesture("unwanted_gesture")
manager.list_gestures()
```

### Data Processor (`data_processor.py`)
Processes collected data for training:
```python
from data_processor import process_gesture_data

output_file = process_gesture_data("path/to/collected.csv", "gesture_name")
```

## Training with New Data

After adding your gestures, you'll need to retrain the model:

1. **Combine all training data** (existing + new)
2. **Update model configuration** (NUM_CLASSES)
3. **Retrain the model** using your training notebooks
4. **Deploy the updated model**

## Best Practices

### Data Collection
- Collect 30-50 sequences per gesture
- Each sequence should be 30-50 frames
- Ensure good lighting and clear visibility
- Include natural variations in gesture performance
- Test with different backgrounds if possible

### Gesture Design
- Make gestures distinct from existing ones
- Avoid overly similar gestures
- Consider the target audience and use case
- Keep gestures simple and repeatable

### Model Management
- Always backup original files before modifications
- Test new gestures thoroughly before deployment
- Monitor model performance after adding new gestures
- Consider removing unused gestures to improve performance

## Troubleshooting

### Camera Issues
- Check camera permissions
- Ensure no other applications are using the camera
- Try different camera indices (0, 1, 2, etc.)

### Data Collection Issues
- Ensure good lighting
- Check MediaPipe landmark detection
- Verify gesture is being performed clearly

### Model Issues
- Check NUM_CLASSES matches dictionary length
- Verify data format compatibility
- Ensure all dependencies are installed

## Advanced Usage

### Batch Operations
```python
# Add multiple gestures
manager.batch_add_gestures(["gesture1", "gesture2", "gesture3"])

# Remove multiple gestures
manager.batch_remove_gestures(["old1", "old2", "old3"])
```

### Custom Data Processing
```python
processor = GestureDataProcessor()
processed = processor.process_collected_data("data.csv", "gesture")
training_data = processor.convert_to_training_format(processed)
```

## Integration with Existing Model

Your custom gestures will be integrated with the existing 250 ASL signs. The model will need to be retrained to recognize the new gestures alongside the existing ones.

**Note:** Adding new gestures requires retraining the entire model, which may take significant time depending on your hardware.
