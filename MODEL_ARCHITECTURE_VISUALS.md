# 📊 Model Architecture Visual Guide

## 🎨 Detailed Visual Diagrams for Panel Presentation

---

## 1. 👤 Face Recognition Model - Detailed Architecture

### Layer-by-Layer Breakdown

```
INPUT LAYER
┌─────────────────────────────────────────────────┐
│ Raw Image: 640×640×3 (RGB)                      │
│ Pixel values: [0-255] normalized to [-1, 1]    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ DETECTION MODULE (RetinaFace)                   │
│ - Multi-scale face detection                    │
│ - Facial landmark detection (5 points)          │
│ - Face alignment and cropping                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ BACKBONE NETWORK (ResNet-100)                   │
│                                                  │
│ Conv1: 7×7, 64 filters                          │
│         ↓                                        │
│ ResBlock 1-3: [64, 64, 256] × 3 layers          │
│         ↓                                        │
│ ResBlock 4-8: [128, 128, 512] × 8 layers        │
│         ↓                                        │
│ ResBlock 9-36: [256, 256, 1024] × 36 layers     │
│         ↓                                        │
│ ResBlock 37-39: [512, 512, 2048] × 3 layers     │
│                                                  │
│ Total Layers: 100                                │
│ Parameters: ~65 million                          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ ARCFACE HEAD                                     │
│                                                  │
│ Global Average Pooling                           │
│         ↓                                        │
│ Fully Connected Layer: 2048 → 512               │
│         ↓                                        │
│ L2 Normalization (Unit Sphere Projection)       │
│         ↓                                        │
│ ArcFace Loss:                                    │
│   L = -log(e^(s·cos(θ+m)) / Σe^(s·cos(θ)))     │
│   where: s=64, m=0.5                            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ OUTPUT: 512-dimensional Embedding Vector        │
│ [0.123, -0.456, 0.789, ..., 0.234]             │
│ L2-normalized: ||v|| = 1                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ SIMILARITY COMPUTATION                           │
│                                                  │
│ Cosine Similarity:                               │
│   similarity = (v1 · v2) / (||v1|| × ||v2||)    │
│                                                  │
│ For normalized vectors:                          │
│   similarity = v1 · v2                           │
│                                                  │
│ Decision:                                        │
│   IF similarity > 0.5 → AUTHENTICATED           │
│   ELSE → REJECTED                                │
└─────────────────────────────────────────────────┘
```

### Mathematical Formulation

**ArcFace Loss Function:**
```
L = -1/N × Σ log(e^(s×cos(θyi + m)) / (e^(s×cos(θyi + m)) + Σ(j≠yi) e^(s×cos(θj))))

Where:
- N: batch size
- s: scale parameter (64)
- m: angular margin (0.5 radians ≈ 28.6°)
- θyi: angle between feature and ground truth class center
- θj: angle between feature and other class centers
```

**Why This Works:**
- Enforces intra-class compactness
- Enforces inter-class discrepancy
- Angular margin increases decision boundary

---

## 2. 🎤 Voice Recognition Model - Detailed Architecture

### Complete Processing Pipeline

