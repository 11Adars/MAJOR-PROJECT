"""
Quick Test Script for Trained NS-AGF Model
===========================================

This script tests your newly trained model to verify it works correctly.

Usage:
    python test_trained_model.py --model_path ./models/ns_agf_best.pth

Features:
1. Loads trained model and verifies architecture
2. Tests on sample data or test set
3. Shows predictions with confidence scores
4. Validates model performance

What to check:
- Model loads without errors
- Predictions make sense (not random)
- Confidence scores are reasonable (50-95%)
- Test accuracy matches training report
"""

import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.graph.topology import MediaPipeGraph
from src.model.nsagf import NSAGF


def load_trained_model(model_path, device='cuda'):
    """Load trained NS-AGF model from checkpoint"""
    
    print("=" * 70)
    print("LOADING TRAINED MODEL")
    print("=" * 70)
    
    # Load checkpoint
    print(f"\n📥 Loading checkpoint: {Path(model_path).name}")
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    # Extract info
    config = checkpoint.get('config', {})
    num_classes = config.get('num_classes', len(checkpoint.get('label_names', [])))
    label_names = checkpoint.get('label_names', [f'Class_{i}' for i in range(num_classes)])
    epoch = checkpoint.get('epoch', 'unknown')
    val_acc = checkpoint.get('val_acc', 0)
    
    print(f"  Epoch: {epoch}")
    print(f"  Validation Accuracy: {val_acc:.2f}%")
    print(f"  Number of classes: {num_classes}")
    print(f"  Classes: {label_names}")
    
    # Check if it's a small dataset model (6 blocks) or full model (10 blocks)
    architecture = config.get('architecture', 'Unknown')
    is_small_model = '6' in architecture or 'Small' in architecture
    
    print(f"  Architecture: {architecture}")
    print(f"  Model Type: {'Small Dataset (6 blocks)' if is_small_model else 'Full (10 blocks)'}")
    
    # Initialize graph
    graph = MediaPipeGraph()
    
    # Create model
    print("\n🤖 Creating model...")
    dropout = config.get('dropout', 0.3)
    model = NSAGF(
        num_classes=num_classes,
        graph=graph,
        in_channels=3,
        dropout=0.0,  # NO dropout for inference!
        edge_importance_weighting=config.get('edge_importance_weighting', True)
    )
    
    # If small model (6 blocks), truncate architecture
    if is_small_model:
        print("  Detected small model - truncating to 6 blocks...")
        model.st_gcn_blocks = nn.ModuleList(model.st_gcn_blocks[:6])
        
        # Update classifier to match 6-block output (256 channels)
        model.classifier = nn.Sequential(
            nn.Dropout(0.0),  # No dropout for inference
            nn.Linear(256, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.0),
            nn.Linear(256, num_classes)
        )
        print("  Updated classifier for 6-block architecture (256 channels)")
    
    # Load weights
    try:
        model.load_state_dict(checkpoint['model_state_dict'])
        print("  ✅ Weights loaded successfully")
    except Exception as e:
        print(f"  ⚠️ Weight loading error: {e}")
        print("  Attempting partial load...")
        model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        print("  ⚠️ Partial weights loaded (some layers may be randomly initialized)")
    
    model.to(device)
    model.eval()
    
    print(f"  ✅ Model ready for inference")
    print(f"  Device: {device}")
    
    return model, label_names


