"""
FIXED Training Script for NS-AGF Model
========================================

CRITICAL FIXES APPLIED:
1. ✅ Class-balanced loss function (prevents "Adress" dominance)
2. ✅ Label smoothing (prevents overconfidence)
3. ✅ Better learning rate schedule
4. ✅ Confusion matrix tracking
5. ✅ Early stopping to prevent overfitting
6. ✅ Validation-based model saving

Usage in Kaggle:
    %run train_agcn_FIXED.py
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns


# ==================== CONFIGURATION ====================
DATA_PATH = "/kaggle/working/processed_data/"
CHECKPOINT_DIR = "/kaggle/working/checkpoints/"
OUTPUT_PATH = "/kaggle/working/"

# Model hyperparameters
NUM_CLASSES = None  # Auto-detected
NUM_NODES = 75
NUM_FEATURES = 3
SEQUENCE_LENGTH = 30
NUM_PERSON = 1

# Training hyperparameters
BATCH_SIZE = 16
NUM_EPOCHS = 50
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.0001
LABEL_SMOOTHING = 0.1  # Prevents overconfidence
EARLY_STOPPING_PATIENCE = 10  # Stop if no improvement for 10 epochs

# Device
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🔧 Using device: {DEVICE}")


# ==================== DATASET CLASS ====================
class WLASLDataset(Dataset):
    """PyTorch Dataset for WLASL landmarks"""
    
    def __init__(self, features, labels):
        self.features = features
        self.labels = labels
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        features = self.features[idx]  # (30, 75, 3)
        
        # Rearrange to (C, T, V, M)
        features = np.transpose(features, (2, 0, 1))  # (3, 30, 75)
        features = np.expand_dims(features, axis=-1)   # (3, 30, 75, 1)
        
        label = self.labels[idx]
        
        return torch.FloatTensor(features), torch.LongTensor([label])[0]


# ==================== MODEL DEFINITION ====================
class MediaPipeGraph:
    """Graph topology for MediaPipe landmarks"""
    def __init__(self):
        self.num_nodes = 75
        self.neighbor_links = self._define_links()
    
    def _define_links(self):
        """Define connections"""
        links = []
        
        # Pose skeleton
        pose_links = [
            (11, 12), (11, 13), (12, 14), (13, 15), (14, 16),
            (11, 23), (12, 24), (23, 24),
        ]
        links.extend(pose_links)
        
        # Wrist to hand connections (CRITICAL!)
        links.append((15, 33))  # Left wrist to left hand
        links.append((16, 54))  # Right wrist to right hand
        
        # Left hand
        left_hand_start = 33
        for i in range(20):
            links.append((left_hand_start + i, left_hand_start + i + 1))
        
        # Right hand
        right_hand_start = 54
        for i in range(20):
            links.append((right_hand_start + i, right_hand_start + i + 1))
        
        return links
    
    def get_adjacency_matrix(self):
        """Generate adjacency matrix"""
        A = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float32)
        
        # Self-connections
        for i in range(self.num_nodes):
            A[i, i] = 1.0
        
        # Neighbor connections
        for i, j in self.neighbor_links:
            A[i, j] = 1.0
            A[j, i] = 1.0
        
        # Normalize
        D = np.sum(A, axis=1)
        D = np.where(D > 0, np.power(D, -0.5), 0)
        D_mat = np.diag(D)
        A_normalized = D_mat @ A @ D_mat
        
        return A_normalized.astype(np.float32)


class STGCNBlock(nn.Module):
    """Spatial-Temporal Graph Convolution Block"""
    def __init__(self, in_channels, out_channels, A, stride=1):
        super().__init__()
        
        self.gcn = nn.Conv2d(in_channels, out_channels, 1)
        kernel_size = 9
        padding = (kernel_size - 1) // 2
        self.tcn = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, (kernel_size, 1), (stride, 1), (padding, 0)),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        
        self.register_buffer('A', torch.FloatTensor(A))
        
        if in_channels != out_channels or stride != 1:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, (stride, 1)),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.residual = lambda x: x
        
        self.relu = nn.ReLU(inplace=True)
    
    def forward(self, x):
        N, C, T, V = x.size()
        x_graph = torch.einsum('nctv,vw->nctw', x, self.A)
        x_out = self.gcn(x_graph)
        x_out = self.tcn(x_out)
        res = self.residual(x)
        x_out = x_out + res
        x_out = self.relu(x_out)
        return x_out


class SimpleAGCN(nn.Module):
    """Simplified 2s-AGCN with class balancing"""
    def __init__(self, num_class, num_point, A):
        super().__init__()
        
        self.data_bn = nn.BatchNorm1d(num_point * 3)
        
        self.st_gcn1 = STGCNBlock(3, 64, A)
        self.st_gcn2 = STGCNBlock(64, 64, A)
        self.st_gcn3 = STGCNBlock(64, 128, A, stride=2)
        self.st_gcn4 = STGCNBlock(128, 128, A)
        self.st_gcn5 = STGCNBlock(128, 256, A, stride=2)
        self.st_gcn6 = STGCNBlock(256, 256, A)
        
        self.fc = nn.Linear(256, num_class)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        N, C, T, V, M = x.size()
        
        # Batch norm
        x = x.permute(0, 4, 3, 1, 2).contiguous()
        x = x.view(N * M, V * C, T)
        x = self.data_bn(x)
        
        # Reshape back
        x = x.view(N * M, V, C, T)
        x = x.permute(0, 2, 3, 1).contiguous()
        
        # ST-GCN layers
        x = self.st_gcn1(x)
        x = self.st_gcn2(x)
        x = self.st_gcn3(x)
        x = self.st_gcn4(x)
        x = self.st_gcn5(x)
        x = self.st_gcn6(x)
        
        # Global pooling
        x = torch.mean(x, dim=[2, 3])
        x = x.view(N, M, -1).mean(dim=1)
        
        x = self.dropout(x)
        x = self.fc(x)
        
        return x


# ==================== TRAINING FUNCTIONS ====================
def calculate_class_weights(labels):
    """Calculate weights for imbalanced classes"""
    class_counts = np.bincount(labels)
    total_samples = len(labels)
    
    # Inverse frequency weighting
    class_weights = total_samples / (len(class_counts) * class_counts)
    
    # Normalize
    class_weights = class_weights / class_weights.sum() * len(class_counts)
    
    return torch.FloatTensor(class_weights)


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc="Training")
    for inputs, labels in pbar:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        pbar.set_postfix({'loss': f'{running_loss/len(dataloader):.4f}', 
                         'acc': f'{100*correct/total:.2f}%'})
    
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
    
    with torch.no_grad():
        for inputs, labels in tqdm(dataloader, desc="Validation"):
            inputs, labels = inputs.to(device), labels.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc, np.array(all_preds), np.array(all_labels)


def plot_confusion_matrix(y_true, y_pred, class_names, save_path):
    """Plot and save confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    
    print(f"✅ Confusion matrix saved to {save_path}")