```
INPUT: Audio Waveform
┌─────────────────────────────────────────────────┐
│ Raw Audio: Variable length, Variable sample rate│
│ Example: 5.2 seconds @ 44100 Hz                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ PREPROCESSING STAGE                              │
│                                                  │
│ Step 1: Resampling                               │
│   - Target: 16000 Hz                             │
│   - Method: librosa.resample()                   │
│                                                  │
│ Step 2: Voice Activity Detection (VAD)          │
│   - Remove silence (threshold: -20dB)            │
│   - Keep only voiced segments                    │
│                                                  │
│ Step 3: Normalization                            │
│   - RMS normalization                            │
│   - Peak normalization to [-1, 1]                │
│                                                  │
│ Step 4: Padding/Trimming                         │
│   - Minimum: 1 second                            │
│   - Maximum: 10 seconds                          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ FEATURE EXTRACTION                               │
│                                                  │
│ Branch 1: ACOUSTIC FEATURES                      │
│ ├─ F0 (Pitch): librosa.pyin()                   │
│ │  - Mean, Std, Skew, Kurtosis                  │
│ │  - Range: 80-400 Hz                           │
│ │                                                │
│ ├─ Spectral Features:                            │
│ │  - Centroid: frequency center of mass         │
│ │  - Rolloff: 85% of spectrum energy            │
│ │  - Bandwidth: spread around centroid          │
│ │                                                │
│ ├─ MFCC (20 coefficients):                       │
│ │  - DCT of log Mel filterbank energies         │
│ │  - Delta (velocity)                            │
│ │  - Delta-Delta (acceleration)                  │
│ │                                                │
│ └─ Formants:                                      │
│    - Pre-emphasis filter                         │
│    - Vocal tract resonance frequencies          │
│                                                  │
│ Branch 2: SPEAKER EMBEDDING                      │
│ (Processed by ECAPA-TDNN - see below)           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ ECAPA-TDNN ARCHITECTURE                          │
│                                                  │
│ Input: Waveform [1, T] where T = samples        │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Frame-level Features                         │ │
│ │ - 80-dim Mel filterbank                      │ │
│ │ - Window: 25ms, Hop: 10ms                    │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ SE-Res2Block 1                               │ │
│ │ ┌─────────────────┐                          │ │
│ │ │ TDNN Layer      │ Dilation: 1              │ │
│ │ │ Channels: 512   │                          │ │
│ │ └─────────────────┘                          │ │
│ │         ↓                                    │ │
│ │ ┌─────────────────┐                          │ │
│ │ │ Res2Net Module  │ Scale: 8                 │ │
│ │ │ Split → Conv →  │ Hierarchical features    │ │
│ │ │ Concatenate     │                          │ │
│ │ └─────────────────┘                          │ │
│ │         ↓                                    │ │
│ │ ┌─────────────────┐                          │ │
│ │ │ SE Attention    │ Channel recalibration    │ │
│ │ │ Squeeze-Excite  │                          │ │
│ │ └─────────────────┘                          │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ SE-Res2Block 2 (Dilation: 2)                    │
│         ↓                                        │
│ SE-Res2Block 3 (Dilation: 3)                    │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Attentive Statistical Pooling                │ │
│ │ - Weighted mean and std pooling              │ │
│ │ - Attention weights learned                  │ │
│ │ Output: [1, 1536]                            │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Fully Connected Layer                        │ │
│ │ 1536 → 192 dimensions                        │ │
│ │ + Batch Normalization                        │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ OUTPUT: 192-dimensional Speaker Embedding       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ VERIFICATION STAGE                               │
│                                                  │
│ Score 1: Embedding Similarity (Weight: 90%)     │
│   sim_emb = cosine(emb1, emb2)                  │
│                                                  │
│ Score 2: Biometric Similarity (Weight: 10%)     │
│   sim_bio = weighted_distance(feat1, feat2)     │
│   Components:                                    │
│   - F0 similarity: 35%                          │
│   - Spectral similarity: 25%                     │
│   - MFCC similarity: 25%                         │
│   - Formant similarity: 15%                      │
│                                                  │
│ Combined Score:                                  │
│   final_score = 0.9×sim_emb + 0.1×sim_bio       │
│                                                  │
│ Decision:                                        │
│   IF final_score > 0.60 → AUTHENTICATED         │
│   ELSE → REJECTED                                │
└─────────────────────────────────────────────────┘
```

### Mathematical Formulation

**Biometric Feature Similarity:**
```
For F0 (fundamental frequency):
  sim_f0 = max(0, 1 - |f0_1.mean - f0_2.mean| / (f0_2.mean × 0.3))

For Spectral Centroid:
  sim_spec = max(0, 1 - |sc_1 - sc_2| / (sc_2 × 0.4))

For MFCC:
  sim_mfcc = max(0, 1 - |mfcc_1.mean - mfcc_2.mean| / (mfcc_2.mean × 0.4))

Combined:
  sim_bio = Σ(weight_i × sim_i)
```

