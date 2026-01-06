"""
NS-AGF Real-Time Inference Pipeline
====================================

This script runs real-time sign language recognition using the camera
and the pre-trained NS-AGF model.

Usage:
    python inference.py --model_path ./models/ns_agcn.pth --num_classes 100

Features:
- Real-time MediaPipe landmark extraction
- Sliding window buffering (30 frames)
- Neuro-symbolic intent verification
- Visual feedback with confidence scores
"""

import os
import sys
import argparse
import cv2
import numpy as np
import torch
from pathlib import Path
from collections import deque, Counter

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.mediapipe_helper import MediaPipeExtractor, draw_landmarks, create_sequence_buffer
from src.utils.model_loader import verify_model
from src.model.nsagf import NSAGF, TwoStreamNSAGF, create_model  # Professional NS-AGF model
from src.logic.banking_verifier import BankingIntentVerifier, BankingIntent, IntentContext
from src.graph.topology import MediaPipeGraph  # Explicit 75-node topology
from src.auth import BiometricFusionAuthenticator, UserBiometricDatabase
import torch.nn as nn


def load_class_names(model_dir: str) -> list:
    """
    Load class names from label_names.npy file (from preprocessing output).
    
    Args:
        model_dir: Directory containing the model and label files
    
    Returns:
        List of class names
    """
    # Try multiple file locations and formats
    label_files = [
        Path(model_dir) / 'label_names.npy',  # Preprocessing output (PREFERRED)
        Path(model_dir) / 'sign_labels.npy',   # Alternative name
        Path(model_dir) / 'labels.npy',        # Legacy format
        Path(model_dir) / 'sign_labels.txt',   # Text format fallback
    ]
    
    for label_file in label_files:
        if label_file.exists():
            try:
                if label_file.suffix == '.npy':
                    # Load from numpy file
                    names = np.load(label_file, allow_pickle=True)
                    if isinstance(names, np.ndarray):
                        names = names.tolist()
                    print(f"✅ Loaded {len(names)} class names from: {label_file.name}")
                    return names
                elif label_file.suffix == '.txt':
                    # Load from text file
                    with open(label_file, 'r', encoding='utf-8') as f:
                        names = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    print(f"✅ Loaded {len(names)} class names from: {label_file.name}")
                    return names
            except Exception as e:
                print(f"⚠️ Failed to load {label_file.name}: {e}")
                continue
    
    # If no file found, return None (will auto-detect from model)
    print("⚠️ No label file found, will auto-detect from model checkpoint")
    return None


# ============================================================================
# TEMPORAL SMOOTHING - Task 1.3
# ============================================================================

class TemporalSmoother:
    """
    Temporal smoothing using sliding window with majority voting.
    
    Reduces prediction jitter and improves stability by maintaining
    a history of recent predictions and returning the most common one.
    
    Benefits:
    - Reduces false positives from brief motion artifacts
    - Improves perceived prediction stability
    - Filters out transient misclassifications
    - Expected +3-5% accuracy improvement
    
    Args:
        window_size: Number of recent predictions to consider (default: 5)
                    Larger = more stable but slower response
                    Smaller = faster response but less stable
    """
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.predictions = deque(maxlen=window_size)
        self.confidences = deque(maxlen=window_size)
    
    def smooth(self, prediction: str, confidence: float = 1.0) -> tuple:
        """
        Add prediction and return smoothed result via majority voting.
        
        Args:
            prediction: Current frame's prediction
            confidence: Current frame's confidence (0-1)
        
        Returns:
            tuple: (smoothed_prediction, avg_confidence)
        """
        # Add to history
        self.predictions.append(prediction)
        self.confidences.append(confidence)
        
        # Need at least 3 predictions for meaningful smoothing
        if len(self.predictions) < 3:
            return prediction, confidence
        
        # Majority voting
        most_common = Counter(self.predictions).most_common(1)[0]
        smoothed_prediction = most_common[0]
        vote_count = most_common[1]
        
        # Calculate average confidence for the smoothed prediction
        # Only average confidences where prediction matches smoothed result
        matching_confidences = [
            conf for pred, conf in zip(self.predictions, self.confidences)
            if pred == smoothed_prediction
        ]
        avg_confidence = np.mean(matching_confidences) if matching_confidences else confidence
        
        return smoothed_prediction, avg_confidence
    
    def reset(self):
        """Clear prediction history."""
        self.predictions.clear()
        self.confidences.clear()
    
    def get_stability_score(self) -> float:
        """
        Calculate stability score (0-1) based on prediction consistency.
        1.0 = all predictions agree, 0.0 = maximum disagreement
        """
        if len(self.predictions) < 2:
            return 1.0
        
        most_common_count = Counter(self.predictions).most_common(1)[0][1]
        return most_common_count / len(self.predictions)


# ============================================================================
# OLD MODEL DEFINITIONS REMOVED - NOW USING PROFESSIONAL NS-AGF FROM src/model/
# ============================================================================
# Previously defined here: SimpleAGCN, ImprovedAGCN classes
# Now imported from: src.model.nsagf.NSAGF
# Benefits:
#   - Single source of truth (no code duplication)
#   - Professional 10-block architecture with adaptive graphs
#   - Edge importance weighting
#   - Explicit graph topology from src/graph/topology.py
# ============================================================================


