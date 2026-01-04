"""
NS-AGF Two-Stream Training Script
===================================

Trains TwoStreamNSAGF (Joint + Bone streams) for improved accuracy.

Expected Improvements:
- Single-stream accuracy: 75-85%
- Two-stream accuracy: 80-90% (+5-8% boost)

Key Features:
- Joint stream: Learns from absolute joint positions
- Bone stream: Learns from relative bone vectors
- Late fusion: Combines both streams before classification
- Larger model: ~8-10M parameters (2x single-stream)
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import CosineAnnealingLR
from pathlib import Path
from tqdm import tqdm
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add src to path
try:
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
except NameError:
    script_dir = Path.cwd()
    project_root = script_dir

sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from src.graph.topology import MediaPipeGraph
from src.model.nsagf import create_model

# ============================================================================
# CONFIGURATION
# ============================================================================

BATCH_SIZE = 12  # Slightly smaller for larger model
LEARNING_RATE = 0.0003  # Lower for stability
NUM_EPOCHS = 200  # More epochs for convergence
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DROPOUT_RATE = 0.3
LABEL_SMOOTHING = 0.1
WEIGHT_DECAY = 5e-4
GRADIENT_CLIP = 0.5
PATIENCE = 25

USE_AMP = True
EDGE_IMPORTANCE_WEIGHTING = True

print("=" * 70)
print("NS-AGF TWO-STREAM Training Configuration")
print("=" * 70)
print(f"Architecture: Two-Stream (Joint + Bone)")
print(f"Device: {DEVICE}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Learning Rate: {LEARNING_RATE}")
print(f"Epochs: {NUM_EPOCHS}")
print(f"Dropout: {DROPOUT_RATE}")
print(f"Label Smoothing: {LABEL_SMOOTHING}")
print(f"Expected Accuracy: 80-90% (+5-8% vs single-stream)")
print("=" * 70)


# ============================================================================
# DATASET
# ============================================================================

class SignLanguageDataset(Dataset):
    """Dataset for sign language sequences."""
    
    def __init__(self, features, labels, augment=False):
        self.features = torch.FloatTensor(features)  # (N, T, V, C)
        self.labels = torch.LongTensor(labels)
        self.augment = augment
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        x = self.features[idx]  # (T, V, C)
        y = self.labels[idx]
        
        # Augmentation during training
        if self.augment:
            x = self._augment(x)
        
        # Transpose to (C, T, V) for model input
        x = x.permute(2, 0, 1)  # (T, V, C) → (C, T, V)
        
        return x, y
    
    def _augment(self, x):
        """Apply on-the-fly augmentation."""
        # Random temporal shift
        if torch.rand(1) < 0.3:
            shift = torch.randint(-2, 3, (1,)).item()
            x = torch.roll(x, shift, dims=0)
        
        # Random noise
        if torch.rand(1) < 0.3:
            noise = torch.randn_like(x) * 0.005
            x = x + noise
        
        return x


# ============================================================================
# LABEL SMOOTHING LOSS
# ============================================================================

class LabelSmoothingCrossEntropy(nn.Module):
    """Cross-entropy with label smoothing."""
    
    def __init__(self, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing
    
    def forward(self, pred, target):
        n_classes = pred.size(-1)
        log_probs = F.log_softmax(pred, dim=-1)
        
        # Smooth labels
        smooth_target = torch.zeros_like(log_probs)
        smooth_target.fill_(self.smoothing / (n_classes - 1))
        smooth_target.scatter_(1, target.unsqueeze(1), 1.0 - self.smoothing)
        
        loss = (-smooth_target * log_probs).sum(dim=-1).mean()
        return loss


# ============================================================================
# TRAINING & EVALUATION
# ============================================================================

def train_epoch(model, train_loader, criterion, optimizer, scaler, epoch):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc=f"Epoch {epoch+1} [Train]")
    
    for inputs, targets in pbar:
        inputs = inputs.to(DEVICE)
        targets = targets.to(DEVICE)
        
        optimizer.zero_grad()
        
        # Mixed precision training
        if USE_AMP:
            with torch.cuda.amp.autocast():
                outputs = model(inputs)
                loss = criterion(outputs, targets)
            
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            optimizer.step()
        
        # Statistics
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        correct += (predicted == targets).sum().item()
        total += targets.size(0)
        
        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'acc': f'{100.*correct/total:.2f}%'
        })
    
    avg_loss = total_loss / len(train_loader)
    accuracy = 100. * correct / total
    
    return avg_loss, accuracy


def validate(model, val_loader, criterion):
    """Validate model."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, targets in tqdm(val_loader, desc="Validation"):
            inputs = inputs.to(DEVICE)
            targets = targets.to(DEVICE)
            
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            correct += (predicted == targets).sum().item()
            total += targets.size(0)
    
    avg_loss = total_loss / len(val_loader)
    accuracy = 100. * correct / total
    
    return avg_loss, accuracy


def test_model(model, test_loader, label_names):
    """Final evaluation on test set."""
    model.eval()
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for inputs, targets in tqdm(test_loader, desc="Testing"):
            inputs = inputs.to(DEVICE)
            targets = targets.to(DEVICE)
            
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())
    
    # Metrics
    accuracy = accuracy_score(all_targets, all_preds)
    report = classification_report(all_targets, all_preds, 
                                    target_names=label_names, 
                                    zero_division=0)
    cm = confusion_matrix(all_targets, all_preds)
    
    return accuracy, report, cm


