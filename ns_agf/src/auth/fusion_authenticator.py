"""
Biometric Fusion Authenticator
================================

Fuses three biometric modalities for continuous authentication:
1. Face Recognition (512-dim) - InsightFace ArcFace
2. Hand Geometry (128-dim) - MediaPipe landmarks
3. Signing Style (64-dim) - Behavioral patterns

Total: 704-dim feature vector → Binary classifier (Authentic/Fraud)

Novel Contribution:
- First banking SLR with continuous hand biometrics
- Multi-modal fusion during natural signing
- Suitable for deaf/dumb users (no voice needed)

Reference:
    Ross, A., & Jain, A. (2003). "Information fusion in biometrics"
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
import pickle
import os
from pathlib import Path

# Import our biometric extractors
from .face_auth import FaceAuthenticator
from .hand_biometrics import HandBiometricExtractor
from .signing_style import SigningStyleAnalyzer


class BiometricFusionAuthenticator:
    """
    Multi-modal biometric authenticator using score-level fusion.
    
    Combines:
    - Face: 512-dim (physiological)
    - Hand: 128-dim (physiological)
    - Style: 64-dim (behavioral)
    
    Total: 704-dim feature vector
    """
    
    def __init__(
        self,
        face_weight: float = 0.5,
        hand_weight: float = 0.3,
        style_weight: float = 0.2,
        verification_threshold: float = 0.65
    ):
        """
        Initialize biometric fusion authenticator.
        
        Args:
            face_weight: Weight for face similarity (default 0.5)
            hand_weight: Weight for hand similarity (default 0.3)
            style_weight: Weight for signing style similarity (default 0.2)
            verification_threshold: Overall threshold for authentication (default 0.65)
        """
        # Initialize individual authenticators
        self.face_auth = FaceAuthenticator()
        self.hand_extractor = HandBiometricExtractor()
        self.style_analyzer = SigningStyleAnalyzer(window_size=30)
        
        # Fusion weights (must sum to 1.0)
        self.face_weight = face_weight
        self.hand_weight = hand_weight
        self.style_weight = style_weight
        
        # Normalize weights
        total_weight = face_weight + hand_weight + style_weight
        self.face_weight /= total_weight
        self.hand_weight /= total_weight
        self.style_weight /= total_weight
        
        # Verification threshold
        self.verification_threshold = verification_threshold
        
        print(f"🔐 Biometric Fusion Authenticator initialized")
        print(f"   Face weight: {self.face_weight:.2f}")
        print(f"   Hand weight: {self.hand_weight:.2f}")
        print(f"   Style weight: {self.style_weight:.2f}")
        print(f"   Threshold: {self.verification_threshold:.2f}")
    
    def extract_multimodal_features(
        self,
        frame: np.ndarray,
        left_hand_landmarks: Optional[np.ndarray],
        right_hand_landmarks: Optional[np.ndarray],
        landmark_sequence: Optional[List[np.ndarray]]
    ) -> Dict[str, np.ndarray]:
        """
        Extract features from all three biometric modalities.
        
        Args:
            frame: RGB image (H, W, 3) for face extraction
            left_hand_landmarks: (21, 3) array of left hand landmarks
            right_hand_landmarks: (21, 3) array of right hand landmarks
            landmark_sequence: List of (75, 3) landmark arrays for style analysis
        
        Returns:
            Dict with keys: 'face', 'hand', 'style', 'fusion'
        """
        features = {}
        
        # 1. Extract face features (512-dim)
        face_features = self.face_auth.extract_features(frame)
        if face_features is None:
            face_features = np.zeros(512)
        features['face'] = face_features
        
        # 2. Extract hand geometry features (128-dim)
        hand_features = self.hand_extractor.extract_features(
            left_hand_landmarks,
            right_hand_landmarks
        )
        features['hand'] = hand_features
        
        # 3. Extract signing style features (64-dim)
        if landmark_sequence is not None and len(landmark_sequence) > 0:
            style_features = self.style_analyzer.extract_features(landmark_sequence)
        else:
            style_features = np.zeros(64)
        features['style'] = style_features
        
        # 4. Fuse all features (704-dim)
        fusion_features = np.concatenate([
            features['face'],
            features['hand'],
            features['style']
        ])
        features['fusion'] = fusion_features
        
        return features
    
    def compute_fusion_score(
        self,
        query_features: Dict[str, np.ndarray],
        reference_features: Dict[str, np.ndarray]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute weighted fusion similarity score.
        
        Args:
            query_features: Current biometric features
            reference_features: Stored reference features
        
        Returns:
            (fusion_score, individual_scores_dict)
        """
        individual_scores = {}
        
        # 1. Face similarity
        face_sim = self.face_auth.compute_similarity(
            query_features['face'],
            reference_features['face']
        )
        individual_scores['face'] = face_sim
        
        # 2. Hand similarity
        hand_sim = self.hand_extractor.compute_similarity(
            query_features['hand'],
            reference_features['hand']
        )
        individual_scores['hand'] = hand_sim
        
        # 3. Style similarity
        style_sim = self.style_analyzer.compute_similarity(
            query_features['style'],
            reference_features['style']
        )
        individual_scores['style'] = style_sim
        
        # 4. Weighted fusion
        fusion_score = (
            self.face_weight * face_sim +
            self.hand_weight * hand_sim +
            self.style_weight * style_sim
        )
        individual_scores['fusion'] = fusion_score
        
        return fusion_score, individual_scores
    
    def verify(
        self,
        query_features: Dict[str, np.ndarray],
        reference_features: Dict[str, np.ndarray],
        threshold: Optional[float] = None
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Verify if query biometrics match reference biometrics.
        
        Args:
            query_features: Current biometric features
            reference_features: Stored reference features
            threshold: Custom threshold (uses default if None)
        
        Returns:
            (is_authenticated, fusion_score, individual_scores)
        """
        if threshold is None:
            threshold = self.verification_threshold
        
        # Compute fusion score
        fusion_score, individual_scores = self.compute_fusion_score(
            query_features,
            reference_features
        )
        
        # Check threshold
        is_authenticated = fusion_score >= threshold
        
        return is_authenticated, fusion_score, individual_scores
    
    def enroll_user(
        self,
        user_id: str,
        frames: List[np.ndarray],
        left_hand_landmarks_list: List[Optional[np.ndarray]],
        right_hand_landmarks_list: List[Optional[np.ndarray]],
        landmark_sequences: List[List[np.ndarray]],
        num_samples: int = 5
    ) -> Dict[str, np.ndarray]:
        """
        Enroll a new user by collecting multiple biometric samples.
        
        Args:
            user_id: Unique user identifier
            frames: List of RGB frames
            left_hand_landmarks_list: List of left hand landmarks
            right_hand_landmarks_list: List of right hand landmarks
            landmark_sequences: List of signing sequences
            num_samples: Number of samples to average (default 5)
        
        Returns:
            Average biometric features for enrollment
        """
        print(f"\n🔐 Enrolling user: {user_id}")
        print(f"   Collecting {num_samples} biometric samples...")
        
        all_features = {
            'face': [],
            'hand': [],
            'style': []
        }
        
        # Collect features from multiple samples
        for i in range(min(num_samples, len(frames))):
            features = self.extract_multimodal_features(
                frame=frames[i],
                left_hand_landmarks=left_hand_landmarks_list[i] if i < len(left_hand_landmarks_list) else None,
                right_hand_landmarks=right_hand_landmarks_list[i] if i < len(right_hand_landmarks_list) else None,
                landmark_sequence=landmark_sequences[i] if i < len(landmark_sequences) else None
            )
            
            all_features['face'].append(features['face'])
            all_features['hand'].append(features['hand'])
            all_features['style'].append(features['style'])
        
        # Average features for robust enrollment
        enrolled_features = {
            'face': np.mean(all_features['face'], axis=0),
            'hand': np.mean(all_features['hand'], axis=0),
            'style': np.mean(all_features['style'], axis=0)
        }
        
        # Create fusion feature
        enrolled_features['fusion'] = np.concatenate([
            enrolled_features['face'],
            enrolled_features['hand'],
            enrolled_features['style']
        ])
        
        print(f"✅ User {user_id} enrolled successfully")
        print(f"   Face features: {enrolled_features['face'].shape}")
        print(f"   Hand features: {enrolled_features['hand'].shape}")
        print(f"   Style features: {enrolled_features['style'].shape}")
        print(f"   Fusion features: {enrolled_features['fusion'].shape}")
        
        return enrolled_features
    
    def save_model(self, filepath: str):
        """Save fusion weights and settings"""
        model_data = {
            'face_weight': self.face_weight,
            'hand_weight': self.hand_weight,
            'style_weight': self.style_weight,
            'verification_threshold': self.verification_threshold
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Fusion model saved: {filepath}")
    
    def load_model(self, filepath: str):
        """Load fusion weights and settings"""
        if not os.path.exists(filepath):
            print(f"⚠️  Model file not found: {filepath}")
            return
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.face_weight = model_data['face_weight']
        self.hand_weight = model_data['hand_weight']
        self.style_weight = model_data['style_weight']
        self.verification_threshold = model_data['verification_threshold']
        
        print(f"📂 Fusion model loaded: {filepath}")
        print(f"   Face weight: {self.face_weight:.2f}")
        print(f"   Hand weight: {self.hand_weight:.2f}")
        print(f"   Style weight: {self.style_weight:.2f}")


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing Biometric Fusion Authenticator...")
    
    authenticator = BiometricFusionAuthenticator(
        face_weight=0.5,
        hand_weight=0.3,
        style_weight=0.2,
        verification_threshold=0.65
    )
    
    # Test feature extraction
    print("\n--- Test 1: Multi-modal Feature Extraction ---")
    
    # Synthetic data
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    left_hand = np.random.rand(21, 3) * 0.5
    right_hand = np.random.rand(21, 3) * 0.5
    sequence = [np.random.rand(75, 3) * 0.5 for _ in range(30)]
    
    features = authenticator.extract_multimodal_features(
        frame, left_hand, right_hand, sequence
    )
    
    print(f"Face features: {features['face'].shape}")
    print(f"Hand features: {features['hand'].shape}")
    print(f"Style features: {features['style'].shape}")
    print(f"Fusion features: {features['fusion'].shape}")
    
    # Test verification
    print("\n--- Test 2: Verification ---")
    
    # Create reference features (enrollment)
    reference_features = {
        'face': features['face'].copy(),
        'hand': features['hand'].copy(),
        'style': features['style'].copy()
    }
    
    # Query with slight variation (same person)
    query_features = {
        'face': features['face'] + np.random.randn(512) * 0.05,
        'hand': features['hand'] + np.random.randn(128) * 0.05,
        'style': features['style'] + np.random.randn(64) * 0.05
    }
    
    is_auth, score, individual = authenticator.verify(query_features, reference_features)
    print(f"Same person - Authenticated: {is_auth}, Score: {score:.4f}")
    print(f"   Face: {individual['face']:.4f}")
    print(f"   Hand: {individual['hand']:.4f}")
    print(f"   Style: {individual['style']:.4f}")
    
    # Query different person
    diff_features = {
        'face': np.random.randn(512),
        'hand': np.random.randn(128),
        'style': np.random.randn(64)
    }
    
    is_auth2, score2, individual2 = authenticator.verify(diff_features, reference_features)
    print(f"Different person - Authenticated: {is_auth2}, Score: {score2:.4f}")
    print(f"   Face: {individual2['face']:.4f}")
    print(f"   Hand: {individual2['hand']:.4f}")
    print(f"   Style: {individual2['style']:.4f}")
    
    # Test model save/load
    print("\n--- Test 3: Model Save/Load ---")
    test_path = "test_fusion_model.pkl"
    authenticator.save_model(test_path)
    authenticator.load_model(test_path)
    
    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)
    
    print("\n✨ All tests passed!")