---

## 3. 🤟 Sign Language Recognition - Detailed Architecture

### Complete End-to-End Pipeline

```
STAGE 1: REAL-TIME CAPTURE
┌─────────────────────────────────────────────────┐
│ Webcam Feed: 30 FPS                              │
│ Resolution: 640×480 (adjustable)                 │
│ Format: BGR (OpenCV)                             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ MEDIAPIPE HOLISTIC PROCESSING                    │
│                                                  │
│ Component 1: POSE ESTIMATION                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ BlazePose Model                              │ │
│ │ - 33 body landmarks                          │ │
│ │ - Each landmark: (x, y, z, visibility)       │ │
│ │ - Coordinates normalized to [0, 1]           │ │
│ │                                              │ │
│ │ Landmark Groups:                             │ │
│ │ • Face: 11 points (nose, eyes, ears, mouth) │ │
│ │ • Torso: 11 points (shoulders, hips, etc)   │ │
│ │ • Arms: 8 points (elbows, wrists)           │ │
│ │ • Legs: 3 points (knees, ankles)            │ │
│ │                                              │ │
│ │ Total: 33 × 4 = 132 features                │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Component 2: HAND TRACKING                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ MediaPipe Hands Model                        │ │
│ │                                              │ │
│ │ LEFT HAND: 21 landmarks                      │ │
│ │ • Wrist: 1 point                             │ │
│ │ • Thumb: 4 points (CMC, MCP, IP, TIP)       │ │
│ │ • Index: 4 points                            │ │
│ │ • Middle: 4 points                           │ │
│ │ • Ring: 4 points                             │ │
│ │ • Pinky: 4 points                            │ │
│ │ Total: 21 × 4 = 84 features                 │ │
│ │                                              │ │
│ │ RIGHT HAND: 21 landmarks                     │ │
│ │ (Same structure)                             │ │
│ │ Total: 21 × 4 = 84 features                 │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Combined Output per Frame: 132 + 84 + 84 = 300 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ SEQUENCE COLLECTION                              │
│                                                  │
│ Recording Duration: 2-3 seconds                  │
│ Capture Rate: ~10 FPS (100ms interval)          │
│ Frames Collected: 20-30 frames                   │
│                                                  │
│ Sequence Buffer:                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Frame 1:  [300 features]                     │ │
│ │ Frame 2:  [300 features]                     │ │
│ │ Frame 3:  [300 features]                     │ │
│ │   ...                                        │ │
│ │ Frame 30: [300 features]                     │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Resampling:                                      │
│ IF len(sequence) < 30:                           │
│   → Linear interpolation to 30 frames            │
│ IF len(sequence) > 30:                           │
│   → Uniform sampling to 30 frames                │
│                                                  │
│ Final Shape: [30, 300]                           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ LSTM CLASSIFICATION MODEL                        │
│                                                  │
│ Input Shape: [batch_size, 30, 300]              │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ LSTM Layer 1                                 │ │
│ │ • Units: 128                                 │ │
│ │ • Activation: tanh                           │ │
│ │ • Return sequences: False                    │ │
│ │ • Recurrent dropout: 0.0                     │ │
│ │                                              │ │
│ │ Hidden State Update:                         │ │
│ │   h(t) = tanh(W_h·[h(t-1), x(t)] + b_h)     │ │
│ │   c(t) = f(t)·c(t-1) + i(t)·c̃(t)            │ │
│ │                                              │ │
│ │ Where:                                       │ │
│ │   f(t) = σ(W_f·[h(t-1), x(t)] + b_f)  Forget│ │
│ │   i(t) = σ(W_i·[h(t-1), x(t)] + b_i)  Input │ │
│ │   o(t) = σ(W_o·[h(t-1), x(t)] + b_o)  Output│ │
│ │   c̃(t) = tanh(W_c·[h(t-1), x(t)] + b_c) Cell│ │
│ │                                              │ │
│ │ Output: [batch_size, 128]                    │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Dropout Layer                                │ │
│ │ • Rate: 0.3                                  │ │
│ │ • Training only (disabled in inference)      │ │
│ │ • Prevents overfitting                       │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Dense Layer (Output)                         │ │
│ │ • Units: num_classes (e.g., 50)             │ │
│ │ • Activation: Softmax                        │ │
│ │                                              │ │
│ │ Softmax:                                     │ │
│ │   P(class=i) = e^(z_i) / Σ(e^(z_j))        │ │
│ │                                              │ │
│ │ Output: [batch_size, num_classes]            │ │
│ │ Each value: probability of that class        │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Prediction Selection                         │ │
│ │                                              │ │
│ │ predicted_class = argmax(probabilities)      │ │
│ │ confidence = max(probabilities)              │ │
│ │                                              │ │
│ │ IF confidence > 0.7:                         │ │
│ │   RETURN labels[predicted_class]             │ │
│ │ ELSE:                                        │ │
│ │   RETURN "uncertain"                         │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                    ↓
OUTPUT: Sign Label + Confidence
Example: ("HELP", 0.87)
```

