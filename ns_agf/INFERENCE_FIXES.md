# 🔧 Fixing Inference Issues - Quick Guide

## Problems Identified

1. **❌ "Intent Unknown"** - The neuro-symbolic verifier was trying to match banking intents but you have custom signs
2. **❌ Rapidly Changing Predictions** - Model was making predictions every frame without proper smoothing
3. **❌ Unknown Sign Mappings** - Using generic "Sign_0", "Sign_1" instead of actual sign names
4. **❌ Low Confidence Noise** - Showing predictions even when model is uncertain

## ✅ Solutions Implemented

### 1. Sign Name Mapping

Created `models/sign_labels.txt` file to map class indices to actual sign names.

**How to use:**
```bash
# Edit the file and replace Sign_0, Sign_1, etc. with your actual sign names
# Line 1 = Class 0, Line 2 = Class 1, etc.
```

**Example:**
```
hello
thank_you
please
sorry
help
yes
no
money
account
balance
withdraw
```

**Important**: The order MUST match your training data folder order (alphabetically sorted).

If your training folders were:
```
dataset/
  ├── account/
  ├── balance/
  ├── hello/
  ├── help/
  └── money/
```

Then `sign_labels.txt` should be:
```
account
balance
hello
help
money
```

### 2. Improved Temporal Smoothing

**Before**: Prediction changed every frame → flickering
**After**: Uses majority voting over 15 frames → stable predictions

The system now:
- Collects predictions over a sliding window of 15 frames
- Uses weighted voting (confidence × frequency)
- Only updates display when confidence > threshold (70%)

### 3. Disabled Intent Verification

**Before**: Showing "Intent: UNKNOWN" for custom signs
**After**: Intent verification disabled by default (optional for custom datasets)

The neuro-symbolic verifier is now only enabled if `intent_rules.json` exists. For custom sign datasets, it's automatically disabled.

### 4. Confidence Threshold Filtering

**Before**: Showing all predictions including noisy low-confidence ones
**After**: Only displaying predictions above 70% confidence

**Color coding**:
- 🟢 **Green** (>70%) - High confidence, stable prediction
- 🟠 **Orange** (50-70%) - Medium confidence
- 🔴 **Red** (<50%) - Low confidence, likely noise

### 5. Added Class ID Display

Now shows the class index (0-10) on screen so you can verify which sign maps to which number.

## 📝 How to Get Your Sign Names

If you don't remember the exact order, run this in your dataset folder:

**Windows PowerShell:**
```powershell
Get-ChildItem -Directory | Sort-Object Name | Select-Object -ExpandProperty Name > sign_order.txt
```

**Linux/Mac:**
```bash
ls -1d */ | sort | sed 's#/##' > sign_order.txt
```

Then copy the contents to `ns_agf/models/sign_labels.txt`.

## 🚀 Testing the Fixes

Run inference again:
```powershell
cd "d:\MAJOR-PROJECT - Copy\ns_agf"
python inference.py
```

**What you should see now:**

1. ✅ Actual sign names (if you updated `sign_labels.txt`)
2. ✅ Stable predictions (not flickering every frame)
3. ✅ No "Intent: UNKNOWN" messages
4. ✅ Only shows predictions when confident
5. ✅ Class ID displayed for verification

## 🎯 Understanding the Display

```
┌─────────────────────────────────────┐
│ ✓ Detected                          │  ← Landmarks detected
│ Sign: hello                         │  ← Predicted sign name
│ Confidence: 85.3%                   │  ← Green = high confidence
│ Class ID: 2                         │  ← Index in model (0-10)
└─────────────────────────────────────┘
```

## 🔍 Debugging Tips

### If predictions are still unstable:

Increase smoothing window in `inference.py`:
```python
self.prediction_window = 20  # Was 15, try 20-30
```

### If confidence is too low:

Lower threshold temporarily:
```python
python inference.py --confidence_threshold 0.5  # Default is 0.7
```

### If wrong sign names:

Check the order in your training data:
```powershell
# In your dataset folder
Get-ChildItem -Directory | Sort-Object Name
```

This shows the exact order used during training.

### To see raw predictions (for debugging):

The system now tracks:
- `result['sign']` - Stable smoothed prediction (shown on screen)
- `result['raw_sign']` - Raw frame-by-frame prediction
- `result['raw_confidence']` - Raw confidence before smoothing

## 📊 Performance Tuning

### For faster response (less stable):
```python
self.prediction_window = 10
self.confidence_threshold = 0.6
```

### For more stable (slower response):
```python
self.prediction_window = 20
self.confidence_threshold = 0.8
```

## 🎓 For Your Thesis

Document these improvements:

1. **Temporal Smoothing**: Majority voting with confidence weighting over N-frame window
2. **Adaptive Thresholding**: Dynamic confidence filtering to reduce false positives
3. **Class Mapping**: Human-readable labels for interpretability

**Metrics to capture:**
- Prediction stability (frames until convergence)
- False positive rate (before/after smoothing)
- User experience (subjective stability rating)

## ❓ Still Having Issues?

Check:
1. **Model loaded correctly?** - Should show "✅ Model loaded: 11 classes"
2. **MediaPipe detecting?** - Should show "✓ Detected" in green
3. **Collecting frames?** - First 30 frames show "Collecting frames (X/30)"
4. **Sign names match?** - Count lines in `sign_labels.txt` = num classes

## 📞 Quick Reference

**Main changes:**
- `models/sign_labels.txt` - Add your sign names here
- `inference.py` - Improved smoothing + disabled intent verification
- Default window: 15 frames
- Default threshold: 70%
- Class ID now displayed on screen

**Files modified:**
- ✅ `ns_agf/inference.py` - Core fixes
- ✅ `ns_agf/models/sign_labels.txt` - Class name mapping

---

**Version**: 1.1.0  
**Date**: December 8, 2024  
**Status**: ✅ Issues Fixed - Ready for Testing
