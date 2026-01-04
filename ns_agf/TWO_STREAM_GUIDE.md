# Task 1.2: Two-Stream Architecture - Implementation Complete ✅

## Overview

Successfully implemented **Two-Stream NS-AGF** architecture with Joint + Bone streams for improved sign language recognition accuracy.

## What Was Implemented

### 1. **TwoStreamNSAGF Model** ([nsagf.py](../src/model/nsagf.py))

```python
class TwoStreamNSAGF(nn.Module):
    """
    Dual-stream architecture:
    - Joint Stream: Learns from absolute joint positions
    - Bone Stream: Learns from relative bone vectors  
    - Late Fusion: Combines both before classification
    """
```

**Architecture:**
```
Input (N, C, T, V) →
├─ Joint Stream: 10 ST-GCN blocks → Features (N, 512)
└─ Bone Stream: Bone computation → 10 ST-GCN blocks → Features (N, 512)
Fusion: Concat [Joint, Bone] → (N, 1024) → Classifier → (N, num_classes)
```

**Key Features:**
- ✅ Separate 10-block ST-GCN for each stream
- ✅ Bone feature computation: `bone = child_joint - parent_joint`
- ✅ Late fusion: Concatenate features before classification
- ✅ ~8-10M parameters (2x single-stream)
- ✅ Expected +5-8% accuracy boost

### 2. **Graph Topology Updates** ([topology.py](../src/graph/topology.py))

Added `get_bone_connections()` method:

```python
def get_bone_connections(self) -> List[List[int]]:
    """Return bone connections for two-stream architecture."""
    return [[i, j] for i, j in self.neighbor_links]
```

**Bone Pairs:**
- 67 bone connections from MediaPipe topology
- Each edge represents a bone (parent → child relationship)
- Used to compute bone features: `bone_vector = child - parent`

### 3. **Updated create_model Factory** ([nsagf.py](../src/model/nsagf.py))

```python
def create_model(
    num_classes: int,
    graph,
    dropout: float = 0.0,
    pretrained_path: Optional[str] = None,
    two_stream: bool = False  # ← New parameter
) -> nn.Module:
    """
    Factory to create single-stream or two-stream model.
    
    Example:
        # Single-stream (existing)
        model = create_model(20, graph, dropout=0.5)
        
        # Two-stream (new)
        model = create_model(20, graph, dropout=0.5, two_stream=True)
    """
```

### 4. **Training Script** ([train_two_stream.py](train_two_stream.py))

New dedicated training script for two-stream architecture:

**Configuration:**
- Batch size: 12 (smaller for larger model)
- Learning rate: 0.0003 (lower for stability)
- Epochs: 200 (more for convergence)
- Dropout: 0.3
- Label smoothing: 0.1
- Scheduler: CosineAnnealingLR

**Features:**
- ✅ Mixed precision training (AMP)
- ✅ Label smoothing cross-entropy
- ✅ Gradient clipping
- ✅ Early stopping (patience=25)
- ✅ Cosine annealing LR schedule
- ✅ On-the-fly augmentation

## Expected Performance

| Model           | Parameters | Accuracy (Expected) | Improvement |
|-----------------|------------|---------------------|-------------|
| Single-stream   | ~4-5M      | 75-85%              | Baseline    |
| Two-stream      | ~8-10M     | 80-90%              | **+5-8%**   |

## How to Train on Kaggle

### Step 1: Upload Files to Kaggle

Upload these files to your Kaggle notebook:
1. `kaggle_scripts/train_two_stream.py`
2. `src/model/nsagf.py` (updated with TwoStreamNSAGF)
3. `src/graph/topology.py` (updated with get_bone_connections)

### Step 2: Install Dependencies

```python
!pip install torch torchvision scikit-learn tqdm matplotlib seaborn
```

### Step 3: Run Preprocessing (if needed)

If you haven't already run Task 1.1 preprocessing with 5x augmentation:

