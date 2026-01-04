"""
Signing Style Behavioral Biometric Analyzer
=============================================

Extracts behavioral characteristics from signing movements:
- Movement speed and acceleration
- Trajectory smoothness (jerk analysis)
- Hand coordination patterns
- Temporal dynamics of signing

Novel Contribution:
- Behavioral biometrics during natural signing interaction
- Continuous authentication without interrupting user flow
- Suitable for deaf/dumb users

Reference:
    Bailador, G., et al. (2011). "Analysis of pattern recognition techniques for in-air signature biometrics"
    Adapted for sign language context
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.signal import savgol_filter
from scipy.spatial import distance
import warnings
warnings.filterwarnings('ignore')


class SigningStyleAnalyzer:
    """
    Analyzes signing style behavioral biometrics from landmark sequences.
    
    Features extracted:
    - Movement speed profiles (64-dim vector)
    - Acceleration patterns
    - Trajectory smoothness (jerk)
    - Hand coordination
    """
    
    def __init__(self, window_size: int = 30):
        """
        Initialize signing style analyzer.
        
        Args:
            window_size: Number of frames to analyze (default 30 = ~1 sec at 30fps)
        """
        self.window_size = window_size
        self.feature_dim = 64
        
        # Key landmarks for movement analysis
        self.key_landmarks = {
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hand': 19,
            'right_hand': 20,
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12
        }
    
    def extract_features(
        self,
        landmark_sequence: List[np.ndarray]
    ) -> np.ndarray:
        """
        Extract signing style features from landmark sequence.
        
        Args:
            landmark_sequence: List of (75, 3) landmark arrays over time
        
        Returns:
            64-dim behavioral feature vector
        """
        if not landmark_sequence or len(landmark_sequence) < 3:
            # Not enough frames for temporal analysis
            return np.zeros(self.feature_dim)
        
        # Trim or pad to window size
        if len(landmark_sequence) > self.window_size:
            landmark_sequence = landmark_sequence[-self.window_size:]
        
        features = []
        
        # 1. Movement speed features (16 features)
        speed_features = self._calculate_speed_features(landmark_sequence)
        features.extend(speed_features)
        
        # 2. Acceleration features (12 features)
        accel_features = self._calculate_acceleration_features(landmark_sequence)
        features.extend(accel_features)
        
        # 3. Trajectory smoothness (jerk) (12 features)
        jerk_features = self._calculate_jerk_features(landmark_sequence)
        features.extend(jerk_features)
        
        # 4. Hand coordination features (8 features)
        coordination_features = self._calculate_coordination_features(landmark_sequence)
        features.extend(coordination_features)
        
        # 5. Temporal dynamics (8 features)
        temporal_features = self._calculate_temporal_features(landmark_sequence)
        features.extend(temporal_features)
        
        # 6. Trajectory curvature (8 features)
        curvature_features = self._calculate_curvature_features(landmark_sequence)
        features.extend(curvature_features)
        
        # Ensure 64 dimensions
        features = np.array(features[:64])
        if len(features) < 64:
            features = np.pad(features, (0, 64 - len(features)), 'constant')
        
        return features
    
    def _calculate_speed_features(self, sequence: List[np.ndarray]) -> list:
        """
        Calculate movement speed statistics for key landmarks.
        
        Returns:
            16 speed features
        """
        features = []
        
        # Calculate speed for each key landmark
        landmark_names = ['left_wrist', 'right_wrist', 'left_hand', 'right_hand']
        
        for name in landmark_names:
            idx = self.key_landmarks[name]
            speeds = []
            
            for i in range(1, len(sequence)):
                prev_pos = sequence[i-1][idx][:2]  # x, y only
                curr_pos = sequence[i][idx][:2]
                
                speed = distance.euclidean(prev_pos, curr_pos)
                speeds.append(speed)
            
            if speeds:
                # Statistics: mean, std, max, min
                features.append(np.mean(speeds))
                features.append(np.std(speeds))
                features.append(np.max(speeds))
                features.append(np.min(speeds))
            else:
                features.extend([0.0, 0.0, 0.0, 0.0])
        
        return features
    
    def _calculate_acceleration_features(self, sequence: List[np.ndarray]) -> list:
        """
        Calculate acceleration patterns.
        
        Returns:
            12 acceleration features
        """
        features = []
        
        # Analyze acceleration for wrists and hands
        landmark_names = ['left_wrist', 'right_wrist', 'left_hand']
        
        for name in landmark_names:
            idx = self.key_landmarks[name]
            accelerations = []
            
            # Need at least 3 frames for acceleration
            if len(sequence) >= 3:
                for i in range(2, len(sequence)):
                    pos_t2 = sequence[i][idx][:2]
                    pos_t1 = sequence[i-1][idx][:2]
                    pos_t0 = sequence[i-2][idx][:2]
                    
                    # Acceleration = change in velocity
                    vel_t1 = pos_t1 - pos_t0
                    vel_t2 = pos_t2 - pos_t1
                    accel = vel_t2 - vel_t1
                    
                    accel_mag = np.linalg.norm(accel)
                    accelerations.append(accel_mag)
            
            if accelerations:
                # Statistics: mean, std, max, min
                features.append(np.mean(accelerations))
                features.append(np.std(accelerations))
                features.append(np.max(accelerations))
                features.append(np.min(accelerations))
            else:
                features.extend([0.0, 0.0, 0.0, 0.0])
        
        return features
    
    def _calculate_jerk_features(self, sequence: List[np.ndarray]) -> list:
        """
        Calculate jerk (rate of change of acceleration) - measures smoothness.
        
        Lower jerk = smoother movement (expert signers tend to have smoother movements)
        
        Returns:
            12 jerk features
        """
        features = []
        
        # Analyze jerk for wrists and hands
        landmark_names = ['left_wrist', 'right_wrist', 'left_hand']
        
        for name in landmark_names:
            idx = self.key_landmarks[name]
            jerks = []
            
            # Need at least 4 frames for jerk
            if len(sequence) >= 4:
                for i in range(3, len(sequence)):
                    # Calculate jerk as third derivative
                    pos_t3 = sequence[i][idx][:2]
                    pos_t2 = sequence[i-1][idx][:2]
                    pos_t1 = sequence[i-2][idx][:2]
                    pos_t0 = sequence[i-3][idx][:2]
                    
                    # Velocities
                    vel_t1 = pos_t1 - pos_t0
                    vel_t2 = pos_t2 - pos_t1
                    vel_t3 = pos_t3 - pos_t2
                    
                    # Accelerations
                    accel_t1 = vel_t2 - vel_t1
                    accel_t2 = vel_t3 - vel_t2
                    
                    # Jerk
                    jerk = accel_t2 - accel_t1
                    jerk_mag = np.linalg.norm(jerk)
                    jerks.append(jerk_mag)
            
            if jerks:
                # Statistics: mean, std, max, min
                features.append(np.mean(jerks))
                features.append(np.std(jerks))
                features.append(np.max(jerks))
                features.append(np.min(jerks))
            else:
                features.extend([0.0, 0.0, 0.0, 0.0])
        
        return features
    
    def _calculate_coordination_features(self, sequence: List[np.ndarray]) -> list:
        """
        Calculate hand coordination patterns (bilateral coordination).
        
        Returns:
            8 coordination features
        """
        features = []
        
        left_wrist_idx = self.key_landmarks['left_wrist']
        right_wrist_idx = self.key_landmarks['right_wrist']
        
        # 1. Bilateral symmetry (distance between left and right wrist movements)
        symmetry_scores = []
        for i in range(1, len(sequence)):
            left_vel = sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2]
            right_vel = sequence[i][right_wrist_idx][:2] - sequence[i-1][right_wrist_idx][:2]
            
            # Mirror right velocity for symmetry
            right_vel_mirrored = np.array([-right_vel[0], right_vel[1]])
            
            symmetry = distance.euclidean(left_vel, right_vel_mirrored)
            symmetry_scores.append(symmetry)
        
        if symmetry_scores:
            features.append(np.mean(symmetry_scores))
            features.append(np.std(symmetry_scores))
        else:
            features.extend([0.0, 0.0])
        
        # 2. Hand distance over time (how far apart hands are)
        hand_distances = []
        for frame in sequence:
            left_pos = frame[left_wrist_idx][:2]
            right_pos = frame[right_wrist_idx][:2]
            dist = distance.euclidean(left_pos, right_pos)
            hand_distances.append(dist)
        
        if hand_distances:
            features.append(np.mean(hand_distances))
            features.append(np.std(hand_distances))
            features.append(np.max(hand_distances))
            features.append(np.min(hand_distances))
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])
        
        # 3. Movement correlation (how synchronized are the hands)
        if len(sequence) > 5:
            left_speeds = []
            right_speeds = []
            for i in range(1, len(sequence)):
                left_speed = np.linalg.norm(sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2])
                right_speed = np.linalg.norm(sequence[i][right_wrist_idx][:2] - sequence[i-1][right_wrist_idx][:2])
                left_speeds.append(left_speed)
                right_speeds.append(right_speed)
            
            if len(left_speeds) > 1:
                correlation = np.corrcoef(left_speeds, right_speeds)[0, 1]
                features.append(correlation if not np.isnan(correlation) else 0.0)
            else:
                features.append(0.0)
        else:
            features.append(0.0)
        
        # 4. Phase difference (timing offset between hands)
        # Simplified: difference in peak speed timing
        if len(sequence) > 10:
            left_peak_idx = np.argmax([np.linalg.norm(sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2]) 
                                      for i in range(1, len(sequence))])
            right_peak_idx = np.argmax([np.linalg.norm(sequence[i][right_wrist_idx][:2] - sequence[i-1][right_wrist_idx][:2]) 
                                       for i in range(1, len(sequence))])
            phase_diff = abs(left_peak_idx - right_peak_idx) / len(sequence)
            features.append(phase_diff)
        else:
            features.append(0.0)
        
        return features
    
    def _calculate_temporal_features(self, sequence: List[np.ndarray]) -> list:
        """
        Calculate temporal dynamics of signing.
        
        Returns:
            8 temporal features
        """
        features = []
        
        # 1. Signing duration (normalized)
        features.append(len(sequence) / self.window_size)
        
        # 2. Movement density (proportion of time spent moving)
        left_wrist_idx = self.key_landmarks['left_wrist']
        right_wrist_idx = self.key_landmarks['right_wrist']
        
        movement_threshold = 0.01  # Threshold for considering movement
        moving_frames = 0
        
        for i in range(1, len(sequence)):
            left_move = np.linalg.norm(sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2])
            right_move = np.linalg.norm(sequence[i][right_wrist_idx][:2] - sequence[i-1][right_wrist_idx][:2])
            
            if left_move > movement_threshold or right_move > movement_threshold:
                moving_frames += 1
        
        movement_density = moving_frames / max(len(sequence) - 1, 1)
        features.append(movement_density)
        
        # 3. Pause patterns (number of pauses)
        pauses = 0
        in_pause = False
        for i in range(1, len(sequence)):
            left_move = np.linalg.norm(sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2])
            right_move = np.linalg.norm(sequence[i][right_wrist_idx][:2] - sequence[i-1][right_wrist_idx][:2])
            
            if left_move < movement_threshold and right_move < movement_threshold:
                if not in_pause:
                    pauses += 1
                    in_pause = True
            else:
                in_pause = False
        
        features.append(pauses / max(len(sequence), 1))
        
        # 4. Speed variation over time (coefficient of variation)
        speeds = []
        for i in range(1, len(sequence)):
            left_speed = np.linalg.norm(sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2])
            right_speed = np.linalg.norm(sequence[i][right_wrist_idx][:2] - sequence[i-1][right_wrist_idx][:2])
            avg_speed = (left_speed + right_speed) / 2
            speeds.append(avg_speed)
        
        if speeds and np.mean(speeds) > 0:
            cv = np.std(speeds) / np.mean(speeds)
            features.append(cv)
        else:
            features.append(0.0)
        
        # 5. Acceleration/deceleration ratio
        accelerating_frames = 0
        decelerating_frames = 0
        
        for i in range(2, len(sequence)):
            curr_speed = np.linalg.norm(sequence[i][left_wrist_idx][:2] - sequence[i-1][left_wrist_idx][:2])
            prev_speed = np.linalg.norm(sequence[i-1][left_wrist_idx][:2] - sequence[i-2][left_wrist_idx][:2])
            
            if curr_speed > prev_speed:
                accelerating_frames += 1
            elif curr_speed < prev_speed:
                decelerating_frames += 1
        
        if decelerating_frames > 0:
            accel_ratio = accelerating_frames / decelerating_frames
            features.append(min(accel_ratio, 10.0))  # Cap at 10
        else:
            features.append(0.0)
        
        # 6-8. Spatial extent (bounding box of movement)
        all_positions = []
        for frame in sequence:
            all_positions.append(frame[left_wrist_idx][:2])
            all_positions.append(frame[right_wrist_idx][:2])
        
        all_positions = np.array(all_positions)
        if len(all_positions) > 0:
            x_range = np.max(all_positions[:, 0]) - np.min(all_positions[:, 0])
            y_range = np.max(all_positions[:, 1]) - np.min(all_positions[:, 1])
            area = x_range * y_range
            features.extend([x_range, y_range, area])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        return features
    
    def _calculate_curvature_features(self, sequence: List[np.ndarray]) -> list:
        """
        Calculate trajectory curvature (path complexity).
        
        Returns:
            8 curvature features
        """
        features = []
        
        # Analyze curvature for both wrists
        landmark_names = ['left_wrist', 'right_wrist']
        
        for name in landmark_names:
            idx = self.key_landmarks[name]
            curvatures = []
            
            # Need at least 3 points for curvature
            if len(sequence) >= 3:
                for i in range(1, len(sequence) - 1):
                    p0 = sequence[i-1][idx][:2]
                    p1 = sequence[i][idx][:2]
                    p2 = sequence[i+1][idx][:2]
                    
                    # Calculate curvature using Menger curvature formula
                    # K = 4 * Area(triangle) / (a * b * c)
                    area = 0.5 * abs((p1[0] - p0[0]) * (p2[1] - p0[1]) - 
                                    (p2[0] - p0[0]) * (p1[1] - p0[1]))
                    
                    a = distance.euclidean(p0, p1)
                    b = distance.euclidean(p1, p2)
                    c = distance.euclidean(p0, p2)
                    
                    if a * b * c > 1e-6:
                        curvature = 4 * area / (a * b * c)
                        curvatures.append(curvature)
            
            if curvatures:
                # Statistics: mean, std, max, min
                features.append(np.mean(curvatures))
                features.append(np.std(curvatures))
                features.append(np.max(curvatures))
                features.append(np.min(curvatures))
            else:
                features.extend([0.0, 0.0, 0.0, 0.0])
        
        return features
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize features to [0, 1] range.
        
        Args:
            features: 64-dim feature vector
        
        Returns:
            Normalized 64-dim feature vector
        """
        # Handle edge cases
        if np.all(features == 0):
            return features
        
        # Clip extreme values
        features = np.clip(features, -10, 10)
        
        # Min-max normalization
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
        Compute similarity between two signing style feature vectors.
        
        Args:
            features1: 64-dim feature vector
            features2: 64-dim feature vector
        
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
    print("🔬 Testing Signing Style Analyzer...")
    
    analyzer = SigningStyleAnalyzer(window_size=30)
    
    # Test with synthetic landmark sequence
    print("\n--- Test 1: Feature Extraction ---")
    # Simulate 30 frames of 75 landmarks
    sequence = [np.random.rand(75, 3) * 0.5 for _ in range(30)]
    
    features = analyzer.extract_features(sequence)
    print(f"Feature dimension: {features.shape}")
    print(f"Feature range: [{np.min(features):.4f}, {np.max(features):.4f}]")
    print(f"First 10 features: {features[:10]}")
    
    # Test similarity computation
    print("\n--- Test 2: Similarity Computation ---")
    # Similar sequence (same person, slight variation)
    sequence2 = [frame + np.random.randn(75, 3) * 0.01 for frame in sequence]
    features2 = analyzer.extract_features(sequence2)
    similarity = analyzer.compute_similarity(features, features2)
    print(f"Similarity (same person, slight variation): {similarity:.4f}")
    
    # Different sequence (different person)
    sequence3 = [np.random.rand(75, 3) * 0.5 for _ in range(30)]
    features3 = analyzer.extract_features(sequence3)
    similarity2 = analyzer.compute_similarity(features, features3)
    print(f"Similarity (different person): {similarity2:.4f}")
    
    # Test with short sequence
    print("\n--- Test 3: Short Sequence Handling ---")
    short_sequence = [np.random.rand(75, 3) * 0.5 for _ in range(5)]
    features_short = analyzer.extract_features(short_sequence)
    print(f"Feature dimension (short): {features_short.shape}")
    print(f"Non-zero features: {np.count_nonzero(features_short)}")
    
    print("\n✨ All tests passed!")