### Loss Function: Focal Loss

```
FOCAL LOSS EXPLAINED
┌─────────────────────────────────────────────────┐
│ Why Focal Loss?                                  │
│                                                  │
│ Problem with Standard Cross-Entropy:            │
│ - Treats all examples equally                    │
│ - Easy examples dominate gradient               │
│ - Hard examples get less attention               │
│                                                  │
│ Focal Loss Solution:                             │
│ - Down-weights easy examples                     │
│ - Focuses on hard-to-classify signs             │
│ - Improves accuracy on rare gestures            │
└─────────────────────────────────────────────────┘

Mathematical Formula:

Standard Cross-Entropy:
  CE(p, y) = -y·log(p)

Focal Loss:
  FL(p, y) = -α·(1-p)^γ·y·log(p)

Where:
  p = predicted probability for true class
  y = ground truth (one-hot encoded)
  α = 0.25 (balance factor)
  γ = 2.0 (focusing parameter)

Example:
  Easy example (p=0.95):
    CE = -log(0.95) = 0.05
    FL = -0.25·(0.05)^2·log(0.95) = 0.0006
    → 100× less loss contribution

  Hard example (p=0.60):
    CE = -log(0.60) = 0.51
    FL = -0.25·(0.40)^2·log(0.60) = 0.02
    → Contributes more to training
```

---

## 4. 💬 Natural Language Generation - Detailed Architecture

### TinyLlama Processing Pipeline

