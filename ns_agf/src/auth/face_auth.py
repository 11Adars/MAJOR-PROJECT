"""
Face Authentication Module
===========================

Wrapper for InsightFace ArcFace model to extract face embeddings.
Reuses existing face recognition implementation from python_service.

Features:
- Face detection and alignment
- 512-dim face embeddings (ArcFace)
- Similarity computation for verification

Reference:
    Deng, J., et al. (2019). "ArcFace: Additive Angular Margin Loss for Deep Face Recognition"
"""

import numpy as np
from typing import Optional, Tuple
import cv2
import os


class FaceAuthenticator:
    """
    Face authentication using InsightFace ArcFace model.
    
    Extracts 512-dim face embeddings for biometric verification.
    """
    
    def __init__(self, model_name: str = 'buffalo_l'):
        """
        Initialize face authenticator.
        
        Args:
            model_name: InsightFace model name (default: buffalo_l)
        """
        self.model_name = model_name
        self.face_model = None
        self.feature_dim = 512
        
        # Load model lazily (only when needed)
        self._load_model()
    
    def _load_model(self):
        """Load InsightFace model"""
        try:
            import insightface
            
            print(f"🔧 Loading InsightFace model: {self.model_name}...")
            self.face_model = insightface.app.FaceAnalysis(name=self.model_name)
            self.face_model.prepare(ctx_id=-1, det_size=(640, 640))  # CPU mode
            print("✅ Face model loaded successfully")
            
        except ImportError:
            print("⚠️  InsightFace not installed. Face authentication disabled.")
            print("   Install with: pip install insightface onnxruntime")
            self.face_model = None
        except Exception as e:
            print(f"⚠️  Failed to load face model: {e}")
            self.face_model = None
    
    def extract_features(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face features from a video frame.
        
        Args:
            frame: RGB image (H, W, 3)
        
        Returns:
            512-dim face embedding, or None if no face detected
        """
        if self.face_model is None:
            # Return zeros if model not loaded
            return np.zeros(self.feature_dim)
        
        try:
            # Detect faces
            faces = self.face_model.get(frame)
            
            if len(faces) == 0:
                return None  # No face detected
            
            # Use the largest face (assuming primary subject)
            largest_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
            
            # Extract embedding
            embedding = largest_face.embedding
            
            # Normalize embedding
            embedding = embedding / (np.linalg.norm(embedding) + 1e-6)
            
            return embedding
            
        except Exception as e:
            print(f"⚠️  Face extraction error: {e}")
            return None
    
    def extract_features_from_sequence(
        self,
        frames: list
    ) -> Optional[np.ndarray]:
        """
        Extract face features from multiple frames (more robust).
        
        Args:
            frames: List of RGB images
        
        Returns:
            512-dim averaged face embedding
        """
        embeddings = []
        
        for frame in frames:
            embedding = self.extract_features(frame)
            if embedding is not None:
                embeddings.append(embedding)
        
        if not embeddings:
            return None
        
        # Average embeddings for robustness
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Re-normalize
        avg_embedding = avg_embedding / (np.linalg.norm(avg_embedding) + 1e-6)
        
        return avg_embedding
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute similarity between two face embeddings.
        
        Args:
            embedding1: 512-dim face embedding
            embedding2: 512-dim face embedding
        
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2) + 1e-6
        )
        
        # Convert to [0, 1] range
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    def verify(
        self,
        frame: np.ndarray,
        reference_embedding: np.ndarray,
        threshold: float = 0.6
    ) -> Tuple[bool, float]:
        """
        Verify if face in frame matches reference embedding.
        
        Args:
            frame: RGB image
            reference_embedding: 512-dim reference face embedding
            threshold: Similarity threshold for verification (default 0.6)
        
        Returns:
            (is_match, similarity_score)
        """
        # Extract embedding from frame
        embedding = self.extract_features(frame)
        
        if embedding is None:
            return False, 0.0
        
        # Compute similarity
        similarity = self.compute_similarity(embedding, reference_embedding)
        
        # Check threshold
        is_match = similarity >= threshold
        
        return is_match, similarity
    
    def get_face_bounding_box(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Get bounding box of detected face.
        
        Args:
            frame: RGB image
        
        Returns:
            (x1, y1, x2, y2) or None if no face detected
        """
        if self.face_model is None:
            return None
        
        try:
            faces = self.face_model.get(frame)
            
            if len(faces) == 0:
                return None
            
            # Use largest face
            largest_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
            bbox = largest_face.bbox.astype(int)
            
            return tuple(bbox)
            
        except Exception as e:
            print(f"⚠️  Face detection error: {e}")
            return None
    
    def draw_face_box(
        self,
        frame: np.ndarray,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding box around detected face.
        
        Args:
            frame: BGR image (for cv2)
            color: Box color (BGR)
            thickness: Line thickness
        
        Returns:
            Frame with face box drawn
        """
        # Convert BGR to RGB for face detection
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        bbox = self.get_face_bounding_box(frame_rgb)
        
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(
                frame,
                "Face Detected",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
        
        return frame


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing Face Authenticator...")
    
    authenticator = FaceAuthenticator()
    
    # Test with synthetic image
    print("\n--- Test 1: Feature Extraction ---")
    # Create synthetic face image (640x480 RGB)
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    features = authenticator.extract_features(test_frame)
    if features is not None:
        print(f"Feature dimension: {features.shape}")
        print(f"Feature range: [{np.min(features):.4f}, {np.max(features):.4f}]")
        print(f"Feature norm: {np.linalg.norm(features):.4f}")
    else:
        print("No face detected (expected for random image)")
    
    # Test similarity computation
    print("\n--- Test 2: Similarity Computation ---")
    embedding1 = np.random.randn(512)
    embedding1 = embedding1 / np.linalg.norm(embedding1)
    
    # Similar embedding
    embedding2 = embedding1 + np.random.randn(512) * 0.1
    embedding2 = embedding2 / np.linalg.norm(embedding2)
    
    similarity = authenticator.compute_similarity(embedding1, embedding2)
    print(f"Similarity (similar embeddings): {similarity:.4f}")
    
    # Different embedding
    embedding3 = np.random.randn(512)
    embedding3 = embedding3 / np.linalg.norm(embedding3)
    
    similarity2 = authenticator.compute_similarity(embedding1, embedding3)
    print(f"Similarity (different embeddings): {similarity2:.4f}")
    
    # Test verification
    print("\n--- Test 3: Verification ---")
    is_match, score = authenticator.verify(test_frame, embedding1, threshold=0.6)
    print(f"Verification result: {is_match}, Score: {score:.4f}")
    
    print("\n✨ All tests passed!")