```python
!python kaggle_scripts/preprocess_wlasl_IMPROVED.py
```

This generates 320 samples per class (5x augmentation).

### Step 4: Train Two-Stream Model

```python
!python kaggle_scripts/train_two_stream.py \
    --data_dir /kaggle/working/processed_data_improved \
    --output_dir /kaggle/working \
    --batch_size 12 \
    --lr 0.0003 \
    --epochs 200
```

**Expected Training Time:**
- With GPU (P100/T4): ~45-60 minutes for 200 epochs
- With GPU (TPU): ~30-40 minutes

### Step 5: Monitor Training

Watch for these metrics:
```
Epoch 1/200
  Train Loss: 2.8451 | Train Acc: 28.50%
  Val Loss:   2.7234 | Val Acc:   32.10%
  
Epoch 50/200
  Train Loss: 0.3421 | Train Acc: 88.20%
  Val Loss:   0.4567 | Val Acc:   85.40%
  ✅ Saved best model (Val Acc: 85.40%)
  
Epoch 100/200
  Train Loss: 0.1234 | Train Acc: 95.10%
  Val Loss:   0.3891 | Val Acc:   88.60%
  ✅ Saved best model (Val Acc: 88.60%)
```

### Step 6: Evaluate Results

After training completes:

```python
import json
import numpy as np

# Load results
with open('/kaggle/working/two_stream_results.json', 'r') as f:
    results = json.load(f)

print(f"Test Accuracy: {results['test_accuracy']*100:.2f}%")
print(f"Best Val Accuracy: {results['best_val_accuracy']:.2f}%")
```

### Step 7: Download Model

```python
from google.colab import files  # Or Kaggle API

# Download trained model
files.download('/kaggle/working/ns_agf_two_stream_best.pth')
files.download('/kaggle/working/two_stream_results.json')
```

## Comparison: Single-Stream vs Two-Stream

### Architecture Differences

| Feature                | Single-Stream        | Two-Stream              |
|------------------------|----------------------|-------------------------|
| Input processing       | Joint positions only | Joint + Bone vectors    |
| ST-GCN blocks          | 10 blocks (1 stream) | 10 blocks × 2 streams   |
| Feature dimension      | 512                  | 1024 (512 + 512)        |
| Parameters             | ~4-5M                | ~8-10M                  |
| Training time          | ~30 min              | ~45-60 min              |
| Memory usage           | ~2GB                 | ~3-4GB                  |
| Expected accuracy      | 75-85%               | 80-90%                  |

### When to Use Each

**Single-Stream (Current):**
- ✅ Limited GPU memory (<4GB)
- ✅ Fast inference required
- ✅ Small datasets (<100 samples/class)
- ✅ Baseline model

**Two-Stream (New):**
- ✅ GPU memory ≥4GB
- ✅ Higher accuracy needed (journal publication)
- ✅ Larger datasets (≥200 samples/class)
- ✅ State-of-the-art performance

## Testing Locally

After downloading the model, test with local inference:

### Option 1: Update inference.py to support two-stream

```python
# In inference.py, modify model loading:

def load_model(self):
    checkpoint = torch.load(self.model_path, ...)
    
    # Check architecture type
    architecture = checkpoint.get('config', {}).get('architecture', 'single_stream')
    
    if architecture == 'two_stream':
        from src.model.nsagf import create_model
        model = create_model(
            num_classes=self.num_classes,
            graph=graph,
            dropout=0.0,
            two_stream=True  # ← Enable two-stream
        )
    else:
        # Existing single-stream loading
        model = NSAGF(...)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    return model
```

### Option 2: Test with simple script

