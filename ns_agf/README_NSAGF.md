# 🧠 NS-AGF: Neuro-Symbolic Adaptive Graph Fusion

## Overview

NS-AGF (Neuro-Symbolic Adaptive Graph Fusion) is a cutting-edge sign language recognition system that combines deep graph neural networks with symbolic reasoning for banking applications.

### Key Innovation

Unlike traditional sign language recognition systems, NS-AGF introduces **Synergistic Biometric Integrity (SLM)** - simultaneous liveness detection and meaning extraction through adaptive graph convolutions on body landmarks.

---

## 🏗️ Architecture

### 1. Graph Topology (75 Nodes)
- **Pose**: 33 landmarks (body core)
- **Left Hand**: 21 landmarks (indices 33-53)
- **Right Hand**: 21 landmarks (indices 54-74)
- **Critical Bridge**: Wrist-to-hand connections for information flow

### 2. Two-Stream Adaptive Graph Convolution (2s-AGCN)

The model implements the equation:

$$H_{out} = \text{ReLU}(BN(\sum_{k} W_k \cdot H_{in} \cdot (A_k + B_k + C_k)))$$

Where:
- **$A_k$**: Physical adjacency (frozen spatial structure)
- **$B_k$**: Learnable global topology (trained parameters)
- **$C_k$**: Data-dependent attention (dynamic computation)

### 3. Neuro-Symbolic Verification

After neural network prediction, symbolic rules ensure:
- Confidence thresholds met
- Required slots filled (e.g., amount for transfer)
- Semantic consistency (no invalid sequences)
- Safety checks (transaction limits)

---

## 📁 Project Structure

```
ns_agf/
├── models/                      # Pre-trained weights (download from Kaggle)
│   └── ns_agcn.pth             # Main model file
│
├── src/
│   ├── graph/                   # Graph topology
│   │   ├── __init__.py
│   │   └── topology.py          # 75-node MediaPipe graph
│   │
│   ├── model/                   # Neural network
│   │   ├── __init__.py
│   │   └── agcn.py             # 2s-AGCN implementation
│   │
│   ├── logic/                   # Symbolic reasoning
│   │   ├── __init__.py
│   │   ├── verifier.py         # Intent verification
│   │   └── intent_rules.json   # Rule definitions
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── mediapipe_helper.py # Landmark extraction
│       └── model_loader.py     # Kaggle integration
│
├── kaggle_scripts/              # Training scripts (upload to Kaggle)
│   ├── README_KAGGLE.md
│   ├── preprocess_wlasl.py
│   ├── train_agcn.py
│   └── export_model.py
│
├── inference.py                 # Real-time inference pipeline
├── requirements_nsagf.txt       # Dependencies
└── README_NSAGF.md             # This file
```

---

## 🚀 Quick Start

### Installation

```bash
# Navigate to ns_agf directory
cd ns_agf

# Install dependencies
pip install -r requirements_nsagf.txt
```

### Training (Kaggle)

**You cannot train locally.** Follow these steps:

1. **Create Kaggle Notebook**:
   - Go to https://www.kaggle.com/code
   - Enable GPU (T4 recommended)

2. **Upload Scripts**:
   - Copy files from `kaggle_scripts/` to notebook

3. **Run Training**:
   ```python
   %run preprocess_wlasl.py
   %run train_agcn.py
   %run export_model.py
   ```

4. **Download Model**:
   - Go to Output tab → `ns_agcn_bankassist.pth`
   - Save to `ns_agf/models/`

See `kaggle_scripts/README_KAGGLE.md` for detailed instructions.

### Inference (Local)

```bash
# Real-time camera
python inference.py --model_path ./models/ns_agcn.pth --num_classes 100

# Process video
python inference.py --video input.mp4 --output output.mp4

# Options
python inference.py --help
```

---

## 🧪 Testing Individual Components

### Test Graph Topology
```bash
cd ns_agf/src/graph
python topology.py
```

### Test Model Architecture
```bash
cd ns_agf/src/model
python agcn.py
```

### Test Neuro-Symbolic Verifier
```bash
cd ns_agf/src/logic
python verifier.py
```

### Test MediaPipe Helper
```bash
cd ns_agf/src/utils
python mediapipe_helper.py
```

---

## 📊 Model Performance

(Add after training)

| Metric | Value |
|--------|-------|
| Training Accuracy | XX% |
| Validation Accuracy | XX% |
| Inference Speed | XX FPS |
| Model Size | XX MB |

---

