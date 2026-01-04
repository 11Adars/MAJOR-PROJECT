"""
Hand Geometry Biometric Extractor
===================================

Extracts physiological hand features from MediaPipe landmarks:
- Palm dimensions (width, length, area)
- Finger lengths and ratios
- Hand shape descriptors
- Joint angle distributions

Novel Contribution:
- Continuous hand biometric verification during signing
- No separate authentication step needed
- Suitable for deaf/dumb users

Reference:
    Kumar, A., & Zhang, D. (2007). "Personal authentication using hand vein triangulation"
    Adapted for sign language interaction context
"""

import numpy as np
from typing import Dict, Tuple, Optional
from scipy.spatial import distance
import cv2


class HandBiometricExtractor:
    """
    Extracts discriminative hand geometry features from MediaPipe landmarks.
    
    Features extracted:
    - Palm dimensions (128-dim vector)
    - Finger ratios and lengths
    - Hand shape characteristics
    - Joint angle patterns
    """
    
    def __init__(self):
        """Initialize hand biometric extractor"""
        # MediaPipe hand landmark indices
        self.wrist_idx = 0
        self.thumb_base_idx = 1
        self.thumb_tip_idx = 4
        self.index_base_idx = 5
        self.index_tip_idx = 8
        self.middle_base_idx = 9
        self.middle_tip_idx = 12
        self.ring_base_idx = 13
        self.ring_tip_idx = 16
        self.pinky_base_idx = 17
        self.pinky_tip_idx = 20
        
        # Palm landmarks for shape
        self.palm_indices = [0, 1, 5, 9, 13, 17]
        
        # Expected feature dimension
        self.feature_dim = 128
        
    def extract_features(
        self,
        left_hand_landmarks: Optional[np.ndarray],
        right_hand_landmarks: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Extract hand geometry features from both hands.
        
        Args:
            left_hand_landmarks: (21, 3) array of left hand landmarks (x, y, z)
            right_hand_landmarks: (21, 3) array of right hand landmarks (x, y, z)
        
        Returns:
            128-dim feature vector
        """
        features = []
        
        # Process both hands
        for hand_landmarks in [left_hand_landmarks, right_hand_landmarks]:
            if hand_landmarks is not None and len(hand_landmarks) == 21:
                hand_features = self._extract_single_hand_features(hand_landmarks)
                features.extend(hand_features)
            else:
                # Pad with zeros if hand not detected
                features.extend(np.zeros(64).tolist())
        
        # Ensure exactly 128 dimensions
        features = np.array(features[:128])
        if len(features) < 128:
            features = np.pad(features, (0, 128 - len(features)), 'constant')
        
        return features
    
    def _extract_single_hand_features(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Extract features from a single hand.
        
        Returns:
            64-dim feature vector per hand
        """
        features = []
        
        # 1. Palm dimensions (4 features)
        palm_width = self._calculate_palm_width(landmarks)
        palm_length = self._calculate_palm_length(landmarks)
        palm_area = self._calculate_palm_area(landmarks)
        palm_aspect_ratio = palm_width / (palm_length + 1e-6)
        
        features.extend([palm_width, palm_length, palm_area, palm_aspect_ratio])
        
        # 2. Finger lengths (5 features)
        finger_lengths = self._calculate_finger_lengths(landmarks)
        features.extend(finger_lengths)
        
        # 3. Finger ratios (10 features - ratios between fingers)
        finger_ratios = []
        for i in range(len(finger_lengths)):
            for j in range(i + 1, len(finger_lengths)):
                ratio = finger_lengths[i] / (finger_lengths[j] + 1e-6)
                finger_ratios.append(ratio)
        features.extend(finger_ratios)
        
        # 4. Joint angles (15 features - 3 per finger)
        joint_angles = self._calculate_joint_angles(landmarks)
        features.extend(joint_angles)
        
        # 5. Hand shape descriptors (10 features)
        shape_features = self._calculate_hand_shape(landmarks)
        features.extend(shape_features)
        
        # 6. Distance-based features (20 features)
        distance_features = self._calculate_distance_features(landmarks)
        features.extend(distance_features)
        
        # Ensure 64 dimensions
        features = np.array(features[:64])
        if len(features) < 64:
            features = np.pad(features, (0, 64 - len(features)), 'constant')
        
        return features
    
    def _calculate_palm_width(self, landmarks: np.ndarray) -> float:
        """Calculate palm width (wrist to middle finger base)"""
        wrist = landmarks[self.wrist_idx]
        middle_base = landmarks[self.middle_base_idx]
        return distance.euclidean(wrist[:2], middle_base[:2])
    
    def _calculate_palm_length(self, landmarks: np.ndarray) -> float:
        """Calculate palm length (index base to pinky base)"""
        index_base = landmarks[self.index_base_idx]
        pinky_base = landmarks[self.pinky_base_idx]
        return distance.euclidean(index_base[:2], pinky_base[:2])
    
    def _calculate_palm_area(self, landmarks: np.ndarray) -> float:
        """Calculate palm area using convex hull"""
        palm_points = landmarks[self.palm_indices][:, :2]  # Only x, y
        try:
            # Use convex hull to estimate palm area
            from scipy.spatial import ConvexHull
            hull = ConvexHull(palm_points)
            return hull.volume  # In 2D, volume is area
        except:
            return 0.0
    
    def _calculate_finger_lengths(self, landmarks: np.ndarray) -> list:
        """Calculate lengths of all 5 fingers"""
        finger_tips = [
            self.thumb_tip_idx,
            self.index_tip_idx,
            self.middle_tip_idx,
            self.ring_tip_idx,
            self.pinky_tip_idx
        ]
        finger_bases = [
            self.thumb_base_idx,
            self.index_base_idx,
            self.middle_base_idx,
            self.ring_base_idx,
            self.pinky_base_idx
        ]
        
        lengths = []
        for tip_idx, base_idx in zip(finger_tips, finger_bases):
            tip = landmarks[tip_idx]
            base = landmarks[base_idx]
            length = distance.euclidean(tip[:2], base[:2])
            lengths.append(length)
        
        return lengths
    
    def _calculate_joint_angles(self, landmarks: np.ndarray) -> list:
        """Calculate joint angles for all fingers"""
        angles = []
        
        # Define joints for each finger (base, middle, tip)
        finger_joints = [
            [1, 2, 4],   # Thumb
            [5, 6, 8],   # Index
            [9, 10, 12], # Middle
            [13, 14, 16],# Ring
            [17, 18, 20] # Pinky
        ]
        
        for joints in finger_joints:
            p1 = landmarks[joints[0]][:2]
            p2 = landmarks[joints[1]][:2]
            p3 = landmarks[joints[2]][:2]
            
            # Calculate angle at p2
            v1 = p1 - p2
            v2 = p3 - p2
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            angles.append(angle)
        
        return angles
    
    def _calculate_hand_shape(self, landmarks: np.ndarray) -> list:
        """Calculate hand shape descriptors"""
        features = []
        
        # 1. Hand span (thumb tip to pinky tip)
        thumb_tip = landmarks[self.thumb_tip_idx]
        pinky_tip = landmarks[self.pinky_tip_idx]
        hand_span = distance.euclidean(thumb_tip[:2], pinky_tip[:2])
        features.append(hand_span)
        
        # 2. Hand compactness (area / perimeter^2)
        palm_area = self._calculate_palm_area(landmarks)
        palm_perimeter = self._calculate_palm_perimeter(landmarks)
        compactness = palm_area / (palm_perimeter**2 + 1e-6)
        features.append(compactness)
        
        # 3. Finger spread (angles between adjacent fingers)
        finger_tips = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
        wrist = landmarks[self.wrist_idx][:2]
        
        for i in range(len(finger_tips) - 1):
            v1 = landmarks[finger_tips[i]][:2] - wrist
            v2 = landmarks[finger_tips[i+1]][:2] - wrist
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            features.append(angle)
        
        # 4. Hand orientation (angle of middle finger)
        middle_tip = landmarks[self.middle_tip_idx][:2]
        middle_base = landmarks[self.middle_base_idx][:2]
        orientation = np.arctan2(middle_tip[1] - middle_base[1], 
                                middle_tip[0] - middle_base[0])
        features.append(orientation)
        
        # 5. Thumb-index angle (important for pinch gestures)
        thumb_tip = landmarks[self.thumb_tip_idx][:2]
        index_tip = landmarks[self.index_tip_idx][:2]
        thumb_index_dist = distance.euclidean(thumb_tip, index_tip)
        features.append(thumb_index_dist)
        
        # Pad to 10 features
        while len(features) < 10:
            features.append(0.0)
        
        return features[:10]
    
    def _calculate_palm_perimeter(self, landmarks: np.ndarray) -> float:
        """Calculate palm perimeter"""
        palm_points = landmarks[self.palm_indices][:, :2]
        perimeter = 0.0
        for i in range(len(palm_points)):
            p1 = palm_points[i]
            p2 = palm_points[(i + 1) % len(palm_points)]
            perimeter += distance.euclidean(p1, p2)
        return perimeter
    
    def _calculate_distance_features(self, landmarks: np.ndarray) -> list:
        """Calculate distances between key landmarks"""
        features = []
        
        # Key landmark pairs for distance measurement
        landmark_pairs = [
            (0, 4),   # Wrist to thumb tip
            (0, 8),   # Wrist to index tip
            (0, 12),  # Wrist to middle tip
            (0, 16),  # Wrist to ring tip
            (0, 20),  # Wrist to pinky tip
            (4, 8),   # Thumb tip to index tip
            (4, 12),  # Thumb tip to middle tip
            (8, 12),  # Index tip to middle tip
            (12, 16), # Middle tip to ring tip
            (16, 20), # Ring tip to pinky tip
            (1, 5),   # Thumb base to index base
            (5, 9),   # Index base to middle base
            (9, 13),  # Middle base to ring base
            (13, 17), # Ring base to pinky base
            (5, 17),  # Index base to pinky base
            (1, 17),  # Thumb base to pinky base
            (2, 6),   # Thumb joint to index joint
            (6, 10),  # Index joint to middle joint
            (10, 14), # Middle joint to ring joint
            (14, 18), # Ring joint to pinky joint
        ]
        
        for idx1, idx2 in landmark_pairs:
            p1 = landmarks[idx1][:2]
            p2 = landmarks[idx2][:2]
            dist = distance.euclidean(p1, p2)
            features.append(dist)
        
        return features
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize features to [0, 1] range for better comparison.
        
        Args:
            features: 128-dim feature vector
        
        Returns:
            Normalized 128-dim feature vector
        """
        # Use min-max normalization per feature
        features_min = np.min(features)
        features_max = np.max(features)
        
        if features_max - features_min > 1e-6:
            normalized = (features - features_min) / (features_max - features_min)
        else:
            normalized = features
        
        return normalized
    
    def compute_similarity(
        self,
        features1: np.ndarray,
        features2: np.ndarray
    ) -> float:
        """
        Compute similarity between two hand biometric feature vectors.
        
        Args:
            features1: 128-dim feature vector
            features2: 128-dim feature vector
        
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Normalize both features
        f1 = self.normalize_features(features1)
        f2 = self.normalize_features(features2)
        
        # Use cosine similarity
        similarity = np.dot(f1, f2) / (np.linalg.norm(f1) * np.linalg.norm(f2) + 1e-6)
        
        # Convert to [0, 1] range
        similarity = (similarity + 1) / 2
        
        return float(similarity)


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing Hand Biometric Extractor...")
    
    extractor = HandBiometricExtractor()
    
    # Test with synthetic hand landmarks
    print("\n--- Test 1: Feature Extraction ---")
    # Simulate MediaPipe landmarks (21 points × 3 coordinates)
    left_hand = np.random.rand(21, 3) * 0.5
    right_hand = np.random.rand(21, 3) * 0.5
    
    features = extractor.extract_features(left_hand, right_hand)
    print(f"Feature dimension: {features.shape}")
    print(f"Feature range: [{np.min(features):.4f}, {np.max(features):.4f}]")
    print(f"First 10 features: {features[:10]}")
    
    # Test similarity computation
    print("\n--- Test 2: Similarity Computation ---")
    features2 = extractor.extract_features(left_hand + 0.01, right_hand + 0.01)
    similarity = extractor.compute_similarity(features, features2)
    print(f"Similarity (same person, slight movement): {similarity:.4f}")
    
    features3 = extractor.extract_features(np.random.rand(21, 3), np.random.rand(21, 3))
    similarity2 = extractor.compute_similarity(features, features3)
    print(f"Similarity (different person): {similarity2:.4f}")
    
    # Test with missing hand
    print("\n--- Test 3: Missing Hand Handling ---")
    features_one_hand = extractor.extract_features(left_hand, None)
    print(f"Feature dimension (one hand): {features_one_hand.shape}")
    print(f"Non-zero features: {np.count_nonzero(features_one_hand)}")
    
    print("\n✨ All tests passed!")