# ============================================================================
# MAIN TRAINING
# ============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, 
                        default='/kaggle/working/processed_data_improved',
                        help='Directory with processed data')
    parser.add_argument('--output_dir', type=str, default='/kaggle/working',
                        help='Output directory for checkpoints')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE)
    parser.add_argument('--lr', type=float, default=LEARNING_RATE)
    parser.add_argument('--epochs', type=int, default=NUM_EPOCHS)
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n📂 Loading dataset...")
    data_dir = Path(args.data_dir)
    
    X = np.load(data_dir / 'features.npy')  # (N, T, V, C)
    y = np.load(data_dir / 'labels.npy')
    label_names = np.load(data_dir / 'label_names.npy', allow_pickle=True)
    
    print(f"✅ Loaded {len(X)} samples")
    print(f"   Shape: {X.shape}")
    print(f"   Classes: {len(label_names)}")
    print(f"   Labels: {label_names}")
    
    # Split data: 70% train, 15% val, 15% test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp  # 0.176 * 0.85 ≈ 0.15
    )
    
    print(f"\n📊 Data Split:")
    print(f"   Train: {len(X_train)} samples")
    print(f"   Val:   {len(X_val)} samples")
    print(f"   Test:  {len(X_test)} samples")
    
    # Create datasets
    train_dataset = SignLanguageDataset(X_train, y_train, augment=True)
    val_dataset = SignLanguageDataset(X_val, y_val, augment=False)
    test_dataset = SignLanguageDataset(X_test, y_test, augment=False)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size,
                               shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size,
                             shuffle=False, num_workers=2, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size,
                              shuffle=False, num_workers=2, pin_memory=True)
    
    # Create model
    print("\n🔧 Creating Two-Stream NS-AGF model...")
    graph = MediaPipeGraph()
    model = create_model(
        num_classes=len(label_names),
        graph=graph,
        dropout=DROPOUT_RATE,
        two_stream=True  # ← Enable two-stream architecture
    )
    model = model.to(DEVICE)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"📊 Model parameters: {total_params:,} (~{total_params*4/1024/1024:.1f}MB)")
    
    # Loss, optimizer, scheduler
    criterion = LabelSmoothingCrossEntropy(smoothing=LABEL_SMOOTHING)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, 
                                   weight_decay=WEIGHT_DECAY)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.cuda.amp.GradScaler() if USE_AMP else None
    
    # Training loop
    print(f"\n🚀 Starting training...")
    best_val_acc = 0
    patience_counter = 0
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    for epoch in range(args.epochs):
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion,
                                             optimizer, scaler, epoch)
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion)
        
        # Update scheduler
        scheduler.step()
        
        # Log
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        print(f"\nEpoch {epoch+1}/{args.epochs}")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%")
        print(f"  LR: {scheduler.get_last_lr()[0]:.6f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'label_names': label_names,
                'num_classes': len(label_names),
                'architecture': 'two_stream',
                'config': {
                    'dropout': DROPOUT_RATE,
                    'num_nodes': 75,
                    'num_features': 3,
                    'sequence_length': X.shape[1]
                }
            }
            
            torch.save(checkpoint, output_dir / 'ns_agf_two_stream_best.pth')
            print(f"  ✅ Saved best model (Val Acc: {val_acc:.2f}%)")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= PATIENCE:
            print(f"\n⏹️  Early stopping triggered (patience={PATIENCE})")
            break
    
    # Final evaluation
    print("\n🎯 Final Evaluation on Test Set...")
    checkpoint = torch.load(output_dir / 'ns_agf_two_stream_best.pth', 
                           map_location=DEVICE, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    test_acc, test_report, cm = test_model(model, test_loader, label_names)
    
    print(f"\n{'='*70}")
    print(f"FINAL TEST ACCURACY: {test_acc*100:.2f}%")
    print(f"{'='*70}")
    print("\nClassification Report:")
    print(test_report)
    
    # Save results
    results = {
        'test_accuracy': float(test_acc),
        'best_val_accuracy': float(best_val_acc),
        'history': history,
        'confusion_matrix': cm.tolist(),
        'classification_report': test_report
    }
    
    with open(output_dir / 'two_stream_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Training complete!")
    print(f"📁 Best model: {output_dir / 'ns_agf_two_stream_best.pth'}")
    print(f"📊 Results: {output_dir / 'two_stream_results.json'}")


if __name__ == '__main__':
    main()


# ============================================================================
# JUPYTER/COLAB HELPER FUNCTION
# ============================================================================

def train_in_notebook(data_dir='/kaggle/working/processed_data_improved',
                     output_dir='/kaggle/working',
                     batch_size=BATCH_SIZE,
                     lr=LEARNING_RATE,
                     epochs=NUM_EPOCHS):
    """
    Helper function to train directly from Jupyter/Colab notebooks.
    
    Usage:
        # In Jupyter/Colab cell:
        from train_two_stream import train_in_notebook
        train_in_notebook(
            data_dir='/kaggle/working/processed_data_improved',
            epochs=200
        )
    """
    import sys
    sys.argv = [
        'train_two_stream.py',
        '--data_dir', data_dir,
        '--output_dir', output_dir,
        '--batch_size', str(batch_size),
        '--lr', str(lr),
        '--epochs', str(epochs)
    ]
    main()
