"""
NS-AGF Professional Training Script
====================================

Publication-Grade Training for Sign Language Recognition with Full NS-AGF Architecture

Key Features:
1. Professional NS-AGF model (10 ST-GCN blocks, adaptive graphs, edge importance)
2. Explicit graph topology (75-node MediaPipe structure)
3. Optimized for 45 videos per class (495 total, ~80 samples/class with augmentation)
4. Label smoothing (0.25) for better confidence calibration
5. Dropout (0.5) during training, 0.0 during inference
6. Cosine annealing learning rate schedule
7. Gradient clipping for stability
8. Mixed precision training (faster, more memory efficient)
9. Comprehensive metrics and visualization
10. Checkpoint saving with best model selection

Model Architecture:
- Input: (N, C, T, V) = (batch, 3 channels, 30 frames, 75 nodes)
- 10 ST-GCN blocks with adaptive graph convolution
- Progressive channel expansion: 64 → 128 → 256 → 512
- Edge importance weighting (learnable adjacency)
- Spatial partitioning (inward/outward/self connections)
- Global average pooling + Two-layer classifier

Training Configuration:
- Batch size: 24 (optimal for 80 samples/class)
- Epochs: 200 (increased for larger dataset)
- Learning rate: 0.001 with cosine annealing
- Patience: 25 epochs early stopping
- Mixed precision: FP16 (faster training)

Usage:
    # On Kaggle (with preprocessed data uploaded as dataset)
    python train_agcn_PROFESSIONAL.py \\
        --data_dir /kaggle/input/your-preprocessed-dataset/ \\
        --output_dir /kaggle/working/ \\
        --num_epochs 200 \\
        --batch_size 24

    # Local
    python train_agcn_PROFESSIONAL.py \\
        --data_dir ./output/ \\
        --output_dir ./models/ \\
        --num_epochs 200 \\
        --batch_size 24

Expected Results:
- Training accuracy: 95-98%
- Validation accuracy: 92-96%
- Test accuracy: 90-95%
- Confidence scores: 75-95%+ for correct predictions
- Training time: ~4-5 hours on Kaggle GPU
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from pathlib import Path
from tqdm import tqdm
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add src to path for imports
# Handle both script execution and Jupyter/Kaggle notebook environments
try:
    # Running as a script
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
except NameError:
    # Running in Jupyter/Kaggle notebook
    script_dir = Path.cwd()
    project_root = script_dir
    # Try common Kaggle paths
    if (script_dir / 'src').exists():
        project_root = script_dir
    elif (script_dir.parent / 'src').exists():
        project_root = script_dir.parent

sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from src.graph.topology import MediaPipeGraph
from src.model.nsagf import NSAGF, create_model

# ============================================================================
# CONFIGURATION
# ============================================================================

# Hyperparameters - Optimized for 45 videos/class (80 samples with augmentation)
BATCH_SIZE = 24  # Larger batch for larger dataset
LEARNING_RATE = 0.001
NUM_EPOCHS = 200  # More epochs for larger, more complex dataset
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DROPOUT_RATE = 0.5  # Training dropout (0.0 for inference)
LABEL_SMOOTHING = 0.25  # High smoothing for confidence calibration
WEIGHT_DECAY = 1e-3  # L2 regularization
GRADIENT_CLIP = 1.0  # Gradient clipping threshold
PATIENCE = 25  # Early stopping patience (increased from 15)

# Mixed precision training
USE_AMP = True  # Automatic Mixed Precision (FP16)

# Model architecture configuration
EDGE_IMPORTANCE_WEIGHTING = True  # Enable adaptive graphs
NUM_ST_GCN_BLOCKS = 10  # Professional architecture (vs 8 in IMPROVED)
IN_CHANNELS = 3  # x, y, z coordinates
NUM_NODES = 75  # MediaPipe Holistic landmarks

print("=" * 70)
print("NS-AGF Professional Training Configuration")
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
print(f"Mixed Precision (AMP): {USE_AMP}")
print(f"ST-GCN Blocks: {NUM_ST_GCN_BLOCKS}")
print(f"Edge Importance Weighting: {EDGE_IMPORTANCE_WEIGHTING}")
print("=" * 70)


# ============================================================================
# DATASET
# ============================================================================

class SignLanguageDataset(Dataset):
    """Dataset for sign language sequences"""
    
    def __init__(self, features, labels):
        """
        Args:
            features: (N, T, V, C) numpy array
            labels: (N,) numpy array
        """
        self.features = torch.FloatTensor(features)  # (N, T, V, C)
        self.labels = torch.LongTensor(labels)
        
        print(f"  Dataset initialized: {len(self)} samples")
        print(f"  Feature shape: {self.features.shape}")  # Should be (N, T, V, C)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        """
        Returns:
            x: (C, T, V) tensor for NS-AGF model
            y: scalar label
        """
        # Convert (T, V, C) -> (C, T, V) format
        x = self.features[idx].permute(2, 0, 1)  # (T, V, C) -> (C, T, V)
        y = self.labels[idx]
        return x, y


# ============================================================================
# FOCAL LOSS (Optional - Better for Hard Examples)
# ============================================================================

class FocalLoss(nn.Module):
    """
    Focal Loss for handling class imbalance and hard examples.
    Focuses training on hard-to-classify samples.
    """
    
    def __init__(self, gamma=2.0, alpha=None, label_smoothing=0.0):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.label_smoothing = label_smoothing
    
    def forward(self, inputs, targets):
        """
        Args:
            inputs: (N, C) logits
            targets: (N,) class indices
        """
        ce_loss = F.cross_entropy(
            inputs, targets,
            reduction='none',
            label_smoothing=self.label_smoothing
        )
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        
        if self.alpha is not None:
            alpha_t = self.alpha[targets]
            focal_loss = alpha_t * focal_loss
        
        return focal_loss.mean()


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
            'architecture': 'NS-AGF Professional (10 blocks)',
            'training_date': datetime.now().isoformat(),
        }
    }
    
    # Save regular checkpoint
    checkpoint_path = output_dir / f'checkpoint_epoch_{epoch}.pth'
    torch.save(checkpoint, checkpoint_path)
    print(f"💾 Saved checkpoint: {checkpoint_path.name}")
    
    # Save best model separately
    if is_best:
        best_path = output_dir / 'ns_agf_best.pth'
        torch.save(checkpoint, best_path)
        print(f"🏆 Saved BEST model: {best_path.name} (Val Acc: {val_acc:.2f}%)")


def plot_training_history(history, output_dir):
    """Plot and save training curves"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Loss curves
    axes[0, 0].plot(history['train_loss'], label='Train Loss', linewidth=2)
    axes[0, 0].plot(history['val_loss'], label='Val Loss', linewidth=2)
    axes[0, 0].set_xlabel('Epoch', fontsize=12)
    axes[0, 0].set_ylabel('Loss', fontsize=12)
    axes[0, 0].set_title('Training and Validation Loss', fontsize=14, fontweight='bold')
    axes[0, 0].legend(fontsize=11)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Accuracy curves
    axes[0, 1].plot(history['train_acc'], label='Train Acc', linewidth=2)
    axes[0, 1].plot(history['val_acc'], label='Val Acc', linewidth=2)
    axes[0, 1].set_xlabel('Epoch', fontsize=12)
    axes[0, 1].set_ylabel('Accuracy (%)', fontsize=12)
    axes[0, 1].set_title('Training and Validation Accuracy', fontsize=14, fontweight='bold')
    axes[0, 1].legend(fontsize=11)
    axes[0, 1].grid(True, alpha=0.3)
    
    # Learning rate schedule
    if 'learning_rate' in history:
        axes[1, 0].plot(history['learning_rate'], linewidth=2, color='green')
        axes[1, 0].set_xlabel('Epoch', fontsize=12)
        axes[1, 0].set_ylabel('Learning Rate', fontsize=12)
        axes[1, 0].set_title('Learning Rate Schedule', fontsize=14, fontweight='bold')
        axes[1, 0].set_yscale('log')
        axes[1, 0].grid(True, alpha=0.3)
    
    # Best metrics summary
    best_val_acc = max(history['val_acc'])
    best_epoch = history['val_acc'].index(best_val_acc) + 1
    final_train_acc = history['train_acc'][-1]
    final_val_acc = history['val_acc'][-1]
    
    summary_text = f"""
    Training Summary
    ================
    
    Best Validation Accuracy: {best_val_acc:.2f}%
    Best Epoch: {best_epoch}/{len(history['train_loss'])}
    
    Final Training Accuracy: {final_train_acc:.2f}%
    Final Validation Accuracy: {final_val_acc:.2f}%
    
    Model: NS-AGF Professional
    Blocks: {NUM_ST_GCN_BLOCKS}
    Edge Importance: {EDGE_IMPORTANCE_WEIGHTING}
    
    Hyperparameters:
    - Batch Size: {BATCH_SIZE}
    - Learning Rate: {LEARNING_RATE}
    - Dropout: {DROPOUT_RATE}
    - Label Smoothing: {LABEL_SMOOTHING}
    - Weight Decay: {WEIGHT_DECAY}
    """
    
    axes[1, 1].text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                    verticalalignment='center', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plot_path = output_dir / 'training_history.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Saved training history plot: {plot_path.name}")
    plt.close()