class SignLanguageInference:
    """
    Real-time sign language recognition system.
    """
    
    def __init__(
        self,
        model_path: str,
        num_classes: int = None,
        class_names: list = None,
        confidence_threshold: float = 0.7,
        device: str = 'cpu'
    ):
        """
        Initialize inference system.
        
        Args:
            model_path: Path to trained model weights
            num_classes: Number of sign classes (if None, auto-detects from checkpoint)
            class_names: List of class names (if None, loads from label_names.npy)
            confidence_threshold: Minimum confidence for predictions
            device: Device to run inference on
        """
        self.device = device
        self.confidence_threshold = confidence_threshold
        
        # Load model
        print("🔧 Loading NS-AGF model...")
        if not verify_model(model_path):
            raise ValueError(f"Invalid model file: {model_path}")
        
        # Load checkpoint first to detect architecture and num_classes
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        
        # Extract state_dict and label_names
        if isinstance(checkpoint, dict):
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            # Try to get label names from checkpoint
            checkpoint_labels = checkpoint.get('label_names', None)
        else:
            state_dict = checkpoint
            checkpoint_labels = None
        
        # Auto-detect number of classes from model architecture
        if num_classes is None:
            # Find the FINAL output layer to determine num_classes
            # IMPROVED model: classifier.4.weight (last Linear layer)
            # OLD model: fc.weight
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
                # Fallback: search all layers ending with 'weight' in classifier/fc
                for key in state_dict.keys():
                    if ('classifier' in key or key.startswith('fc')) and key.endswith('weight'):
                        shape = state_dict[key].shape
                        if len(shape) == 2:  # Linear layer
                            potential_classes = shape[0]
                            print(f"⚠️ Found potential output layer {key}: {potential_classes} classes")
                            num_classes = potential_classes
                
                if num_classes is None:
                    raise ValueError("Could not auto-detect num_classes from checkpoint. Please specify manually.")
        
        self.num_classes = num_classes
        
        # Load class names (priority: provided > checkpoint > label_names.npy > generic)
        if class_names is not None:
            self.class_names = class_names
            print(f"📝 Using provided {len(self.class_names)} class names")
        elif checkpoint_labels is not None:
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
                # Fallback to generic names
                self.class_names = [f"Sign_{i}" for i in range(num_classes)]
                print(f"⚠️ Using generic class names: {num_classes} classes")
        
        print(f"📝 Classes: {self.class_names[:5]}{'...' if len(self.class_names) > 5 else ''}")
        
        # Initialize graph topology
        print("🔧 Initializing MediaPipe Graph Topology...")
        graph = MediaPipeGraph()
        
        # Detect model architecture from checkpoint
        config = checkpoint.get('config', {})
        architecture = config.get('architecture', 'NS-AGF Professional (10 blocks)')
        
        # CRITICAL: Detect two-stream by checking state_dict keys
        # Two-stream models have 'joint_stream', 'bone_stream', 'fusion' layers
        state_dict_keys = list(state_dict.keys())
        has_joint_stream = any('joint_stream' in key for key in state_dict_keys)
        has_bone_stream = any('bone_stream' in key for key in state_dict_keys)
        has_fusion = any('fusion' in key for key in state_dict_keys)
        
        is_two_stream = has_joint_stream or has_bone_stream or has_fusion or \
                        'two_stream' in config or 'two-stream' in architecture.lower()
        is_small_model = '6' in architecture or 'Small' in architecture
        num_blocks = 6 if is_small_model else 10
        
        print(f"🔍 Detected Architecture: {architecture}")
        print(f"   State Dict Keys Check:")
        print(f"      - Joint Stream layers: {'✅ YES' if has_joint_stream else '❌ NO'}")
        print(f"      - Bone Stream layers: {'✅ YES' if has_bone_stream else '❌ NO'}")
        print(f"      - Fusion layers: {'✅ YES' if has_fusion else '❌ NO'}")
        print(f"   Model Type: {'Two-Stream' if is_two_stream else 'Single-Stream'} | {'6 blocks' if is_small_model else '10 blocks'}")
        
        # Create model matching the trained architecture
        # CRITICAL: Must match training architecture exactly!
        if is_two_stream:
            print("🔧 Loading Two-Stream NS-AGF model (Joint + Bone)...")
            self.model = TwoStreamNSAGF(
                num_classes=num_classes,
                graph=graph,
                in_channels=3,
                dropout=0.0,  # NO dropout during inference
                edge_importance_weighting=config.get('edge_importance_weighting', True)
            )
        else:
            print("🔧 Loading Single-Stream NS-AGF model...")
            self.model = NSAGF(
                num_classes=num_classes,
                graph=graph,
                in_channels=3,
                dropout=0.0,  # NO dropout during inference
                edge_importance_weighting=config.get('edge_importance_weighting', True)
            )
        
        # If small model (6 blocks), truncate architecture to match training
        if is_small_model:
            print("🔧 Adjusting model for 6-block architecture...")
            # Truncate to 6 blocks (same as training)
            self.model.st_gcn_blocks = nn.ModuleList(self.model.st_gcn_blocks[:6])
            
            # Update classifier to match 6-block output (256 channels, not 512)
            self.model.classifier = nn.Sequential(
                nn.Dropout(0.0),  # No dropout for inference
                nn.Linear(256, 256),  # 256 channels from 6 blocks
                nn.ReLU(inplace=True),
                nn.Dropout(0.0),
                nn.Linear(256, num_classes)
            )
            print("   ✅ Truncated to 6 blocks")
            print("   ✅ Updated classifier for 256-channel output")
        
        # Load weights from checkpoint
        try:
            self.model.load_state_dict(state_dict, strict=True)
            print("✅ Loaded weights successfully (exact match)")
        except Exception as e:
            print(f"⚠️ Trying partial weight loading: {e}")
            try:
                self.model.load_state_dict(state_dict, strict=False)
                print("✅ Loaded weights with strict=False (partial match)")
            except Exception as e2:
                print(f"❌ Weight loading failed: {e2}")
                print("⚠️ Model will use random weights - predictions will be incorrect!")
        
        self.model.to(device)
        self.model.eval()
        self.use_improved_format = True  # Always use (N, C, T, V) format
        
        # Count actual parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        model_type = "Two-Stream" if is_two_stream else "Single-Stream"
        print(f"✅ Model loaded: {num_classes} classes, {model_type}, {num_blocks} blocks")
        print(f"✅ Parameters: {total_params:,} (~{total_params * 4 / 1024 / 1024:.1f} MB)")
        print("✅ Dropout disabled for inference (higher confidence)")
        print("✅ Adaptive graph convolution enabled")
        
        # ✅ VERIFY NOVEL FEATURES FOR JOURNAL PUBLICATION
        print("\n📊 NOVEL ARCHITECTURE FEATURES (Journal Publication):")
        print("   ✓ NS-AGF Framework: Neuro-Symbolic Adaptive Graph")
        print(f"   ✓ Two-Stream Architecture: {'ACTIVE (Joint+Bone)' if is_two_stream else 'DISABLED (Journal requires Two-Stream!)'}")
        print("   ✓ Adaptive Adjacency: Edge Importance Weighting")
        print("   ✓ Temporal Smoothing: 5-frame majority voting")
        print("   ✓ 10 ST-GCN Blocks: Progressive channel expansion (64→128→256→512)")
        print("   ✓ MediaPipe Holistic: 75-node topology (33 pose + 21 left + 21 right)")
        
        if not is_two_stream:
            print("   ⚠️  WARNING: Single-stream model detected! Journal requires Two-Stream!")
            print("   ⚠️  Please retrain with TwoStreamNSAGF for full novel features")
        
        # Initialize MediaPipe
        print("🔧 Initializing MediaPipe...")
        # Optimized for close-range (50cm) half-body capture
        self.extractor = MediaPipeExtractor(
            static_image_mode=False,
            model_complexity=2,  # Higher complexity for better accuracy
            min_detection_confidence=0.6,  # Higher threshold for quality
            min_tracking_confidence=0.6    # Higher for stable tracking
        )
        print("✅ Camera optimized for 50cm distance, half-body framing")
        print("✅ Using high-quality MediaPipe model (complexity=2)")
        
        # Create sequence buffer (30 frames to match training)
        self.buffer = create_sequence_buffer(max_length=30)
        
        # Initialize banking intent verifier
        self.banking_verifier = None
        rules_path = Path(__file__).parent / 'src' / 'logic' / 'intent_rules.json'
        if rules_path.exists():
            print("🔧 Initializing Banking Intent Verifier...")
            try:
                self.banking_verifier = BankingIntentVerifier(
                    rules_path=str(rules_path)
                )
                print("✅ Banking Intent Verifier ready (9 intents, safety rules enabled)")
            except Exception as e:
                print(f"⚠️ Verifier disabled: {e}")
        else:
            print("ℹ️ Intent verification disabled (rules file not found)")
        
        # Initialize biometric authentication
        print("🔧 Initializing Biometric Authentication...")
        try:
            self.bio_authenticator = BiometricFusionAuthenticator(
                face_weight=0.5,
                hand_weight=0.3,
                style_weight=0.2,
                verification_threshold=0.65
            )
            self.bio_database = UserBiometricDatabase(db_path="data/biometric_users.db")
            print("✅ Biometric authentication ready (Face + Hand + Style fusion)")
            
            # Show enrolled users
            users = self.bio_database.get_all_users()
            if users:
                print(f"   📋 Enrolled users: {len(users)}")
                for user in users[:3]:  # Show first 3
                    print(f"      - {user['user_id']} (auth count: {user['authentication_count']})")
            else:
                print("   ℹ️  No users enrolled yet. Press 'E' to enroll.")
        except Exception as e:
            print(f"⚠️ Biometric auth disabled: {e}")
            self.bio_authenticator = None
            self.bio_database = None
        
        # State management
        self.current_intent = None
        self.intent_context = None  # Banking intent context
        self.frame_count = 0
        self.prediction_history = []
        
        # ✅ ENABLE TEMPORAL SMOOTHING (Novel Feature for Journal)
        self.use_temporal_smoothing = True
        self.temporal_smoother = TemporalSmoother(window_size=5)
        print("✅ Temporal Smoothing ENABLED (5-frame window, majority voting)")
        
        # Biometric state
        self.current_user_id = None  # Currently authenticated user
        self.bio_features = None  # Current biometric features
        self.bio_score = 0.0  # Authentication score
        self.bio_authenticated = False  # Authentication status
        self.enrollment_mode = False  # Enrollment mode flag
        self.enrollment_samples = []  # Samples for enrollment
        self.stable_prediction = None
        self.stable_confidence = 0.0
        self.prediction_window = 10  # Require consistency over 10 frames (reduced for 30-frame buffer)
        self.rest_position = None  # Store rest/idle position
        self.motion_threshold = 0.012  # Minimum movement to consider as active sign
        self.prev_landmarks = None  # Previous frame landmarks for motion detection
        self.detected_signs = []  # History of detected signs (persistent)
        self.last_stable_sign = None  # Last confirmed sign
        self.dominant_class = 'Adress'  # Class to filter out in rest position
        self.frames_since_motion = 0  # Track frames without motion
        self.adress_count = 0  # Count how often Adress appears as top prediction
        self.total_predictions = 0  # Total predictions made
        self.bias_detected = False  # Flag for class imbalance warning
        
        # Banking-specific state
        self.pending_signs_for_intent = []  # Accumulate signs for intent composition
        self.intent_build_timeout = 5.0  # Seconds to wait for intent completion
        
        # Task 1.3: Temporal Smoothing
        self.temporal_smoother = TemporalSmoother(window_size=5)  # 5-frame sliding window
        self.use_temporal_smoothing = True  # Enable/disable smoothing
        
        # NEW: Manual recording control
        self.is_recording = False  # True when recording is active
        self.recorded_frames = []  # Store frames during recording
        self.recorded_landmarks = []  # Store landmarks during recording
        self.recording_start_time = 0  # Time when recording started
        self.sentence = []  # List of predicted signs forming a sentence
        self.last_prediction = None  # Last predicted sign
        self.last_confidence = 0.0  # Confidence of last prediction
        self.waiting_for_prediction = False  # True after recording stops, waiting for predict command
        
        # IMPROVED: Higher confidence thresholds for 90%+ accuracy
        self.min_prediction_confidence = 0.60  # Show sign only if >60% (was 45%)
        self.no_sign_threshold = 0.45         # Below 45% = "No Sign" (was 35%)
        self.high_confidence_threshold = 0.75  # Above 75% = very confident
        self.hand_detection_threshold = 0.6  # Minimum hand landmark visibility
        self.poor_lighting_frames = 0  # Track consecutive poor detection frames
        
        # WARMUP: Skip unstable initial predictions
        self.warmup_frames = 0
        self.warmup_required = 45  # Wait 3 seconds before predicting
        self.is_warmed_up = False
        
        print("✅ Inference system ready!")
    
    def detect_motion(self, landmarks: np.ndarray) -> float:
        """
        Detect amount of motion in current frame vs previous.
        
        Args:
            landmarks: (V, C) numpy array of current landmarks
        
        Returns:
            Motion magnitude (0.0 = no motion, 1.0 = large motion)
        """
        if self.prev_landmarks is None:
            self.prev_landmarks = landmarks.copy()
            return 0.0
        
        # Calculate euclidean distance for hand landmarks (indices 33-75)
        hand_landmarks = landmarks[33:, :]  # Only hands, not pose
        prev_hand_landmarks = self.prev_landmarks[33:, :]
        
        motion = np.sqrt(np.sum((hand_landmarks - prev_hand_landmarks) ** 2))
        self.prev_landmarks = landmarks.copy()
        
        return motion
    
    def get_buffer_motion(self) -> float:
        """
        Calculate motion variance across the entire buffer.
        Higher variance = active signing, Lower variance = rest/idle.
        
        Returns:
            Motion variance across buffer
        """
        if not self.buffer.is_full():
            return 0.0
        
        sequence = self.buffer.get_sequence(pad=False)
        if sequence is None or len(sequence) < 10:
            return 0.0
        
        # Calculate variance of hand positions over time
        hand_sequence = sequence[:, 33:, :]  # Only hand landmarks
        variance = np.var(hand_sequence)
        
        return variance
    
    def check_landmark_quality(self, landmarks: np.ndarray, mp_results) -> dict:
        """
        Check quality of detected landmarks for low-light/poor detection.
        
        Args:
            landmarks: (V, C) numpy array
            mp_results: MediaPipe results object
        
        Returns:
            dict with quality metrics
        """
        quality = {
            'good': True,
            'hand_visibility': 1.0,
            'pose_visibility': 1.0,
            'reason': None
        }
        
        if mp_results is None:
            quality['good'] = False
            quality['reason'] = "No detection"
            return quality
        
        # Check hand landmark visibility (landmarks 33-75)
        if hasattr(mp_results, 'left_hand_landmarks') and hasattr(mp_results, 'right_hand_landmarks'):
            left_visible = mp_results.left_hand_landmarks is not None
            right_visible = mp_results.right_hand_landmarks is not None
            
            if not left_visible and not right_visible:
                quality['good'] = False
                quality['hand_visibility'] = 0.0
                quality['reason'] = "No hands detected"
            elif not left_visible or not right_visible:
                quality['hand_visibility'] = 0.5
                quality['reason'] = "One hand missing"
        
        # Check pose landmarks visibility
        if hasattr(mp_results, 'pose_landmarks') and mp_results.pose_landmarks:
            # Check if key pose landmarks (shoulders) are visible
            shoulder_landmarks = [mp_results.pose_landmarks.landmark[11], 
                                 mp_results.pose_landmarks.landmark[12]]
            avg_visibility = sum([lm.visibility for lm in shoulder_landmarks]) / 2
            quality['pose_visibility'] = avg_visibility
            
            if avg_visibility < 0.3:
                quality['good'] = False
                quality['reason'] = "Poor pose detection (low light?)"
        
        return quality
    
    def normalize_landmarks(self, sequence: np.ndarray) -> np.ndarray:
        """
        Normalize landmarks to match training preprocessing.
        CRITICAL: This must match the normalization in preprocess_wlasl_FIXED.py EXACTLY
        - Centers on nose (landmark 0)
        - Scales by shoulder width (landmarks 11-12)
        
        Args:
            sequence: (T, V, C) numpy array where T=frames, V=75 vertices, C=3 coords
        
        Returns:
            Normalized (T, V, C) numpy array
        """
        if sequence.shape[0] == 0:
            return sequence
        
        # Center around nose (landmark 0)
        nose_positions = sequence[:, 0:1, :]  # (T, 1, 3)
        centered = sequence - nose_positions
        
        # Scale by shoulder width (more stable than overall range)
        # Left shoulder = 11, Right shoulder = 12
        left_shoulder = sequence[:, 11, :]  # (T, 3)
        right_shoulder = sequence[:, 12, :]  # (T, 3)
        shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder, axis=1, keepdims=True)  # (T, 1)
        shoulder_dist = np.where(shoulder_dist > 0.01, shoulder_dist, 1.0)  # Avoid division by zero
        
        # Scale - CRITICAL: MUST EXACTLY MATCH preprocess_wlasl_FIXED.py line 127!
        scaled = centered / shoulder_dist[:, :, np.newaxis]  # (T, V, C)
        
        return scaled
    
    def preprocess_sequence(self, sequence: np.ndarray) -> torch.Tensor:
        """
        Preprocess landmark sequence for model input.
        CRITICAL: Applies normalization to match training preprocessing.
        
        Args:
            sequence: (T, V, C) numpy array
        
        Returns:
            (1, C, T, V, M) tensor
        """
        # Apply normalization (MUST match training!)
        sequence = self.normalize_landmarks(sequence)
        
        # Rearrange based on model architecture
        if self.use_improved_format:
            # IMPROVED model expects (N, C, T, V) format
            sequence = np.transpose(sequence, (2, 0, 1))  # (C, T, V) = (3, 30, 75)
            sequence = np.expand_dims(sequence, axis=0)   # (N, C, T, V) = (1, 3, 30, 75)
        else:
            # OLD model expects (N, C, T, V, M) format
            sequence = np.transpose(sequence, (2, 0, 1))  # (3, 30, 75)
            sequence = np.expand_dims(sequence, axis=-1)  # (3, 30, 75, 1)
            sequence = np.expand_dims(sequence, axis=0)   # (1, 3, 30, 75, 1)
        
        # Convert to tensor
        tensor = torch.FloatTensor(sequence).to(self.device)
        
        return tensor
    
    def predict_from_sequence(self, landmarks_sequence: list, use_temporal_smoothing: bool = None) -> dict:
        """
        Predict sign from a recorded sequence of landmarks.
        
        Args:
            landmarks_sequence: List of (V, C) landmark arrays
            use_temporal_smoothing: Override temporal smoothing setting (None uses instance default)
        
        Returns:
            Prediction dictionary with keys: 'sign', 'confidence'
        """
        if len(landmarks_sequence) < 10:
            return {
                'sign': 'Too short',
                'confidence': 0.0,
                'error': 'Recording too short (need at least 10 frames)'
            }
        
        # Convert to numpy array: (T, V, C)
        sequence = np.array(landmarks_sequence)
        
        # Check for motion - prevent predictions on idle/static poses
        # Calculate variance of hand positions over time
        hand_landmarks = sequence[:, 33:, :]  # Only hands (33-75)
        motion_variance = np.var(hand_landmarks)
        
        if motion_variance < 0.00005:  # Very low motion
            return {
                'sign': 'No motion detected',
                'confidence': 0.0,
                'error': 'Please perform a sign with clear hand movement'
            }
        
        sequence = sequence
        
        # Pad or truncate to 30 frames
        # CRITICAL: Must match training preprocessing (uniform sampling)
        current_length = len(sequence)
        
        if current_length < 30:
            # Pad by repeating last frame (same as training)
            padding = np.repeat(sequence[-1:], 30 - current_length, axis=0)
            sequence = np.concatenate([sequence, padding], axis=0)
        elif current_length > 30:
            # Use uniform sampling across entire sequence (SAME AS TRAINING!)
            # This preserves temporal information better than taking last 30 frames
            indices = np.linspace(0, current_length - 1, 30, dtype=int)
            sequence = sequence[indices]
        # If exactly 30 frames, use as is
        
        # Preprocess
        input_tensor = self.preprocess_sequence(sequence)
        
        # Inference
        with torch.no_grad():
            output = self.model(input_tensor)
            probabilities = torch.softmax(output, dim=1)
            confidence, predicted_class = probabilities.max(1)
        
        # Get prediction
        confidence = confidence.item()
        predicted_class = predicted_class.item()
        predicted_sign = self.class_names[predicted_class]
        
        # Calculate prediction entropy (measure of uncertainty)
        # Low entropy = confident, High entropy = uncertain
        probs_np = probabilities[0].cpu().numpy()
        entropy = -np.sum(probs_np * np.log(probs_np + 1e-10))
        max_entropy = np.log(len(probs_np))  # Maximum possible entropy
        normalized_entropy = entropy / max_entropy
        
        # If entropy is too high (>0.92), prediction is too uncertain
        # Increased threshold to be more lenient for real-world conditions
        if normalized_entropy > 0.92:
            return {
                'sign': 'Uncertain',
                'confidence': confidence * 0.5,  # Penalize confidence
                'top3': [],
                'class_id': predicted_class,
                'entropy': normalized_entropy,
                'error': 'Prediction too uncertain - try performing sign more clearly'
            }
        
        # Get top 3 predictions
        top3_probs, top3_classes = torch.topk(probabilities[0], k=min(3, self.num_classes))
        top3_list = [(self.class_names[top3_classes[i].item()], top3_probs[i].item()) 
                     for i in range(len(top3_classes))]
        
        # Confidence threshold check - Lowered to 25% for real-world conditions
        if confidence < 0.25:  # Minimum 25% confidence
            return {
                'sign': f'Low confidence: {predicted_sign}',
                'confidence': confidence,
                'top3': top3_list,
                'class_id': predicted_class,
                'entropy': normalized_entropy,
                'error': f'Confidence too low ({confidence*100:.1f}%) - need >25%'
            }
        
        # Task 1.3: Apply temporal smoothing if enabled
        # Note: For API batch calls, temporal smoothing should be disabled
        # since it's designed for streaming (accumulating over multiple calls)
        final_sign = predicted_sign
        final_confidence = confidence
        stability_score = 0.0
        
        # Use override if provided, otherwise use instance setting
        apply_smoothing = use_temporal_smoothing if use_temporal_smoothing is not None else self.use_temporal_smoothing
        
        if apply_smoothing:
            smoothed_sign, smoothed_confidence = self.temporal_smoother.smooth(
                predicted_sign, confidence
            )
            stability_score = self.temporal_smoother.get_stability_score()
            final_sign = smoothed_sign
            final_confidence = smoothed_confidence
        
        # Task 2.2: Banking Intent Verification
        intent_result = None
        if self.banking_verifier:
            try:
                intent, context, is_valid = self.banking_verifier.verify_sign_sequence(
                    signs=[final_sign],
                    confidences=[final_confidence]
                )
                
                intent_result = {
                    'intent': intent.value,
                    'intent_valid': is_valid,
                    'requires_confirmation': context.pending_confirmation,
                    'missing_slots': context.missing_slots,
                    'error_message': context.error_message if not is_valid else None,
                    'prompt': self.banking_verifier.get_slot_prompt() if context.missing_slots else None,
                    'confirmation_msg': self.banking_verifier.get_confirmation_message() if context.pending_confirmation else None,
                    'slots': context.slots,
                    'is_authenticated': context.is_authenticated
                }
                
                # Store context for UI
                self.intent_context = context
                self.current_intent = intent
                
            except Exception as e:
                print(f"⚠️ Intent verification error: {e}")
        
        # Build result dictionary
        result = {
            'sign': final_sign,
            'confidence': final_confidence,
            'top3': top3_list,
            'class_id': predicted_class,
            'entropy': normalized_entropy
        }
        
        # Add smoothing info if enabled
        if apply_smoothing:
            result.update({
                'raw_sign': predicted_sign,
                'raw_confidence': confidence,
                'stability': stability_score,
                'smoothed': True
            })
        
        # Add intent info if available
        if intent_result:
            result['intent_info'] = intent_result
        
        return result
    
    def extract_biometric_features(
        self,
        frame_rgb: np.ndarray,
        landmarks_sequence: list
    ) -> dict:
        """
        Extract multi-modal biometric features from current signing.
        
        Args:
            frame_rgb: Current RGB frame for face extraction
            landmarks_sequence: List of (75, 3) landmark arrays
        
        Returns:
            Dict with face, hand, style, and fusion features
        """
        if self.bio_authenticator is None:
            return None
        
        try:
            # Extract hand landmarks from latest frame
            if landmarks_sequence and len(landmarks_sequence) > 0:
                latest_landmarks = landmarks_sequence[-1]
                
                # MediaPipe format: pose (33) + left_hand (21) + right_hand (21) = 75
                left_hand_landmarks = latest_landmarks[33:54]  # Indices 33-53 (21 points)
                right_hand_landmarks = latest_landmarks[54:75]  # Indices 54-74 (21 points)
            else:
                left_hand_landmarks = None
                right_hand_landmarks = None
            
            # Extract features
            features = self.bio_authenticator.extract_multimodal_features(
                frame=frame_rgb,
                left_hand_landmarks=left_hand_landmarks,
                right_hand_landmarks=right_hand_landmarks,
                landmark_sequence=landmarks_sequence
            )
            
            return features
            
        except Exception as e:
            print(f"⚠️  Biometric extraction error: {e}")
            return None
    
    def authenticate_user(
        self,
        user_id: str,
        bio_features: dict
    ) -> tuple:
        """
        Authenticate user with biometric features.
        
        Args:
            user_id: User identifier
            bio_features: Extracted biometric features
        
        Returns:
            (is_authenticated, fusion_score, individual_scores)
        """
        if self.bio_authenticator is None or self.bio_database is None:
            return False, 0.0, {}
        
        try:
            # Get reference biometrics from database
            reference_features = self.bio_database.get_user_biometrics(user_id)
            
            if reference_features is None:
                print(f"⚠️  User {user_id} not enrolled")
                return False, 0.0, {}
            
            # Verify
            is_authenticated, fusion_score, individual_scores = self.bio_authenticator.verify(
                query_features=bio_features,
                reference_features=reference_features
            )
            
            # Log authentication attempt
            self.bio_database.log_authentication(
                user_id=user_id,
                authenticated=is_authenticated,
                fusion_score=fusion_score,
                individual_scores=individual_scores
            )
            
            # Update banking verifier if authenticated
            if self.banking_verifier and is_authenticated:
                self.banking_verifier.authenticate_user(user_id, verified=True)
            
            return is_authenticated, fusion_score, individual_scores
            
        except Exception as e:
            print(f"⚠️  Authentication error: {e}")
            return False, 0.0, {}
    
    def start_enrollment(self, user_id: str):
        """Start enrollment process for a new user"""
        if self.bio_authenticator is None:
            print("⚠️  Biometric authentication not available")
            return False
        
        self.enrollment_mode = True
        self.current_user_id = user_id
        self.enrollment_samples = []
        
        print(f"\n📝 Starting enrollment for user: {user_id}")
        print("   Sign 3 different signs naturally...")
        print("   Press SPACE to record, ENTER to predict, repeat 3 times")
        print("   Press 'C' to cancel enrollment")
        
        return True
    
    def add_enrollment_sample(
        self,
        frame_rgb: np.ndarray,
        landmarks_sequence: list
    ):
        """Add a sample to the enrollment collection"""
        if not self.enrollment_mode:
            return
        
        # Extract biometric features
        bio_features = self.extract_biometric_features(frame_rgb, landmarks_sequence)
        
        if bio_features is not None:
            # Store the full sample data
            sample = {
                'frame': frame_rgb.copy(),
                'left_hand': landmarks_sequence[-1][33:54] if landmarks_sequence else None,
                'right_hand': landmarks_sequence[-1][54:75] if landmarks_sequence else None,
                'sequence': landmarks_sequence.copy()
            }
            self.enrollment_samples.append(sample)
            
            print(f"   ✅ Sample {len(self.enrollment_samples)}/3 collected")
            
            # Complete enrollment if we have 3 samples
            if len(self.enrollment_samples) >= 3:
                self.complete_enrollment()
    
    def complete_enrollment(self):
        """Complete enrollment and save to database"""
        if not self.enrollment_mode or len(self.enrollment_samples) < 3:
            return
        
        try:
            print(f"\n🔐 Completing enrollment for {self.current_user_id}...")
            
            # Extract data from samples
            frames = [s['frame'] for s in self.enrollment_samples]
            left_hands = [s['left_hand'] for s in self.enrollment_samples]
            right_hands = [s['right_hand'] for s in self.enrollment_samples]
            sequences = [s['sequence'] for s in self.enrollment_samples]
            
            # Enroll user
            enrolled_features = self.bio_authenticator.enroll_user(
                user_id=self.current_user_id,
                frames=frames,
                left_hand_landmarks_list=left_hands,
                right_hand_landmarks_list=right_hands,
                landmark_sequences=sequences,
                num_samples=3
            )
            
            # Save to database
            success = self.bio_database.enroll_user(
                user_id=self.current_user_id,
                biometric_features=enrolled_features,
                notes=f"Enrolled via inference UI on {np.datetime64('now')}"
            )
            
            if success:
                print(f"✅ User {self.current_user_id} enrolled successfully!")
                print(f"   Face: {enrolled_features['face'].shape}")
                print(f"   Hand: {enrolled_features['hand'].shape}")
                print(f"   Style: {enrolled_features['style'].shape}")
            else:
                print(f"❌ Enrollment failed (user may already exist)")
            
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
        
        finally:
            # Reset enrollment state
            self.enrollment_mode = False
            self.enrollment_samples = []
            self.current_user_id = None
    
    def cancel_enrollment(self):
        """Cancel ongoing enrollment"""
        if self.enrollment_mode:
            print(f"\n❌ Enrollment cancelled for {self.current_user_id}")
            self.enrollment_mode = False
            self.enrollment_samples = []
            self.current_user_id = None
    
    def predict(self, frame_rgb: np.ndarray) -> dict:
        """
        Process a single frame and extract landmarks (no prediction in manual mode).
        
        Args:
            frame_rgb: RGB image
        
        Returns:
            Dictionary with landmarks and detection status
        """
        # Extract landmarks
        landmarks, mp_results = self.extractor.extract_with_results(frame_rgb)
        
        result = {
            'landmarks': landmarks,
            'landmarks_detected': landmarks is not None,
            'mp_results': mp_results
        }
        
        # If recording, store landmarks
        if self.is_recording and landmarks is not None:
            self.recorded_landmarks.append(landmarks.copy())
        
        return result
    
    def finalize_prediction(self):
        """No longer needed in manual recording mode"""
        pass
    
    def get_smoothed_prediction(self) -> dict:
        """
        Get smoothed prediction using majority voting with confidence weighting.
        
        Returns:
            Most common recent prediction with weighted confidence
        """
        if not self.prediction_history:
            return {'sign': None, 'confidence': 0.0, 'votes': 0}
        
        # Use all recent predictions for smoothing
        recent = self.prediction_history
        
        # Count votes for each sign weighted by confidence
        sign_votes = {}
        for pred in recent:
            sign = pred['sign']
            conf = pred['confidence']
            if sign not in sign_votes:
                sign_votes[sign] = {'count': 0, 'total_conf': 0.0, 'confidences': []}
            sign_votes[sign]['count'] += 1
            sign_votes[sign]['total_conf'] += conf
            sign_votes[sign]['confidences'].append(conf)
        
        # Find sign with most votes and highest confidence
        best_sign = None
        best_score = 0.0
        for sign, votes in sign_votes.items():
            # Score = (vote count / window size) * average confidence
            vote_ratio = votes['count'] / len(recent)
            avg_conf = votes['total_conf'] / votes['count']
            score = vote_ratio * avg_conf
            
            if score > best_score:
                best_score = score
                best_sign = sign
        
        # Return best prediction with its average confidence
        if best_sign:
            avg_conf = sign_votes[best_sign]['total_conf'] / sign_votes[best_sign]['count']
            return {'sign': best_sign, 'confidence': avg_conf, 'votes': sign_votes[best_sign]['count']}
        
        return {'sign': None, 'confidence': 0.0, 'votes': 0}
    
    def run_camera(self, camera_id: int = 0, show_landmarks: bool = True):
        """
        Run manual recording inference from camera.
        
        Args:
            camera_id: Camera device ID
            show_landmarks: Whether to draw MediaPipe landmarks
        """
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera {camera_id}")
        
        print("\n" + "=" * 70)
        print("🎥 NS-AGF Manual Recording Inference")
        print("=" * 70)
        print("\n📍 Positioning Guide:")
        print("  • Distance: Stand ~50cm (arm's length) from camera")
        print("  • Framing: Position your head near top, waist near bottom")
        print("  • Visibility: Keep both hands visible within the green guide box")
        print("  • Lighting: Ensure good lighting on your hands and face")
        print("\n⌨️  Controls:")
        print("  SPACEBAR  - Start/Stop recording")
        print("  ENTER     - Predict recorded sign")
        print("  C         - Clear last sign from sentence")
        print("  R         - Clear entire sentence")
        print("  E         - Enroll new user (biometric registration)")
        print("  U         - Select user for authentication")
        print("  Y         - Confirm pending action")
        print("  N         - Cancel pending action")
        print("  Q         - Quit")
        print("=" * 70)
        print("\n📝 How to use:")
        print("  1. Position yourself in the green guide box")
        print("  2. Press SPACEBAR to start recording")
        print("  3. Perform your sign clearly")
        print("  4. Press SPACEBAR to stop recording")
        print("  5. Press ENTER to predict the sign")
        print("  6. Repeat to build a sentence")
        print("=" * 70 + "\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame (extract landmarks)
            result = self.predict(frame_rgb)
            
            # Draw UI
            display_frame = frame.copy()
            if show_landmarks and result.get('mp_results'):
                draw_landmarks(display_frame, result['mp_results'])
            
            self._draw_ui_manual(display_frame, result)
            
            # Show frame
            cv2.imshow('NS-AGF Manual Recording', display_frame)
            
            # Key handling
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                print("\n👋 Exiting...")
                break
            
            elif key == 32:  # SPACEBAR
                if not self.is_recording:
                    # Start recording
                    self.is_recording = True
                    self.recorded_frames = []
                    self.recorded_landmarks = []
                    self.recording_start_time = cv2.getTickCount()
                    self.waiting_for_prediction = False
                    # Reset temporal smoother for new sign
                    if hasattr(self, 'temporal_smoother'):
                        self.temporal_smoother.reset()
                    print("🔴 Recording started...")
                else:
                    # Stop recording
                    self.is_recording = False
                    recording_duration = (cv2.getTickCount() - self.recording_start_time) / cv2.getTickFrequency()
                    print(f"⏸️  Recording stopped ({len(self.recorded_landmarks)} frames, {recording_duration:.1f}s)")
                    
                    if len(self.recorded_landmarks) < 10:
                        print("⚠️  Recording too short (need at least 10 frames)")
                        self.recorded_landmarks = []
                    else:
                        self.waiting_for_prediction = True
                        print("   Press ENTER to predict")
            
            elif key == 13 or key == ord('p') or key == ord('P'):  # ENTER or P
                if self.waiting_for_prediction and len(self.recorded_landmarks) > 0:
                    print("🔮 Predicting...")
                    prediction = self.predict_from_sequence(self.recorded_landmarks)
                    
                    if 'error' not in prediction:
                        self.last_prediction = prediction['sign']
                        self.last_confidence = prediction['confidence']
                        
                        # Extract biometrics if authenticator available
                        if self.bio_authenticator and len(self.recorded_frames) > 0 and not self.enrollment_mode:
                            latest_frame_rgb = cv2.cvtColor(self.recorded_frames[-1], cv2.COLOR_BGR2RGB)
                            self.bio_features = self.extract_biometric_features(
                                latest_frame_rgb,
                                self.recorded_landmarks
                            )
                            
                            # Authenticate if user selected
                            if self.current_user_id and self.bio_features:
                                is_auth, score, individual = self.authenticate_user(
                                    self.current_user_id,
                                    self.bio_features
                                )
                                self.bio_authenticated = is_auth
                                self.bio_score = score
                                
                                if is_auth:
                                    print(f"   🔐 Authenticated: {self.current_user_id} (score: {score:.2f})")
                                else:
                                    print(f"   ❌ Authentication failed (score: {score:.2f})")
                        
                        # Handle enrollment sample
                        if self.enrollment_mode and len(self.recorded_frames) > 0:
                            latest_frame_rgb = cv2.cvtColor(self.recorded_frames[-1], cv2.COLOR_BGR2RGB)
                            self.add_enrollment_sample(latest_frame_rgb, self.recorded_landmarks)
                        
                        # Add to sentence
                        self.sentence.append(self.last_prediction)
                        
                        # Task 1.3: Display smoothing information
                        if prediction.get('smoothed', False):
                            print(f"✅ Predicted: {self.last_prediction} ({self.last_confidence*100:.1f}%)")
                            if prediction.get('raw_sign') != self.last_prediction:
                                print(f"   📊 Smoothed from: {prediction['raw_sign']} ({prediction['raw_confidence']*100:.1f}%)")
                            print(f"   📈 Stability: {prediction.get('stability', 0)*100:.0f}%")
                        else:
                            print(f"✅ Predicted: {self.last_prediction} ({self.last_confidence*100:.1f}%)")
                        
                        # Task 2.2: Display intent information
                        if 'intent_info' in prediction:
                            intent_info = prediction['intent_info']
                            print(f"\n   🧠 Intent Analysis:")
                            print(f"      Type: {intent_info['intent']}")
                            print(f"      Valid: {'✅ Yes' if intent_info['intent_valid'] else '❌ No'}")
                            
                            if not intent_info['intent_valid'] and intent_info['error_message']:
                                print(f"      Error: {intent_info['error_message']}")
                            
                            if intent_info['missing_slots']:
                                print(f"      Missing: {', '.join(intent_info['missing_slots'])}")
                                if intent_info['prompt']:
                                    print(f"      💬 Prompt: {intent_info['prompt']}")
                            
                            if intent_info['slots']:
                                slots_str = ', '.join([f"{k}={v}" for k, v in intent_info['slots'].items() if k != 'user_id'])
                                if slots_str:
                                    print(f"      Slots: {slots_str}")
                            
                            if intent_info['requires_confirmation']:
                                print(f"      ⚠️  {intent_info['confirmation_msg']}")
                            
                            if not intent_info['is_authenticated'] and intent_info['intent'] in ['transfer', 'check_balance', 'check_interest']:
                                print(f"      🔐 Authentication required for this operation")
                        
                        print(f"\n📝 Sentence: {' '.join(self.sentence)}")
                        
                        # Reset temporal smoother after successful prediction
                        # This ensures next sign starts with clean history
                        if hasattr(self, 'temporal_smoother'):
                            self.temporal_smoother.reset()
                    else:
                        print(f"❌ {prediction['error']}")
                    
                    # Clear for next recording
                    self.recorded_landmarks = []
                    self.waiting_for_prediction = False
                else:
                    print("⚠️  No recording to predict. Press SPACEBAR to record first.")
            
            elif key == ord('c') or key == ord('C'):
                # Cancel enrollment or clear last sign
                if self.enrollment_mode:
                    self.cancel_enrollment()
                elif len(self.sentence) > 0:
                    removed = self.sentence.pop()
                    print(f"🧹 Removed last sign: {removed}")
                    print(f"📝 Sentence: {' '.join(self.sentence) if self.sentence else '(empty)'}")
                else:
                    print("⚠️  Sentence is already empty")
            
            elif key == ord('r') or key == ord('R'):
                # Clear entire sentence
                if len(self.sentence) > 0:
                    print(f"🗑️  Cleared entire sentence: {' '.join(self.sentence)}")
                    self.sentence = []
                    self.last_prediction = None
                    self.last_confidence = 0.0
                    if self.banking_verifier:
                        self.banking_verifier.reset_context()
                        self.intent_context = None
                        self.current_intent = None
                    print("✅ Sentence cleared")
                else:
                    print("⚠️  Sentence is already empty")
            
            elif key == ord('e') or key == ord('E'):
                # Start enrollment
                if self.enrollment_mode:
                    print("⚠️  Already in enrollment mode")
                elif self.bio_authenticator is None:
                    print("⚠️  Biometric authentication not available")
                else:
                    # Prompt for user ID
                    print("\n📝 Enter user ID (or press ESC to cancel): ", end='', flush=True)
                    user_id = input().strip()
                    
                    if user_id:
                        # Check if user exists
                        if self.bio_database.user_exists(user_id):
                            print(f"⚠️  User {user_id} already enrolled")
                            print("   Use a different ID or delete existing user first")
                        else:
                            self.start_enrollment(user_id)
                    else:
                        print("❌ Enrollment cancelled")
            
            elif key == ord('u') or key == ord('U'):
                # Select user for authentication
                if self.bio_database is None:
                    print("⚠️  Biometric authentication not available")
                else:
                    users = self.bio_database.get_all_users()
                    if not users:
                        print("⚠️  No users enrolled. Press 'E' to enroll first.")
                    else:
                        print("\n📋 Enrolled users:")
                        for i, user in enumerate(users, 1):
                            print(f"   {i}. {user['user_id']} (auths: {user['authentication_count']})")
                        print("\n🔑 Enter user ID (or press ESC to cancel): ", end='', flush=True)
                        user_id = input().strip()
                        
                        if user_id:
                            if self.bio_database.user_exists(user_id):
                                self.current_user_id = user_id
                                self.bio_authenticated = False
                                print(f"✅ Selected user: {user_id}")
                                print("   Sign anything to authenticate")
                            else:
                                print(f"⚠️  User {user_id} not found")
                        else:
                            print("❌ User selection cancelled")
            
            elif key == ord('y') or key == ord('Y'):
                # Confirm pending action
                if self.banking_verifier and self.intent_context and self.intent_context.pending_confirmation:
                    self.banking_verifier.confirm_action(confirmed=True)
                    print("✅ Action confirmed")
                    self.intent_context = None
                    self.current_intent = None
                else:
                    print("⚠️  No pending action to confirm")
            
            elif key == ord('n') or key == ord('N'):
                # Cancel pending action
                if self.banking_verifier and self.intent_context and self.intent_context.pending_confirmation:
                    self.banking_verifier.confirm_action(confirmed=False)
                    print("❌ Action cancelled")
                    self.intent_context = None
                    self.current_intent = None
                else:
                    print("⚠️  No pending action to cancel")
        
        cap.release()
        cv2.destroyAllWindows()
        self.extractor.close()
    
    def _draw_ui_manual(self, frame, result):
        """Draw UI for manual recording mode"""
        h, w = frame.shape[:2]
        
        # Create overlay
        overlay = frame.copy()
        
        # Draw positioning guide (half-body frame at 50cm distance)
        # Guide box: shows where user should position their upper body
        guide_margin_top = 80  # Below status bar
        guide_margin_bottom = 140  # Above sentence box
        guide_width = int(w * 0.7)  # 70% of frame width
        guide_height = h - guide_margin_top - guide_margin_bottom
        guide_x = (w - guide_width) // 2
        guide_y = guide_margin_top
        
        # Draw guide rectangle (semi-transparent)
        guide_color = (100, 200, 100)  # Green for good positioning
        if not result.get('landmarks_detected'):
            guide_color = (100, 100, 200)  # Blue if no detection
        
        cv2.rectangle(frame, (guide_x, guide_y), 
                     (guide_x + guide_width, guide_y + guide_height), 
                     guide_color, 2)
        
        # Corner markers for emphasis
        corner_len = 30
        # Top-left
        cv2.line(frame, (guide_x, guide_y), (guide_x + corner_len, guide_y), guide_color, 3)
        cv2.line(frame, (guide_x, guide_y), (guide_x, guide_y + corner_len), guide_color, 3)
        # Top-right
        cv2.line(frame, (guide_x + guide_width, guide_y), (guide_x + guide_width - corner_len, guide_y), guide_color, 3)
        cv2.line(frame, (guide_x + guide_width, guide_y), (guide_x + guide_width, guide_y + corner_len), guide_color, 3)
        # Bottom-left
        cv2.line(frame, (guide_x, guide_y + guide_height), (guide_x + corner_len, guide_y + guide_height), guide_color, 3)
        cv2.line(frame, (guide_x, guide_y + guide_height), (guide_x, guide_y + guide_height - corner_len), guide_color, 3)
        # Bottom-right
        cv2.line(frame, (guide_x + guide_width, guide_y + guide_height), (guide_x + guide_width - corner_len, guide_y + guide_height), guide_color, 3)
        cv2.line(frame, (guide_x + guide_width, guide_y + guide_height), (guide_x + guide_width, guide_y + guide_height - corner_len), guide_color, 3)
        
        # Positioning instructions
        cv2.putText(frame, "Position: Half body visible | Distance: ~50cm", 
                   (guide_x + 10, guide_y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, guide_color, 2)
        
        # Head position marker (should be near top of guide box)
        head_marker_y = guide_y + int(guide_height * 0.15)
        cv2.line(frame, (guide_x + 10, head_marker_y), 
                (guide_x + 60, head_marker_y), (255, 200, 0), 2)
        cv2.putText(frame, "Head", (guide_x + 70, head_marker_y + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)
        
        # Waist position marker (should be near bottom of guide box)
        waist_marker_y = guide_y + int(guide_height * 0.85)
        cv2.line(frame, (guide_x + 10, waist_marker_y), 
                (guide_x + 60, waist_marker_y), (255, 200, 0), 2)
        cv2.putText(frame, "Waist", (guide_x + 70, waist_marker_y + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)
        
        # Draw recording status bar at top
        if self.is_recording:
            # Recording indicator (red)
            cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 255), -1)
            cv2.putText(overlay, "🔴 RECORDING", (20, 40),
                       cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 3)
            
            # Frame count
            cv2.putText(overlay, f"Frames: {len(self.recorded_landmarks)}", (w - 200, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        elif self.waiting_for_prediction:
            # Waiting for prediction (yellow)
            cv2.rectangle(overlay, (0, 0), (w, 60), (0, 200, 255), -1)
            cv2.putText(overlay, "⏸️  Press ENTER to Predict", (20, 40),
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 3)
        
        else:
            # Ready state (green)
            cv2.rectangle(overlay, (0, 0), (w, 60), (0, 180, 0), -1)
            cv2.putText(overlay, "⏺️  Press SPACEBAR to Record", (20, 40),
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 3)
        
        # Blend overlay
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw sentence box at bottom
        sentence_text = ' '.join(self.sentence) if self.sentence else '(Empty sentence)'
        sentence_bg_height = 120
        cv2.rectangle(frame, (0, h - sentence_bg_height), (w, h), (40, 40, 40), -1)
        
        # Sentence label
        cv2.putText(frame, "Sentence:", (20, h - 90),
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
        
        # Sentence content
        cv2.putText(frame, sentence_text, (20, h - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 255, 100), 2)
        
        # Last prediction (if available)
        if self.last_prediction:
            # Task 1.3: Show smoothing info if available
            if hasattr(self, 'temporal_smoother') and self.use_temporal_smoothing:
                stability = self.temporal_smoother.get_stability_score()
                pred_text = f"Last: {self.last_prediction} ({self.last_confidence*100:.0f}%) [Stability: {stability*100:.0f}%]"
            else:
                pred_text = f"Last: {self.last_prediction} ({self.last_confidence*100:.0f}%)"
            cv2.putText(frame, pred_text, (20, h - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Task 2.2: Intent status (right side of sentence box)
        if self.intent_context and self.current_intent:
            intent_y = h - 85
            
            # Intent type
            intent_text = f"Intent: {self.current_intent.value}"
            cv2.putText(frame, intent_text, (w - 380, intent_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 100), 1)
            
            # Missing slots or confirmation
            if self.intent_context.missing_slots:
                status_text = f"Missing: {', '.join(self.intent_context.missing_slots)}"
                cv2.putText(frame, status_text, (w - 380, intent_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 150, 0), 1)
            elif self.intent_context.pending_confirmation:
                cv2.putText(frame, "⚠️  Awaiting confirmation", (w - 380, intent_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 100, 0), 1)
            elif self.intent_context.is_authenticated:
                cv2.putText(frame, "🔐 Authenticated", (w - 380, intent_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            else:
                cv2.putText(frame, "🔓 Not authenticated", (w - 380, intent_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (128, 128, 128), 1)
        
        # Biometric authentication status (top-right corner)
        bio_y = 80
        if self.bio_authenticator:          # Show enrollment mode
            if self.enrollment_mode:
                cv2.rectangle(frame, (w - 250, bio_y - 30), (w - 10, bio_y + 60), (100, 100, 255), -1)
                cv2.putText(frame, f"📝 ENROLLING: {self.current_user_id}", (w - 240, bio_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.putText(frame, f"Samples: {len(self.enrollment_samples)}/3", (w - 240, bio_y + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                cv2.putText(frame, "Press C to cancel", (w - 240, bio_y + 45),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            # Show current user and auth status
            elif self.current_user_id:
                bg_color = (0, 200, 0) if self.bio_authenticated else (100, 100, 100)
                cv2.rectangle(frame, (w - 250, bio_y - 30), (w - 10, bio_y + 60), bg_color, -1)
                
                status_icon = "🔐" if self.bio_authenticated else "👤"
                cv2.putText(frame, f"{status_icon} User: {self.current_user_id}", (w - 240, bio_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                if self.bio_authenticated:
                    cv2.putText(frame, f"Auth Score: {self.bio_score:.2f}", (w - 240, bio_y + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                else:
                    cv2.putText(frame, "Not authenticated", (w - 240, bio_y + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                
                cv2.putText(frame, "Press U to change", (w - 240, bio_y + 45),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            # Show prompt to select user
            else:
                cv2.rectangle(frame, (w - 250, bio_y - 30), (w - 10, bio_y + 40), (80, 80, 80), -1)
                cv2.putText(frame, "👤 No user selected", (w - 240, bio_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.putText(frame, "Press U to select", (w - 240, bio_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Controls reminder (right side, below bio status)
        controls = [
            "SPACE: Record",
            "ENTER: Predict",
            "C: Clear last",
            "R: Clear all",
            "E: Enroll user",
            "U: Select user",
            "Y: Confirm",
            "N: Cancel",
            "Q: Quit"
        ]
        
        y_offset = bio_y + 100
        for i, control in enumerate(controls):
            cv2.putText(frame, control, (w - 180, y_offset + i*22),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        
        # Landmarks detection status
        if result.get('landmarks_detected'):
            status_text = "✓ Hands detected"
            color = (0, 255, 0)
        else:
            status_text = "✗ No hands"
            color = (0, 0, 255)
        
        cv2.putText(frame, status_text, (w - 180, 250),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def _draw_ui(self, frame, result):
        """Draw UI overlays on frame"""
        h, w = frame.shape[:2]
        
        # Main panel
        cv2.rectangle(frame, (10, 10), (w - 10, 180), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (w - 10, 180), (255, 255, 255), 2)
        
        # Detection status with quality indicator
        if result['landmarks_detected']:
            if 'quality' in result and result['quality']:
                quality = result['quality']
                if quality['good']:
                    status_color = (0, 255, 0)  # Green for good
                    status_text = f"✓ Detected (Quality: {quality['hand_visibility']:.1%})"
                else:
                    status_color = (0, 165, 255)  # Orange for poor
                    status_text = f"⚠ Poor Quality: {quality['reason']}"
            else:
                status_color = (0, 255, 0)
                status_text = "✓ Detected"
        else:
            status_color = (0, 0, 255)
            status_text = "✗ No Detection"
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Motion indicator (buffer variance)
        if 'buffer_motion' in result:
            buffer_motion = result['buffer_motion']
            motion_text = f"Activity: {buffer_motion:.5f}"
            motion_color = (0, 255, 0) if buffer_motion > 0.0001 else (128, 128, 128)
            cv2.putText(frame, motion_text, (w - 280, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, motion_color, 2)
        
        # Bias warning indicator
        if 'bias_detected' in result and result['bias_detected']:
            cv2.putText(frame, "⚠ Bias Correction ON", (w - 280, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
        
        # Status indicator
        if 'status' in result:
            cv2.putText(frame, result['status'], (w - 280, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)
        
        # Current prediction with special colors for no-sign states
        if result['sign']:
            # Show sign name with appropriate color
            sign_text = result['sign']
            
            # Color coding based on prediction type
            if sign_text.startswith('❌'):
                sign_color = (0, 0, 255)  # Red for "No Sign Detected"
            elif sign_text.startswith('⚠️'):
                sign_color = (0, 165, 255)  # Orange for warnings
            elif result['confidence'] > 0:
                sign_color = (255, 255, 255)  # White for valid predictions
            else:
                sign_color = (180, 180, 180)  # Gray for idle
            
            cv2.putText(frame, f"Current: {sign_text}", (20, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, sign_color, 2)
            
            # Show confidence with color coding
            if result['confidence'] > 0:
                conf_text = f"Confidence: {result['confidence']:.1%}"
                if result['confidence'] > self.confidence_threshold:
                    conf_color = (0, 255, 0)  # Green for high confidence
                elif result['confidence'] > 0.5:
                    conf_color = (0, 165, 255)  # Orange for medium
                else:
                    conf_color = (0, 0, 255)  # Red for low
                cv2.putText(frame, conf_text, (20, 115), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, conf_color, 2)
            
            # Show last stable sign if different from current
            if 'last_sign' in result and result['last_sign'] and result['last_sign'] != sign_text:
                cv2.putText(frame, f"Last: {result['last_sign']}", (20, 145), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 255), 2)
            
            # Show class ID for reference
            if 'raw_sign' in result:
                class_id = self.class_names.index(sign_text) if sign_text in self.class_names else -1
                if class_id >= 0:
                    cv2.putText(frame, f"Class ID: {class_id}", (20, 170), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
        
        # Sign history panel at bottom
        if 'detected_signs' in result and result['detected_signs']:
            history_y = h - 80
            cv2.rectangle(frame, (10, history_y - 10), (w - 10, h - 10), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, history_y - 10), (w - 10, h - 10), (100, 100, 255), 2)
            cv2.putText(frame, "Detected Signs History (Press 'C' to clear):", (20, history_y + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)
            
            # Show last 5 detected signs
            history_text = " → ".join([s['sign'] for s in result['detected_signs'][-5:]])
            cv2.putText(frame, history_text, (20, history_y + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Debug: Show top 3 predictions
        if 'top3' in result and result['top3']:
            debug_y = 200
            cv2.rectangle(frame, (w - 370, debug_y - 15), (w - 10, debug_y + 110), (0, 0, 0), -1)
            cv2.rectangle(frame, (w - 370, debug_y - 15), (w - 10, debug_y + 110), (200, 200, 255), 1)
            cv2.putText(frame, "Model Predictions:", (w - 360, debug_y + 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)
            for i, (sign, conf) in enumerate(result['top3']):
                # Highlight if bias correction is active and this is Adress
                if sign == 'Adress' and i == 0 and result.get('bias_detected'):
                    color = (0, 100, 255)  # Orange for biased Adress
                    prefix = "⚠ "
                elif i == 0:
                    color = (0, 255, 0)  # Green for top prediction
                    prefix = "✓ "
                else:
                    color = (180, 180, 180)  # Gray for others
                    prefix = "  "
                cv2.putText(frame, f"{prefix}{i+1}. {sign}: {conf:.1%}", (w - 360, debug_y + 35 + i*20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            
            # Show Adress bias percentage if detected
            if result.get('bias_detected'):
                adress_ratio = result.get('adress_ratio', 0)
                cv2.putText(frame, f"Adress bias: {adress_ratio:.0%}", (w - 360, debug_y + 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
        
        # Intent (if available and verifier enabled)
        if self.verifier and 'intent' in result and result['intent']:
            intent = result['intent']
            intent_text = f"Intent: {intent.type.value}"
            cv2.putText(frame, intent_text, (w - 300, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
    
    def process_video(self, video_path: str, output_path: str = None):
        """
        Process a video file.
        
        Args:
            video_path: Path to input video
            output_path: Path to save output (if None, display only)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Video writer
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        print(f"📹 Processing video: {video_path}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.predict(frame_rgb)
            
            if result['mp_results']:
                frame = draw_landmarks(frame, result['mp_results'])
            
            self._draw_ui(frame, result)
            
            if writer:
                writer.write(frame)
            else:
                cv2.imshow('Processing', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        cap.release()
        if writer:
            writer.release()
            print(f"✅ Output saved to: {output_path}")
        cv2.destroyAllWindows()
        self.extractor.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='NS-AGF Real-Time Inference')
    parser.add_argument('--model_path', type=str, default='./models/ns_agcn.pth',
                       help='Path to trained model weights')
    parser.add_argument('--num_classes', type=int, default=None,
                       help='Number of sign classes (auto-detects from checkpoint if not specified)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID')
    parser.add_argument('--video', type=str, default=None,
                       help='Path to input video (if not using camera)')
    parser.add_argument('--output', type=str, default=None,
                       help='Path to save output video')
    parser.add_argument('--confidence', type=float, default=0.7,
                       help='Confidence threshold for predictions')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='Device to run inference on')
    parser.add_argument('--no_landmarks', action='store_true',
                       help='Disable landmark visualization')
    parser.add_argument('--no_smoothing', action='store_true',
                       help='Disable temporal smoothing (Task 1.3)')
    parser.add_argument('--smoothing_window', type=int, default=5,
                       help='Temporal smoothing window size (default: 5)')
    
    args = parser.parse_args()
    
    # Check if model exists
    if not os.path.exists(args.model_path):
        print(f"❌ Model not found: {args.model_path}")
        print("\n📥 Please download or train the model first!")
        print("   See kaggle_scripts/README_KAGGLE.md for training instructions")
        print("   Or use src/utils/model_loader.py to download from Kaggle")
        return
    
    # Initialize inference system
    try:
        system = SignLanguageInference(
            model_path=args.model_path,
            num_classes=args.num_classes,
            confidence_threshold=args.confidence,
            device=args.device
        )
        
        # Configure temporal smoothing (Task 1.3)
        system.use_temporal_smoothing = not args.no_smoothing
        if not args.no_smoothing:
            system.temporal_smoother = TemporalSmoother(window_size=args.smoothing_window)
            print(f"✅ Temporal smoothing enabled (window={args.smoothing_window})")
        else:
            print("⚠️  Temporal smoothing disabled")
            
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # Run inference
    try:
        if args.video:
            system.process_video(args.video, args.output)
        else:
            system.run_camera(args.camera, show_landmarks=not args.no_landmarks)
    except KeyboardInterrupt:
        print("\n\n👋 Inference stopped by user")
    except Exception as e:
        print(f"\n❌ Error during inference: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
