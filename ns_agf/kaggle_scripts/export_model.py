"""
Model Export Script for Kaggle
================================

This script prepares the trained model for download and use in local VS Code.

Usage in Kaggle:
    %run export_model.py
"""

import os
import torch
import json
from pathlib import Path


# ==================== CONFIGURATION ====================
MODEL_PATH = "/kaggle/working/ns_agcn_bankassist.pth"
OUTPUT_DIR = "/kaggle/working/"
CHECKPOINT_DIR = "/kaggle/working/checkpoints/"


def export_model():
    """Export model with metadata"""
    print("=" * 60)
    print("NS-AGF Model Export")
    print("=" * 60)
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        print("   Make sure training completed successfully!")
        return
    
    print(f"\n✅ Found model at {MODEL_PATH}")
    
    # Load model to verify
    try:
        state_dict = torch.load(MODEL_PATH, map_location='cpu')
        print(f"✅ Model loaded successfully")
        print(f"   Model contains {len(state_dict)} parameter tensors")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Create metadata
    metadata = {
        'model_type': 'NS-AGF 2s-AGCN',
        'num_nodes': 75,
        'num_features': 3,
        'architecture': 'Two-Stream Adaptive Graph Convolutional Network',
        'dataset': 'WLASL',
        'framework': 'PyTorch',
        'input_shape': '(N, 3, 30, 75, 1)',
        'output_shape': '(N, num_classes)',
        'usage': 'Load with torch.load() and feed MediaPipe landmarks'
    }
    
    # Save metadata
    metadata_path = os.path.join(OUTPUT_DIR, "model_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to {metadata_path}")
    
    # Create README for model usage
    readme_content = """# NS-AGF Model - Usage Instructions

## Model Information
- **Type**: Two-Stream Adaptive Graph Convolutional Network (2s-AGCN)
- **Input**: MediaPipe Holistic landmarks (75 nodes, 3 features)
- **Output**: Sign language class predictions

## Input Format
The model expects input tensors of shape: `(N, C, T, V, M)`
- N: Batch size
- C: Number of channels (3 for x, y, z coordinates)
- T: Temporal dimension (30 frames)
- V: Number of vertices (75 nodes)
- M: Number of people (1)

## Loading in VS Code (Local)

```python
import torch
from ns_agf.src.model.agcn import Model

# Load model
model = Model(
    num_class=100,  # Adjust based on your dataset
    num_point=75,
    num_person=1,
    graph_args={'labeling_mode': 'spatial'},
    in_channels=3
)

# Load weights
model.load_state_dict(torch.load('ns_agcn_bankassist.pth', map_location='cpu'))
model.eval()

# Use for inference
# See ns_agf/inference.py for complete example
```

## MediaPipe Landmark Extraction

The model uses a 75-node subgraph from MediaPipe Holistic:
- Nodes 0-32: Pose landmarks
- Nodes 33-53: Left hand landmarks
- Nodes 54-74: Right hand landmarks

See `ns_agf/src/graph/topology.py` for node definitions.

## Integration

This model is designed to be used with the NS-AGF inference pipeline.
See `ns_agf/inference.py` for real-time camera integration.

## Citation

If you use this model in research, please cite:
[Your paper reference here]
"""
    
    readme_path = os.path.join(OUTPUT_DIR, "MODEL_README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ README saved to {readme_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📦 Export Summary")
    print("=" * 60)
    print(f"✅ Model file: {MODEL_PATH}")
    print(f"✅ Metadata: {metadata_path}")
    print(f"✅ README: {readme_path}")
    
    # File sizes
    model_size = os.path.getsize(MODEL_PATH) / (1024 * 1024)  # MB
    print(f"\n📊 Model size: {model_size:.2f} MB")
    
    # Instructions
    print("\n" + "=" * 60)
    print("📥 Download Instructions")
    print("=" * 60)
    print("1. Go to the 'Output' tab in this Kaggle notebook")
    print("2. Find 'ns_agcn_bankassist.pth'")
    print("3. Option A: Download directly")
    print("4. Option B: Click 'Create New Model' to save as Kaggle Model")
    print("   - This allows automatic download via kagglehub in VS Code")
    print("   - See ns_agf/src/utils/model_loader.py for usage")
    print("\n✨ Export complete!")


if __name__ == "__main__":
    export_model()
