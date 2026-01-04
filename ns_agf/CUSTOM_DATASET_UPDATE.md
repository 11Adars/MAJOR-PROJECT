# ✅ Custom Dataset Enhancement - Update Summary

## 🎯 Changes Made

The NS-AGF preprocessing pipeline has been updated to handle **your custom dataset structure** without requiring pre-split train/val folders.

---

## 📝 Modified Files

### 1. **`ns_agf/kaggle_scripts/preprocess_wlasl.py`** ✅
**Complete rewrite** to support custom dataset structure:

**Before** (Expected WLASL structure):
```
dataset/
├── train/
│   ├── class1/
│   └── class2/
└── val/
    ├── class1/
    └── class2/
```

**After** (Your custom structure):
```
dataset/
├── sign1/
│   ├── video1.mp4
│   ├── video2.mp4
├── sign2/
│   ├── video1.mp4
│   └── video2.mp4
```

**Key Features Added**:
- ✅ Automatic train/val split (80/20) using `sklearn.train_test_split`
- ✅ Stratified splitting (balanced classes)
- ✅ Support for multiple video formats (`.mp4`, `.avi`, `.mov`)
- ✅ Detailed progress tracking per sign class
- ✅ Error handling for missing/corrupted videos
- ✅ Class name preservation in `sign_labels.npy`

### 2. **`ns_agf/IMPLEMENTATION_GUIDE.md`** ✅
Updated sections:
- Step 1.2: Added note about updating `DATASET_ROOT` path
- Step 1.2: Added `scikit-learn` to dependencies
- Step 1.2: Clarified auto-split behavior (80/20)

### 3. **`ns_agf/kaggle_scripts/README_KAGGLE.md`** ✅
Updated sections:
- Step 2: Changed from WLASL to custom dataset upload instructions
- Dependencies: Added `scikit-learn`
- Added note about auto-splitting

### 4. **`ns_agf/CUSTOM_DATASET_GUIDE.md`** ✅ NEW
**Complete guide for custom dataset users** including:
- Required folder structure
- Step-by-step Kaggle upload
- Customization options
- Example output
- Troubleshooting guide
- Thesis documentation template

---

## 🚀 How to Use (Quick Start)

### 1. Organize Your Videos
```powershell
your-dataset/
├── hello/
│   ├── video1.mp4
│   ├── video2.mp4
├── thank_you/
│   ├── video1.mp4
│   └── video2.mp4
```

### 2. Upload to Kaggle
- Go to kaggle.com/datasets → New Dataset
- Upload your sign folders
- Note the dataset name

### 3. Update Preprocessing Script
Edit `ns_agf/kaggle_scripts/preprocess_wlasl.py` line 44:
```python
DATASET_PATH = "/kaggle/input/your-dataset-name"  # ← Change this!
```

### 4. Run in Kaggle Notebook
```python
# Cell 1: Install deps
!pip install mediapipe scikit-learn

# Cell 2: Preprocess (auto-splits 80/20)
%run preprocess_wlasl.py

# Cell 3: Train
%run train_agcn.py
```

---

## 🔍 What Changed Internally

### Old Approach (WLASL-specific)
```python
def process_dataset(video_dir, split='train'):
    # Expected pre-split folders
    # Required metadata JSON
    # Class labels from JSON
```

### New Approach (Custom Dataset)
```python
def process_custom_dataset(dataset_root):
    # 1. Scan all sign folders
    # 2. Extract landmarks from all videos
    # 3. Auto-split using sklearn (stratified 80/20)
    # 4. Save train + val numpy arrays
```

**Key Algorithm**:
```python
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(
    all_features,      # All extracted landmarks
    all_labels,        # Class indices
    test_size=0.2,     # 20% validation
    train_size=0.8,    # 80% training
    stratify=all_labels,  # Balanced classes
    random_state=42    # Reproducible
)
```

---

## 📊 Output Files

**Before** (2 files per split):
```
train_features.npy
train_labels.npy
val_features.npy
val_labels.npy
```

**After** (5 files total):
```
features_train.npy     # (N_train, 30, 75, 3)
labels_train.npy       # (N_train,)
features_val.npy       # (N_val, 30, 75, 3)
labels_val.npy         # (N_val,)
sign_labels.npy        # [sign_names] ← NEW!
```

The `sign_labels.npy` preserves your original folder names for later inference.

---

## ⚙️ Configuration Options

All configurable in `preprocess_wlasl.py`:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `DATASET_PATH` | `/kaggle/input/your-custom-dataset` | Root folder with sign folders |
| `SEQUENCE_LENGTH` | 30 | Frames per video |
| `TRAIN_RATIO` | 0.8 | Training split percentage |
| `VAL_RATIO` | 0.2 | Validation split percentage |
| `VIDEO_EXTENSIONS` | `['.mp4', '.avi', '.mov']` | Supported formats |

---

## ✅ Verification

Test the preprocessing script locally (without MediaPipe processing):

```powershell
cd "d:\MAJOR-PROJECT - Copy\ns_agf\kaggle_scripts"

# Check imports
python -c "from sklearn.model_selection import train_test_split; print('✅ sklearn imported')"

# Check file exists
ls preprocess_wlasl.py
```

---

## 🎓 For Your Thesis

**Methodological Contribution**:
```
Our preprocessing pipeline automatically handles heterogeneous 
video datasets without requiring manual train/validation splitting. 
The stratified split ensures balanced class representation, 
critical for avoiding bias in sign language recognition where 
class imbalance is common.
```

**Algorithm Pseudocode**:
```
Algorithm 1: Custom Dataset Preprocessing
Input: Dataset root D with sign folders {S₁, S₂, ..., Sₙ}
Output: Training and validation sets with 80/20 split

1: for each sign folder Sᵢ ∈ D do
2:    for each video vⱼ ∈ Sᵢ do
3:       Extract 75-node landmarks → Lⱼ
4:       Normalize to 30 frames → L'ⱼ
5:       Append (L'ⱼ, class_id(Sᵢ)) to dataset
6:    end for
7: end for
8: Apply stratified split (80% train, 20% val)
9: Save numpy arrays
```

---

## 🐛 Troubleshooting

### Issue: "No sign folders found"
**Solution**: Ensure videos are in direct subfolders, not nested

### Issue: "Failed to process some videos"
**Normal**: Some videos may have no detectable landmarks - this is expected

### Issue: "Not enough samples for split"
**Solution**: Each sign needs minimum 2 videos for train/val split

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `CUSTOM_DATASET_GUIDE.md` | Complete guide for custom datasets |
| `IMPLEMENTATION_GUIDE.md` | Full workflow (updated) |
| `README_KAGGLE.md` | Kaggle-specific instructions (updated) |
| `NS_AGF_QUICK_START.md` | Quick reference (no changes needed) |

---

## ✨ Summary

**What you requested**: 
> "I'm not taking dataset from external, I'm using my own dataset which I prepared, but I'm not classified as train or val. I put all videos in particular sign folders, so update the code."

**What was delivered**:
✅ Complete rewrite of preprocessing script
✅ Automatic train/val split (80/20)
✅ Support for any folder-organized dataset
✅ Stratified splitting for balanced classes
✅ Comprehensive documentation
✅ Troubleshooting guide
✅ Thesis-ready templates

**Status**: ✅ Ready to use on Kaggle with your custom dataset

---

**Next Action**: Upload your sign folders to Kaggle and start preprocessing! 🚀

**Need help?** See `CUSTOM_DATASET_GUIDE.md` for detailed instructions.

---

**Version**: 1.0.1  
**Date**: December 2025  
**Updated**: Custom dataset support
