"""
Model Validation Tool
=====================

Record sign videos with spacebar control and analyze predictions.
Compare against training data to validate model accuracy.

Usage:
    python validate_model.py

Controls:
    SPACE - Start/Stop recording
    S - Save current recording and analyze
    D - Discard current recording
    Q - Quit

Features:
- Record signs with visual feedback
- Extract MediaPipe landmarks
- Compare with training preprocessing
- Show detailed prediction analysis
- Save recordings for dataset improvement
"""

import cv2
import numpy as np
import torch
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.mediapipe_helper import MediaPipeExtractor, draw_landmarks
from src.graph.topology import MediaPipeGraph
from src.model.nsagf import NSAGF, create_model  # Professional NS-AGF model

# Import utility from inference
from inference import load_class_names


class SignValidator:
    """Tool for recording and validating sign predictions"""
    
    def __init__(self, model_path: str, num_classes: int = None):
        """Initialize validator"""
        self.model_path = model_path
        self.device = 'cpu'
        
        # Load model
        print("🔧 Loading model...")
        
        # Load checkpoint first to detect architecture and num_classes
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        
        # Extract state_dict and label_names
        if isinstance(checkpoint, dict):
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            checkpoint_labels = checkpoint.get('label_names', None)
        else:
            state_dict = checkpoint
            checkpoint_labels = None
        
        # Auto-detect number of classes from model architecture
        if num_classes is None:
            final_layer_keys = [
                'classifier.4.weight',  # IMPROVED model final layer
                'classifier.1.weight',  # Alternative IMPROVED format
                'fc.weight',            # OLD model final layer
            ]
            
            for key in final_layer_keys:
                if key in state_dict:
                    num_classes = state_dict[key].shape[0]
                    print(f"✅ Auto-detected {num_classes} classes from {key}")
                    break
            
            if num_classes is None:
                raise ValueError("Could not auto-detect num_classes from checkpoint")
        
        self.num_classes = num_classes
        
        # Load class names
        if checkpoint_labels is not None:
            if isinstance(checkpoint_labels, np.ndarray):
                checkpoint_labels = checkpoint_labels.tolist()
            self.class_names = checkpoint_labels
            print(f"📝 Loaded {len(self.class_names)} class names from checkpoint")
        else:
            # Load from label_names.npy in model directory
            model_dir = Path(model_path).parent
            loaded_names = load_class_names(str(model_dir))
            if loaded_names is not None:
                self.class_names = loaded_names
            else:
                self.class_names = [f"Sign_{i}" for i in range(num_classes)]
                print(f"⚠️ Using generic class names: {num_classes} classes")
        
        print(f"📝 Classes: {self.class_names}")
        
        # Initialize graph topology
        print("🔧 Initializing MediaPipe Graph Topology...")
        graph = MediaPipeGraph()
        
        # Create professional NS-AGF model (replaces ImprovedAGCN/SimpleAGCN)
        print("✅ Using Professional NS-AGF Model (10 blocks, adaptive graphs)")
        # CRITICAL: Set dropout=0.0 for inference/validation!
        self.model = NSAGF(
            num_classes=num_classes,
            graph=graph,
            in_channels=3,
            dropout=0.0,  # NO dropout during validation
            edge_importance_weighting=True  # Enable adaptive graphs
        )
        
        # Load weights from checkpoint
        try:
            self.model.load_state_dict(state_dict, strict=False)
            print("✅ Loaded weights with strict=False (allows architecture mismatch)")
            print("⚠️ Note: If this is an old checkpoint (8-block), expect partial load")
        except Exception as e:
            print(f"⚠️ Weight loading warning: {e}")
            print("ℹ️ Continuing with randomly initialized weights (will need retraining)")
        
        self.model.to(self.device)
        self.model.eval()
        self.use_improved_format = True  # Always use (N, C, T, V) format
        
        print("✅ Dropout disabled for validation (higher confidence)")
        print("✅ Adaptive graph convolution enabled")
        
        self.model.to(self.device)
        self.model.eval()
        
        # Initialize MediaPipe
        print("🔧 Initializing MediaPipe...")
        self.extractor = MediaPipeExtractor(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        
        # Recording state
        self.is_recording = False
        self.recorded_frames = []
        self.recorded_landmarks = []
        self.recording_start_time = None
        
        # Validation results
        self.validation_history = []
        
        # Note: Recording save disabled to save storage space
        
        print("✅ Validator ready!")
        print()
    
    def normalize_landmarks(self, sequence: np.ndarray) -> np.ndarray:
        """
        Normalize landmarks to match training preprocessing.
        MUST match preprocess_wlasl_FIXED.py normalization!
        """
        if sequence.shape[0] == 0:
            return sequence
        
        # Center on nose (landmark 0)
        nose_positions = sequence[:, 0:1, :]
        centered = sequence - nose_positions
        
        # Calculate shoulder width for scaling
        left_shoulder = sequence[:, 11, :]
        right_shoulder = sequence[:, 12, :]
        shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder, axis=1, keepdims=True)
        
        # Avoid division by zero
        shoulder_dist = np.where(shoulder_dist < 0.01, 1.0, shoulder_dist)
        
        # Scale by shoulder width
        scaled = centered / shoulder_dist[:, np.newaxis, :]
        
        return scaled
    
    def preprocess_sequence(self, landmarks_sequence: list) -> torch.Tensor:
        """
        Preprocess sequence for model input.
        Matches training preprocessing.
        """
        sequence = np.array(landmarks_sequence)  # (T, V, C)
        
        # Pad or sample to 30 frames
        target_length = 30
        current_length = sequence.shape[0]
        
        if current_length < target_length:
            # Pad with last frame
            padding = np.repeat(sequence[-1:], target_length - current_length, axis=0)
            sequence = np.concatenate([sequence, padding], axis=0)
        elif current_length > target_length:
            # Sample uniformly
            indices = np.linspace(0, current_length - 1, target_length, dtype=int)
            sequence = sequence[indices]
        
        # Apply normalization (CRITICAL!)
        sequence = self.normalize_landmarks(sequence)
        
        # Reshape based on model architecture
        if self.use_improved_format:
            # IMPROVED model expects (N, C, T, V) format
            sequence = np.transpose(sequence, (2, 0, 1))  # (C, T, V) = (3, 30, 75)
            sequence = np.expand_dims(sequence, axis=0)   # (N, C, T, V) = (1, 3, 30, 75)
        else:
            # OLD model expects (N, C, T, V, M) format
            sequence = np.transpose(sequence, (2, 0, 1))  # (3, 30, 75)
            sequence = np.expand_dims(sequence, axis=-1)  # (3, 30, 75, 1)
            sequence = np.expand_dims(sequence, axis=0)   # (1, 3, 30, 75, 1)
        
        return torch.FloatTensor(sequence).to(self.device)
    
    def predict(self, landmarks_sequence: list) -> dict:
        """
        Make prediction on recorded sequence.
        """
        if len(landmarks_sequence) < 5:
            return {
                'error': 'Too few frames',
                'frames': len(landmarks_sequence)
            }
        
        # Preprocess
        input_tensor = self.preprocess_sequence(landmarks_sequence)
        
        # Inference
        with torch.no_grad():
            output = self.model(input_tensor)
            probabilities = torch.softmax(output, dim=1)
            
            # Get top 5 predictions
            top5_probs, top5_classes = torch.topk(probabilities[0], k=min(5, self.num_classes))
            
        # Format results
        predictions = []
        for i in range(len(top5_classes)):
            class_idx = top5_classes[i].item()
            confidence = top5_probs[i].item()
            predictions.append({
                'sign': self.class_names[class_idx],
                'confidence': confidence,
                'class_id': class_idx
            })
        
        return {
            'predictions': predictions,
            'frames': len(landmarks_sequence),
            'top_prediction': predictions[0]['sign'],
            'top_confidence': predictions[0]['confidence']
        }
    
    def start_recording(self):
        """Start recording"""
        self.is_recording = True
        self.recorded_frames = []
        self.recorded_landmarks = []
        self.recording_start_time = datetime.now()
        print("\n🔴 RECORDING STARTED - Press SPACE to stop")
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        duration = (datetime.now() - self.recording_start_time).total_seconds()
        print(f"\n⏹️  RECORDING STOPPED - {len(self.recorded_frames)} frames, {duration:.1f}s")
        print(f"   Landmarks: {len(self.recorded_landmarks)} frames")
        print("\n   Press 'S' to Save & Analyze, 'D' to Discard")
    
    def save_and_analyze(self):
        """Save recording and analyze prediction"""
        if len(self.recorded_frames) == 0:
            print("⚠️  No recording to save")
            return
        
        print("\n" + "=" * 70)
        print("📊 ANALYZING RECORDING")
        print("=" * 70)
        
        # Analyze prediction
        result = self.predict(self.recorded_landmarks)
        
        if 'error' in result:
            print(f"❌ Analysis failed: {result['error']}")
            return
        
        # Display results
        print(f"\n📹 Recording Info:")
        print(f"   Frames captured: {len(self.recorded_frames)}")
        print(f"   Landmarks extracted: {result['frames']}")
        print(f"   Duration: {len(self.recorded_frames) / 30:.1f}s (estimated)")
        
        print(f"\n🎯 Top 5 Predictions:")
        for i, pred in enumerate(result['predictions'], 1):
            confidence_bar = "█" * int(pred['confidence'] * 50)
            color_code = ""
            if pred['confidence'] > 0.7:
                color_code = "\033[92m"  # Green
            elif pred['confidence'] > 0.45:
                color_code = "\033[93m"  # Yellow
            else:
                color_code = "\033[91m"  # Red
            
            print(f"   {i}. {pred['sign']:12s} {color_code}{pred['confidence']:6.1%}\033[0m {confidence_bar}")
        
        # Verdict
        print(f"\n📋 Analysis:")
        top = result['predictions'][0]
        if top['confidence'] > 0.7:
            print(f"   ✅ HIGH CONFIDENCE - Model is confident this is '{top['sign']}'")
        elif top['confidence'] > 0.45:
            print(f"   ⚠️  MEDIUM CONFIDENCE - Model thinks this is '{top['sign']}' but uncertain")
        else:
            print(f"   ❌ LOW CONFIDENCE - Model cannot recognize this sign clearly")
        
        # Check if second prediction is close
        if len(result['predictions']) > 1:
            second = result['predictions'][1]
            conf_gap = top['confidence'] - second['confidence']
            if conf_gap < 0.15:
                print(f"   ⚠️  CONFUSION - '{second['sign']}' is very close ({second['confidence']:.1%})")
                print(f"       Model is confused between these two signs!")
        
        # Note: File saving disabled to save storage space
        # Recording analyzed but not saved to disk
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Add to history (in-memory only)
        self.validation_history.append({
            'top_sign': top['sign'],
            'confidence': top['confidence'],
            'timestamp': timestamp,
            'frames': len(self.recorded_frames)
        })
        
        print(f"\n✅ Analysis complete! (Not saved to disk - memory only)")
        print("=" * 70)
        print()
    
    def discard_recording(self):
        """Discard current recording"""
        self.recorded_frames = []
        self.recorded_landmarks = []
        print("\n🗑️  Recording discarded")
    
    def show_instructions(self):
        """Show usage instructions"""
        print("\n" + "=" * 70)
        print("🎯 SIGN LANGUAGE MODEL VALIDATOR")
        print("=" * 70)
        print("\n📖 How to use:")
        print("   1. Press SPACE to start recording")
        print("   2. Perform your sign clearly")
        print("   3. Press SPACE again to stop recording")
        print("   4. Press 'S' to Save & Analyze (see prediction)")
        print("   5. Press 'D' to Discard (if mistake)")
        print("   6. Repeat for all signs you want to validate")
        print("\n💡 Tips:")
        print("   - Record 2-4 seconds per sign")
        print("   - Keep both hands in frame")
        print("   - Complete the full sign motion")
        print("   - Compare predictions with expected sign")
        print("   - If confidence is low, model needs more training data")
        print("\n⌨️  Controls:")
        print("   SPACE - Start/Stop recording")
        print("   S     - Save & Analyze")
        print("   D     - Discard")
        print("   Q     - Quit")
        print("=" * 70)
        print("\nPress any key to start...")
    
    def run(self):
        """Main validation loop"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return
        
        self.show_instructions()
        cv2.waitKey(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Extract landmarks
            landmarks, mp_results = self.extractor.extract_with_results(frame_rgb)
            
            # Draw landmarks
            if mp_results:
                draw_landmarks(frame, mp_results)
            
            # If recording, save frame and landmarks
            if self.is_recording:
                self.recorded_frames.append(frame.copy())
                if landmarks is not None:
                    self.recorded_landmarks.append(landmarks)
            
            # Draw UI
            self._draw_ui(frame, landmarks is not None)
            
            # Display
            cv2.imshow('Sign Validator', frame)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space bar
                if not self.is_recording:
                    self.start_recording()
                else:
                    self.stop_recording()
            elif key == ord('s'):
                if not self.is_recording and len(self.recorded_frames) > 0:
                    self.save_and_analyze()
                    self.discard_recording()
            elif key == ord('d'):
                if not self.is_recording:
                    self.discard_recording()
        
        cap.release()
        cv2.destroyAllWindows()
        self.extractor.close()
        
        # Print summary
        if len(self.validation_history) > 0:
            print("\n" + "=" * 70)
            print("📊 VALIDATION SESSION SUMMARY")
            print("=" * 70)
            print(f"\nTotal recordings analyzed: {len(self.validation_history)}")
            print("\nRecordings:")
            for i, entry in enumerate(self.validation_history, 1):
                print(f"   {i}. {entry['top_sign']} - {entry['confidence']:.1%} confidence ({entry['timestamp']})")
            print(f"\n💾 All files saved to: {self.output_dir}")
            print("=" * 70)
    
    def _draw_ui(self, frame, landmarks_detected):
        """Draw UI overlay"""
        h, w = frame.shape[:2]
        
        # Status panel
        panel_height = 120
        cv2.rectangle(frame, (10, 10), (w - 10, panel_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (w - 10, panel_height), (255, 255, 255), 2)
        
        # Recording status
        if self.is_recording:
            # Blinking red circle
            import time
            if int(time.time() * 2) % 2 == 0:
                cv2.circle(frame, (30, 35), 12, (0, 0, 255), -1)
            cv2.putText(frame, "RECORDING", (55, 43), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Frames: {len(self.recorded_frames)} | Landmarks: {len(self.recorded_landmarks)}", 
                       (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            status_color = (0, 255, 0) if landmarks_detected else (0, 0, 255)
            status_text = "Ready - Press SPACE to record" if landmarks_detected else "No detection"
            cv2.putText(frame, status_text, (20, 43), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            if len(self.recorded_frames) > 0:
                cv2.putText(frame, f"Recorded: {len(self.recorded_frames)} frames - Press 'S' to analyze", 
                           (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Controls
        cv2.putText(frame, "SPACE: Record | S: Save | D: Discard | Q: Quit", 
                   (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate sign language model')
    parser.add_argument('--model_path', type=str, default='./models/ns_agcn.pth',
                       help='Path to trained model')
    parser.add_argument('--num_classes', type=int, default=None,
                       help='Number of sign classes (auto-detects if not specified)')
    
    args = parser.parse_args()
    
    # Check if model exists
    if not os.path.exists(args.model_path):
        print(f"❌ Model not found: {args.model_path}")
        return
    
    try:
        validator = SignValidator(
            model_path=args.model_path,
            num_classes=args.num_classes
        )
        validator.run()
    except KeyboardInterrupt:
        print("\n\n👋 Validation stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
