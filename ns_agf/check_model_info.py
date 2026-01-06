import torch

ckpt = torch.load('models/ns_agcn.pth', map_location='cpu', weights_only=False)
config = ckpt.get('config', {})

print('=' * 70)
print('MODEL TRAINING INFO')
print('=' * 70)
print(f'Architecture: {config.get("architecture", "Unknown")}')
print(f'Classes: {len(ckpt.get("label_names", []))}')
print(f'Labels: {ckpt.get("label_names", [])}')
print(f'Epoch: {ckpt.get("epoch", "Unknown")}')
print(f'Val Acc: {ckpt.get("val_acc", 0):.2f}%')
print(f'Data path: {config.get("data_path", "Unknown")}')
print(f'Total samples: {config.get("total_samples", "Unknown")}')
print(f'Normalization: {config.get("normalization", "Unknown")}')
print(f'Sampling method: {config.get("sampling_method", "Unknown")}')
print('=' * 70)
