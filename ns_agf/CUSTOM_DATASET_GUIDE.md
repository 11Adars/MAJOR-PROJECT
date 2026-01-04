# 🎯 Custom Dataset Setup Guide for NS-AGF

## ✅ What Changed

The preprocessing script has been updated to handle **your custom dataset structure** where:
- Videos are organized in folders by sign name
- **No pre-split train/val folders needed**
- The script automatically splits your data (80% train / 20% validation)

---

## 📂 Required Dataset Structure

Organize your videos like this:

```
your-custom-dataset/
├── sign1/
│   ├── video1.mp4
│   ├── video2.mp4
│   ├── video3.mp4
│   └── ... (more videos of sign1)
├── sign2/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── ... (more videos of sign2)
├── sign3/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── ... (more videos of sign3)
└── ... (more sign folders)
```

### Rules:
- ✅ Each sign must have its own folder
- ✅ Folder name = sign class name
- ✅ Put all videos for that sign inside its folder
- ✅ Supported formats: `.mp4`, `.avi`, `.mov` (case insensitive)
- ✅ Minimum 2 videos per sign (for train/val split)
- ❌ No nested folders
- ❌ No train/val pre-splitting needed

---

## 🚀 How to Use in Kaggle

### Step 1: Upload Your Dataset to Kaggle

1. Go to https://www.kaggle.com/datasets
2. Click "New Dataset"
3. Upload your sign folders (you can zip them first)
4. Make it private or public
5. Note the dataset path (e.g., `/kaggle/input/my-sign-dataset`)

### Step 2: Update Preprocessing Script

Open `preprocess_wlasl.py` and change line 44:

```python
# Before:
DATASET_PATH = "/kaggle/input/your-custom-dataset"  # ← UPDATE THIS!

# After (example):
DATASET_PATH = "/kaggle/input/my-sign-dataset"  # Your actual dataset name
```

### Step 3: Run Preprocessing

In Kaggle notebook:

```python
# Install dependencies
!pip install mediapipe scikit-learn

# Run preprocessing
%run preprocess_wlasl.py
```

**Output files** (saved to `/kaggle/working/processed_data/`):
- `features_train.npy` - Training features (N_train, 30, 75, 3)
- `labels_train.npy` - Training labels (N_train,)
- `features_val.npy` - Validation features (N_val, 30, 75, 3)
- `labels_val.npy` - Validation labels (N_val,)
- `sign_labels.npy` - Class names mapping

### Step 4: Train the Model

```python
%run train_agcn.py
```

The training script will automatically:
- Load the processed data
- Determine number of classes from your dataset
- Train for 50 epochs
- Save checkpoints and best model

---

## 📊 What the Script Does

### 1. **Video Processing**
- Opens each video file
- Extracts MediaPipe landmarks (75 nodes) from every frame
- Handles variable-length videos:
  - **Too short** (< 30 frames): Pads with zeros
  - **Too long** (> 30 frames): Samples uniformly to 30 frames

### 2. **Automatic Train/Val Split**
- Uses `sklearn.train_test_split`
- **Stratified split**: Ensures each class appears in both train and val
- Default ratio: 80% train, 20% validation
- Random seed: 42 (reproducible)

### 3. **Class Mapping**
- Sign folder names become class labels
- Automatically sorted alphabetically
- Saved in `sign_labels.npy` for later use

---

## 🔧 Customization Options

### Change Split Ratio

In `preprocess_wlasl.py`, modify lines 51-52:

```python
# Default:
TRAIN_RATIO = 0.8
VAL_RATIO = 0.2

# For more validation data:
TRAIN_RATIO = 0.7
VAL_RATIO = 0.3
```

### Change Sequence Length

In `preprocess_wlasl.py`, modify line 48:

```python
# Default: 30 frames per video
SEQUENCE_LENGTH = 30

# For longer sequences:
SEQUENCE_LENGTH = 60
```

### Add More Video Formats

In `preprocess_wlasl.py`, modify line 55:

```python
# Default:
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.MP4', '.AVI', '.MOV']

# Add more:
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.MP4', '.AVI', '.MOV']
```

---

## 📈 Example Output

When you run `preprocess_wlasl.py`, you'll see:

