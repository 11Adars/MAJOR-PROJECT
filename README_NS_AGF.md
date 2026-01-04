# 🏦 BankAssist AI - NS-AGF Implementation

[![Status](https://img.shields.io/badge/Status-Ready%20for%20Training-yellow)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)]()
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

## 🎯 Project Overview

BankAssist AI with **NS-AGF (Neuro-Symbolic Adaptive Graph Fusion)** - A cutting-edge multimodal banking system combining sign language recognition with biometric authentication.

### Novel Contribution: SLM (Synergistic Biometric Integrity)

Unlike traditional systems that check liveness separately, we verify identity **through** the act of signing - the biomechanical micro-movements of the hand signing are part of the liveness signature.

---

## 📂 Project Structure

```
MAJOR-PROJECT/
├── 📘 Documentation (START HERE)
│   ├── NS_AGF_QUICK_START.md        ← ⚡ Quick reference
│   ├── NS_AGF_COMPLETE_SUMMARY.md   ← 📖 Comprehensive guide
│   ├── NS_AGF_VISUAL_SUMMARY.md     ← 🎨 Visual diagrams
│   ├── NS_AGF_FILE_TREE.md          ← 📂 File navigation
│   └── NS_AGF_INTEGRATION_PLAN.md   ← 🔗 Integration roadmap
│
├── 🧠 NS-AGF Module (NEW)
│   └── ns_agf/                       ← See detailed structure below
│
└── ✅ Existing System (PRESERVED)
    ├── backend/                      ← Node.js backend
    ├── frontend/                     ← React frontend
    ├── python_service/               ← Face/Voice auth
    ├── Sign/                         ← Legacy LSTM model
    └── chatbot/                      ← Chatbot service
```

### NS-AGF Module Structure

```
ns_agf/
├── inference.py                 ← Run this for real-time recognition
├── verify_installation.py       ← Test installation
├── requirements_nsagf.txt       ← Dependencies
├── IMPLEMENTATION_GUIDE.md      ← Step-by-step execution
│
├── models/                      ← Download trained weights here
├── src/
│   ├── graph/                   ← 75-node topology
│   ├── model/                   ← 2s-AGCN architecture
│   ├── logic/                   ← Neuro-symbolic verifier
│   └── utils/                   ← Helpers
│
└── kaggle_scripts/              ← Upload to Kaggle for training
    ├── preprocess_wlasl.py
    ├── train_agcn.py
    └── export_model.py
```

---

## 🚀 Quick Start

### Step 1: Verify Installation

```powershell
cd "d:\MAJOR-PROJECT - Copy\ns_agf"
python verify_installation.py
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements_nsagf.txt
```

### Step 3: Train on Kaggle (Required)

**You cannot train locally.** Follow these steps:

1. Go to https://www.kaggle.com/code
2. Create notebook with GPU T4
3. Upload scripts from `ns_agf/kaggle_scripts/`
4. Run training (6-8 hours)
5. Download `ns_agcn_bankassist.pth` to `ns_agf/models/`

**Detailed instructions**: See `ns_agf/kaggle_scripts/README_KAGGLE.md`

### Step 4: Run Inference

```powershell
# Real-time camera
python ns_agf/inference.py --model_path ./ns_agf/models/ns_agcn.pth --camera 0

# Process video
python ns_agf/inference.py --video input.mp4 --output output.mp4
```

---

## 🎓 For Thesis/Research

### Novel Contributions

1. **NS-AGF Architecture**: Two-stream adaptive graph convolution with neuro-symbolic verification
2. **SLM (Synergistic Biometric Integrity)**: Continuous face-sign synchronization for liveness
3. **Feature-Level Fusion**: Beyond score averaging (2018) to embedding fusion (2025 SOTA)
4. **Practical Workflow**: Kaggle-local hybrid deployment pattern

### Key Papers to Cite

- Shi et al. (2019) - 2s-AGCN
- Yan et al. (2018) - ST-GCN
- Li et al. (2020) - WLASL Dataset
- MediaPipe Holistic (Google Research)

### Figures to Include

1. 75-node graph topology
2. Training curves (loss/accuracy)
3. Confusion matrix
4. Real-time inference demo
5. Architecture comparison diagram

**Visual templates**: See `NS_AGF_VISUAL_SUMMARY.md`

---

## 🧪 Testing

### Unit Tests (No Training Required)

```powershell
cd ns_agf

# Test individual components
python src/graph/topology.py
python src/model/agcn.py
python src/logic/verifier.py
python src/utils/mediapipe_helper.py
```

### Integration Tests (After Training)

```powershell
# Verify installation
python verify_installation.py

# Run inference
python inference.py --camera 0
```

---

## 🔗 Integration with Existing System

### Current Status

- ✅ **NS-AGF**: Standalone module (complete)
- ⏳ **Training**: Pending on Kaggle
- 📝 **Integration**: Optional future work

### Integration Options

**Option 1**: Replace existing Sign service
```javascript
// backend/index.js
app.post('/api/sign', (req, res) => {
  // Call NS-AGF instead of Sign/sign_service.py
  const result = fetch('http://localhost:5000/ns-agf/predict');
  res.json(result);
});
```

**Option 2**: Run both (A/B testing)
- Keep `Sign/` for comparison
- Add NS-AGF as alternative endpoint
- Compare accuracy and performance

**Option 3**: Feature-level fusion
- Combine NS-AGF sign features with face/voice features
- See `NS_AGF_INTEGRATION_PLAN.md` for details

---

## 📊 Performance Expectations

| Metric | Target | Notes |
|--------|--------|-------|
| Training Accuracy | 85-95% | On WLASL 100 classes |
| Validation Accuracy | 80-90% | Depends on data quality |
| Inference Speed | 20-30 FPS | CPU, 60+ FPS on GPU |
| Model Size | 50-150 MB | Depends on architecture depth |
| Latency | <100ms | MediaPipe + Inference + Verification |

---

## 🐛 Troubleshooting

### Issue: Model not found
```
FileNotFoundError: Model not found at ./models/ns_agcn.pth
```
**Solution**: Train on Kaggle first, then download model

### Issue: Import errors
```
ModuleNotFoundError: No module named 'ns_agf'
```
**Solution**: Run from correct directory or add to PYTHONPATH

### Issue: GPU OOM (Kaggle)
```
CUDA out of memory
```
**Solution**: Reduce batch size in `train_agcn.py` to 8 or 4

**Full troubleshooting guide**: See `ns_agf/IMPLEMENTATION_GUIDE.md`

---

## 📖 Documentation Index

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `NS_AGF_QUICK_START.md` | Quick reference | First time setup |
| `NS_AGF_COMPLETE_SUMMARY.md` | Complete overview | Before starting |
| `NS_AGF_VISUAL_SUMMARY.md` | Visual diagrams | For thesis/presentation |
| `NS_AGF_FILE_TREE.md` | File navigation | When exploring code |
| `ns_agf/IMPLEMENTATION_GUIDE.md` | Step-by-step | During execution |
| `ns_agf/kaggle_scripts/README_KAGGLE.md` | Training guide | Before Kaggle |
| `ns_agf/README_NSAGF.md` | API documentation | During integration |

---

## 🎯 Success Checklist

- [x] Code implemented ✅
- [ ] Dependencies installed
- [ ] Installation verified (`verify_installation.py`)
- [ ] Model trained on Kaggle
- [ ] Inference tested locally
- [ ] Results documented for thesis

---

## 🤝 Contributing

This is a research project for thesis work. For questions or improvements:

1. Review documentation in `ns_agf/`
2. Check troubleshooting guides
3. Test with `verify_installation.py`
4. Document any issues or improvements

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- **MediaPipe Team** (Google) - Landmark detection framework
- **WLASL Dataset** - Sign language data
- **2s-AGCN Authors** - Architecture inspiration
- **Kaggle** - Free GPU training platform

---

## 📞 Contact

[Your Contact Information]

---

## 🎉 Project Status

| Component | Status | Action Required |
|-----------|--------|-----------------|
| 🟢 Code | Complete | ✅ Done |
| 🟡 Dependencies | Ready | `pip install -r requirements_nsagf.txt` |
| 🟡 Training | Pending | Upload to Kaggle |
| 🟡 Testing | Pending | After training |
| 🔵 Integration | Optional | Future work |

---

## 🚀 Next Steps

1. **Immediate**: Run `verify_installation.py` to test setup
2. **Next**: Upload scripts to Kaggle and start training
3. **While Training**: Test local components and prepare thesis figures
4. **After Training**: Download model and test inference
5. **Final**: Document results and prepare thesis

---

**🎓 Your NS-AGF implementation is complete and ready for training!**

For detailed execution steps, see: **`ns_agf/IMPLEMENTATION_GUIDE.md`**  
For quick reference, see: **`NS_AGF_QUICK_START.md`**  
For visual diagrams, see: **`NS_AGF_VISUAL_SUMMARY.md`**

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: ✅ Ready for Training
