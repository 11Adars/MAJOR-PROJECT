# 🎯 Model Validation Tool - Quick Guide

## What This Tool Does

**Problem:** Hard to analyze sign predictions in real-time inference
**Solution:** Record signs with spacebar control → Analyze predictions → Save results

---

## 🚀 Quick Start

### Run the validator:
```bash
cd "d:\MAJOR-PROJECT - Copy\ns_agf"
python validate_model.py
```

---

## ⌨️ Controls

| Key | Action |
|-----|--------|
| **SPACE** | Start/Stop recording |
| **S** | Save & Analyze recording |
| **D** | Discard recording |
| **Q** | Quit |

---

## 📝 Step-by-Step Usage

### 1. **Start Recording**
- Press **SPACE**
- Red circle appears (blinking)
- Shows "RECORDING" with frame count

### 2. **Perform Your Sign**
- Do complete sign motion (2-4 seconds)
- Keep both hands in frame
- Complete the full gesture

### 3. **Stop Recording**
- Press **SPACE** again
- Shows frame count and landmark count

### 4. **Analyze**
- Press **S** to save and analyze
- See detailed prediction breakdown
- Check top 5 predictions with confidence

### 5. **Review Results**
```
📊 ANALYZING RECORDING
======================================================================
📹 Recording Info:
   Frames captured: 78
   Landmarks extracted: 30
   Duration: 2.6s

🎯 Top 5 Predictions:
   1. Manager      68.5% ██████████████████████████████████
   2. Adress       15.2% ███████
   3. Bank          8.3% ████
   4. Account       4.1% ██
   5. ATM           2.9% █

📋 Analysis:
   ✅ HIGH CONFIDENCE - Model is confident this is 'Manager'

💾 Saved to: validation_recordings/Manager_68%_20251210_185423
```

---

## 📊 Understanding Results

### **High Confidence (>70%)** ✅
```
Manager      72.3% ████████████████████████████████████
```
- **Meaning:** Model is confident - sign is clear
- **Action:** ✅ This sign is working well!

### **Medium Confidence (45-70%)** ⚠️
```
Manager      58.2% █████████████████████████████
Adress       42.1% █████████████████████
```
- **Meaning:** Model is uncertain - may confuse signs
- **Action:** ⚠️ Need more training data or clearer distinction

### **Low Confidence (<45%)** ❌
```
Manager      38.5% ███████████████████
Bank         35.2% █████████████████
Account      26.3% █████████████
```
- **Meaning:** Model cannot recognize this sign
- **Action:** ❌ Sign not learned properly - needs retraining

### **Confusion Warning** ⚠️
```
Manager      51.2% █████████████████████████
Adress       48.7% ████████████████████████
⚠️  CONFUSION - 'Adress' is very close (48.7%)
    Model is confused between these two signs!
```
- **Meaning:** Two signs look very similar to model
- **Action:** ⚠️ Need better class separation or more diverse training data

---

## 📁 Output Files

### Saved to: `validation_recordings/`

Each recording creates 3 files:

1. **Video file** (`.mp4`)
   - Original recording with landmarks
   - Can review your signing motion

2. **Landmarks file** (`_landmarks.npy`)
   - Extracted 75-node landmarks (30 frames)
   - Can add to training dataset if good

3. **Analysis file** (`_analysis.json`)
   ```json
   {
     "timestamp": "20251210_185423",
     "frames": 78,
     "landmarks_frames": 30,
     "predictions": [
       {"sign": "Manager", "confidence": 0.685, "class_id": 5},
       {"sign": "Adress", "confidence": 0.152, "class_id": 9}
     ],
     "video_file": "Manager_68%_20251210_185423.mp4"
   }
   ```

---

## 🧪 Validation Workflow

### Test All Signs Systematically

```
1. ATM      → Record → Analyze
2. Account  → Record → Analyze
3. Amount   → Record → Analyze
4. Bank     → Record → Analyze
5. Illegal  → Record → Analyze
6. Manager  → Record → Analyze
7. Passbook → Record → Analyze
8. Remove   → Record → Analyze
9. Report   → Record → Analyze
10. Adress  → Record → Analyze
11. Speak   → Record → Analyze
```

### After Testing All Signs

Check which signs have:
- ✅ **High confidence** (>70%) - Working well
- ⚠️ **Medium confidence** (45-70%) - Need attention
- ❌ **Low confidence** (<45%) - Need retraining

---

## 💡 Use Cases

### 1. **Validate Current Model**
- Test each sign 2-3 times
- Check consistency of predictions
- Identify which signs work well

### 2. **Find Problem Signs**
- If Manager always predicts as Adress → Class imbalance
- If confidence always low → Need more training data
- If predictions random → Sign not learned

