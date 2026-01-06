"""
Test Video Prediction Script
=============================

Test NS-AGF model predictions on a video file.
This helps debug prediction accuracy on known training videos.

Usage:
    python test_video_prediction.py --video path/to/video.mp4
    python test_video_prediction.py --video path/to/video.mp4 --show-frames
"""

import cv2
import numpy as np
import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from inference import SignLanguageInference


def extract_frames_from_video(video_path, max_frames=50):
    """
    Extract frames from video file.
    
    Args:
        video_path: Path to video file
        max_frames: Maximum number of frames to extract
        
    Returns:
        List of BGR frames
    """
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file: {video_path}")
        return []
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"\n📹 Video Info:")
    print(f"   Total frames: {total_frames}")
    print(f"   FPS: {fps:.2f}")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Will extract: {min(max_frames, total_frames)} frames")
    
    frames = []
    frame_interval = max(1, total_frames // max_frames)
    
    frame_count = 0
    extracted_count = 0
    
    while cap.isOpened() and extracted_count < max_frames:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Extract every N-th frame
        if frame_count % frame_interval == 0:
            frames.append(frame)
            extracted_count += 1
        
        frame_count += 1
    
    cap.release()
    
    print(f"✅ Extracted {len(frames)} frames from video")
    return frames


def test_video_prediction(video_path, model_path, show_frames=False, save_output=False):
    """
    Test prediction on a video file.
    
    Args:
        video_path: Path to video file
        model_path: Path to model checkpoint
        show_frames: Whether to show frames with landmarks
        save_output: Whether to save output visualization
    """
    print("=" * 70)
    print("NS-AGF Video Prediction Test")
    print("=" * 70)
    
    # Check if video exists
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return
    
    # Initialize inference system
    print("\n🔧 Loading NS-AGF inference system...")
    inference_system = SignLanguageInference(
        model_path=str(model_path),
        num_classes=None,  # Auto-detect
        class_names=None,  # Load from checkpoint
        confidence_threshold=0.25,  # Lenient for testing
        device='cpu'
    )
    print("✅ Model loaded successfully")
    print(f"   Classes: {inference_system.num_classes}")
    print(f"   Labels: {', '.join(inference_system.class_names[:5])}...")
    
    # Extract frames
    print(f"\n🎬 Processing video: {video_path.name}")
    frames = extract_frames_from_video(video_path, max_frames=50)
    
    if not frames:
        print("❌ No frames extracted from video")
        return
    
    # Extract landmarks
    print("\n🔍 Extracting landmarks from frames...")
    landmarks_sequence = []
    valid_frame_indices = []
    
    for i, frame in enumerate(frames):
        # Convert BGR to RGB (MediaPipe expects RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Extract landmarks
        landmarks, mp_results = inference_system.extractor.extract_with_results(frame_rgb)
        
        if landmarks is not None:
            landmarks_sequence.append(landmarks)
            valid_frame_indices.append(i)
            
            # Optionally show frame with landmarks
            if show_frames:
                from src.utils.mediapipe_helper import draw_landmarks
                vis_frame = frame.copy()
                vis_frame = draw_landmarks(vis_frame, mp_results)
                
                cv2.imshow('Frame with Landmarks', vis_frame)
                cv2.waitKey(50)  # Show for 50ms
    
    if show_frames:
        cv2.destroyAllWindows()
    
    print(f"✅ Extracted landmarks from {len(landmarks_sequence)}/{len(frames)} frames")
    print(f"   Valid frame indices: {valid_frame_indices[:10]}..." if len(valid_frame_indices) > 10 else f"   Valid frame indices: {valid_frame_indices}")
    
    if len(landmarks_sequence) < 10:
        print(f"❌ Insufficient valid frames ({len(landmarks_sequence)}) - need at least 10")
        return
    
    # Make prediction
    print("\n🔮 Making prediction...")
    result = inference_system.predict_from_sequence(landmarks_sequence)
    
    # Display results
    print("\n" + "=" * 70)
    print("PREDICTION RESULTS")
    print("=" * 70)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Predicted Sign: {result['sign']}")
        print(f"   Confidence: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
        
        if 'entropy' in result:
            print(f"   Entropy: {result['entropy']:.4f} (lower = more certain)")
        
        if 'top3' in result and result['top3']:
            print(f"\n📊 Top 3 Predictions:")
            for i, (sign, prob) in enumerate(result['top3'], 1):
                print(f"   {i}. {sign}: {prob:.4f} ({prob*100:.2f}%)")
    
    print("=" * 70)
    
    # Additional diagnostics
    print(f"\n🔬 Diagnostics:")
    print(f"   Frames processed: {len(frames)}")
    print(f"   Valid landmarks: {len(landmarks_sequence)}")
    print(f"   Landmarks shape: {landmarks_sequence[0].shape if landmarks_sequence else 'N/A'}")
    
    # Check motion variance
    if landmarks_sequence:
        sequence_array = np.array(landmarks_sequence)
        hand_landmarks = sequence_array[:, 33:, :]  # Hands only
        motion_variance = np.var(hand_landmarks)
        print(f"   Hand motion variance: {motion_variance:.6f}")
        print(f"   {'✅ Good motion' if motion_variance > 0.00005 else '⚠️ Low motion detected'}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Test NS-AGF predictions on video')
    parser.add_argument('--video', '-v', required=True, help='Path to video file')
    parser.add_argument('--model', '-m', 
                       default='models/ns_agcn.pth',
                       help='Path to model checkpoint (default: models/ns_agcn.pth)')
    parser.add_argument('--show-frames', '-s', 
                       action='store_true',
                       help='Show frames with landmarks during processing')
    parser.add_argument('--save-output', '-o',
                       action='store_true',
                       help='Save output visualization')
    
    args = parser.parse_args()
    
    # Run test
    result = test_video_prediction(
        video_path=args.video,
        model_path=args.model,
        show_frames=args.show_frames,
        save_output=args.save_output
    )
    
    # Exit code based on success
    if result and 'error' not in result:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed or returned error")
        sys.exit(1)


if __name__ == '__main__':
    main()
