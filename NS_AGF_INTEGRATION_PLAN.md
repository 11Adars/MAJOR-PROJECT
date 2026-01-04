# 🏗️ NS-AGF Architecture Integration Plan

## 📊 Current Project Analysis

### Existing Components:
1. **Sign Service** (`Sign/`)
   - TensorFlow/LSTM model for sign language recognition
   - MediaPipe landmark extraction
   - Flask service on port (check sign_service.py)
   
2. **Biometric Auth** (`python_service/`)
   - InsightFace (ArcFace) for face recognition
   - SpeechBrain ECAPA-TDNN for voice verification
   - Currently commented out (needs reactivation)

3. **Backend** (`backend/`)
   - Node.js/Express
   - Support ticket system
   - Payment integration

4. **Frontend** (`frontend/`)
   - React UI

---

## 🎯 Proposed NS-AGF Integration Structure

```
MAJOR-PROJECT/
├── backend/                    # ✅ KEEP AS-IS
├── frontend/                   # ✅ KEEP AS-IS
├── chatbot/                    # ✅ KEEP AS-IS
│
├── python_service/            # ✅ UPGRADE (Reactivate + Feature Fusion)
│   ├── app.py                 # Add feature-level fusion
│   └── pretrained_models/
│
├── Sign/                      # ✅ KEEP (Legacy LSTM Model)
│   ├── sign_service.py        # Existing service
│   └── saved_model_landmarks/ # Current TF model
│
├── ns_agf/                    # 🆕 NEW NS-AGF MODULE
│   ├── models/                # Downloaded .pth weights from Kaggle
│   │   └── ns_agcn.pth        # (Downloaded, not trained locally)
│   │
│   ├── src/
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   └── topology.py    # 75-node MediaPipe graph
│   │   │
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── agcn.py        # 2s-AGCN PyTorch model
│   │   │   └── layers.py      # Adaptive graph conv layers
│   │   │
│   │   ├── logic/
│   │   │   ├── __init__.py
│   │   │   ├── verifier.py    # Neuro-symbolic rules
│   │   │   └── intent_rules.json
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── mediapipe_helper.py
│   │       └── model_loader.py  # Kaggle downloader
│   │
│   ├── kaggle_scripts/        # 📤 UPLOAD TO KAGGLE
│   │   ├── README_KAGGLE.md   # Instructions for Kaggle
│   │   ├── train_agcn.py      # Training script
│   │   ├── preprocess_wlasl.py
│   │   └── export_model.py
│   │
│   ├── inference.py           # Real-time NS-AGF inference
│   ├── requirements_nsagf.txt # NS-AGF specific deps
│   └── README_NSAGF.md        # NS-AGF documentation
│
└── integration/               # 🆕 INTEGRATION LAYER
    ├── multimodal_fusion.py   # SLM: Face + Voice + Sign fusion
    ├── transaction_guard.py   # Continuous verification
    └── README_INTEGRATION.md
```

---

## 🔗 Integration Strategy

### Phase 1: NS-AGF Core (Standalone)
- Build NS-AGF in isolated `ns_agf/` folder
- Can run independently for testing
- No modifications to existing services

### Phase 2: Biometric Upgrade
- Reactivate `python_service/app.py`
- Upgrade from score-level to feature-level fusion
- Add continuous verification endpoint

### Phase 3: Full Integration
- Create `integration/` layer
- Connect NS-AGF inference → Biometric check → Backend
- Implement SLM (Simultaneous Liveness & Meaning)

---

## 🚀 Execution Order

1. ✅ Create NS-AGF folder structure
2. ✅ Implement graph topology (75 nodes)
3. ✅ Implement 2s-AGCN model
4. ✅ Create Kaggle training scripts
5. ✅ Build inference pipeline
6. ✅ Create integration layer
7. 📝 Update documentation

---

## 📦 Dependencies Management

- **Existing**: `requirements.txt` (keeps all current deps)
- **New**: `ns_agf/requirements_nsagf.txt` (NS-AGF specific)
- **Merge Strategy**: Update main requirements.txt with NS-AGF additions

---

## 🎓 Thesis Positioning

### Novel Contributions:
1. **NS-AGF Architecture**: Two-stream adaptive graph convolution with neuro-symbolic verification
2. **SLM (Synergistic Biometric Integrity)**: Continuous face-sign synchronization
3. **Feature-Level Multimodal Fusion**: Beyond score averaging
4. **Kaggle-Local Hybrid Workflow**: Practical deployment pattern

### Existing Work (Acknowledge):
- Baseline LSTM model (Sign/)
- Standard biometric auth (python_service/)
