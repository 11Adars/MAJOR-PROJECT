"""
Training Data Balance Checker
==============================

This script helps you check if your training data is balanced.
Imbalanced data causes one class to dominate predictions.

Usage:
    python check_data_balance.py --dataset_path "path/to/your/dataset"
"""

import argparse
from pathlib import Path
from collections import defaultdict

def check_balance(dataset_path):
    """Check class balance in dataset"""
    
    dataset_path = Path(dataset_path)
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    print("\n" + "=" * 60)
    print("📊 Training Data Balance Report")
    print("=" * 60)
    print(f"Dataset: {dataset_path}\n")
    
    # Get all sign folders
    sign_folders = sorted([f for f in dataset_path.iterdir() if f.is_dir()])
    
    if not sign_folders:
        print("❌ No sign folders found!")
        return
    
    # Count videos per sign
    video_counts = {}
    total_videos = 0
    
    for sign_folder in sign_folders:
        sign_name = sign_folder.name
        
        # Count video files
        video_files = list(sign_folder.glob('*.mp4')) + \
                     list(sign_folder.glob('*.avi')) + \
                     list(sign_folder.glob('*.mov'))
        
        count = len(video_files)
        video_counts[sign_name] = count
        total_videos += count
    
    # Calculate statistics
    avg_count = total_videos / len(sign_folders)
    max_count = max(video_counts.values())
    min_count = min(video_counts.values())
    
    print(f"Total Signs: {len(sign_folders)}")
    print(f"Total Videos: {total_videos}")
    print(f"Average per Sign: {avg_count:.1f}")
    print(f"Range: {min_count} - {max_count}\n")
    
    # Display counts
    print("=" * 60)
    print("Class Distribution:")
    print("=" * 60)
    
    # Sort by count (descending)
    sorted_counts = sorted(video_counts.items(), key=lambda x: x[1], reverse=True)
    
    for sign_name, count in sorted_counts:
        # Calculate percentage
        percentage = (count / total_videos) * 100
        
        # Visual bar
        bar_length = int((count / max_count) * 40)
        bar = "█" * bar_length
        
        # Color coding
        if count > avg_count * 1.5:
            status = "⚠️  OVERREPRESENTED"
            color_code = "🔴"
        elif count < avg_count * 0.5:
            status = "⚠️  UNDERREPRESENTED"
            color_code = "🟡"
        else:
            status = "✅ BALANCED"
            color_code = "🟢"
        
        print(f"{color_code} {sign_name:15s} {bar:40s} {count:3d} ({percentage:5.1f}%) {status}")
    
    print("\n" + "=" * 60)
    print("Analysis:")
    print("=" * 60)
    
    # Find problems
    overrepresented = [(name, count) for name, count in video_counts.items() if count > avg_count * 1.5]
    underrepresented = [(name, count) for name, count in video_counts.items() if count < avg_count * 0.5]
    
    if overrepresented:
        print(f"\n🔴 OVERREPRESENTED CLASSES (>{avg_count * 1.5:.0f} videos):")
        for name, count in sorted(overrepresented, key=lambda x: x[1], reverse=True):
            excess = count - int(avg_count)
            print(f"   - {name}: {count} videos (remove {excess} to balance)")
    
    if underrepresented:
        print(f"\n🟡 UNDERREPRESENTED CLASSES (<{avg_count * 0.5:.0f} videos):")
        for name, count in sorted(underrepresented, key=lambda x: x[1]):
            needed = int(avg_count) - count
            print(f"   - {name}: {count} videos (add {needed} more to balance)")
    
    if not overrepresented and not underrepresented:
        print("\n✅ Dataset is well balanced!")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("💡 Recommendations:")
    print("=" * 60)
    
    if overrepresented:
        print("\n1. REDUCE overrepresented classes:")
        for name, count in overrepresented[:3]:
            target = int(avg_count * 1.2)
            print(f"   - Keep only {target} best quality videos from '{name}'")
    
    if underrepresented:
        print("\n2. INCREASE underrepresented classes:")
        for name, count in underrepresented[:3]:
            needed = int(avg_count) - count
            print(f"   - Record {needed} more videos for '{name}'")
    
    print("\n3. TARGET DISTRIBUTION:")
    target_per_class = int(avg_count)
    print(f"   - Aim for {target_per_class} videos per class (±3)")
    print(f"   - This means {target_per_class * len(sign_folders)} total videos")
    
    print("\n4. QUICK FIX for inference:")
    if overrepresented:
        dominant = overrepresented[0][0]
        print(f"   - '{dominant}' is likely dominating predictions")
        print(f"   - Inference now has bias correction enabled")
        print(f"   - For best results, retrain with balanced data")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Check training data balance')
    parser.add_argument(
        '--dataset_path',
        type=str,
        required=True,
        help='Path to dataset folder (contains sign subfolders)'
    )
    
    args = parser.parse_args()
    check_balance(args.dataset_path)


if __name__ == '__main__':
    main()
