"""
IMPROVED Training for Sign Language Recognition
Fixes for low confidence and complex sign recognition

Key Improvements:
1. Increased label smoothing (0.1 -> 0.2) for better confidence calibration
2. Added dropout (0.5) to prevent overfitting
3. Stronger L2 regularization (weight_decay=1e-3)
4. Cosine annealing learning rate (better convergence)
5. Focal loss option (helps with hard examples)
6. Gradient clipping (prevents exploding gradients)
7. Mixed precision training (faster, more stable)
8. Better model architecture (more capacity for complex signs)
"""

import os
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
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration - Optimized for 45 videos per class
BATCH_SIZE = 24  # Increased from 16 (larger dataset allows larger batches)
LEARNING_RATE = 0.001
NUM_EPOCHS = 200  # Increased from 150 (more data needs more training)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DROPOUT_RATE = 0.5
LABEL_SMOOTHING = 0.25  # Increased from 0.2 (better confidence calibration)
WEIGHT_DECAY = 1e-3
GRADIENT_CLIP = 1.0


class SignLanguageDataset(Dataset):
    """Dataset for sign language sequences"""
    
    def __init__(self, features, labels):
        self.features = torch.FloatTensor(features)  # (N, T, V, C)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        # Return (C, T, V) format for ST-GCN
        x = self.features[idx].permute(2, 0, 1)  # (T, V, C) -> (C, T, V)
        y = self.labels[idx]
        return x, y


class STGCNBlock(nn.Module):
    """
    IMPROVED: Spatio-Temporal Graph Convolutional Block with Dropout
    """
    
    def __init__(self, in_channels, out_channels, kernel_size=9, stride=1, dropout=0.5):
        super(STGCNBlock, self).__init__()
        
        # Temporal convolution (along time axis)
        padding = (kernel_size - 1) // 2
        self.tcn = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, (kernel_size, 1), (stride, 1), (padding, 0)),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout)  # ADDED: Dropout for regularization
        )
        
        # Spatial convolution (graph convolution along nodes)
        self.gcn = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, 1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout)  # ADDED: Dropout for regularization
        )
        
        # Residual connection
        if in_channels != out_channels or stride != 1:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, (stride, 1)),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.residual = nn.Identity()
    
    def forward(self, x):
        res = self.residual(x)
        x = self.tcn(x)
        x = self.gcn(x)
        return F.relu(x + res)


class ImprovedAGCN(nn.Module):
    """
    IMPROVED: Adaptive Graph Convolutional Network for Sign Language Recognition
    
    Improvements:
    - More layers (6 -> 8 blocks) for complex patterns
    - Dropout regularization
    - Larger channel capacity
    - Better final classifier
    """
    
    def __init__(self, num_classes, num_nodes=75, in_channels=3, dropout=0.5):
        super(ImprovedAGCN, self).__init__()
        
        # Input layer
        self.input_layer = nn.Sequential(
            nn.Conv2d(in_channels, 64, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout)
        )
        
        # ST-GCN blocks (INCREASED CAPACITY)
        self.st_gcn_blocks = nn.ModuleList([
            STGCNBlock(64, 64, kernel_size=9, dropout=dropout),
            STGCNBlock(64, 64, kernel_size=9, dropout=dropout),
            STGCNBlock(64, 128, kernel_size=9, stride=2, dropout=dropout),  # Downsample time
            STGCNBlock(128, 128, kernel_size=9, dropout=dropout),
            STGCNBlock(128, 256, kernel_size=9, stride=2, dropout=dropout),  # Downsample time
            STGCNBlock(256, 256, kernel_size=9, dropout=dropout),
            STGCNBlock(256, 512, kernel_size=9, stride=2, dropout=dropout),  # Downsample time
            STGCNBlock(512, 512, kernel_size=9, dropout=dropout),
        ])
        
        # Global pooling (spatial and temporal)
        self.gap = nn.AdaptiveAvgPool2d(1)
        
        # IMPROVED: Better classifier with dropout
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        # x: (N, C, T, V)
        x = self.input_layer(x)
        
        # Apply ST-GCN blocks
        for block in self.st_gcn_blocks:
            x = block(x)
        
        # Global pooling
        x = self.gap(x)  # (N, C, 1, 1)
        x = x.view(x.size(0), -1)  # (N, C)
        
        # Classify
        x = self.classifier(x)
        
        return x