```
STAGE 1: INPUT PREPARATION
┌─────────────────────────────────────────────────┐
│ Keywords from Sign Recognition                   │
│ ["HELP", "ACCOUNT", "BALANCE"]                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ PROMPT ENGINEERING                               │
│                                                  │
│ System Prompt:                                   │
│ "You are a banking assistant. Convert keyword   │
│  lists into complete sentences."                 │
│                                                  │
│ Few-Shot Examples (In-Context Learning):         │
│ ┌─────────────────────────────────────────────┐ │
│ │ Example 1:                                   │ │
│ │ Keywords: [MY, CARD, MISSING]                │ │
│ │ Output: My card is missing.                  │ │
│ ├─────────────────────────────────────────────┤ │
│ │ Example 2:                                   │ │
│ │ Keywords: [HELP, ONLINE, ACCOUNT]            │ │
│ │ Output: I need help with my online account.  │ │
│ ├─────────────────────────────────────────────┤ │
│ │ Example 3:                                   │ │
│ │ Keywords: [LOAN, STATUS]                     │ │
│ │ Output: What is the status of my loan?      │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ User Query:                                      │
│ Keywords: [HELP, ACCOUNT, BALANCE]              │
│                                                  │
│ Final Prompt (with special tokens):              │
│ <|system|>                                       │
│ You are a banking assistant...                   │
│ </s>                                             │
│ <|user|>                                         │
│ Keywords: [MY, CARD, MISSING]                    │
│ </s>                                             │
│ <|assistant|>                                    │
│ My card is missing.                              │
│ </s>                                             │
│ ... (more examples) ...                          │
│ <|user|>                                         │
│ Keywords: [HELP, ACCOUNT, BALANCE]              │
│ </s>                                             │
│ <|assistant|>                                    │
│ [MODEL GENERATES HERE]                           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ TINYLLAMA TRANSFORMER ARCHITECTURE               │
│                                                  │
│ Model: Llama-style Decoder-only Transformer     │
│ Parameters: 1.1 Billion                          │
│ Layers: 22                                       │
│ Hidden Size: 2048                                │
│ Attention Heads: 32                              │
│ Vocabulary Size: 32,000 tokens                   │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ TOKEN EMBEDDING                              │ │
│ │ Input: [token_ids]                           │ │
│ │ Output: [seq_len, 2048]                      │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ TRANSFORMER BLOCK 1-22 (repeated)            │ │
│ │                                              │ │
│ │  ┌────────────────────────────────────────┐ │ │
│ │  │ Multi-Head Attention                    │ │ │
│ │  │                                         │ │ │
│ │  │ Q = Linear(x)  [seq_len, 2048]         │ │ │
│ │  │ K = Linear(x)  [seq_len, 2048]         │ │ │
│ │  │ V = Linear(x)  [seq_len, 2048]         │ │ │
│ │  │                                         │ │ │
│ │  │ Split into 32 heads:                   │ │ │
│ │  │   head_dim = 2048 / 32 = 64            │ │ │
│ │  │                                         │ │ │
│ │  │ For each head h:                       │ │ │
│ │  │   scores = Q_h · K_h^T / √64           │ │ │
│ │  │   attention = softmax(scores)          │ │ │
│ │  │   output_h = attention · V_h           │ │ │
│ │  │                                         │ │ │
│ │  │ Concatenate heads                       │ │ │
│ │  │ Output projection                       │ │ │
│ │  └────────────────────────────────────────┘ │ │
│ │         ↓                                   │ │
│ │  ┌────────────────────────────────────────┐ │ │
│ │  │ Add & LayerNorm                         │ │ │
│ │  │ x = LayerNorm(x + attention(x))        │ │ │
│ │  └────────────────────────────────────────┘ │ │
│ │         ↓                                   │ │
│ │  ┌────────────────────────────────────────┐ │ │
│ │  │ Feed Forward Network                    │ │ │
│ │  │                                         │ │ │
│ │  │ FFN(x) = GELU(Linear1(x)) · Linear2    │ │ │
│ │  │         2048 → 8192 → 2048              │ │ │
│ │  │                                         │ │ │
│ │  │ GELU(x) = 0.5x(1+tanh(√(2/π)(x+0.044x³)))│ │
│ │  └────────────────────────────────────────┘ │ │
│ │         ↓                                   │ │
│ │  ┌────────────────────────────────────────┐ │ │
│ │  │ Add & LayerNorm                         │ │ │
│ │  │ x = LayerNorm(x + FFN(x))              │ │ │
│ │  └────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────┘ │
│         ↓ (repeat 22 times)                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ OUTPUT HEAD                                  │ │
│ │                                              │ │
│ │ Final LayerNorm                              │ │
│ │         ↓                                    │ │
│ │ Language Model Head: Linear(2048, 32000)     │ │
│ │         ↓                                    │ │
│ │ Logits for each token in vocabulary          │ │
│ └─────────────────────────────────────────────┘ │
│         ↓                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ TOKEN SAMPLING                               │ │
│ │                                              │ │
│ │ Temperature Scaling:                         │ │
│ │   logits = logits / temperature (0.3)        │ │
│ │                                              │ │
│ │ Softmax:                                     │ │
│ │   probs = softmax(logits)                    │ │
│ │                                              │ │
│ │ Sampling Strategy:                           │ │
│ │   - Top-k: Keep top k tokens                 │ │
│ │   - Top-p (nucleus): Keep top tokens         │ │
│ │     with cumulative prob > p                 │ │
│ │   - Sample from filtered distribution        │ │
│ │                                              │ │
│ │ Generate tokens until:                       │ │
│ │   - Max tokens reached (50)                  │ │
│ │   - Stop token encountered (</s>)            │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ POST-PROCESSING                                  │
│                                                  │
│ 1. Strip special tokens                          │
│ 2. Remove leading/trailing whitespace            │
│ 3. Capitalize first letter                       │
│ 4. Ensure proper punctuation                     │
│                                                  │
│ Raw output:                                      │
│ " i need help with my account balance"          │
│                                                  │
│ Processed:                                       │
│ "I need help with my account balance."          │
└─────────────────────────────────────────────────┘
                    ↓
OUTPUT: Natural Language Sentence
"I need help with my account balance."
```

