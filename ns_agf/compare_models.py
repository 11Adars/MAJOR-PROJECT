import torch
import numpy as np

print("=" * 80)
print("COMPARING MODEL CHECKPOINTS")
print("=" * 80)

# Check ns_agcn.pth
print("\n1. models/ns_agcn.pth:")
ckpt1 = torch.load('models/ns_agcn.pth', map_location='cpu', weights_only=False)
config1 = ckpt1.get('config', {})
labels1 = ckpt1.get('label_names', [])
print(f"   Classes: {len(labels1)}")
print(f"   Labels: {labels1}")
print(f"   Epoch: {ckpt1.get('epoch', 'Unknown')}")
print(f"   Val Acc: {ckpt1.get('val_acc', 0):.2f}%")
print(f"   Architecture: {config1.get('architecture', 'Unknown')}")
print(f"   File size: 300 MB")

# Check test.pth
print("\n2. models/test.pth:")
ckpt2 = torch.load('models/test.pth', map_location='cpu', weights_only=False)
config2 = ckpt2.get('config', {})
labels2 = ckpt2.get('label_names', [])
print(f"   Classes: {len(labels2)}")
print(f"   Labels: {labels2}")
print(f"   Epoch: {ckpt2.get('epoch', 'Unknown')}")
print(f"   Val Acc: {ckpt2.get('val_acc', 0):.2f}%")
print(f"   Architecture: {config2.get('architecture', 'Unknown')}")
print(f"   File size: 26 MB")

# Check label_names.npy
print("\n3. models/label_names.npy:")
try:
    labels_npy = np.load('models/label_names.npy', allow_pickle=True)
    print(f"   Labels: {labels_npy}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)

if len(labels1) == len(labels2):
    print(f"Both models have {len(labels1)} classes")
    print("Try testing with test.pth instead:")
    print("  python diagnose_prediction.py --video loan.mp4 --expected loan --model test.pth")
else:
    print("Models have different number of classes!")
    print("Use the model that matches your training videos.")
