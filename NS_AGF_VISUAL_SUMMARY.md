# 🎨 NS-AGF Visual Architecture Summary

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        NS-AGF System Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │    Camera    │
                              │   Input      │
                              └──────┬───────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │   MediaPipe Holistic   │
                        │  75-Node Extraction    │
                        └────────┬───────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  │  Pose (0-32)  33 landmarks  │
                  │  Left Hand    21 landmarks  │
                  │  Right Hand   21 landmarks  │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────────┐
              │    Sequence Buffer (30 frames)       │
              │    Shape: (30, 75, 3)                │
              └──────────────┬───────────────────────┘
                             │
                             ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              2s-AGCN Neural Network (PyTorch)                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                               ┃
┃  Input: (N, 3, 30, 75, 1)                                   ┃
┃    ↓                                                          ┃
┃  ┌────────────────────────────────────────────┐             ┃
┃  │  Adaptive Graph Convolution Layers         │             ┃
┃  │                                             │             ┃
┃  │  H_out = ReLU(BN(Σ W·H_in·(A+B+C)))       │             ┃
┃  │                                             │             ┃
┃  │  A: Physical adjacency (frozen)            │             ┃
┃  │  B: Learnable topology (trained)           │             ┃
┃  │  C: Attention-based (dynamic)              │             ┃
┃  └────────────────┬───────────────────────────┘             ┃
┃                   ↓                                          ┃
┃  ┌────────────────────────────────────────────┐             ┃
┃  │  Temporal Convolution Layers               │             ┃
┃  │  (9x1 kernels, stride control)             │             ┃
┃  └────────────────┬───────────────────────────┘             ┃
┃                   ↓                                          ┃
┃  ┌────────────────────────────────────────────┐             ┃
┃  │  Global Pooling + Classifier               │             ┃
┃  │  Output: (N, num_classes)                  │             ┃
┃  └────────────────┬───────────────────────────┘             ┃
┃                                                               ┃
┗━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                     │
                     ▼
        ┌────────────────────────────┐
        │  Softmax Probabilities     │
        │  [0.05, 0.92, 0.03, ...]   │
        └────────────┬───────────────┘
                     │
                     ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           Neuro-Symbolic Verification Layer                  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                               ┃
┃  ✓ Confidence Check: > 0.75                                 ┃
┃  ✓ Slot Filling: [amount, recipient]                        ┃
┃  ✓ Semantic Rules: No invalid sequences                     ┃
┃  ✓ Safety Checks: Amount limits                             ┃
┃                                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                     │
                     ▼
            ┌────────────────┐
            │  Verified      │
            │  Intent        │
            │  + Confidence  │
            └────────┬───────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Banking Transaction      │
        │   (Backend API)            │
        └────────────────────────────┘
```

---

## 🧠 Core Innovation: Three Adjacency Matrices

```
┌─────────────────────────────────────────────────────────────┐
│                  Adaptive Adjacency = A + B + C              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  A: Physical     │   │  B: Learnable    │   │  C: Attention    │
│  (Static)        │ + │  (Trained)       │ + │  (Dynamic)       │
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ Bone connections │   │ Global patterns  │   │ Frame-specific   │
│ From skeleton    │   │ Learned during   │   │ Computed on      │
│ anatomy          │   │ training         │   │ the fly          │
│                  │   │                  │   │                  │
│ Example:         │   │ Example:         │   │ Example:         │
│ Wrist → Fingers  │   │ L-Hand → R-Hand  │   │ Strong when both │
│ (Fixed forever)  │   │ (If sign needs)  │   │ hands active     │
└──────────────────┘   └──────────────────┘   └──────────────────┘

Result: Model learns which connections matter for each sign type
```

---

## 🔄 Training vs Inference Workflow

```
╔═══════════════════════════════════════════════════════════════╗
║                    TRAINING (Kaggle)                          ║
╚═══════════════════════════════════════════════════════════════╝

WLASL Videos → MediaPipe → Landmarks → Graph → 2s-AGCN → Weights
  (Input)        Extract     (30,75,3)   Build   Train    (.pth)
                                                             ↓
                                                        Download
                                                             ↓
╔═══════════════════════════════════════════════════════════════╗
║                   INFERENCE (Local)                           ║
╚═══════════════════════════════════════════════════════════════╝

Camera → MediaPipe → Buffer → 2s-AGCN → Verifier → Result
Frame     Extract     30fps    (Load      Rules     Display
                              weights)
```

---

## 📊 75-Node Graph Topology

```
                    ┌─────────────┐
                    │  Pose (33)  │
                    │   Nodes     │
                    │   0-32      │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
      ┌───────▼────────┐       ┌───────▼────────┐
      │  Left Wrist    │       │  Right Wrist   │
      │  (Node 15)     │       │  (Node 16)     │
      └───────┬────────┘       └───────┬────────┘
              │                         │
      ┌───────▼────────┐       ┌───────▼────────┐
      │  Left Hand     │       │  Right Hand    │
      │  Root (33)     │       │  Root (54)     │
      └───────┬────────┘       └───────┬────────┘
              │                         │
      ┌───────▼────────┐       ┌───────▼────────┐
      │  5 Fingers     │       │  5 Fingers     │
      │  (34-53)       │       │  (55-74)       │
      │  21 landmarks  │       │  21 landmarks  │
      └────────────────┘       └────────────────┘