def test_on_preprocessed_data(model, data_dir, label_names, device='cuda'):
    """Test model on preprocessed test set"""
    
    print("\n" + "=" * 70)
    print("TESTING ON PREPROCESSED DATA")
    print("=" * 70)
    
    # Load test data
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("   Cannot run test on preprocessed data")
        return None, None
    
    print(f"\n📁 Loading data from: {data_path}")
    
    try:
        features = np.load(data_path / 'features.npy')
        labels = np.load(data_path / 'labels.npy')
        print(f"  Features: {features.shape}")
        print(f"  Labels: {labels.shape}")
    except FileNotFoundError as e:
        print(f"❌ Required files not found: {e}")
        return None, None
    
    # Create test split (same as training)
    from sklearn.model_selection import train_test_split
    _, X_temp, _, y_temp = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    _, X_test, _, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"\n📊 Test set: {len(X_test)} samples")
    
    # Convert to tensors
    X_test_tensor = torch.FloatTensor(X_test).permute(0, 3, 1, 2)  # (N,T,V,C) -> (N,C,T,V)
    y_test_tensor = torch.LongTensor(y_test)
    
    # Run inference
    print("\n🔮 Running predictions...")
    all_preds = []
    all_probs = []
    
    model.eval()
    with torch.no_grad():
        batch_size = 32
        for i in tqdm(range(0, len(X_test_tensor), batch_size)):
            batch = X_test_tensor[i:i+batch_size].to(device)
            outputs = model(batch)
            probs = torch.softmax(outputs, dim=1)
            preds = outputs.argmax(dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, all_preds)
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"\n🎯 Test Accuracy: {accuracy * 100:.2f}%")
    
    # Per-class accuracy
    print("\n📊 Per-Class Performance:")
    for i, class_name in enumerate(label_names):
        class_mask = y_test == i
        if class_mask.sum() > 0:
            class_acc = (all_preds[class_mask] == i).mean()
            class_conf = all_probs[class_mask, i].mean()
            print(f"  {class_name:20s}: Acc={class_acc*100:5.1f}%  Avg Conf={class_conf*100:5.1f}%")
    
    # Show some predictions
    print("\n🔍 Sample Predictions:")
    for i in range(min(10, len(all_preds))):
        true_label = label_names[y_test[i]]
        pred_label = label_names[all_preds[i]]
        confidence = all_probs[i, all_preds[i]] * 100
        status = "✅" if all_preds[i] == y_test[i] else "❌"
        print(f"  {status} True: {true_label:15s} | Pred: {pred_label:15s} | Conf: {confidence:5.1f}%")
    
    # Classification report
    print("\n📋 Detailed Classification Report:")
    report = classification_report(
        y_test, all_preds,
        target_names=label_names,
        digits=3,
        zero_division=0
    )
    print(report)
    
    return accuracy, all_preds


def test_on_single_sample(model, label_names, device='cuda'):
    """Test model on a random synthetic sample"""
    
    print("\n" + "=" * 70)
    print("TESTING ON RANDOM SAMPLE (SANITY CHECK)")
    print("=" * 70)
    
    print("\n🎲 Generating random sample...")
    # Create random sample: (1, C=3, T=30, V=75)
    sample = torch.randn(1, 3, 30, 75).to(device)
    
    print(f"  Input shape: {tuple(sample.shape)}")
    
    # Run inference
    model.eval()
    with torch.no_grad():
        output = model(sample)
        probs = torch.softmax(output, dim=1)
        pred_class = output.argmax(dim=1).item()
        confidence = probs[0, pred_class].item() * 100
    
    print(f"\n🔮 Prediction:")
    print(f"  Class: {label_names[pred_class]}")
    print(f"  Confidence: {confidence:.2f}%")
    
    # Show top-5 predictions
    top5_probs, top5_indices = probs[0].topk(min(5, len(label_names)))
    print(f"\n📊 Top-5 Predictions:")
    for i, (prob, idx) in enumerate(zip(top5_probs, top5_indices)):
        print(f"  {i+1}. {label_names[idx]:15s}: {prob.item()*100:5.1f}%")
    
    print("\n✅ Model forward pass successful!")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Test Trained NS-AGF Model')
    parser.add_argument(
        '--model_path',
        type=str,
        default='./models/ns_agf_best.pth',
        help='Path to trained model checkpoint'
    )
    parser.add_argument(
        '--data_dir',
        type=str,
        default='./output',
        help='Path to preprocessed data (features.npy, labels.npy)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cuda' if torch.cuda.is_available() else 'cpu',
        help='Device to use (cuda/cpu)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("NS-AGF MODEL TESTING")
    print("=" * 70)
    print(f"Model: {args.model_path}")
    print(f"Data: {args.data_dir}")
    print(f"Device: {args.device}")
    
    # Load model
    model, label_names = load_trained_model(args.model_path, args.device)
    
    # Test 1: Random sample (sanity check)
    test_on_single_sample(model, label_names, args.device)
    
    # Test 2: Preprocessed test set (if available)
    if Path(args.data_dir).exists():
        accuracy, predictions = test_on_preprocessed_data(
            model, args.data_dir, label_names, args.device
        )
        
        if accuracy is not None:
            if accuracy > 0.7:
                print("\n✅ EXCELLENT! Model performs well (>70% accuracy)")
            elif accuracy > 0.5:
                print("\n⚠️ MODERATE: Model is learning but needs improvement (50-70% accuracy)")
            else:
                print("\n❌ POOR: Model needs more training or data (<50% accuracy)")
    else:
        print(f"\n⚠️ Data directory not found: {args.data_dir}")
        print("   Skipping test set evaluation")
    
    print("\n" + "=" * 70)
    print("✅ TESTING COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. If accuracy is good (>70%), use inference.py for real-time testing")
    print("  2. If accuracy is poor (<50%), retrain with more data or different hyperparameters")
    print("  3. Check confusion matrix to see which signs are confused")
    print("  4. Test with real camera: python inference.py --model_path <model_path>")


if __name__ == "__main__":
    main()
