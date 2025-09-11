# Video Processing and Augmentation System

## 🎯 Purpose
This system processes recorded videos to generate augmented training data for gesture recognition. It can:
- Process videos from folders
- Generate 5 augmented versions per video (brightness, contrast, rotation, zoom, noise)
- Extract MediaPipe landmarks from all videos
- Save training data in CSV format
- Train advanced machine learning models

## 📁 Folder Structure Options

### Option 1: Organized by Gesture (Recommended)
```
your_videos/
├── hello/
│   ├── hello_video1.mp4
│   ├── hello_video2.mp4
│   └── hello_video3.mp4
├── goodbye/
│   ├── goodbye_video1.mp4
│   └── goodbye_video2.mp4
└── thumbs_up/
    ├── thumbs_up_video1.mp4
    └── thumbs_up_video2.mp4
```

### Option 2: Flat Structure
```
your_videos/
├── hello_1.mp4
├── hello_2.mp4
├── goodbye_1.mp4
├── goodbye_2.mp4
├── thumbs_up_1.mp4
└── thumbs_up_2.mp4
```

## 🚀 How to Use

### Method 1: Interactive Script (Easiest)
1. Double-click `process_videos.bat` or run:
   ```bash
   python process_videos.py
   ```
2. Follow the prompts:
   - Enter your video folder path
   - Choose number of augmentations (default: 5)
   - Choose whether to extract landmarks (default: yes)

### Method 2: Command Line
```bash
# Process videos with default settings (5 augmentations)
python video_processor.py "path/to/your/videos"

# Custom settings
python video_processor.py "path/to/your/videos" --augmentations 3 --output "processed" --gesture-data "training_data"

# Only generate videos, skip landmark extraction
python video_processor.py "path/to/your/videos" --no-landmarks
```

## 📊 What Gets Generated

### For each original video, you get:
1. **Original video landmarks** → CSV data
2. **5 augmented videos** with variations:
   - Brightness changes (70%-130%)
   - Contrast changes (80%-120%)  
   - Rotation (-10° to +10°)
   - Zoom (90%-110%)
   - Noise (2%-8%)
3. **Augmented video landmarks** → CSV data

### Output Structure:
```
your_videos_processed/
├── hello/
│   ├── hello_video1_aug_1_brightness_contrast.mp4
│   ├── hello_video1_aug_2_rotation_zoom.mp4
│   ├── hello_video1_aug_3_noise_brightness.mp4
│   └── ... (more augmented versions)
└── goodbye/
    └── ... (augmented videos)

your_videos_gesture_data/
├── hello_landmarks.csv
├── goodbye_landmarks.csv
├── thumbs_up_landmarks.csv
└── all_gestures_landmarks.csv  # Combined data
```

## 🤖 Training Models

### Quick Training
```bash
# Train using all CSV files in gesture_data folder
python advanced_train.py

# Train using specific CSV file
python advanced_train.py --csv-file "all_gestures_landmarks.csv"
```

### Advanced Training Options
```bash
# Custom model name and output location
python advanced_train.py --model-name "my_gesture_model" --output-folder "my_models"

# Skip dataset balancing
python advanced_train.py --no-balance

# Skip cross-validation (faster)
python advanced_train.py --no-cv
```

## 📈 Training Features

### Multiple Model Types:
- **RandomForest** (Fast, good for many features)
- **GradientBoosting** (High accuracy)
- **SVM** (Good generalization)
- **Neural Network** (Deep learning approach)

### Advanced Features:
- **Hyperparameter tuning** with RandomizedSearchCV
- **Cross-validation** for robust evaluation
- **Dataset balancing** to handle unequal gesture samples
- **Confusion matrix visualization**
- **Detailed performance metrics**

## 🎯 Tips for Best Results

### Video Recording:
- **Consistent lighting** (avoid shadows)
- **Clear background** (minimal distractions)
- **Full gesture visibility** (hands/face in frame)
- **Natural speed** (not too fast/slow)
- **Multiple angles** per gesture

### Data Quality:
- **Minimum 5-10 videos per gesture**
- **Various lighting conditions**
- **Different distances from camera**
- **Multiple people performing same gesture**

### Training Optimization:
- **Use augmentation** (increases data 6x)
- **Balance your dataset** (equal samples per gesture)
- **Cross-validation** for reliable accuracy estimates
- **Try multiple models** to find best performer

## 🔧 Troubleshooting

### Common Issues:

1. **"No videos found"**
   - Check file extensions (.mp4, .avi, .mov, .mkv, .wmv, .flv)
   - Verify folder path is correct

2. **"MediaPipe detection failed"**
   - Ensure good lighting in videos
   - Check that hands/face are visible
   - Try shorter video clips

3. **"Memory error during training"**
   - Reduce number of augmentations
   - Use smaller video files
   - Try training on individual gesture CSVs

4. **"Low accuracy"**
   - Record more training videos
   - Improve video quality
   - Ensure gestures are distinct
   - Check for mislabeled data

### Performance Optimization:
- **GPU acceleration**: Install `tensorflow-gpu` for faster processing
- **Parallel processing**: Script uses all CPU cores automatically
- **Memory management**: Large datasets are processed in chunks

## 📝 File Formats

### Video Input: 
Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`

### CSV Output:
- **Face landmarks**: 468 points × 3 coordinates = 1,404 features
- **Pose landmarks**: 33 points × 3 coordinates = 99 features  
- **Hand landmarks**: 21 points × 3 coordinates × 2 hands = 126 features
- **Total**: 1,629 features per frame (padded to 1,500 for consistency)

### Model Output:
- `model_name.pkl` - Trained classifier
- `model_name_scaler.pkl` - Feature scaler
- `model_name_mapping.json` - Gesture labels
- `model_name_features.json` - Feature column names
- `model_name_metadata.json` - Training information

## 🎉 Expected Results

With proper data:
- **Training accuracy**: 95-99%
- **Cross-validation**: 90-95%
- **Real-time performance**: 30+ FPS
- **False positive rate**: <5%

The augmentation typically increases your effective dataset size by 6x, leading to much more robust gesture recognition!
