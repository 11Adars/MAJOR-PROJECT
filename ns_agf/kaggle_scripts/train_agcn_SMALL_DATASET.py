"""
NS-AGF Training Script - OPTIMIZED FOR SMALL DATASETS
======================================================

This version is specifically tuned for training with LIMITED DATA:
- Small dataset (50-80 samples per class)
- Prevents overfitting
- Simplified architecture
- Conservative hyperparameters

Key Differences from Professional Version:
1. Smaller model (6 ST-GCN blocks instead of 10)
2. Lower dropout (0.3 instead of 0.5)
3. Lower label smoothing (0.1 instead of 0.25)
4. Simple learning rate decay (no cosine annealing)
5. More aggressive early stopping
6. Data augmentation strategies

Expected Results with Small Dataset:
- Training accuracy: 85-90%
- Validation accuracy: 75-85%
- Test accuracy: 70-80%
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import StepLR
from pathlib import Path
from tqdm import tqdm
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add src to path for imports
try:
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
except NameError:
    script_dir = Path.cwd()
    project_root = script_dir
    if (script_dir / 'src').exists():
        project_root = script_dir
    elif (script_dir.parent / 'src').exists():
        project_root = script_dir.parent

sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from src.graph.topology import MediaPipeGraph
from src.model.nsagf import NSAGF

# ============================================================================
# CONFIGURATION - OPTIMIZED FOR SMALL DATASETS
# ============================================================================

BATCH_SIZE = 16  # Smaller batch for small dataset
LEARNING_RATE = 0.0005  # Lower learning rate
NUM_EPOCHS = 150  # Fewer epochs to prevent overfitting
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DROPOUT_RATE = 0.3  # Lower dropout (less aggressive)
LABEL_SMOOTHING = 0.1  # Lower label smoothing
WEIGHT_DECAY = 5e-4  # Lower weight decay
GRADIENT_CLIP = 0.5  # Lower gradient clipping
PATIENCE = 20  # More aggressive early stopping

# Mixed precision
USE_AMP = True

# Model architecture - SMALLER MODEL FOR SMALL DATASET
EDGE_IMPORTANCE_WEIGHTING = True
NUM_ST_GCN_BLOCKS = 6  # Reduced from 10 (smaller model)
IN_CHANNELS = 3
NUM_NODES = 75

print("=" * 70)
print("NS-AGF SMALL DATASET Training Configuration")
print("=" * 70)
print(f"⚠️  OPTIMIZED FOR SMALL DATASETS (50-80 samples/class)")
print("=" * 70)
print(f"Device: {DEVICE}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Learning Rate: {LEARNING_RATE}")
print(f"Epochs: {NUM_EPOCHS}")
print(f"Dropout (Training): {DROPOUT_RATE}")
print(f"Label Smoothing: {LABEL_SMOOTHING}")
print(f"Weight Decay: {WEIGHT_DECAY}")
print(f"Gradient Clip: {GRADIENT_CLIP}")
print(f"Early Stopping Patience: {PATIENCE}")
print(f"ST-GCN Blocks: {NUM_ST_GCN_BLOCKS} (reduced for small data)")
print("=" * 70)


# ============================================================================
# DATASET WITH AUGMENTATION
# ============================================================================

class SignLanguageDataset(Dataset):
    """Dataset with optional augmentation for small datasets"""
    
    def __init__(self, features, labels, augment=False):
        self.features = torch.FloatTensor(features)
        self.labels = torch.LongTensor(labels)
        self.augment = augment
        
        print(f"  Dataset initialized: {len(self)} samples (augment={augment})")
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        x = self.features[idx].permute(2, 0, 1)  # (T,V,C) -> (C,T,V)
        y = self.labels[idx]
        
        # Apply augmentation during training
        if self.augment:
            x = self.augment_sample(x)
        
        return x, y
    
    def augment_sample(self, x):
        """Apply random augmentations"""
        # Random temporal shifting (±2 frames)
        if torch.rand(1) > 0.5:
            shift = torch.randint(-2, 3, (1,)).item()
            x = torch.roll(x, shifts=shift, dims=1)
        
        # Random noise (small)
        if torch.rand(1) > 0.5:
            noise = torch.randn_like(x) * 0.01
            x = x + noise
        
        # Random scaling (0.95 to 1.05)
        if torch.rand(1) > 0.5:
            scale = 0.95 + torch.rand(1).item() * 0.1
            x = x * scale
        
        return x


# ============================================================================
# TRAINING UTILITIES
# ============================================================================

def save_checkpoint(model, optimizer, epoch, train_loss, val_loss, val_acc, 
                   label_names, output_dir, is_best=False):
    """Save model checkpoint"""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'train_loss': train_loss,
        'val_loss': val_loss,
        'val_acc': val_acc,
        'label_names': label_names,
        'config': {
            'num_classes': len(label_names),
            'num_nodes': NUM_NODES,
            'in_channels': IN_CHANNELS,
            'dropout': DROPOUT_RATE,
            'edge_importance_weighting': EDGE_IMPORTANCE_WEIGHTING,
            'architecture': f'NS-AGF Small Dataset ({NUM_ST_GCN_BLOCKS} blocks)',
            'training_date': datetime.now().isoformat(),
        }
    }
    
    checkpoint_path = output_dir / f'checkpoint_epoch_{epoch}.pth'
    torch.save(checkpoint, checkpoint_path)
    print(f"💾 Saved checkpoint: {checkpoint_path.name}")
    
    if is_best:
        best_path = output_dir / 'ns_agf_best.pth'
        torch.save(checkpoint, best_path)
        print(f"🏆 Saved BEST model: {best_path.name} (Val Acc: {val_acc:.2f}%)")


def plot_training_history(history, output_dir):
    """Plot training curves"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Loss
    axes[0, 0].plot(history['train_loss'], label='Train Loss', linewidth=2)
    axes[0, 0].plot(history['val_loss'], label='Val Loss', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Training and Validation Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Accuracy
    axes[0, 1].plot(history['train_acc'], label='Train Acc', linewidth=2)
    axes[0, 1].plot(history['val_acc'], label='Val Acc', linewidth=2)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Accuracy (%)')
    axes[0, 1].set_title('Training and Validation Accuracy')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Learning rate
    axes[1, 0].plot(history['learning_rate'], linewidth=2, color='green')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Learning Rate')
    axes[1, 0].set_title('Learning Rate Schedule')
    axes[1, 0].set_yscale('log')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Summary
    best_val_acc = max(history['val_acc'])
    best_epoch = history['val_acc'].index(best_val_acc) + 1
    
    summary = f"""
    Training Summary
    ================
    
    Best Val Accuracy: {best_val_acc:.2f}%
    Best Epoch: {best_epoch}
    
    Final Train Acc: {history['train_acc'][-1]:.2f}%
    Final Val Acc: {history['val_acc'][-1]:.2f}%
    
    Model: NS-AGF Small Dataset
    Blocks: {NUM_ST_GCN_BLOCKS}
    """
    
    axes[1, 1].text(0.1, 0.5, summary, fontsize=10, family='monospace',
                    verticalalignment='center', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'training_history.png', dpi=300)
    print(f"📊 Saved training history plot")
    plt.close()


def plot_confusion_matrix(y_true, y_pred, class_names, output_dir):
    """Plot confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    plt.figure(figsize=(max(12, len(class_names) * 0.5), max(10, len(class_names) * 0.5)))
    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Test Set Confusion Matrix')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / 'confusion_matrix.png', dpi=300)
    print(f"📊 Saved confusion matrix")
    plt.close()


# ============================================================================
# TRAINING LOOP
# ============================================================================

def train_epoch(model, dataloader, criterion, optimizer, device, scaler=None):
    """Train for one epoch"""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc='Training', leave=False)
    for inputs, targets in pbar:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        
        if scaler is not None:
            with torch.cuda.amp.autocast():
                outputs = model(inputs)
                loss = criterion(outputs, targets)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
        
        pbar.set_postfix({'loss': f'{loss.item():.4f}', 'acc': f'{100.*correct/total:.2f}%'})
    
    return total_loss / len(dataloader), 100.0 * correct / total


def validate_epoch(model, dataloader, criterion, device):
    """Validate for one epoch"""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        pbar = tqdm(dataloader, desc='Validation', leave=False)
        for inputs, targets in pbar:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
            all_predictions.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}', 'acc': f'{100.*correct/total:.2f}%'})
    
    return total_loss / len(dataloader), 100.0 * correct / total, all_predictions, all_targets


# ============================================================================
# MAIN TRAINING FUNCTION
# ============================================================================

def train_ns_agf_model(data_dir, output_dir, num_epochs=NUM_EPOCHS, batch_size=BATCH_SIZE):
    """Train NS-AGF model on small dataset"""
    
    print("\n" + "=" * 70)
    print("NS-AGF SMALL DATASET TRAINING")
    print("=" * 70)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n📁 Loading preprocessed data...")
    data_dir = Path(data_dir)
    features = np.load(data_dir / 'features.npy')
    labels = np.load(data_dir / 'labels.npy')
    label_names = np.load(data_dir / 'label_names.npy', allow_pickle=True)
    
    print(f"  Features: {features.shape}")
    print(f"  Labels: {labels.shape}")
    print(f"  Classes: {len(label_names)}")
    print(f"  Samples per class: {len(features) // len(label_names):.0f}")
    
    num_classes = len(label_names)
    samples_per_class = len(features) // num_classes
    
    # Warning for small datasets
    if samples_per_class < 80:
        print(f"\n⚠️  WARNING: Only {samples_per_class} samples per class detected!")
        print(f"⚠️  This is a SMALL DATASET. Using optimized configuration.")
        print(f"⚠️  Expected accuracy: 70-80% (not 90%+)")
    
    # Split data
    print("\n✂️ Splitting data (80% train, 10% val, 10% test)...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    
    # Create datasets with augmentation for training
    train_dataset = SignLanguageDataset(X_train, y_train, augment=True)
    val_dataset = SignLanguageDataset(X_val, y_val, augment=False)
    test_dataset = SignLanguageDataset(X_test, y_test, augment=False)
    
    # Dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Initialize smaller model
    print("\n🤖 Creating Smaller NS-AGF Model...")
    graph = MediaPipeGraph()
    
    # Create model with SMALLER architecture
    model = NSAGF(
        num_classes=num_classes,
        graph=graph,
        in_channels=IN_CHANNELS,
        dropout=DROPOUT_RATE,
        edge_importance_weighting=EDGE_IMPORTANCE_WEIGHTING
    )
    
    # Manually reduce model size by using only first 6 blocks
    # (The NSAGF class creates 10 blocks, we'll keep only 6)
    # Blocks 1-2: 64 channels, Blocks 3-4: 128 channels, Blocks 5-6: 256 channels
    model.st_gcn_blocks = nn.ModuleList(model.st_gcn_blocks[:NUM_ST_GCN_BLOCKS])
    
    # Update classifier to match 6-block output (256 channels, not 512)
    # The original classifier expects 512 channels from 10 blocks
    model.classifier = nn.Sequential(
        nn.Dropout(DROPOUT_RATE),
        nn.Linear(256, 256),  # 256 channels from 6 blocks
        nn.ReLU(inplace=True),
        nn.Dropout(DROPOUT_RATE),
        nn.Linear(256, num_classes)
    )
    
    model = model.to(DEVICE)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {total_params:,} (~{total_params * 4 / 1024 / 1024:.1f} MB)")
    print(f"  Samples/Param Ratio: 1:{total_params/len(X_train):.0f}")
    
    if total_params / len(X_train) > 100:
        print(f"  ⚠️  WARNING: Model might be too large for dataset!")
    
    # Setup training
    print("\n⚙️ Setting up training...")
    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    
    # Simple step decay (more stable than cosine annealing)
    scheduler = StepLR(optimizer, step_size=30, gamma=0.5)
    
    scaler = torch.cuda.amp.GradScaler() if USE_AMP and DEVICE.type == 'cuda' else None
    
    # Training loop
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': [], 'learning_rate': []}
    best_val_acc = 0.0
    patience_counter = 0
    
    print("\n" + "=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)
    
    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch+1}/{num_epochs}")
        print("-" * 70)
        
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE, scaler)
        val_loss, val_acc, val_preds, val_targets = validate_epoch(model, val_loader, criterion, DEVICE)
        
        scheduler.step()
        current_lr = optimizer.param_groups[0]['lr']
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['learning_rate'].append(current_lr)
        
        print(f"\n📈 Epoch {epoch+1}:")
        print(f"  Train: Loss={train_loss:.4f}, Acc={train_acc:.2f}%")
        print(f"  Val:   Loss={val_loss:.4f}, Acc={val_acc:.2f}%")
        print(f"  LR: {current_lr:.6f}")
        
        is_best = val_acc > best_val_acc
        if is_best:
            best_val_acc = val_acc
            patience_counter = 0
            print(f"  🏆 New best: {best_val_acc:.2f}%")
        else:
            patience_counter += 1
            print(f"  ⏳ Patience: {patience_counter}/{PATIENCE}")
        
        if (epoch + 1) % 10 == 0 or is_best:
            save_checkpoint(model, optimizer, epoch+1, train_loss, val_loss, val_acc,
                          label_names.tolist(), output_dir, is_best=is_best)
        
        if patience_counter >= PATIENCE:
            print(f"\n⛔ Early stopping at epoch {epoch+1}")
            break
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETED")
    print("=" * 70)
    
    # Save final
    save_checkpoint(model, optimizer, epoch+1, train_loss, val_loss, val_acc,
                   label_names.tolist(), output_dir, is_best=False)
    
    plot_training_history(history, output_dir)
    
    # Test evaluation
    print("\n" + "=" * 70)
    print("TEST SET EVALUATION")
    print("=" * 70)
    
    best_model_path = output_dir / 'ns_agf_best.pth'
    if best_model_path.exists():
        checkpoint = torch.load(best_model_path, map_location=DEVICE, weights_only=False)
        model.load_state_dict(checkpoint['model_state_dict'])
    
    test_loss, test_acc, test_preds, test_targets = validate_epoch(model, test_loader, criterion, DEVICE)
    
    print(f"\n🎯 Test Results:")
    print(f"  Loss: {test_loss:.4f}")
    print(f"  Accuracy: {test_acc:.2f}%")
    
    plot_confusion_matrix(test_targets, test_preds, label_names.tolist(), output_dir)
    
    report = classification_report(test_targets, test_preds, target_names=label_names.tolist(), digits=4)
    print(f"\n{report}")
    
    with open(output_dir / 'classification_report.txt', 'w') as f:
        f.write(report)
    
    # Save summary
    summary = {
        'model': 'NS-AGF Small Dataset',
        'architecture': f'{NUM_ST_GCN_BLOCKS} ST-GCN blocks',
        'num_classes': num_classes,
        'training_samples': len(X_train),
        'validation_samples': len(X_val),
        'test_samples': len(X_test),
        'samples_per_class': int(samples_per_class),
        'hyperparameters': {
            'batch_size': batch_size,
            'learning_rate': LEARNING_RATE,
            'num_epochs': num_epochs,
            'dropout': DROPOUT_RATE,
            'label_smoothing': LABEL_SMOOTHING,
            'weight_decay': WEIGHT_DECAY,
        },
        'results': {
            'best_val_acc': float(best_val_acc),
            'test_acc': float(test_acc),
        },
        'total_parameters': total_params,
    }
    
    with open(output_dir / 'training_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ COMPLETE! Best Val: {best_val_acc:.2f}% | Test: {test_acc:.2f}%")
    print("=" * 70)


# ============================================================================
# CLI
# ============================================================================

def is_notebook():
    try:
        shell = get_ipython().__class__.__name__
        return shell == 'ZMQInteractiveShell' or 'google.colab' in str(get_ipython().__class__)
    except NameError:
        return False


if __name__ == "__main__":
    if is_notebook():
        print("\n🎓 NOTEBOOK MODE")
        print("Call: train_ns_agf_model(data_dir='...', output_dir='...', num_epochs=150, batch_size=16)")
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('--data_dir', type=str, default='/kaggle/input/wlasl-preprocessed')
        parser.add_argument('--output_dir', type=str, default='/kaggle/working')
        parser.add_argument('--num_epochs', type=int, default=NUM_EPOCHS)
        parser.add_argument('--batch_size', type=int, default=BATCH_SIZE)
        args = parser.parse_args()
        
        train_ns_agf_model(args.data_dir, args.output_dir, args.num_epochs, args.batch_size)