### Quantization: Q4_K_M Explained

```
┌─────────────────────────────────────────────────┐
│ MODEL QUANTIZATION (GGUF Format)                 │
│                                                  │
│ Original (FP16):                                 │
│   16 bits per weight                             │
│   1.1B params × 16 bits = 17.6 GB              │
│                                                  │
│ Quantized (Q4_K_M):                              │
│   ~4 bits per weight (mixed precision)           │
│   1.1B params × 4 bits ≈ 4.4 GB                 │
│                                                  │
│ Savings: 75% reduction in size                   │
│ Speed: 3-4× faster inference                     │
│ Accuracy: <2% degradation                        │
│                                                  │
│ Q4_K_M Strategy:                                 │
│ • Most layers: 4-bit quantization                │
│ • Critical layers (attention): 6-bit             │
│ • K-means clustering for quantization bins      │
│ • Mixed precision for quality/speed balance      │
└─────────────────────────────────────────────────┘
```

---

## 📈 Performance Comparison Table

### Model Comparison Matrix

```
┌────────────────────────────────────────────────────────────────────────┐
│                         MODEL PERFORMANCE METRICS                       │
├──────────────┬────────────┬──────────┬────────────┬──────────┬─────────┤
│ Model        │ Parameters │ Memory   │ Inference  │ Accuracy │ Dataset │
│              │            │ Usage    │ Time       │          │         │
├──────────────┼────────────┼──────────┼────────────┼──────────┼─────────┤
│ Face         │ 65M        │ ~500MB   │ 100-200ms  │ 99.8%    │ LFW     │
│ Recognition  │ (ResNet)   │          │            │          │         │
│ (ArcFace)    │            │          │            │          │         │
├──────────────┼────────────┼──────────┼────────────┼──────────┼─────────┤
│ Voice        │ 24M        │ ~800MB   │ 200-500ms  │ 95%      │ VoxCeleb│
│ Recognition  │ (ECAPA)    │          │            │ (EER)    │         │
│ (ECAPA-TDNN) │            │          │            │          │         │
├──────────────┼────────────┼──────────┼────────────┼──────────┼─────────┤
│ Sign         │ 2.5M       │ ~2GB     │ 300-800ms  │ 85-90%   │ Custom  │
│ Recognition  │ (LSTM)     │ (with    │ (full      │          │ Banking │
│ (Landmarks)  │            │ MediaPipe│ pipeline)  │          │ Signs   │
│              │            │ models)  │            │          │         │
├──────────────┼────────────┼──────────┼────────────┼──────────┼─────────┤
│ Language     │ 1.1B       │ ~4.4GB   │ 1-3 sec    │ N/A      │ Multi-  │
│ Generation   │ (Llama)    │ (Q4_K_M) │ (CPU)      │ (Genera- │ domain  │
│ (TinyLlama)  │            │          │ 200-400ms  │  tion)   │ Chat    │
│              │            │          │ (GPU)      │          │         │
└──────────────┴────────────┴──────────┴────────────┴──────────┴─────────┘
```

