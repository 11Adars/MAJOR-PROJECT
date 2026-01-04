"""
Biometric Authentication Module for Banking Sign Language System
=================================================================

Novel continuous authentication approach for deaf/dumb users:
- Face Recognition (InsightFace ArcFace)
- Hand Geometry Biometrics (MediaPipe landmarks)
- Signing Style Behavioral Biometrics (Movement patterns)

Author: NS-AGF Project
Date: December 2025
"""

from .hand_biometrics import HandBiometricExtractor
from .signing_style import SigningStyleAnalyzer
from .face_auth import FaceAuthenticator
from .fusion_authenticator import BiometricFusionAuthenticator
from .user_database import UserBiometricDatabase

__all__ = [
    'HandBiometricExtractor',
    'SigningStyleAnalyzer',
    'FaceAuthenticator',
    'BiometricFusionAuthenticator',
    'UserBiometricDatabase'
]
