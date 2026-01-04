# Kaggle Training Workflow Guide
## NS-AGF Professional Model Training on Kaggle

---

## ✅ File Name Verification

### **Preprocessing Output** (preprocess_wlasl_IMPROVED.py)
```
output/
├── features.npy          # (N, T, V, C) - Training data
├── labels.npy            # (N,) - Encoded labels
├── label_names.npy       # (num_classes,) - Class names
└── metadata.json         # Dataset info
```

### **Training Script Input** (train_agcn_PROFESSIONAL.py)
```python
features = np.load(data_dir / 'features.npy')       ✅ MATCHES
labels = np.load(data_dir / 'labels.npy')           ✅ MATCHES
label_names = np.load(data_dir / 'label_names.npy') ✅ MATCHES
```

**✅ ALL FILE NAMES NOW MATCH!**

---

## 🚀 Kaggle Workflow (With Preprocessed Data)

### **Step 1: Upload Preprocessed Dataset to Kaggle**

1. **Compress your preprocessed data:**
   ```bash
   cd "d:\MAJOR-PROJECT - Copy\ns_agf"
   # Create a zip file with preprocessing output
   # Make sure it contains: features.npy, labels.npy, label_names.npy
   ```

2. **Upload to Kaggle:**
   - Go to [kaggle.com/datasets](https://www.kaggle.com/datasets)
   - Click "New Dataset"
   - Upload the folder containing:
     - `features.npy`
     - `labels.npy`
     - `label_names.npy`
     - `metadata.json` (optional)
   - Name it: `wlasl-preprocessed-nsagf` (or your choice)
   - Set visibility: Private (or Public if sharing)
   - Click "Create"

---

### **Step 2: Create Kaggle Notebook**

1. **Create new notebook:**
   - Go to [kaggle.com/code](https://www.kaggle.com/code)
   - Click "New Notebook"
   - Select: **GPU Accelerator** (P100 or T4)
   - Enable: **Internet** (for downloading packages if needed)

2. **Add your dataset:**
   - Click "Add data" → "Your datasets"
   - Select: `wlasl-preprocessed-nsagf`
   - It will be mounted at: `/kaggle/input/wlasl-preprocessed-nsagf/`

---

### **Step 3: Upload Training Script and Dependencies**

**Option A: Upload as files**

Upload these files to Kaggle notebook:
- `train_agcn_PROFESSIONAL.py`
- `src/graph/topology.py`
- `src/model/nsagf.py`

**Option B: Copy-paste code cells**

Create cells in order:

**Cell 1: Directory Structure**
```python
# Create src directory structure
!mkdir -p src/graph src/model
```

**Cell 2: topology.py**
```python
%%writefile src/graph/topology.py
# Paste entire content of src/graph/topology.py here
```

**Cell 3: nsagf.py**
```python
%%writefile src/model/nsagf.py
# Paste entire content of src/model/nsagf.py here
```

**Cell 4: __init__.py files**
```python
# Create empty __init__.py files
!touch src/__init__.py src/graph/__init__.py src/model/__init__.py
```

**Cell 5: Training Script**
```python
%%writefile train_agcn_PROFESSIONAL.py
# Paste entire content of train_agcn_PROFESSIONAL.py here
```

---

### **Step 4: Verify Dataset Path**

**Check your dataset location:**
```python
import os
print("Available datasets:")
for root, dirs, files in os.walk('/kaggle/input'):
    for file in files:
        print(os.path.join(root, file))
```

**Expected output:**
```
/kaggle/input/wlasl-preprocessed-nsagf/features.npy
/kaggle/input/wlasl-preprocessed-nsagf/labels.npy
/kaggle/input/wlasl-preprocessed-nsagf/label_names.npy
/kaggle/input/wlasl-preprocessed-nsagf/metadata.json
```

**Update data_dir if needed:**
```python
# If your dataset is at different path, update this:
DATA_DIR = '/kaggle/input/wlasl-preprocessed-nsagf'
# or
DATA_DIR = '/kaggle/input/your-dataset-name'
```

---

### **Step 5: Run Training**

**Method 1: Direct Python execution**
```python
!python train_agcn_PROFESSIONAL.py \
    --data_dir /kaggle/input/wlasl-preprocessed-nsagf \
    --output_dir /kaggle/working \
    --num_epochs 200 \
    --batch_size 24
```

**Method 2: Import and run as module**
```python
import sys
sys.path.insert(0, '/kaggle/working')

# Import training function
from train_agcn_PROFESSIONAL import train_ns_agf_model

# Run training
train_ns_agf_model(
    data_dir='/kaggle/input/wlasl-preprocessed-nsagf',
    output_dir='/kaggle/working',
    num_epochs=200,
    batch_size=24
)
```

---

### **Step 6: Monitor Training**

**Training will show:**
```
======================================================================
NS-AGF PROFESSIONAL TRAINING
======================================================================

📁 Loading preprocessed data...
  Features shape: (1600, 30, 75, 3)  # Example: 1600 samples
  Labels shape: (1600,)
  Number of classes: 20
  Class names: ['hello', 'thank you', ...]

✂️ Splitting data (80% train, 10% val, 10% test)...
  Training samples: 1280
  Validation samples: 160
  Test samples: 160

🌐 Initializing MediaPipe Graph Topology...
  Graph nodes: 75
  Graph edges: 67

🤖 Creating NS-AGF Professional Model...
  Total parameters: 12,266,041
  Trainable parameters: 12,266,041
  Model size: ~46.79 MB (fp32)

======================================================================
STARTING TRAINING
======================================================================

Epoch 1/200
----------------------------------------------------------------------
Training: 100%|██████████| loss: 2.8543, acc: 15.23%
Validation: 100%|██████████| loss: 2.6234, acc: 22.50%

📈 Epoch 1 Summary:
  Train Loss: 2.8543 | Train Acc: 15.23%
  Val Loss: 2.6234 | Val Acc: 22.50%
  Learning Rate: 0.001000
  🏆 New best validation accuracy: 22.50%
💾 Saved checkpoint: checkpoint_epoch_1.pth
🏆 Saved BEST model: ns_agf_best.pth (Val Acc: 22.50%)

...

Epoch 150/200
----------------------------------------------------------------------
Training: 100%|██████████| loss: 0.1234, acc: 96.48%
Validation: 100%|██████████| loss: 0.2876, acc: 93.75%

📈 Epoch 150 Summary:
  Train Loss: 0.1234 | Train Acc: 96.48%
  Val Loss: 0.2876 | Val Acc: 93.75%
  Learning Rate: 0.000234
  🏆 New best validation accuracy: 93.75%
```

---

### **Step 7: Download Trained Model**

**After training completes, download outputs:**

```python
# List all output files
import os
print("\n📂 Output files:")
for file in os.listdir('/kaggle/working'):
    print(f"  {file}")
```

**Expected outputs:**
```
📂 Output files:
  ns_agf_best.pth                    # ⭐ Best model checkpoint
  checkpoint_epoch_10.pth
  checkpoint_epoch_20.pth
  ...
  training_history.png               # Training curves
  confusion_matrix.png               # Confusion matrix
  classification_report.txt          # Detailed metrics
  training_summary.json              # Training config and results
```

**Download the best model:**
- Right-click on `ns_agf_best.pth` in Kaggle output
- Click "Download"
- Save to your local project folder

---

## ⚙️ Kaggle-Specific Optimizations

### **GPU Settings**

**Check available GPU:**
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

**Expected on Kaggle:**
- GPU: Tesla P100-PCIE-16GB (or T4)
- Memory: ~16 GB
- Training time: ~4-5 hours for 200 epochs

### **Batch Size Adjustment**

**If you get CUDA Out of Memory:**
```python
# Reduce batch size
!python train_agcn_PROFESSIONAL.py \
    --data_dir /kaggle/input/wlasl-preprocessed-nsagf \
    --output_dir /kaggle/working \
    --num_epochs 200 \
    --batch_size 16  # Reduced from 24
```

**Batch size guide:**
- P100 (16GB): batch_size=24 ✅
- T4 (16GB): batch_size=20 ✅
- K80 (12GB): batch_size=16 ⚠️
- CPU: batch_size=4 (very slow)

### **Early Stopping**

Training will automatically stop if no improvement for 25 epochs:
```
⛔ Early stopping triggered! No improvement for 25 epochs.
```

This saves GPU time and prevents overfitting.

---

## 📊 Expected Results

### **Training Progress**

| Epoch | Train Acc | Val Acc | Notes |
|-------|-----------|---------|-------|
| 1-10 | 10-40% | 15-35% | Initial learning |
| 10-50 | 40-80% | 35-70% | Rapid improvement |
| 50-100 | 80-95% | 70-88% | Fine-tuning |
| 100-150 | 92-98% | 88-93% | Convergence |
| 150-200 | 95-98% | 90-95% | Best performance |

### **Final Metrics**

**Expected results for 45 videos/class:**
- Training accuracy: **95-98%**
- Validation accuracy: **92-96%**
- Test accuracy: **90-95%**
- Confidence (correct): **75-95%+**

### **Output Files Size**

- `ns_agf_best.pth`: ~190 MB (model + optimizer)
- `training_history.png`: ~500 KB
- `confusion_matrix.png`: ~300 KB
- `classification_report.txt`: ~5 KB
- `training_summary.json`: ~2 KB

---

## 🔍 Troubleshooting

### **Problem 1: File Not Found**
```
FileNotFoundError: [Errno 2] No such file or directory: 'features.npy'
```

**Solution:**
Check dataset path:
```python
import os
print(os.listdir('/kaggle/input'))
print(os.listdir('/kaggle/input/wlasl-preprocessed-nsagf'))
```

Update `--data_dir` to correct path.

---

### **Problem 2: Import Error**
```
ModuleNotFoundError: No module named 'src.graph.topology'
```

**Solution:**
Create `__init__.py` files:
```python
!touch src/__init__.py
!touch src/graph/__init__.py
!touch src/model/__init__.py
```

---

### **Problem 3: CUDA Out of Memory**
```
RuntimeError: CUDA out of memory
```

**Solution:**
Reduce batch size:
```bash
--batch_size 16  # or 12, or 8
```

---

### **Problem 4: Shape Mismatch**
```
RuntimeError: size mismatch, got input (N, T, V, C), expected (N, C, T, V)
```

**Solution:**
Preprocessing output is already in (N, T, V, C) format.
Training script handles conversion automatically.
Should not happen with updated script.

---

## 🎯 Quick Command Reference

**Full training command (Kaggle):**
```bash
!python train_agcn_PROFESSIONAL.py \
    --data_dir /kaggle/input/wlasl-preprocessed-nsagf \
    --output_dir /kaggle/working \
    --num_epochs 200 \
    --batch_size 24
```

**Quick test (10 epochs):**
```bash
!python train_agcn_PROFESSIONAL.py \
    --data_dir /kaggle/input/wlasl-preprocessed-nsagf \
    --output_dir /kaggle/working \
    --num_epochs 10 \
    --batch_size 24
```

**Small batch size (if OOM):**
```bash
!python train_agcn_PROFESSIONAL.py \
    --data_dir /kaggle/input/wlasl-preprocessed-nsagf \
    --output_dir /kaggle/working \
    --num_epochs 200 \
    --batch_size 16
```

---

## ✅ Checklist

**Before starting training:**
- [ ] Preprocessed data uploaded to Kaggle as dataset
- [ ] Dataset contains: features.npy, labels.npy, label_names.npy
- [ ] Training script uploaded or pasted to notebook
- [ ] src/graph/topology.py uploaded or pasted
- [ ] src/model/nsagf.py uploaded or pasted
- [ ] __init__.py files created in src/, src/graph/, src/model/
- [ ] GPU accelerator enabled in notebook
- [ ] Dataset path verified

**During training:**
- [ ] Monitor training progress
- [ ] Check validation accuracy improving
- [ ] Watch for CUDA OOM errors
- [ ] Verify checkpoints being saved

**After training:**
- [ ] Download ns_agf_best.pth
- [ ] Download training_history.png
- [ ] Download confusion_matrix.png
- [ ] Review classification_report.txt
- [ ] Check training_summary.json

---

## 🏆 Success Criteria

✅ Training completes without errors  
✅ Validation accuracy reaches 92%+ by epoch 150  
✅ Best model saved with 90%+ test accuracy  
✅ Confusion matrix shows good per-class performance  
✅ Training curves show smooth convergence  

---

**Last Updated:** December 2024  
**Status:** ✅ File names verified and matched!  
**Ready for:** Kaggle training with preprocessed data

---

*Your preprocessed data is ready - just upload and train! 🚀*