### Hardware Requirements

```
┌────────────────────────────────────────────────────────────────────────┐
│                     RECOMMENDED HARDWARE SPECS                          │
├──────────────┬────────────────────┬────────────────────────────────────┤
│ Component    │ Minimum            │ Recommended                        │
├──────────────┼────────────────────┼────────────────────────────────────┤
│ CPU          │ Intel i5 / AMD R5  │ Intel i7 / AMD R7 or better       │
│              │ 4 cores            │ 8+ cores                           │
├──────────────┼────────────────────┼────────────────────────────────────┤
│ RAM          │ 8 GB               │ 16 GB or more                      │
│              │                    │ (32GB for comfortable dev)         │
├──────────────┼────────────────────┼────────────────────────────────────┤
│ GPU          │ Not required       │ NVIDIA RTX (2060+)                │
│              │ (CPU only)         │ - 10× faster sign recognition      │
│              │                    │ - Real-time frame processing       │
├──────────────┼────────────────────┼────────────────────────────────────┤
│ Storage      │ 10 GB free         │ 20 GB+ SSD                        │
│              │                    │ - Faster model loading             │
├──────────────┼────────────────────┼────────────────────────────────────┤
│ Webcam       │ 720p @ 30fps       │ 1080p @ 30fps or better           │
│              │                    │ - Better landmark detection        │
├──────────────┼────────────────────┼────────────────────────────────────┤
│ Microphone   │ Built-in           │ External USB mic                   │
│              │                    │ - Better voice quality             │
└──────────────┴────────────────────┴────────────────────────────────────┘
```

---

## 🎯 Model Training Details

### Sign Language Model Training

```
TRAINING CONFIGURATION
┌─────────────────────────────────────────────────┐
│ Hyperparameters:                                 │
│ • Optimizer: Adam                                │
│ • Learning Rate: 0.001                           │
│ • Batch Size: 32                                 │
│ • Epochs: 100 (with early stopping)              │
│ • Loss: Focal Loss (α=0.25, γ=2.0)             │
│ • Validation Split: 20%                          │
│                                                  │
│ Data Augmentation:                               │
│ • Random scaling: ±10%                           │
│ • Random rotation: ±15°                          │
│ • Random translation: ±5%                        │
│ • Temporal stretching: ±20%                      │
│ • Landmark noise: Gaussian (σ=0.01)             │
│                                                  │
│ Callbacks:                                       │
│ • EarlyStopping: patience=10                     │
│ • ModelCheckpoint: save best only                │
│ • ReduceLROnPlateau: factor=0.5, patience=5      │
│ • TensorBoard: logging                           │
└─────────────────────────────────────────────────┘

TRAINING PROGRESS (Example)
┌─────────────────────────────────────────────────┐
│ Epoch │ Train Loss │ Val Loss │ Val Acc │ LR    │
├───────┼────────────┼──────────┼─────────┼───────┤
│   1   │   2.450    │  2.123   │  45.2%  │ 1e-3  │
│   10  │   0.823    │  0.912   │  72.8%  │ 1e-3  │
│   20  │   0.412    │  0.534   │  83.1%  │ 1e-3  │
│   30  │   0.234    │  0.398   │  87.4%  │ 5e-4  │
│   40  │   0.156    │  0.321   │  89.2%  │ 5e-4  │
│   50  │   0.098    │  0.287   │  90.1%  │ 2.5e-4│
│   60  │   0.067    │  0.279   │  90.5%  │ 2.5e-4│
│  *65  │   0.052    │  0.276   │ *90.7%  │ 1.25e │
└───────┴────────────┴──────────┴─────────┴───────┘
* Best model saved at epoch 65

FINAL METRICS
┌─────────────────────────────────────────────────┐
│ Test Accuracy: 89.3%                             │
│ Precision: 88.7%                                 │
│ Recall: 87.9%                                    │
│ F1-Score: 88.3%                                  │
│                                                  │
│ Confusion Matrix (Top-3 Confusions):            │
│ • "HELP" ↔ "NEED": 5.2%                         │
│ • "ACCOUNT" ↔ "CARD": 4.1%                      │
│ • "MONEY" ↔ "BALANCE": 3.8%                     │
└─────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Foundations

### Key Equations Summary

#### 1. Cosine Similarity (Face & Voice)
```
cos(θ) = (A · B) / (||A|| × ||B||)

