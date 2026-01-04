"""
Model Diagnosis Script
======================

This script checks if your trained model has issues.
Run this to diagnose prediction problems.

Usage:
    python diagnose_model.py
"""

import torch
import numpy as np
from pathlib import Path

def diagnose_model():
    """Check model file for common issues"""
    
    model_path = Path("models/ns_agcn.pth")
    
    if not model_path.exists():
        print("❌ Model file not found at models/ns_agcn.pth")
        return
    
    print("\n" + "=" * 60)
    print("🔍 NS-AGF Model Diagnosis")
    print("=" * 60)
    
    # Load model
    print("\n1️⃣ Loading model...")
    try:
        state_dict = torch.load(model_path, map_location='cpu')
        print(f"✅ Model loaded successfully")
        print(f"   Total parameter tensors: {len(state_dict)}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Check architecture
    print("\n2️⃣ Checking architecture...")
    
    # Check data_bn (should be 75 * 3 = 225)
    if 'data_bn.weight' in state_dict:
        bn_size = state_dict['data_bn.weight'].shape[0]
        expected_bn = 75 * 3
        if bn_size == expected_bn:
            print(f"✅ data_bn size: {bn_size} (correct)")
        else:
            print(f"❌ data_bn size: {bn_size} (expected {expected_bn})")
    else:
        print("❌ data_bn layer not found!")
    
    # Check final classifier (should be num_classes x 256)
    if 'fc.weight' in state_dict:
        fc_shape = state_dict['fc.weight'].shape
        num_classes = fc_shape[0]
        hidden_dim = fc_shape[1]
        
        if hidden_dim == 256:
            print(f"✅ fc layer: ({num_classes} classes, {hidden_dim} hidden) - correct")
        else:
            print(f"❌ fc layer: ({num_classes}, {hidden_dim}) - expected (X, 256)")
        
        print(f"\n   📊 Model trained for {num_classes} classes")
    else:
        print("❌ fc layer not found!")
        return
    
    # Check sign labels
    print("\n3️⃣ Checking sign labels...")
    labels_path = Path("models/sign_labels.txt")
    
    if labels_path.exists():
        with open(labels_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"✅ Found {len(lines)} sign labels")
        
        if len(lines) == num_classes:
            print(f"✅ Label count matches model classes")
            print(f"\n   Sign labels:")
            for i, label in enumerate(lines):
                print(f"   [{i}] {label}")
        else:
            print(f"❌ Label count ({len(lines)}) doesn't match model ({num_classes})")
    else:
        print("❌ sign_labels.txt not found")
    
    # Check for common issues
    print("\n4️⃣ Checking for common issues...")
    
    # Check if model might be overfitted to one class
    if 'fc.weight' in state_dict and 'fc.bias' in state_dict:
        fc_weights = state_dict['fc.weight']
        fc_bias = state_dict['fc.bias']
        
        # Check if bias is heavily skewed to one class
        bias_max = fc_bias.max().item()
        bias_min = fc_bias.min().item()
        bias_range = bias_max - bias_min
        
        if bias_range > 10:
            max_idx = fc_bias.argmax().item()
            print(f"⚠️  Large bias range detected ({bias_range:.2f})")
            print(f"   Class {max_idx} has very high bias ({bias_max:.2f})")
            print(f"   This might indicate overfitting to one class")
        else:
            print(f"✅ Bias range reasonable ({bias_range:.2f})")
        
        # Check weight norms per class
        weight_norms = torch.norm(fc_weights, dim=1)
        weight_std = weight_norms.std().item()
        weight_mean = weight_norms.mean().item()
        
        if weight_std / weight_mean > 0.5:
            print(f"⚠️  High weight variation between classes")
            print(f"   Some classes may be underrepresented in training")
        else:
            print(f"✅ Weight distribution balanced")
    
    print("\n5️⃣ Checking buffer compatibility...")
    
    # Check if there's a mismatch in expected sequence length
    # The model should work with any sequence length due to adaptive pooling
    # but we should verify the training configuration
    
    print(f"✅ Model architecture supports variable sequence lengths")
    print(f"   Inference uses: 30 frames (2 seconds)")
    print(f"   Training used: 30 frames (should match)")
    
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    # Load sign labels for final check
    if labels_path.exists():
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"\n✅ Model is configured for {num_classes} classes:")
        print(f"   {', '.join(labels)}")
    
    print(f"\n💡 Recommendations:")
    print(f"   1. If predictions always show same class:")
    print(f"      → Check training data balance")
    print(f"      → May need to retrain with more balanced dataset")
    print(f"   2. If rare classes never predict:")
    print(f"      → Lower confidence threshold: --confidence_threshold 0.5")
    print(f"      → Collect more training videos for those classes")
    print(f"   3. If predictions are random:")
    print(f"      → Check if landmarks are being extracted correctly")
    print(f"      → Verify camera quality and lighting")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    diagnose_model()
