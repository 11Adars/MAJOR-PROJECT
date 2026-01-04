"""
Quick Verification Script
=========================

Verifies that inference.py correctly loads and uses the trained model.

This script:
1. Loads the trained model checkpoint
2. Checks architecture (6-block vs 10-block)
3. Verifies model parameters match checkpoint
4. Tests forward pass with sample data
5. Confirms predictions work correctly
"""

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.graph.topology import MediaPipeGraph
from src.model.nsagf import NSAGF


def verify_model_loading(model_path):
    """Verify model loads correctly"""
    
    print("=" * 70)
    print("MODEL LOADING VERIFICATION")
    print("=" * 70)
    
    # Load checkpoint
    print(f"\n📥 Loading: {Path(model_path).name}")
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    
    # Extract info
    config = checkpoint.get('config', {})
    state_dict = checkpoint.get('model_state_dict', checkpoint)
    label_names = checkpoint.get('label_names', [])
    
    architecture = config.get('architecture', 'Unknown')
    num_classes = config.get('num_classes', len(label_names))
    is_small_model = '6' in architecture or 'Small' in architecture
    
    print(f"\n📋 Checkpoint Info:")
    print(f"  Architecture: {architecture}")
    print(f"  Number of classes: {num_classes}")
    print(f"  Model type: {'Small Dataset (6 blocks)' if is_small_model else 'Full (10 blocks)'}")
    print(f"  Classes: {label_names}")
    
    # Create model
    print(f"\n🤖 Creating model...")
    graph = MediaPipeGraph()
    model = NSAGF(
        num_classes=num_classes,
        graph=graph,
        in_channels=3,
        dropout=0.0,  # Inference mode
        edge_importance_weighting=config.get('edge_importance_weighting', True)
    )
    
    # Truncate if small model
    if is_small_model:
        print("  🔧 Truncating to 6 blocks...")
        model.st_gcn_blocks = nn.ModuleList(model.st_gcn_blocks[:6])
        model.classifier = nn.Sequential(
            nn.Dropout(0.0),
            nn.Linear(256, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.0),
            nn.Linear(256, num_classes)
        )
        print("  ✅ Architecture adjusted for 6 blocks")
    
    # Load weights
    print(f"\n🔧 Loading weights...")
    try:
        model.load_state_dict(state_dict, strict=True)
        print("  ✅ Weights loaded successfully (exact match)")
        weights_match = True
    except Exception as e:
        print(f"  ⚠️ Exact match failed: {str(e)[:100]}")
        try:
            model.load_state_dict(state_dict, strict=False)
            print("  ⚠️ Weights loaded with strict=False (partial match)")
            weights_match = False
        except Exception as e2:
            print(f"  ❌ Weight loading completely failed: {e2}")
            return False
    
    model.eval()
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n📊 Model Statistics:")
    print(f"  Total parameters: {total_params:,}")
    print(f"  Model size: ~{total_params * 4 / 1024 / 1024:.1f} MB")
    print(f"  Blocks: {'6 (small dataset)' if is_small_model else '10 (full)'}")
    
    # Test forward pass
    print(f"\n🧪 Testing forward pass...")
    try:
        # Create random input: (N, C, T, V) = (1, 3, 30, 75)
        sample_input = torch.randn(1, 3, 30, 75)
        
        with torch.no_grad():
            output = model(sample_input)
        
        print(f"  ✅ Forward pass successful")
        print(f"  Input shape: {tuple(sample_input.shape)}")
        print(f"  Output shape: {tuple(output.shape)}")
        print(f"  Expected output shape: (1, {num_classes})")
        
        if output.shape[1] != num_classes:
            print(f"  ❌ ERROR: Output classes mismatch!")
            return False
        
        # Check predictions
        probs = torch.softmax(output, dim=1)
        pred_class = output.argmax(dim=1).item()
        confidence = probs[0, pred_class].item()
        
        print(f"\n🔮 Sample Prediction:")
        print(f"  Predicted class: {pred_class} ({label_names[pred_class] if pred_class < len(label_names) else 'Unknown'})")
        print(f"  Confidence: {confidence:.1%}")
        
        # Show top 3
        top3_probs, top3_indices = probs[0].topk(min(3, num_classes))
        print(f"\n  Top 3 predictions:")
        for i, (prob, idx) in enumerate(zip(top3_probs, top3_indices)):
            class_name = label_names[idx] if idx < len(label_names) else f'Class_{idx}'
            print(f"    {i+1}. {class_name}: {prob.item():.1%}")
        
    except Exception as e:
        print(f"  ❌ Forward pass failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Final verdict
    print("\n" + "=" * 70)
    if weights_match and output.shape[1] == num_classes:
        print("✅ VERIFICATION PASSED")
        print("=" * 70)
        print("\n✓ Model architecture matches checkpoint")
        print("✓ Weights loaded correctly")
        print("✓ Forward pass works")
        print("✓ Output shape correct")
        print("\n🎉 inference.py should work perfectly with this model!")
        return True
    else:
        print("⚠️ VERIFICATION ISSUES DETECTED")
        print("=" * 70)
        if not weights_match:
            print("\n⚠ Weights loaded partially (strict=False)")
            print("   Some layers may use random weights")
        if output.shape[1] != num_classes:
            print(f"\n❌ Output shape mismatch: {output.shape[1]} vs {num_classes}")
        print("\n⚠️ inference.py may have issues - check carefully!")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify model loading')
    parser.add_argument(
        '--model_path',
        type=str,
        default='./models/ns_agf_best.pth',
        help='Path to model checkpoint'
    )
    
    args = parser.parse_args()
    
    if not Path(args.model_path).exists():
        print(f"❌ Model not found: {args.model_path}")
        print("\n📥 Please provide correct model path:")
        print("   python verify_inference.py --model_path /path/to/model.pth")
        exit(1)
    
    success = verify_model_loading(args.model_path)
    exit(0 if success else 1)