def plot_confusion_matrix(y_true, y_pred, class_names, output_dir, title='Confusion Matrix'):
    """Plot and save confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    # Normalize confusion matrix
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    plt.figure(figsize=(max(12, len(class_names) * 0.5), max(10, len(class_names) * 0.5)))
    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names,
                cbar_kws={'label': 'Normalized Count'})
    plt.xlabel('Predicted', fontsize=12, fontweight='bold')
    plt.ylabel('True', fontsize=12, fontweight='bold')
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    cm_path = output_dir / 'confusion_matrix.png'
    plt.savefig(cm_path, dpi=300, bbox_inches='tight')
    print(f"📊 Saved confusion matrix: {cm_path.name}")
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
    for batch_idx, (inputs, targets) in enumerate(pbar):
        inputs, targets = inputs.to(device), targets.to(device)
        
        optimizer.zero_grad()
        
        if scaler is not None:
            # Mixed precision training
            with torch.cuda.amp.autocast():
                outputs = model(inputs)
                loss = criterion(outputs, targets)
            
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            scaler.step(optimizer)
            scaler.update()
        else:
            # Regular training
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
        
        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'acc': f'{100.*correct/total:.2f}%'
        })
    
    avg_loss = total_loss / len(dataloader)
    accuracy = 100.0 * correct / total
    
    return avg_loss, accuracy


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
            
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100.*correct/total:.2f}%'
            })
    
    avg_loss = total_loss / len(dataloader)
    accuracy = 100.0 * correct / total
    
    return avg_loss, accuracy, all_predictions, all_targets


# ============================================================================
# MAIN TRAINING FUNCTION
# ============================================================================

def train_ns_agf_model(data_dir, output_dir, num_epochs=NUM_EPOCHS, batch_size=BATCH_SIZE):
    """
    Main training function for NS-AGF model.
    
    Args:
        data_dir: Directory containing preprocessed data
        output_dir: Directory to save outputs
        num_epochs: Number of training epochs
        batch_size: Batch size for training
    """
    print("=" * 70)
    print("NS-AGF PROFESSIONAL TRAINING")
    print("=" * 70)
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load preprocessed data
    print("\n📁 Loading preprocessed data...")
    data_dir = Path(data_dir)
    
    # Match preprocessing output filenames
    features = np.load(data_dir / 'features.npy')
    labels = np.load(data_dir / 'labels.npy')
    label_names = np.load(data_dir / 'label_names.npy', allow_pickle=True)
    
    print(f"  Features shape: {features.shape}")  # Should be (N, T, V, C)
    print(f"  Labels shape: {labels.shape}")
    print(f"  Number of classes: {len(label_names)}")
    print(f"  Class names: {label_names.tolist()}")
    
    num_classes = len(label_names)
    
    # Split data
    print("\n✂️ Splitting data (80% train, 10% val, 10% test)...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Test samples: {len(X_test)}")
    
    # Create datasets
    print("\n📦 Creating datasets...")
    train_dataset = SignLanguageDataset(X_train, y_train)
    val_dataset = SignLanguageDataset(X_val, y_val)
    test_dataset = SignLanguageDataset(X_test, y_test)
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size,
        shuffle=True, num_workers=0, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size,
        shuffle=False, num_workers=0, pin_memory=True
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size,
        shuffle=False, num_workers=0, pin_memory=True
    )
    
    # Initialize graph topology
    print("\n🌐 Initializing MediaPipe Graph Topology...")
    graph = MediaPipeGraph()
    print(f"  Graph nodes: {graph.num_nodes}")
    print(f"  Graph edges: {len(graph.neighbor_links)}")
    
    # Create NS-AGF model
    print("\n🤖 Creating NS-AGF Professional Model...")
    model = NSAGF(
        num_classes=num_classes,
        graph=graph,
        in_channels=IN_CHANNELS,
        dropout=DROPOUT_RATE,  # 0.5 for training
        edge_importance_weighting=EDGE_IMPORTANCE_WEIGHTING
    )
    model = model.to(DEVICE)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
    print(f"  Model size: ~{total_params * 4 / 1024 / 1024:.2f} MB (fp32)")
    
    # Loss function with label smoothing
    print("\n⚙️ Setting up training components...")
    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
    
    # Optimizer with weight decay
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )
    
    # Cosine annealing learning rate schedule
    scheduler = CosineAnnealingWarmRestarts(
        optimizer,
        T_0=10,  # Restart every 10 epochs
        T_mult=2,  # Double period after each restart
        eta_min=1e-6
    )
    
    # Mixed precision scaler
    scaler = torch.cuda.amp.GradScaler() if USE_AMP and DEVICE.type == 'cuda' else None
    
    # Training history
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': [],
        'learning_rate': []
    }
    
    # Early stopping
    best_val_acc = 0.0
    patience_counter = 0
    
    # Training loop
    print("\n" + "=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)
    
    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch+1}/{num_epochs}")
        print("-" * 70)
        
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, DEVICE, scaler
        )
        
        # Validate
        val_loss, val_acc, val_preds, val_targets = validate_epoch(
            model, val_loader, criterion, DEVICE
        )
        
        # Update learning rate
        scheduler.step()
        current_lr = optimizer.param_groups[0]['lr']
        
        # Save history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['learning_rate'].append(current_lr)
        
        # Print epoch summary
        print(f"\n📈 Epoch {epoch+1} Summary:")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        print(f"  Learning Rate: {current_lr:.6f}")
        
        # Check for best model
        is_best = val_acc > best_val_acc
        if is_best:
            best_val_acc = val_acc
            patience_counter = 0
            print(f"  🏆 New best validation accuracy: {best_val_acc:.2f}%")
        else:
            patience_counter += 1
            print(f"  ⏳ Patience: {patience_counter}/{PATIENCE}")
        
        # Save checkpoint every 10 epochs or if best
        if (epoch + 1) % 10 == 0 or is_best:
            save_checkpoint(
                model, optimizer, epoch+1,
                train_loss, val_loss, val_acc,
                label_names.tolist(), output_dir,
                is_best=is_best
            )
        
        # Early stopping
        if patience_counter >= PATIENCE:
            print(f"\n⛔ Early stopping triggered! No improvement for {PATIENCE} epochs.")
            break
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETED")
    print("=" * 70)
    
    # Save final checkpoint
    save_checkpoint(
        model, optimizer, epoch+1,
        train_loss, val_loss, val_acc,
        label_names.tolist(), output_dir,
        is_best=False
    )
    
    # Plot training history
    print("\n📊 Generating plots...")
    plot_training_history(history, output_dir)
    
    # Final evaluation on test set
    print("\n" + "=" * 70)
    print("FINAL EVALUATION ON TEST SET")
    print("=" * 70)
    
    # Load best model
    best_model_path = output_dir / 'ns_agf_best.pth'
    if best_model_path.exists():
        print(f"\n📥 Loading best model from {best_model_path.name}...")
        checkpoint = torch.load(best_model_path, map_location=DEVICE, weights_only=False)
        model.load_state_dict(checkpoint['model_state_dict'])
    
    test_loss, test_acc, test_preds, test_targets = validate_epoch(
        model, test_loader, criterion, DEVICE
    )
    
    print(f"\n🎯 Test Set Results:")
    print(f"  Test Loss: {test_loss:.4f}")
    print(f"  Test Accuracy: {test_acc:.2f}%")
    
    # Confusion matrix
    plot_confusion_matrix(
        test_targets, test_preds,
        label_names.tolist(), output_dir,
        title='Test Set Confusion Matrix'
    )
    
    # Classification report
    print("\n📊 Classification Report:")
    report = classification_report(
        test_targets, test_preds,
        target_names=label_names.tolist(),
        digits=4
    )
    print(report)
    
    # Save classification report
    report_path = output_dir / 'classification_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"💾 Saved classification report: {report_path.name}")
    
    # Save training summary
    summary = {
        'model': 'NS-AGF Professional',
        'architecture': f'{NUM_ST_GCN_BLOCKS} ST-GCN blocks',
        'edge_importance_weighting': EDGE_IMPORTANCE_WEIGHTING,
        'num_classes': num_classes,
        'class_names': label_names.tolist(),
        'training_samples': len(X_train),
        'validation_samples': len(X_val),
        'test_samples': len(X_test),
        'hyperparameters': {
            'batch_size': batch_size,
            'learning_rate': LEARNING_RATE,
            'num_epochs': num_epochs,
            'dropout': DROPOUT_RATE,
            'label_smoothing': LABEL_SMOOTHING,
            'weight_decay': WEIGHT_DECAY,
            'gradient_clip': GRADIENT_CLIP,
            'patience': PATIENCE,
        },
        'results': {
            'best_val_acc': float(best_val_acc),
            'final_train_acc': float(history['train_acc'][-1]),
            'final_val_acc': float(history['val_acc'][-1]),
            'test_acc': float(test_acc),
            'test_loss': float(test_loss),
        },
        'total_parameters': total_params,
        'trainable_parameters': trainable_params,
        'training_date': datetime.now().isoformat(),
    }
    
    summary_path = output_dir / 'training_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Saved training summary: {summary_path.name}")
    
    print("\n" + "=" * 70)
    print("✅ TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📂 All outputs saved to: {output_dir}")
    print(f"\n🏆 Best Model: {best_model_path.name}")
    print(f"   Validation Accuracy: {best_val_acc:.2f}%")
    print(f"   Test Accuracy: {test_acc:.2f}%")
    print("\n" + "=" * 70)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def is_notebook():
    """Check if running in Jupyter/Colab notebook"""
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif 'google.colab' in str(get_ipython().__class__):
            return True   # Google Colab
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


if __name__ == "__main__":
    # Check if running in notebook environment
    if is_notebook():
        print("\n" + "=" * 70)
        print("🎓 NOTEBOOK MODE DETECTED")
        print("=" * 70)
        print("\nTo start training, call the function directly:")
        print("\ntrain_ns_agf_model(")
        print("    data_dir='/kaggle/input/wlasl-preprocessed-45videos',")
        print("    output_dir='/kaggle/working',")
        print("    num_epochs=200,")
        print("    batch_size=24")
        print(")")
        print("\n" + "=" * 70)
    else:
        # Command line execution
        parser = argparse.ArgumentParser(
            description='Train NS-AGF Professional Model for Sign Language Recognition'
        )
        
        parser.add_argument(
            '--data_dir',
            type=str,
            default='/kaggle/input/wlasl-preprocessed-45videos',
            help='Directory containing preprocessed data (features.npy, labels.npy, label_names.npy)'
        )
        
        parser.add_argument(
            '--output_dir',
            type=str,
            default='/kaggle/working',
            help='Directory to save trained models and outputs'
        )
        
        parser.add_argument(
            '--num_epochs',
            type=int,
            default=NUM_EPOCHS,
            help=f'Number of training epochs (default: {NUM_EPOCHS})'
        )
        
        parser.add_argument(
            '--batch_size',
            type=int,
            default=BATCH_SIZE,
            help=f'Batch size for training (default: {BATCH_SIZE})'
        )
        
        args = parser.parse_args()
        
        # Run training
        train_ns_agf_model(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size
        )