```
============================================================
🎯 Processing Custom Dataset
============================================================
Dataset Root: /kaggle/input/my-sign-dataset
Found 10 sign classes
Train/Val Split: 80% / 20%

Sign Classes Preview: ['hello', 'thank_you', 'please', 'yes', 'no']
... and 5 more

Processing signs: 100%|██████████| 10/10 [05:23<00:00, 32.35s/it]

📁 hello: Processing 25 videos
   ✅ Success: 25 | ❌ Failed: 0

📁 thank_you: Processing 30 videos
   ✅ Success: 28 | ❌ Failed: 2

... (more signs)

============================================================
📊 TOTAL Dataset Statistics
============================================================
Total samples: 245
Feature shape: (245, 30, 75, 3)
Classes: 10

🔀 Splitting dataset...

============================================================
✅ TRAIN Set
============================================================
Samples: 196
Shape: (196, 30, 75, 3)

============================================================
✅ VALIDATION Set
============================================================
Samples: 49
Shape: (49, 30, 75, 3)

============================================================
📈 Class Distribution (Training)
============================================================
  hello: 20 samples
  thank_you: 22 samples
  please: 18 samples
  yes: 19 samples
  no: 21 samples
  ... (5 more classes)

============================================================
💾 Saving processed data...
============================================================
✅ Saved to: /kaggle/working/processed_data/
  - features_train.npy (34.56 MB)
  - labels_train.npy
  - features_val.npy (8.64 MB)
  - labels_val.npy
  - sign_labels.npy

============================================================
✨ Preprocessing Complete!
============================================================

📦 Dataset Summary:
  Total Classes: 10
  Training Samples: 196
  Validation Samples: 49
  Feature Shape: (196, 30, 75, 3)

🎯 Next Step: Run train_agcn.py to train the model
```

---

## ⚠️ Common Issues

### Issue 1: No videos found in folders
**Error**: `Warning: No videos found in sign_name, skipping...`

**Solution**: 
- Check file extensions (must be `.mp4`, `.avi`, or `.mov`)
- Ensure videos are directly inside sign folders (no nested folders)

### Issue 2: Dataset path not found
**Error**: `FileNotFoundError: Dataset not found at /kaggle/input/...`

**Solution**: 
- Verify dataset name in Kaggle
- Update `DATASET_PATH` in script to match exactly
- Check you added the dataset to your notebook

### Issue 3: Failed to process videos
**Error**: `❌ Failed: 5` (some videos skipped)

**Possible reasons**:
- Corrupted video files
- No landmarks detected (person not in frame)
- Very low quality videos

**Solution**: This is normal - some videos may fail. As long as most succeed, you're fine.

### Issue 4: Not enough samples for train/val split
**Error**: `ValueError: The least populated class has only 1 member`

**Solution**: Ensure each sign has at least 2 videos (minimum for splitting)

---

## 🎓 For Thesis Documentation

When documenting your custom dataset:

```latex
\subsection{Dataset Preparation}

We prepared a custom sign language dataset consisting of \textit{N} classes with \textit{M} total video samples. Videos were organized by sign class and automatically split into training (80\%) and validation (20\%) sets using stratified sampling to ensure balanced class representation.

\textbf{Preprocessing Pipeline:}
\begin{enumerate}
    \item MediaPipe Holistic landmark extraction (75 nodes: 33 pose + 21 left hand + 21 right hand)
    \item Temporal normalization to 30 frames per video via uniform sampling or zero-padding
    \item Train-validation split with stratification (80/20 ratio)
\end{enumerate}

\textbf{Dataset Statistics:}
\begin{itemize}
    \item Total classes: [Your number]
    \item Training samples: [Your number]
    \item Validation samples: [Your number]
    \item Feature dimensionality: $(N, 30, 75, 3)$ where $N$ is number of samples
\end{itemize}
```

---

## ✅ Success Checklist

Before running training, verify:

- [ ] Dataset uploaded to Kaggle with correct structure
- [ ] `DATASET_PATH` updated in `preprocess_wlasl.py`
- [ ] Dependencies installed (`mediapipe`, `scikit-learn`)
- [ ] Preprocessing completed successfully
- [ ] All output files created in `/kaggle/working/processed_data/`
- [ ] No critical errors in preprocessing log
- [ ] Number of classes matches your expectation

---

## 🎯 Next Steps

1. ✅ Preprocessing complete
2. ⏩ Run `train_agcn.py` to train the model
3. ⏩ Monitor training for 50 epochs (6-8 hours)
4. ⏩ Download trained model (`ns_agcn_bankassist.pth`)
5. ⏩ Test inference locally

---

**Questions?** See `README_KAGGLE.md` for full Kaggle workflow or `IMPLEMENTATION_GUIDE.md` for complete setup instructions.

**Version**: 1.0.1  
**Updated**: For custom dataset support  
**Status**: ✅ Ready to use
