"""
MediaPipe Helper Utilities
===========================

Helper functions for extracting and processing MediaPipe Holistic landmarks.
"""

import numpy as np
import mediapipe as mp
from typing import Optional, Tuple


# Initialize MediaPipe
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


class MediaPipeExtractor:
    """
    Extract 75-node landmarks from MediaPipe Holistic.
    """
    
    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        Initialize MediaPipe Holistic processor.
        
        Args:
            static_image_mode: Whether to treat input as static images
            model_complexity: 0 (lite), 1 (full), or 2 (heavy)
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
        """
        self.holistic = mp_holistic.Holistic(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=False,
            refine_face_landmarks=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.num_nodes = 75
        self.num_features = 3
    
    def extract_landmarks(self, frame_rgb: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 75 landmarks from a single RGB frame.
        
        Args:
            frame_rgb: RGB image (H, W, 3)
        
        Returns:
            Landmarks array of shape (75, 3) or None if detection fails
        """
        # Process frame
        results = self.holistic.process(frame_rgb)
        
        # Check if any landmarks detected
        if results.pose_landmarks is None:
            return None
        
        # Initialize landmarks array
        landmarks = np.zeros((self.num_nodes, self.num_features), dtype=np.float32)
        
        # Extract pose landmarks (0-32)
        for i, lm in enumerate(results.pose_landmarks.landmark):
            if i < 33:
                landmarks[i] = [lm.x, lm.y, lm.z]
        
        # Extract left hand landmarks (33-53)
        if results.left_hand_landmarks:
            for i, lm in enumerate(results.left_hand_landmarks.landmark):
                landmarks[33 + i] = [lm.x, lm.y, lm.z]
        
        # Extract right hand landmarks (54-74)
        if results.right_hand_landmarks:
            for i, lm in enumerate(results.right_hand_landmarks.landmark):
                landmarks[54 + i] = [lm.x, lm.y, lm.z]
        
        return landmarks
    
    def extract_with_results(self, frame_rgb: np.ndarray) -> Tuple[Optional[np.ndarray], any]:
        """
        Extract landmarks and return MediaPipe results for visualization.
        
        Args:
            frame_rgb: RGB image
        
        Returns:
            (landmarks, mediapipe_results)
        """
        results = self.holistic.process(frame_rgb)
        
        if results.pose_landmarks is None:
            return None, results
        
        landmarks = np.zeros((self.num_nodes, self.num_features), dtype=np.float32)
        
        # Extract as before
        for i, lm in enumerate(results.pose_landmarks.landmark):
            if i < 33:
                landmarks[i] = [lm.x, lm.y, lm.z]
        
        if results.left_hand_landmarks:
            for i, lm in enumerate(results.left_hand_landmarks.landmark):
                landmarks[33 + i] = [lm.x, lm.y, lm.z]
        
        if results.right_hand_landmarks:
            for i, lm in enumerate(results.right_hand_landmarks.landmark):
                landmarks[54 + i] = [lm.x, lm.y, lm.z]
        
        return landmarks, results
    
    def close(self):
        """Release MediaPipe resources"""
        self.holistic.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def draw_landmarks(frame, results):
    """
    Draw MediaPipe landmarks on frame for visualization.
    
    Args:
        frame: BGR image
        results: MediaPipe Holistic results
    
    Returns:
        Frame with landmarks drawn
    """
    # Draw pose
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
    
    # Draw left hand
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.left_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style()
        )
    
    # Draw right hand
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.right_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style()
        )
    
    return frame


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """
    Normalize landmarks to be scale and translation invariant.
    
    Args:
        landmarks: (V, 3) array
    
    Returns:
        Normalized landmarks
    """
    # Center at origin (use pose center - node 0: nose)
    center = landmarks[0].copy()
    landmarks_centered = landmarks - center
    
    # Scale normalization (use shoulder width as reference)
    left_shoulder = landmarks_centered[11]
    right_shoulder = landmarks_centered[12]
    shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder)
    
    if shoulder_dist > 0:
        landmarks_normalized = landmarks_centered / shoulder_dist
    else:
        landmarks_normalized = landmarks_centered
    
    return landmarks_normalized.astype(np.float32)


def create_sequence_buffer(max_length: int = 30):
    """
    Create a circular buffer for storing landmark sequences.
    
    Args:
        max_length: Maximum sequence length
    
    Returns:
        Buffer object
    """
    return SequenceBuffer(max_length)


class SequenceBuffer:
    """
    Circular buffer for maintaining a sliding window of landmarks.
    """
    
    def __init__(self, max_length: int):
        self.max_length = max_length
        self.buffer = []
    
    def add(self, landmarks: np.ndarray):
        """Add new landmarks to buffer"""
        self.buffer.append(landmarks)
        if len(self.buffer) > self.max_length:
            self.buffer.pop(0)
    
    def get_sequence(self, pad: bool = True) -> np.ndarray:
        """
        Get current sequence.
        
        Args:
            pad: Whether to pad if buffer not full
        
        Returns:
            Sequence of shape (T, V, C)
        """
        if len(self.buffer) == 0:
            return np.zeros((self.max_length, 75, 3), dtype=np.float32)
        
        sequence = np.array(self.buffer)
        
        if pad and len(sequence) < self.max_length:
            padding = np.zeros((self.max_length - len(sequence), 75, 3), dtype=np.float32)
            sequence = np.vstack([padding, sequence])
        
        return sequence
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return len(self.buffer) >= self.max_length
    
    def clear(self):
        """Clear buffer"""
        self.buffer = []
    
    def __len__(self):
        return len(self.buffer)


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing MediaPipe Helper...")
    
    # Test with a blank frame
    import cv2
    
    # Create test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test extractor
    with MediaPipeExtractor() as extractor:
        print("✅ MediaPipe extractor initialized")
        
        # Extract landmarks
        landmarks = extractor.extract_landmarks(test_frame)
        
        if landmarks is not None:
            print(f"✅ Landmarks extracted: {landmarks.shape}")
        else:
            print("⚠️ No landmarks detected (expected for blank frame)")
    
    # Test sequence buffer
    buffer = create_sequence_buffer(max_length=30)
    print(f"✅ Sequence buffer created: {buffer.max_length} frames")
    
    # Add dummy landmarks
    for i in range(10):
        dummy_landmarks = np.random.randn(75, 3).astype(np.float32)
        buffer.add(dummy_landmarks)
    
    sequence = buffer.get_sequence(pad=True)
    print(f"✅ Sequence shape: {sequence.shape}")
    print(f"✅ Buffer full: {buffer.is_full()}")
    
    print("\n✨ All tests passed!")