```python
import torch
from src.model.nsagf import create_model
from src.graph.topology import MediaPipeGraph

# Load checkpoint
checkpoint = torch.load('ns_agf_two_stream_best.pth', map_location='cpu')

# Create model
graph = MediaPipeGraph()
model = create_model(
    num_classes=checkpoint['num_classes'],
    graph=graph,
    dropout=0.0,
    two_stream=True
)

model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Test forward pass
x = torch.randn(1, 3, 30, 75)  # (N, C, T, V)
with torch.no_grad():
    output = model(x)
    probs = torch.softmax(output, dim=1)
    pred = torch.argmax(probs, dim=1)

print(f"Prediction: {pred.item()}")
print(f"Confidence: {probs[0, pred].item()*100:.2f}%")
```

## Troubleshooting

### Issue 1: Out of Memory (OOM)

**Symptom:** `RuntimeError: CUDA out of memory`

**Solutions:**
1. Reduce batch size: `--batch_size 8` (from 12)
2. Use gradient accumulation:
   ```python
   accumulation_steps = 2
   loss = loss / accumulation_steps
   loss.backward()
   if (step + 1) % accumulation_steps == 0:
       optimizer.step()
       optimizer.zero_grad()
   ```
3. Reduce model size (not recommended - affects accuracy)

### Issue 2: Slow Training

**Symptom:** Training takes >90 minutes

**Solutions:**
1. Enable mixed precision (should be default):
   ```python
   USE_AMP = True  # Already enabled
   ```
2. Increase batch size (if memory allows): `--batch_size 16`
3. Use fewer workers: `num_workers=1` (from 2)
4. Reduce epochs: `--epochs 150` (from 200)

### Issue 3: Overfitting

**Symptom:** Train acc 95%+, Val acc <80%

**Solutions:**
1. Increase dropout: Change `DROPOUT_RATE = 0.5` (from 0.3)
2. Increase augmentation in preprocessing
3. Add more label smoothing: `LABEL_SMOOTHING = 0.2` (from 0.1)
4. Reduce model size (6 blocks instead of 10)

### Issue 4: Bone Features Not Working

**Symptom:** Two-stream performs same as single-stream

**Verification:**
```python
# Check bone feature computation
bone_features = model._compute_bone_features(x)
print(f"Bone features shape: {bone_features.shape}")
print(f"Bone features range: [{bone_features.min():.4f}, {bone_features.max():.4f}]")
print(f"Bone features mean: {bone_features.mean():.4f}")

# Should show non-zero values indicating bone vectors computed
```

**Solution:** Ensure graph topology has `get_bone_connections()` method

## Next Steps After Task 1.2

After successfully training two-stream model:

1. **Compare Results:**
   - Single-stream accuracy: __%
   - Two-stream accuracy: __%
   - Improvement: __%

2. **If accuracy ≥85%:** ✅ Move to Task 1.3 (Temporal Smoothing)

3. **If accuracy <85%:** Consider:
   - Task 1.1 complete? (5x augmentation = 320 samples/class)
   - Train longer (250-300 epochs)
   - Combine single-stream + two-stream ensemble

4. **Update inference.py** to support two-stream models

5. **Document results** in project README

## Files Modified/Created

✅ **Modified:**
- `src/model/nsagf.py` - Added TwoStreamNSAGF class
- `src/graph/topology.py` - Added get_bone_connections()

✅ **Created:**
- `kaggle_scripts/train_two_stream.py` - Training script
- `TWO_STREAM_GUIDE.md` - This guide

## Expected Outcome

After completing Task 1.2:

**Before (Single-Stream):**
- Model: NSAGF (4-5M params)
- Accuracy: 75-85%
- Training: ~30 min

**After (Two-Stream):**
- Model: TwoStreamNSAGF (8-10M params)
- Accuracy: 80-90% (**+5-8% boost**)
- Training: ~45-60 min

**Progress:**
- Task 1.1: ✅ Augmentation 2x→5x (320 samples/class)
- Task 1.2: ✅ Two-Stream Architecture (Joint + Bone)
- Task 1.3: ⏳ Temporal Smoothing (next)

---

**Status:** ✅ Implementation Complete - Ready for Training on Kaggle

**Date:** December 27, 2025
