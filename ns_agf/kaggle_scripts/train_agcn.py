"""
NS-AGF Model Training Script for Kaggle
========================================

This script trains the 2s-AGCN model on preprocessed WLASL data.

Prerequisites:
    - Run preprocess_wlasl.py first
    - GPU enabled in Kaggle settings

Usage in Kaggle:
    %run train_agcn.py
"""

import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import pickle
import matplotlib.pyplot as plt


# ==================== CONFIGURATION ====================
# Data paths
DATA_PATH = "/kaggle/working/processed_data/"
CHECKPOINT_DIR = "/kaggle/working/checkpoints/"
OUTPUT_PATH = "/kaggle/working/"

# Model hyperparameters
NUM_CLASSES = None  # Will be auto-detected from data
NUM_NODES = 75
NUM_FEATURES = 3
SEQUENCE_LENGTH = 30
NUM_PERSON = 1

# Training hyperparameters
BATCH_SIZE = 16  # Reduce if GPU OOM
NUM_EPOCHS = 50
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.0001
STEP_SIZE = 10  # For learning rate scheduler
GAMMA = 0.1  # Learning rate decay

# Device
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🔧 Using device: {DEVICE}")


# ==================== DATASET CLASS ====================
class WLASLDataset(Dataset):
    """PyTorch Dataset for WLASL landmarks"""
    
    def __init__(self, features, labels):
        """
        Args:
            features: numpy array of shape (N, T, V, C)
            labels: numpy array of shape (N,)
        """
        self.features = features
        self.labels = labels
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        # Get features: (T, V, C) -> (C, T, V, M)
        features = self.features[idx]  # (30, 75, 3)
        
        # Rearrange to (C, T, V, M) format expected by model
        features = np.transpose(features, (2, 0, 1))  # (3, 30, 75)
        features = np.expand_dims(features, axis=-1)   # (3, 30, 75, 1)
        
        label = self.labels[idx]
        
        return torch.FloatTensor(features), torch.LongTensor([label])[0]


# ==================== MODEL DEFINITION ====================
# We need to copy the model definition here since Kaggle won't have the package
# Copy from ns_agf/src/model/agcn.py or use a simplified version

class MediaPipeGraph:
    """Simplified graph topology for Kaggle"""
    def __init__(self):
        self.num_nodes = 75
        self.neighbor_links = self._define_links()
    
    def _define_links(self):
        """Define critical connections"""
        links = []
        
        # Pose skeleton (simplified)
        pose_links = [
            (11, 12), (11, 13), (12, 14), (13, 15), (14, 16),  # Shoulders and arms
            (11, 23), (12, 24), (23, 24),  # Torso
        ]
        links.extend(pose_links)
        
        # Left hand (simplified - just palm connections)
        for i in range(5):
            links.append((33, 33 + 1 + i * 4))
            for j in range(3):
                links.append((33 + 1 + i * 4 + j, 33 + 1 + i * 4 + j + 1))
        
        # Right hand (simplified)
        for i in range(5):
            links.append((54, 54 + 1 + i * 4))
            for j in range(3):
                links.append((54 + 1 + i * 4 + j, 54 + 1 + i * 4 + j + 1))
        
        # Bridge connections (CRITICAL)
        links.extend([(15, 33), (16, 54)])
        
        return links
    
    def get_adjacency_matrix(self):
        """Generate normalized adjacency matrix"""
        A = np.zeros((self.num_nodes, self.num_nodes))
        
        for i, j in self.neighbor_links:
            A[i, j] = 1
            A[j, i] = 1
        
        # Add self-connections
        A += np.eye(self.num_nodes)
        
        # Normalize
        D = np.sum(A, axis=1)
        D_inv_sqrt = np.power(D, -0.5)
        D_inv_sqrt[np.isinf(D_inv_sqrt)] = 0
        D_mat = np.diag(D_inv_sqrt)
        A_normalized = D_mat @ A @ D_mat
        
        return A_normalized.astype(np.float32)


# Simplified ST-GCN Block
class STGCNBlock(nn.Module):
    """Spatial-Temporal Graph Convolution Block"""
    def __init__(self, in_channels, out_channels, A, stride=1):
        super().__init__()
        
        # Spatial convolution
        self.gcn = nn.Conv2d(in_channels, out_channels, 1)
        
        # Temporal convolution
        kernel_size = 9
        padding = (kernel_size - 1) // 2
        self.tcn = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, (kernel_size, 1), (stride, 1), (padding, 0)),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        
        # Register adjacency
        self.register_buffer('A', torch.FloatTensor(A))
        
        # Residual
        if in_channels != out_channels or stride != 1:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, (stride, 1)),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.residual = lambda x: x
        
        self.relu = nn.ReLU(inplace=True)
    
    def forward(self, x):
        # x: (N, C, T, V)
        N, C, T, V = x.size()
        
        # Apply graph convolution
        x_graph = torch.einsum('nctv,vw->nctw', x, self.A)
        x_out = self.gcn(x_graph)
        
        # Apply temporal convolution
        x_out = self.tcn(x_out)
        
        # Residual connection
        res = self.residual(x)
        x_out = x_out + res
        x_out = self.relu(x_out)
        
        return x_out


