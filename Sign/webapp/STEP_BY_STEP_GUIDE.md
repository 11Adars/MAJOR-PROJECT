# 📋 Complete Step-by-Step Guide: Adding New Gestures

## 🚀 Quick Start

```bash
cd D:\MAJOR-PROJECT\Sign\webapp
python custom_gesture_workflow.py
```

---

## 📖 **Method 1: Live Webcam Recording (Recommended)**

### **Step 1: Launch the System**
```bash
python custom_gesture_workflow.py
```
Select **Option 1**: Add new gesture (webcam)

### **Step 2: Configure Your Gesture**
- **Gesture Name**: Enter a descriptive name (e.g., "hello", "welcome", "goodbye")
- **Number of Sequences**: 30-50 (more = better accuracy)
- **Frames per Sequence**: 20-50 (duration of each recording)

### **Step 3: Setup Your Recording Environment**
- ✅ **Good Lighting**: Natural daylight or bright room lighting
- ✅ **Clear Background**: Solid color wall (white/light colored preferred)
- ✅ **Camera Position**: Chest-up view, hands clearly visible
- ✅ **Stable Position**: Sit or stand in consistent position

### **Step 4: Recording Process**
1. **Position yourself** in front of camera
2. **Press SPACE** to start each recording
3. **Perform gesture clearly** for 2-3 seconds
4. **Stay consistent** across all sequences
5. **Repeat** until all sequences are collected

### **Step 5: Automatic Processing**
The system automatically:
- ✅ Extracts MediaPipe landmarks
- ✅ Processes data for training format
- ✅ Adds gesture to dictionary
- ✅ Updates model configuration

---

## 🎥 **Method 2: From Existing Video Files**

### **Step 1: Launch Video Processor**
```bash
python custom_gesture_workflow.py
```
Select **Option 2**: Add gesture from video file

### **Step 2: Prepare Your Video**
- **Format**: MP4, AVI, MOV (common video formats)
- **Quality**: Clear gesture visibility
- **Duration**: Can be any length
- **Content**: Should contain multiple instances of the gesture

### **Step 3: Configure Processing**
- **Gesture Name**: Enter descriptive name
- **Video Path**: Full path to your video file
- **Start Time**: When gesture segments begin (seconds)
- **End Time**: When gesture segments end (optional)
- **Segment Duration**: Length of each gesture sequence (3-5 seconds recommended)

### **Step 4: Video Processing**
The system will:
- Extract gesture sequences automatically
- Process each segment for landmarks
- Create training data
- Update gesture dictionary

### **Example Video Processing:**
```python
# For a 2-minute video with gestures from 10s to 90s
Video Path: D:\videos\my_gesture.mp4
Start Time: 10
End Time: 90
Segment Duration: 3
```

---

## 🛠️ **Method 3: Manual Component Usage**

### **Individual Gesture Collection**
```bash
python gesture_collector.py
```

### **Gesture Dictionary Management**
```bash
python gesture_manager.py
```

### **Data Processing**
```bash
python data_processor.py
```

---

## 📁 **File Structure After Adding Gestures**

```
Sign/webapp/
├── custom_gestures/
│   ├── welcome_20250901_222442.csv          # Raw collected data
│   ├── my_gesture_from_video_20250901.csv   # Video extracted data
│   └── ...
├── processed_data/
│   ├── welcome_training_data.csv            # Processed training data
│   ├── my_gesture_training_data.csv
│   └── combined_training_data.csv           # All custom gestures
├── backup/
│   └── dict_sign_original.csv               # Original dictionary backup
└── module/islr/
    └── dict_sign.csv                        # Updated gesture dictionary
```

---

## 🎯 **Best Practices for Data Collection**

### **📹 Recording Tips:**
1. **Consistency**: Perform gesture the same way each time
2. **Variation**: Include slight natural variations
3. **Speed**: Normal signing speed (not too slow/fast)
4. **Visibility**: Ensure hands/face are clearly visible
5. **Background**: Use consistent, uncluttered background

### **📊 Data Quality:**
- **Minimum**: 20 sequences per gesture
- **Recommended**: 30-50 sequences
- **Professional**: 100+ sequences
- **Frame Rate**: 20-50 frames per sequence

### **🎨 Environment Setup:**
- **Lighting**: Even, bright lighting on face and hands
- **Camera**: HD resolution (720p minimum)
- **Distance**: 3-6 feet from camera
- **Angle**: Slightly above eye level
- **Clothing**: Contrasting colors (avoid white on white)

---

## 🗑️ **Removing Unwanted Gestures**

### **Individual Removal:**
```bash
python gesture_manager.py
# Select option 3: Remove gesture
```

### **Batch Removal:**
```bash
python custom_gesture_workflow.py
# Select option 3: Remove gestures
# Enter comma-separated list: "gesture1, gesture2, gesture3"
```

### **Gestures You Might Want to Remove:**
Common gestures you might not need:
- `jeans`, `vacuum`, `zipper` (clothing/household items)
- `cowboy`, `clown`, `fireman` (specific professions)
- Very similar gestures that cause confusion

---

## 🔄 **After Adding Gestures: Model Retraining**

### **Step 1: Prepare Training Data**
Your new gesture data is automatically formatted for training and saved in `processed_data/`

### **Step 2: Update Training Configuration**
The model configuration is automatically updated with the new number of classes.

### **Step 3: Retrain the Model**
Use your existing training notebooks:
1. Open `Sign/code/model_training.ipynb`
2. Update the data loading section to include your new gestures
3. Run the training process

### **Step 4: Deploy Updated Model**
Replace the existing model files with your newly trained model.

---

## 🧪 **Testing Your New Gestures**

### **Test Individual Components:**
```bash
python test_custom_gestures.py
```

### **Test New Gesture Recognition:**
After retraining, test your gestures in the main application to ensure they're recognized correctly.

---

## 🚨 **Troubleshooting**

### **Camera Issues:**
- Check camera permissions
- Close other applications using camera
- Try different camera index (0, 1, 2)

### **Video Processing Issues:**
- Ensure video file path is correct
- Check video format compatibility
- Verify video contains clear gesture visibility

### **Data Quality Issues:**
- Collect more sequences if accuracy is low
- Ensure consistent gesture performance
- Check lighting and background conditions

### **Model Issues:**
- Verify NUM_CLASSES matches dictionary length
- Ensure data format compatibility
- Check for corrupted training data

---

## 💡 **Advanced Tips**

### **For Better Accuracy:**
1. **Collect in different conditions**: Various lighting, backgrounds
2. **Multiple performers**: Different people performing same gesture
3. **Temporal variations**: Different speeds and timing
4. **Spatial variations**: Different positions and angles

### **For Professional Results:**
1. **Data validation**: Review collected sequences before training
2. **Cross-validation**: Test with unseen data
3. **Confusion matrix**: Analyze gesture recognition errors
4. **Iterative improvement**: Collect more data for problematic gestures

---

## 📞 **Support and Next Steps**

After adding your gestures:
1. ✅ **Verify data quality** in CSV files
2. ✅ **Test gesture dictionary** updates
3. ✅ **Retrain the model** with new data
4. ✅ **Deploy and test** in your application
5. ✅ **Collect feedback** and improve

Your custom gesture system is now ready for production use!
