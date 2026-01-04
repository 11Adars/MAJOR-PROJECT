"""
Helper script to generate sign_labels.txt from your dataset folder structure.

Usage:
    python create_sign_labels.py --dataset_path "path/to/your/dataset"
    
This will scan your dataset folder and create sign_labels.txt with the correct order.
"""

import os
import argparse
from pathlib import Path


def create_sign_labels(dataset_path: str, output_path: str = None):
    """
    Create sign_labels.txt from dataset folder structure.
    
    Args:
        dataset_path: Path to dataset folder containing sign subfolders
        output_path: Path to save sign_labels.txt (default: ./models/sign_labels.txt)
    """
    dataset_path = Path(dataset_path)
    
    if not dataset_path.exists():
        print(f"❌ Error: Dataset path not found: {dataset_path}")
        return
    
    # Get all subdirectories (sign folders)
    sign_folders = [d for d in dataset_path.iterdir() if d.is_dir()]
    
    if not sign_folders:
        print(f"❌ Error: No subdirectories found in {dataset_path}")
        return
    
    # Sort alphabetically (same as preprocessing)
    sign_names = sorted([d.name for d in sign_folders])
    
    print(f"\n📂 Found {len(sign_names)} sign folders:")
    for idx, name in enumerate(sign_names):
        print(f"  [{idx}] {name}")
    
    # Set output path
    if output_path is None:
        output_path = Path(__file__).parent / 'models' / 'sign_labels.txt'
    else:
        output_path = Path(output_path)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Sign Language Class Labels\n")
        f.write("# Auto-generated from dataset folder structure\n")
        f.write(f"# Dataset: {dataset_path}\n")
        f.write("#\n")
        f.write("# Format: One sign name per line (line number = class index)\n")
        f.write("# Line 1 = Class 0, Line 2 = Class 1, etc.\n")
        f.write("#\n\n")
        
        for name in sign_names:
            f.write(f"{name}\n")
    
    print(f"\n✅ Created: {output_path}")
    print(f"\n📝 Class mapping:")
    for idx, name in enumerate(sign_names):
        print(f"   Class {idx:2d} → {name}")
    
    print(f"\n🎯 Total: {len(sign_names)} classes")
    print(f"\n💡 Next step: Run inference with these labels")
    print(f"   python inference.py")


def main():
    parser = argparse.ArgumentParser(
        description='Generate sign_labels.txt from dataset folder structure'
    )
    parser.add_argument(
        '--dataset_path',
        type=str,
        required=True,
        help='Path to dataset folder containing sign subfolders'
    )
    parser.add_argument(
        '--output_path',
        type=str,
        default=None,
        help='Path to save sign_labels.txt (default: ./models/sign_labels.txt)'
    )
    
    args = parser.parse_args()
    
    create_sign_labels(args.dataset_path, args.output_path)


if __name__ == '__main__':
    main()