For normalized vectors:
cos(θ) = Σ(A_i × B_i)

Where:
• A, B: embedding vectors
• ||A||: L2 norm of A
• Range: [-1, 1]
• 1 = identical, -1 = opposite
```

#### 2. LSTM Cell Operations
```
Forget Gate:
  f_t = σ(W_f · [h_{t-1}, x_t] + b_f)

Input Gate:
  i_t = σ(W_i · [h_{t-1}, x_t] + b_i)

Cell State Candidate:
  C̃_t = tanh(W_C · [h_{t-1}, x_t] + b_C)

Cell State Update:
  C_t = f_t ⊙ C_{t-1} + i_t ⊙ C̃_t

Output Gate:
  o_t = σ(W_o · [h_{t-1}, x_t] + b_o)

Hidden State:
  h_t = o_t ⊙ tanh(C_t)

Where:
• σ: sigmoid function
• ⊙: element-wise multiplication
• W: weight matrices
• b: bias vectors
```

#### 3. Focal Loss
```
FL(p_t) = -α_t(1 - p_t)^γ log(p_t)

Where:
  p_t = { p      if y = 1
        { 1 - p  otherwise

Parameters:
• α_t: weighting factor (0.25)
• γ: focusing parameter (2.0)
• p: predicted probability
• y: true label (0 or 1)
```

#### 4. Attention Mechanism (Transformer)
```
Attention(Q, K, V) = softmax(QK^T / √d_k)V

Multi-Head:
  head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
  
  MultiHead(Q,K,V) = Concat(head_1,...,head_h)W^O

Where:
• Q: query matrix
• K: key matrix
• V: value matrix
• d_k: dimension of keys
• h: number of heads
• W: learned projection matrices
```

---

## 🎨 Visual Representation of Data Flow

### Complete System Data Flow

```
USER INPUT
    │
    ├─── Camera ────────────► Face/Sign Recognition
    │                         │
    ├─── Microphone ─────────► Voice Recognition
    │                         │
    └─── Touch/Keyboard ─────► OTP Authentication
                             │
                             ▼
                    ┌─────────────────┐
                    │  Authentication │
                    │     Layer       │
                    └─────────────────┘
                             │
                             ▼ (JWT Token)
                    ┌─────────────────┐
                    │    Dashboard    │
                    └─────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Banking    │   │ Customer     │   │  Support     │
│  Operations  │   │   Support    │   │   Tickets    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                  │                    │
        │                  ▼                    │
        │          Sign Recognition             │
        │                  │                    │
        │                  ├─► Landmarks        │
        │                  ├─► LSTM Model       │
        │                  ├─► Keywords         │
        │                  └─► NLG → Query      │
        │                          │            │
        └──────────────────────────┼────────────┘
                                   ▼
                           ┌──────────────┐
                           │   Database   │
                           │  PostgreSQL  │
                           └──────────────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │     Email    │
                           │   Service    │
                           └──────────────┘
```

---

**Document Version:** 1.0  
**Last Updated:** November 13, 2025  
**Purpose:** Panel Demonstration Visual Aid