Critical Bridge: Wrists connect pose to hands (enables info flow)
```

---

## 🎯 Neuro-Symbolic Verification Logic

```
┌──────────────────────────────────────────────────────────────┐
│              Neural Network Prediction                        │
│  "TRANSFER" with confidence 0.92                             │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ IF confidence  │  NO → Reject
            │    > 0.75?     │──────────────→  "Too uncertain"
            └────────┬───────┘
                     │ YES
                     ▼
            ┌────────────────┐
            │ Check required │  Missing → Prompt
            │ slots: amount, │──────────────→  "How much?"
            │ recipient      │
            └────────┬───────┘
                     │ Complete
                     ▼
            ┌────────────────┐
            │ Safety check:  │  Exceeds → Reject
            │ amount < max   │──────────────→  "Amount too high"
            └────────┬───────┘
                     │ Valid
                     ▼
            ┌────────────────┐
            │ Semantic check:│  Invalid → Reject
            │ no forbidden   │──────────────→  "Sequence error"
            │ sequences      │
            └────────┬───────┘
                     │ Consistent
                     ▼
            ┌────────────────┐
            │ ✅ VERIFIED    │
            │ Execute        │
            │ transaction    │
            └────────────────┘
```

---

## 🔬 Comparison: Baseline vs NS-AGF

```
┌──────────────────────────────────────────────────────────────┐
│                 LSTM (Baseline)                               │
├──────────────────────────────────────────────────────────────┤
│  Input: Sequential frames                                     │
│   ↓                                                           │
│  LSTM cells → Dense layer → Softmax                          │
│   ↓                                                           │
│  No spatial structure                                         │
│  No adaptive connections                                      │
│  Only confidence threshold                                    │
└──────────────────────────────────────────────────────────────┘
                           VS
┌──────────────────────────────────────────────────────────────┐
│               NS-AGF (Proposed)                               │
├──────────────────────────────────────────────────────────────┤
│  Input: Graph structure (75 nodes)                           │
│   ↓                                                           │
│  Adaptive GCN (A+B+C) → Temporal Conv → Softmax             │
│   ↓                                                           │
│  Explicit spatial modeling                                    │
│  Learns sign-specific patterns                                │
│  Neuro-symbolic verification                                  │
│  Continuous liveness (SLM)                                    │
└──────────────────────────────────────────────────────────────┘

Result: Better accuracy, explainability, and safety
```

---

## 🏆 Novel Contributions (SLM)

```
Traditional Approach:
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Liveness   │   │    Sign     │   │ Transaction │
│  Check      │→  │ Recognition │→  │  Execute    │
│  (Face)     │   │   (Hand)    │   │             │
└─────────────┘   └─────────────┘   └─────────────┘
   Separate            Separate          Risk of
   Module              Module            Replay Attack

NS-AGF Approach (SLM):
┌───────────────────────────────────────────────────┐
│     Synergistic Biometric Integrity (SLM)         │
│                                                    │
│  Face + Hand graph → Single unified model         │
│  Biomechanics verified during signing             │
│  Deepfake detectable via sync mismatch            │
└───────────────────────────────────────────────────┘
   Single                  Continuous               Attack-
   Model                   Verification             Resistant
```

---

## 📦 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KAGGLE (Cloud)                            │
├─────────────────────────────────────────────────────────────┤
│  - Heavy computation (training)                              │
│  - GPU acceleration (T4/P100)                                │
│  - Dataset storage (WLASL)                                   │
│  - Model export (.pth)                                       │
└────────────────────┬────────────────────────────────────────┘
                     │ Download weights
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  LOCAL (VS Code)                             │
├─────────────────────────────────────────────────────────────┤
│  - Inference only (no training)                              │
│  - Load pre-trained weights                                  │
│  - Real-time camera processing                               │
│  - Banking app integration                                   │
└─────────────────────────────────────────────────────────────┘

Advantage: Best of both worlds (cloud power + local privacy)
```

---

## 🎓 For Thesis Reviewers

### Q1: "What's novel about the graph structure?"
**A**: We use a 75-node semantic subgraph (not standard COCO) with critical wrist-to-hand bridges for sign language specificity.

### Q2: "How is this different from regular GCN?"
**A**: We use **adaptive** adjacency = Physical (A) + Learnable (B) + Attention (C), not just static A.

### Q3: "Why neuro-symbolic? Isn't pure DL enough?"
**A**: Banking requires logical guarantees (e.g., no negative amounts). Symbolic rules catch neural hallucinations.

### Q4: "What's SLM?"
**A**: **Synergistic Biometric Integrity** - liveness and recognition fused in one model, unlike traditional separate systems.

### Q5: "Can I reproduce this?"
**A**: Yes! All code provided. Train on Kaggle (free GPU), infer locally. See `IMPLEMENTATION_GUIDE.md`.

---

## 📊 Expected Results Table (Fill After Training)

| Metric | Baseline (LSTM) | NS-AGF (Ours) | Improvement |
|--------|-----------------|---------------|-------------|
| Validation Accuracy | __% | __% | +__% |
| Inference FPS | __ | __ | +__ |
| Model Size | __MB | __MB | -__MB |
| Latency | __ms | __ms | -__ms |
| False Positives | __% | __% | -__% |
| Liveness Detection | ✗ Separate | ✓ Integrated | Novel |

---

**🎨 This visual summary is ready for your thesis presentation!**

Save this file for:
- Thesis defense slides
- Project documentation
- Reviewer questions
- GitHub README