### 3. **Compare Signers**
- Record same sign by different people
- Check if model generalizes
- Identify signer-specific issues

### 4. **Test Variations**
- Record sign at different speeds
- Different camera distances
- Different hand starting positions
- Check robustness

### 5. **Collect Good Training Data**
- Record high-quality signs
- Use saved landmarks as training data
- Augment dataset with validated recordings

---

## 📈 Example Session

```
🎯 SIGN LANGUAGE MODEL VALIDATOR
======================================================================
Testing "Manager" sign...

Recording 1:
✅ Manager 72.3% - HIGH CONFIDENCE
✅ Good! Model recognizes this well.

Recording 2:
⚠️  Manager 58.2% - MEDIUM CONFIDENCE
⚠️  CONFUSION - 'Adress' is close (41.8%)
⚠️  Model sometimes confuses Manager with Adress

Recording 3:
✅ Manager 69.1% - MEDIUM-HIGH CONFIDENCE
✅ Better! But still some uncertainty.

Analysis:
- Manager works but sometimes confused with Adress
- Need to increase Manager training data
- Or reduce Adress training data (class imbalance)
- Consider retraining with fixed preprocessing

Next: Test "Adress" to see if it has same issue
```

---

## 🔍 Troubleshooting

### Recording shows 0 landmarks
**Problem:** Landmarks not detected during recording
**Solution:**
- Check lighting (increase brightness)
- Keep both hands in frame
- Face camera directly
- Slow down sign motion

### All predictions are low confidence
**Problem:** Model not confident about any sign
**Solution:**
- Check if you're performing training signs correctly
- May need to retrain model
- Check if model file is correct version

### Wrong sign always predicted
**Problem:** Model learned wrong association
**Solution:**
- Check training data for that sign
- Verify video labels are correct
- May have class imbalance (e.g., too many "Adress" videos)
- Retrain with balanced dataset

### Predictions are random
**Problem:** Model hasn't learned the sign
**Solution:**
- Need more training data for this sign
- Check quality of training videos
- Retrain with at least 20-30 videos per sign

---

## 🎓 What to Look For

### ✅ Good Signs (Model Works Well)
- Confidence >70% consistently
- Same prediction across multiple recordings
- Clear separation from other signs in top-5

### ⚠️ Problematic Signs (Need Attention)
- Confidence 45-70% (uncertain)
- Different predictions for same sign
- Two signs with similar confidence (confusion)

### ❌ Failed Signs (Need Retraining)
- Confidence <45%
- Random predictions
- Never appears in top prediction
- Always predicts wrong sign

---

## 📊 Decision Guide

### After Validation, Based on Results:

**If most signs have high confidence (>70%):**
- ✅ Model is good! Just fix specific problem signs
- Add 5-10 more training videos for medium-confidence signs

**If many signs have medium confidence (45-70%):**
- ⚠️ Model needs improvement
- Follow COMPLETE_RETRAINING_GUIDE.md
- Use fixed preprocessing with normalization

**If many signs have low confidence (<45%):**
- ❌ Model needs complete retraining
- Check training data quality
- Ensure at least 20-30 videos per sign
- Verify preprocessing is correct

**If seeing "Adress" bias (Adress appears in all top-5):**
- 🔴 CRITICAL: Class imbalance issue
- Reduce Adress training videos to 25
- Retrain with class-weighted loss
- Follow COMPLETE_RETRAINING_GUIDE.md

---

## 💾 Using Recordings for Training

### If you recorded a good sign (high confidence):

1. Recording saved to `validation_recordings/Manager_72%_20251210_185423.mp4`
2. Landmarks saved to `Manager_72%_20251210_185423_landmarks.npy`
3. **Can add this to training data!**

```python
# In preprocessing script, load validated landmarks:
validated_landmarks = np.load('Manager_72%_20251210_185423_landmarks.npy')
# Add to training dataset
```

---

## 🎯 Summary

**This tool helps you:**
1. ✅ Test model predictions systematically
2. ✅ Identify which signs work vs. don't work
3. ✅ Understand confidence levels
4. ✅ Find class confusion (Manager vs Adress)
5. ✅ Validate before deployment
6. ✅ Collect good training data
7. ✅ Make informed decisions about retraining

**Next Steps:**
1. Run validator and test all 11 signs
2. Document which signs have low confidence
3. If >50% of signs have issues → Retrain (see COMPLETE_RETRAINING_GUIDE.md)
4. If <50% have issues → Just add more training data for those specific signs

---

**File:** `ns_agf/validate_model.py`  
**Version:** 1.0  
**Date:** December 2025
