# 🚀 NS-AGF Quick Start Card

## ⚡ TL;DR - Get Started in 3 Steps

### 1️⃣ Train on Kaggle (REQUIRED - Do First)
```
1. Go to: https://www.kaggle.com/code
2. Create notebook with GPU T4
3. Copy-paste scripts from: ns_agf/kaggle_scripts/
4. Run: preprocess → train → export (6-8 hours)
5. Download: ns_agcn_bankassist.pth → ns_agf/models/
```

### 2️⃣ Test Locally (After Training)
```powershell
cd "d:\MAJOR-PROJECT - Copy\ns_agf"
pip install -r requirements_nsagf.txt
python inference.py --model_path ./models/ns_agcn.pth --camera 0
```

### 3️⃣ Document for Thesis
- Save training curves from Kaggle
- Record demo video of live inference
- Calculate accuracy, FPS, latency

---

## 📁 Essential Files

| File | Purpose |
|------|---------|
| `ns_agf/kaggle_scripts/train_agcn.py` | **Upload to Kaggle** |
| `ns_agf/inference.py` | **Run locally after training** |
| `NS_AGF_COMPLETE_SUMMARY.md` | **Read for overview** |
| `ns_agf/IMPLEMENTATION_GUIDE.md` | **Follow step-by-step** |

---

## 🎯 What Makes This Novel

1. **SLM** - Liveness + Recognition in one model
2. **Adaptive Graph** - 3 adjacency matrices (A+B+C)
3. **Neuro-Symbolic** - Neural + Logic rules
4. **Practical Workflow** - Kaggle training + Local inference

---

## ⚠️ Common Mistakes to Avoid

❌ Don't try to train locally (will fail)  
❌ Don't skip Kaggle step (model required for inference)  
❌ Don't modify existing folders (ns_agf is standalone)  
❌ Don't commit model files to git (use .gitignore)

---

## ✅ Status Checklist

- [x] Code implemented (DONE)
- [ ] Model trained on Kaggle (DO THIS NOW)
- [ ] Inference tested locally (AFTER TRAINING)
- [ ] Results documented (FOR THESIS)

---

## 🆘 Help Commands

```powershell
# Test components (no training needed)
python ns_agf/src/graph/topology.py
python ns_agf/src/logic/verifier.py

# Check if model exists
ls ns_agf/models/

# Install dependencies
pip install -r ns_agf/requirements_nsagf.txt
```

---

## 📚 Read Next

1. **Before Kaggle**: `ns_agf/kaggle_scripts/README_KAGGLE.md`
2. **After Training**: `ns_agf/IMPLEMENTATION_GUIDE.md`
3. **For Thesis**: `NS_AGF_COMPLETE_SUMMARY.md`

---

**🎓 Your NS-AGF implementation is complete. Start Kaggle training now!**