## 🔗 Integration with Existing System

### With Current Sign Service

The NS-AGF system **coexists** with your existing `Sign/sign_service.py`:

- **Existing**: LSTM-based model (keep for comparison)
- **NS-AGF**: Graph-based model (new architecture)
- **Integration**: Run both, compare results, or switch entirely

### With Biometric Auth (`python_service/`)

NS-AGF can integrate with face/voice auth:

```python
from ns_agf.inference import SignLanguageInference
from python_service.app import face_model, voice_model

# Initialize NS-AGF
sign_recognizer = SignLanguageInference(model_path='./models/ns_agcn.pth')

# Get sign prediction
sign_result = sign_recognizer.predict(frame)

# Get face embedding (from python_service)
face_embedding = face_model.get(frame)

# Feature-level fusion
combined_features = np.concatenate([sign_result['features'], face_embedding])

# Verify transaction
is_valid = verify_multimodal(combined_features)
```

See `../integration/multimodal_fusion.py` for complete example (to be created).

---

## 📝 API Reference

### Inference

```python
from ns_agf.inference import SignLanguageInference

# Initialize
system = SignLanguageInference(
    model_path='./models/ns_agcn.pth',
    num_classes=100,
    confidence_threshold=0.7,
    device='cpu'
)

# Predict from frame
result = system.predict(frame_rgb)
# Returns: {'sign': 'TRANSFER', 'confidence': 0.92, 'intent': Intent(...)}

# Run camera
system.run_camera(camera_id=0)

# Process video
system.process_video('input.mp4', 'output.mp4')
```

### Graph

```python
from ns_agf.src.graph import MediaPipeGraph

graph = MediaPipeGraph()
adjacency_matrix = graph.get_adjacency_matrix(strategy='spatial')
node_groups = graph.get_node_groups()
```

### Verification

```python
from ns_agf.src.logic import NeuroSymbolicVerifier

verifier = NeuroSymbolicVerifier(confidence_threshold=0.75)
intent, is_valid, message = verifier.verify(
    gloss_sequence=['TRANSFER', '5000', 'ACCOUNT_123'],
    confidence_scores=[0.9, 0.95, 0.88],
    predicted_intent='transfer'
)
```

---

## 🎓 For Thesis Documentation

### Novel Contributions

1. **NS-AGF Architecture**: First application of adaptive graph convolutions to sign language banking
2. **SLM (Synergistic Biometric Integrity)**: Continuous face-sign synchronization
3. **Neuro-Symbolic Fusion**: Rule-based verification of neural predictions
4. **Kaggle-Local Workflow**: Practical deployment pattern for resource-constrained environments

### Comparison with Baseline

| Aspect | Baseline (LSTM) | NS-AGF (2s-AGCN) |
|--------|-----------------|------------------|
| Input | Sequential frames | Graph structure |
| Topology | None | Adaptive 75-node |
| Verification | Confidence only | Neuro-symbolic |
| Liveness | Separate | Integrated (SLM) |

### Figures to Include

1. 75-node graph topology visualization
2. Training curves (loss/accuracy)
3. Confusion matrix
4. Real-time inference screenshots
5. Architecture diagram

---

## 🐛 Troubleshooting

### Model Not Found
```bash
# Download from Kaggle
python -c "from ns_agf.src.utils.model_loader import fetch_trained_weights; fetch_trained_weights('your-username/ns-agcn-model/pytorch/1')"
```

### GPU Out of Memory (Training)
- Reduce batch size in `train_agcn.py`: `BATCH_SIZE = 8`

### MediaPipe Not Detecting
- Ensure good lighting
- Face camera directly
- Check camera permissions

### Import Errors
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## 📚 References

1. Shi et al. (2019) - Two-Stream Adaptive Graph Convolutional Networks
2. Yan et al. (2018) - Spatial Temporal Graph Convolutional Networks
3. Li et al. (2020) - Word-Level Deep Sign Language Recognition (WLASL)
4. MediaPipe Holistic - Google Research

---

## 📧 Support

For questions about NS-AGF:
1. Check `kaggle_scripts/README_KAGGLE.md` for training issues
2. Review test scripts in each module
3. See integration plan in `../NS_AGF_INTEGRATION_PLAN.md`

---

## ⚖️ License

[Your License]

---

## 🙏 Acknowledgments

- **MediaPipe Team** (Google) - Landmark detection
- **WLASL Dataset** - Sign language data
- **2s-AGCN Authors** - Architecture inspiration

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Ready for Training & Deployment