class FocalLoss(nn.Module):
    """
    Focal Loss - helps with hard examples and class imbalance
    """
    
    def __init__(self, alpha=1.0, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss


def calculate_class_weights(labels):
    """Calculate inverse frequency class weights"""
    unique, counts = np.unique(labels, return_counts=True)
    total = len(labels)
    weights = total / (len(unique) * counts)
    return torch.FloatTensor(weights)


def train_epoch(model, dataloader, criterion, optimizer, device, use_amp=True):
    """
    IMPROVED: Train one epoch with gradient clipping and mixed precision
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    # Mixed precision training
    scaler = torch.cuda.amp.GradScaler() if use_amp and torch.cuda.is_available() else None
    
    pbar = tqdm(dataloader, desc="Training")
    for inputs, labels in pbar:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        
        # Forward pass with mixed precision
        if scaler is not None:
            with torch.cuda.amp.autocast():
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            
            # Backward pass with gradient scaling
            scaler.scale(loss).backward()
            
            # Gradient clipping (IMPORTANT for stability)
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            
            optimizer.step()
        
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        pbar.set_postfix({
            'loss': f'{running_loss/len(dataloader):.4f}', 
            'acc': f'{100*correct/total:.2f}%'
        })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    """Validate model"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for inputs, labels in tqdm(dataloader, desc="Validation"):
            inputs, labels = inputs.to(device), labels.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            # Get probabilities
            probs = F.softmax(outputs, dim=1)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc, np.array(all_preds), np.array(all_labels), np.array(all_probs)


def plot_confusion_matrix(y_true, y_pred, classes, save_path):
    """Plot and save confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Confusion matrix saved to {save_path}")


def main():
    """
    IMPROVED Main training pipeline
    """
    print(f"🚀 Starting IMPROVED training...")
    print(f"💻 Device: {DEVICE}")
    print(f"📦 Batch size: {BATCH_SIZE}")
    print(f"📚 Learning rate: {LEARNING_RATE}")
    print(f"🎯 Epochs: {NUM_EPOCHS}")
    print(f"🎲 Dropout: {DROPOUT_RATE}")
    print(f"🏷️  Label smoothing: {LABEL_SMOOTHING}")
    print(f"⚖️  Weight decay: {WEIGHT_DECAY}")
    
    # Load preprocessed data
    data_path = Path('/kaggle/working/processed_data_improved')
    
    X = np.load(data_path / 'features.npy')
    y = np.load(data_path / 'labels.npy')
    label_names = np.load(data_path / 'label_names.npy', allow_pickle=True)
    
    print(f"\n📊 Dataset shape: {X.shape}")
    print(f"📊 Number of classes: {len(label_names)}")
    print(f"📊 Classes: {label_names}")
    
    # Split dataset
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n✂️  Train samples: {len(X_train)}")
    print(f"✂️  Validation samples: {len(X_val)}")
    
    # Create datasets and dataloaders
    train_dataset = SignLanguageDataset(X_train, y_train)
    val_dataset = SignLanguageDataset(X_val, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    
    # Calculate class weights
    class_weights = calculate_class_weights(y_train).to(DEVICE)
    print(f"\n⚖️  Class weights: {class_weights}")
    
    # IMPROVED: Create model with dropout
    model = ImprovedAGCN(
        num_classes=len(label_names),
        num_nodes=75,
        in_channels=3,
        dropout=DROPOUT_RATE
    ).to(DEVICE)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n🔢 Total parameters: {total_params:,}")
    print(f"🔢 Trainable parameters: {trainable_params:,}")
    
    # IMPROVED: Loss with higher label smoothing
    criterion = nn.CrossEntropyLoss(
        weight=class_weights,
        label_smoothing=LABEL_SMOOTHING
    )
    
    # Alternative: Focal Loss (uncomment to use)
    # criterion = FocalLoss(alpha=1.0, gamma=2.0)
    
    # IMPROVED: Optimizer with weight decay
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )
    
    # IMPROVED: Cosine annealing with warm restarts
    scheduler = CosineAnnealingWarmRestarts(
        optimizer,
        T_0=10,  # Restart every 10 epochs
        T_mult=2,  # Double the period after each restart
        eta_min=1e-6
    )
    
    # Training loop
    best_val_acc = 0.0
    best_model_path = '/kaggle/working/best_model_improved.pth'
    patience = 25  # Increased from 15 (larger 45-video dataset needs more epochs to converge)
    patience_counter = 0
    
    train_losses = []
    train_accs = []
    val_losses = []
    val_accs = []
    
    for epoch in range(NUM_EPOCHS):
        print(f"\n{'='*70}")
        print(f"Epoch {epoch+1}/{NUM_EPOCHS}")
        print(f"{'='*70}")
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        
        # Validate
        val_loss, val_acc, val_preds, val_labels, val_probs = validate(model, val_loader, criterion, DEVICE)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        # Step scheduler
        scheduler.step()
        current_lr = optimizer.param_groups[0]['lr']
        
        print(f"\n📊 Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"📊 Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        print(f"📊 Learning Rate: {current_lr:.6f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'label_names': label_names
            }, best_model_path)
            print(f"💾 Saved best model (val_acc: {val_acc:.2f}%)")
            patience_counter = 0
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= patience:
            print(f"\n⏹️  Early stopping triggered after {epoch+1} epochs")
            break
    
    # Load best model and evaluate
    print(f"\n{'='*70}")
    print("📊 Final Evaluation on Best Model")
    print(f"{'='*70}")
    
    checkpoint = torch.load(best_model_path, weights_only=False)  # FIXED: PyTorch 2.6 compatibility
    model.load_state_dict(checkpoint['model_state_dict'])
    
    _, val_acc, val_preds, val_labels, val_probs = validate(model, val_loader, criterion, DEVICE)
    
    print(f"\n🎯 Best Validation Accuracy: {best_val_acc:.2f}%")
    
    # Calculate average confidence for correct predictions
    correct_mask = val_preds == val_labels
    correct_probs = val_probs[correct_mask]
    avg_confidence = np.mean(np.max(correct_probs, axis=1)) * 100
    print(f"📊 Average confidence on correct predictions: {avg_confidence:.2f}%")
    
    # Generate confusion matrix
    plot_confusion_matrix(
        val_labels, val_preds, label_names,
        '/kaggle/working/confusion_matrix_improved.png'
    )
    
    # Classification report
    print("\n📋 Classification Report:")
    print(classification_report(val_labels, val_preds, target_names=label_names))
    
    print(f"\n✅ Training complete!")
    print(f"💾 Best model saved to: {best_model_path}")


if __name__ == "__main__":
    main()