# ==================== MAIN TRAINING LOOP ====================
def main():
    print("=" * 60)
    print("🚀 NS-AGF Training (FIXED VERSION)")
    print("=" * 60)
    
    # Load data
    print("\n📂 Loading preprocessed data...")
    train_features = np.load(os.path.join(DATA_PATH, "train_features.npy"))
    train_labels = np.load(os.path.join(DATA_PATH, "train_labels.npy"))
    val_features = np.load(os.path.join(DATA_PATH, "val_features.npy"))
    val_labels = np.load(os.path.join(DATA_PATH, "val_labels.npy"))
    
    print(f"✅ Train: {train_features.shape}, Val: {val_features.shape}")
    
    # Auto-detect classes
    num_classes = len(np.unique(train_labels))
    print(f"📊 Detected {num_classes} classes")
    
    # Load sign labels
    try:
        sign_labels = np.load(os.path.join(DATA_PATH, "sign_labels.npy"), allow_pickle=True)
        print(f"✅ Sign labels: {list(sign_labels)}")
    except:
        print("⚠️ sign_labels.npy not found")
        sign_labels = [f"Class_{i}" for i in range(num_classes)]
    
    # Calculate class weights
    print("\n⚖️ Calculating class weights...")
    class_weights = calculate_class_weights(train_labels)
    print(f"Class weights: {class_weights.numpy()}")
    
    # Create datasets
    train_dataset = WLASLDataset(train_features, train_labels)
    val_dataset = WLASLDataset(val_features, val_labels)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    
    # Initialize model
    print("\n🏗️ Building model...")
    graph = MediaPipeGraph()
    A = graph.get_adjacency_matrix()
    
    model = SimpleAGCN(num_class=num_classes, num_point=NUM_NODES, A=A)
    model = model.to(DEVICE)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"✅ Model parameters: {total_params:,}")
    
    # Loss with class weights and label smoothing
    criterion = nn.CrossEntropyLoss(
        weight=class_weights.to(DEVICE),
        label_smoothing=LABEL_SMOOTHING
    )
    
    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5, verbose=True
    )
    
    # Training loop
    print("\n🎯 Starting training...")
    print("=" * 60)
    
    best_val_acc = 0.0
    epochs_without_improvement = 0
    train_losses, train_accs = [], []
    val_losses, val_accs = [], []
    
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    for epoch in range(NUM_EPOCHS):
        print(f"\nEpoch [{epoch+1}/{NUM_EPOCHS}]")
        print("-" * 60)
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        
        # Validate
        val_loss, val_acc, val_preds, val_true = validate(model, val_loader, criterion, DEVICE)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        # Learning rate schedule
        scheduler.step(val_acc)
        
        print(f"\n📊 Epoch {epoch+1} Summary:")
        print(f"   Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"   Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            epochs_without_improvement = 0
            
            checkpoint_path = os.path.join(CHECKPOINT_DIR, f"best_model_epoch{epoch+1}.pth")
            torch.save(model.state_dict(), checkpoint_path)
            print(f"   ✅ New best model saved! (Val Acc: {val_acc:.2f}%)")
            
            # Save confusion matrix for best model
            cm_path = os.path.join(OUTPUT_PATH, "confusion_matrix_best.png")
            plot_confusion_matrix(val_true, val_preds, sign_labels, cm_path)
        else:
            epochs_without_improvement += 1
            print(f"   No improvement for {epochs_without_improvement} epochs")
        
        # Early stopping
        if epochs_without_improvement >= EARLY_STOPPING_PATIENCE:
            print(f"\n⚠️ Early stopping triggered after {epoch+1} epochs")
            break
    
    # Save final model
    final_model_path = os.path.join(OUTPUT_PATH, "ns_agcn.pth")
    torch.save(model.state_dict(), final_model_path)
    print(f"\n✅ Final model saved to {final_model_path}")
    
    # Plot training curves
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Training and Validation Loss')
    
    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Acc')
    plt.plot(val_accs, label='Val Acc')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.title('Training and Validation Accuracy')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_PATH, "training_curves.png"), dpi=150)
    plt.close()
    
    print(f"\n📈 Training curves saved")
    print(f"\n🎉 Training complete!")
    print(f"   Best validation accuracy: {best_val_acc:.2f}%")
    print(f"\n📦 Output files:")
    print(f"   - {final_model_path}")
    print(f"   - {os.path.join(OUTPUT_PATH, 'training_curves.png')}")
    print(f"   - {os.path.join(OUTPUT_PATH, 'confusion_matrix_best.png')}")


if __name__ == "__main__":
    main()