class SimpleAGCN(nn.Module):
    """Simplified 2s-AGCN for Kaggle training"""
    def __init__(self, num_class, num_point, A):
        super().__init__()
        
        self.data_bn = nn.BatchNorm1d(num_point * 3)
        
        # ST-GCN layers
        self.st_gcn1 = STGCNBlock(3, 64, A)
        self.st_gcn2 = STGCNBlock(64, 64, A)
        self.st_gcn3 = STGCNBlock(64, 128, A, stride=2)
        self.st_gcn4 = STGCNBlock(128, 128, A)
        self.st_gcn5 = STGCNBlock(128, 256, A, stride=2)
        self.st_gcn6 = STGCNBlock(256, 256, A)
        
        # Classifier
        self.fc = nn.Linear(256, num_class)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        # x: (N, C, T, V, M)
        N, C, T, V, M = x.size()
        
        # Reshape for batch norm: (N, M, V, C, T) -> (N*M, V*C, T)
        x = x.permute(0, 4, 3, 1, 2).contiguous()  # (N, M, V, C, T)
        x = x.view(N * M, V * C, T)  # (N*M, V*C, T)
        x = self.data_bn(x)
        
        # Reshape back to (N*M, C, T, V)
        x = x.view(N * M, V, C, T)  # (N*M, V, C, T)
        x = x.permute(0, 2, 3, 1).contiguous()  # (N*M, C, T, V)
        
        # ST-GCN layers
        x = self.st_gcn1(x)
        x = self.st_gcn2(x)
        x = self.st_gcn3(x)
        x = self.st_gcn4(x)
        x = self.st_gcn5(x)
        x = self.st_gcn6(x)
        
        # Global pooling
        x = torch.mean(x, dim=[2, 3])  # (N*M, 256)
        x = x.view(N, M, -1).mean(dim=1)  # (N, 256)
        
        # Classifier
        x = self.dropout(x)
        x = self.fc(x)
        
        return x


# ==================== TRAINING FUNCTIONS ====================
def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc="Training")
    for inputs, labels in pbar:
        inputs = inputs.to(device)
        labels = labels.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        # Update progress bar
        pbar.set_postfix({'loss': loss.item(), 'acc': 100 * correct / total})
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    """Validate the model"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, labels in tqdm(dataloader, desc="Validation"):
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    val_loss = running_loss / len(dataloader)
    val_acc = 100 * correct / total
    
    return val_loss, val_acc


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("NS-AGF Training Pipeline")
    print("=" * 60)
    
    # Load preprocessed data
    print("\n📂 Loading preprocessed data...")
    train_features = np.load(os.path.join(DATA_PATH, "train_features.npy"))
    train_labels = np.load(os.path.join(DATA_PATH, "train_labels.npy"))
    val_features = np.load(os.path.join(DATA_PATH, "val_features.npy"))
    val_labels = np.load(os.path.join(DATA_PATH, "val_labels.npy"))
    
    print(f"✅ Train: {train_features.shape}, Val: {val_features.shape}")
    
    # Auto-detect number of classes
    num_classes = len(np.unique(train_labels))
    print(f"📊 Detected {num_classes} classes in dataset")
    
    # Load sign labels if available
    try:
        sign_labels = np.load(os.path.join(DATA_PATH, "sign_labels.npy"), allow_pickle=True)
        print(f"✅ Sign labels: {list(sign_labels[:5])}{'...' if len(sign_labels) > 5 else ''}")
    except:
        print("⚠️ sign_labels.npy not found")
    
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
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"✅ Model parameters: {total_params:,}")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=STEP_SIZE, gamma=GAMMA)
    
    # Training loop
    print(f"\n🚀 Starting training for {NUM_EPOCHS} epochs...")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    best_val_acc = 0.0
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    for epoch in range(NUM_EPOCHS):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch+1}/{NUM_EPOCHS}")
        print(f"{'='*60}")
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, DEVICE)
        
        # Scheduler step
        scheduler.step()
        
        # Log
        print(f"\n📊 Epoch {epoch+1} Results:")
        print(f"   Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"   Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_DIR, "best_model.pth"))
            print(f"✅ Best model saved! Val Acc: {best_val_acc:.2f}%")
        
        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
            }, os.path.join(CHECKPOINT_DIR, f"checkpoint_epoch_{epoch+1}.pth"))
    
    # Save final model
    print("\n💾 Saving final model...")
    torch.save(model.state_dict(), os.path.join(OUTPUT_PATH, "ns_agcn_bankassist.pth"))
    
    # Save training history
    with open(os.path.join(OUTPUT_PATH, "training_history.pkl"), 'wb') as f:
        pickle.dump(history, f)
    
    # Plot training curves
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train')
    plt.plot(history['val_loss'], label='Val')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Training Loss')
    
    plt.subplot(1, 2, 2)
    plt.plot(history['train_acc'], label='Train')
    plt.plot(history['val_acc'], label='Val')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.title('Training Accuracy')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_PATH, "training_curves.png"), dpi=300)
    
    print("\n✨ Training complete!")
    print(f"📁 Model saved to: {OUTPUT_PATH}ns_agcn_bankassist.pth")
    print(f"🏆 Best Val Accuracy: {best_val_acc:.2f}%")


if __name__ == "__main__":
    main()
