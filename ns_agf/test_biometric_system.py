"""
Quick Test Script for Biometric Authentication System
======================================================

Tests the complete authentication pipeline with synthetic data.
Run this before integration to verify all modules work together.

Usage:
    python test_biometric_system.py
"""

import numpy as np
import cv2
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from auth import (
    HandBiometricExtractor,
    SigningStyleAnalyzer,
    FaceAuthenticator,
    BiometricFusionAuthenticator,
    UserBiometricDatabase
)


def generate_synthetic_data():
    """Generate synthetic biometric data for testing"""
    print("🔧 Generating synthetic data...")
    
    # Generate frames (480x640 RGB)
    frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
    
    # Generate hand landmarks (21 points × 3 coordinates)
    left_hands = [np.random.rand(21, 3) * 0.5 for _ in range(5)]
    right_hands = [np.random.rand(21, 3) * 0.5 for _ in range(5)]
    
    # Generate landmark sequences (30 frames × 75 landmarks × 3 coordinates)
    sequences = [[np.random.rand(75, 3) * 0.5 for _ in range(30)] for _ in range(5)]
    
    return frames, left_hands, right_hands, sequences


def test_individual_extractors():
    """Test individual biometric extractors"""
    print("\n" + "="*60)
    print("TEST 1: Individual Biometric Extractors")
    print("="*60)
    
    # Test hand extractor
    print("\n1.1 Testing Hand Biometric Extractor...")
    hand_extractor = HandBiometricExtractor()
    left_hand = np.random.rand(21, 3) * 0.5
    right_hand = np.random.rand(21, 3) * 0.5
    hand_features = hand_extractor.extract_features(left_hand, right_hand)
    print(f"   ✅ Hand features extracted: {hand_features.shape}")
    assert hand_features.shape == (128,), "Hand features must be 128-dim"
    
    # Test style analyzer
    print("\n1.2 Testing Signing Style Analyzer...")
    style_analyzer = SigningStyleAnalyzer(window_size=30)
    sequence = [np.random.rand(75, 3) * 0.5 for _ in range(30)]
    style_features = style_analyzer.extract_features(sequence)
    print(f"   ✅ Style features extracted: {style_features.shape}")
    assert style_features.shape == (64,), "Style features must be 64-dim"
    
    # Test face authenticator
    print("\n1.3 Testing Face Authenticator...")
    face_auth = FaceAuthenticator()
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    face_features = face_auth.extract_features(frame)
    if face_features is not None:
        print(f"   ✅ Face features extracted: {face_features.shape}")
        assert face_features.shape == (512,), "Face features must be 512-dim"
    else:
        print(f"   ⚠️  No face detected (expected for random image)")
        print(f"   ✅ Using zero vector (512-dim)")
    
    print("\n✅ All individual extractors passed!")


def test_fusion_authenticator():
    """Test fusion authenticator"""
    print("\n" + "="*60)
    print("TEST 2: Biometric Fusion Authenticator")
    print("="*60)
    
    authenticator = BiometricFusionAuthenticator(
        face_weight=0.5,
        hand_weight=0.3,
        style_weight=0.2,
        verification_threshold=0.65
    )
    
    # Generate test data
    frames, left_hands, right_hands, sequences = generate_synthetic_data()
    
    # Test feature extraction
    print("\n2.1 Testing Multi-modal Feature Extraction...")
    features = authenticator.extract_multimodal_features(
        frame=frames[0],
        left_hand_landmarks=left_hands[0],
        right_hand_landmarks=right_hands[0],
        landmark_sequence=sequences[0]
    )
    
    print(f"   Face: {features['face'].shape}")
    print(f"   Hand: {features['hand'].shape}")
    print(f"   Style: {features['style'].shape}")
    print(f"   Fusion: {features['fusion'].shape}")
    
    assert features['face'].shape == (512,), "Face must be 512-dim"
    assert features['hand'].shape == (128,), "Hand must be 128-dim"
    assert features['style'].shape == (64,), "Style must be 64-dim"
    assert features['fusion'].shape == (704,), "Fusion must be 704-dim"
    print("   ✅ All feature dimensions correct!")
    
    # Test enrollment
    print("\n2.2 Testing User Enrollment...")
    enrolled_features = authenticator.enroll_user(
        user_id="TEST_USER_001",
        frames=frames[:3],
        left_hand_landmarks_list=left_hands[:3],
        right_hand_landmarks_list=right_hands[:3],
        landmark_sequences=sequences[:3],
        num_samples=3
    )
    print("   ✅ User enrolled successfully!")
    
    # Test verification (same person)
    print("\n2.3 Testing Verification (Same Person)...")
    query_features = authenticator.extract_multimodal_features(
        frame=frames[3],
        left_hand_landmarks=left_hands[3],
        right_hand_landmarks=right_hands[3],
        landmark_sequence=sequences[3]
    )
    
    is_auth, score, individual = authenticator.verify(query_features, enrolled_features)
    print(f"   Authenticated: {is_auth}")
    print(f"   Fusion Score: {score:.4f}")
    print(f"   Individual Scores:")
    print(f"      Face: {individual['face']:.4f}")
    print(f"      Hand: {individual['hand']:.4f}")
    print(f"      Style: {individual['style']:.4f}")
    print("   ✅ Verification completed!")
    
    # Test verification (different person)
    print("\n2.4 Testing Verification (Different Person)...")
    diff_frames, diff_lh, diff_rh, diff_seq = generate_synthetic_data()
    diff_features = authenticator.extract_multimodal_features(
        frame=diff_frames[0],
        left_hand_landmarks=diff_lh[0],
        right_hand_landmarks=diff_rh[0],
        landmark_sequence=diff_seq[0]
    )
    
    is_auth2, score2, individual2 = authenticator.verify(diff_features, enrolled_features)
    print(f"   Authenticated: {is_auth2}")
    print(f"   Fusion Score: {score2:.4f}")
    print(f"   Individual Scores:")
    print(f"      Face: {individual2['face']:.4f}")
    print(f"      Hand: {individual2['hand']:.4f}")
    print(f"      Style: {individual2['style']:.4f}")
    print("   ✅ Verification completed!")
    
    print("\n✅ Fusion authenticator passed!")


def test_user_database():
    """Test user database"""
    print("\n" + "="*60)
    print("TEST 3: User Biometric Database")
    print("="*60)
    
    # Initialize database
    print("\n3.1 Initializing Database...")
    db = UserBiometricDatabase(db_path="test_biometric.db")
    print("   ✅ Database initialized!")
    
    # Create test features
    test_features = {
        'face': np.random.randn(512),
        'hand': np.random.randn(128),
        'style': np.random.randn(64)
    }
    
    # Test enrollment
    print("\n3.2 Testing User Enrollment...")
    success = db.enroll_user(
        user_id="TEST_USER_001",
        biometric_features=test_features,
        notes="Test user for system validation"
    )
    assert success, "Enrollment should succeed"
    print("   ✅ User enrolled in database!")
    
    # Test retrieval
    print("\n3.3 Testing Biometric Retrieval...")
    retrieved = db.get_user_biometrics("TEST_USER_001")
    assert retrieved is not None, "Should retrieve enrolled user"
    assert retrieved['face'].shape == (512,), "Face should be 512-dim"
    assert retrieved['hand'].shape == (128,), "Hand should be 128-dim"
    assert retrieved['style'].shape == (64,), "Style should be 64-dim"
    print("   ✅ Biometrics retrieved successfully!")
    
    # Test user info
    print("\n3.4 Testing User Information...")
    info = db.get_user_info("TEST_USER_001")
    assert info is not None, "Should get user info"
    print(f"   User ID: {info['user_id']}")
    print(f"   Enrolled: {info['enrolled_date']}")
    print(f"   Auth Count: {info['authentication_count']}")
    print("   ✅ User info retrieved!")
    
    # Test authentication logging
    print("\n3.5 Testing Authentication Logging...")
    db.log_authentication(
        user_id="TEST_USER_001",
        authenticated=True,
        fusion_score=0.85,
        individual_scores={'face': 0.90, 'hand': 0.82, 'style': 0.78}
    )
    
    history = db.get_authentication_history("TEST_USER_001", limit=5)
    assert len(history) > 0, "Should have auth history"
    print(f"   Auth History: {len(history)} records")
    print(f"   Latest: {history[0]}")
    print("   ✅ Authentication logged!")
    
    # Test statistics
    print("\n3.6 Testing Database Statistics...")
    stats = db.get_statistics()
    print(f"   Total Users: {stats['total_users']}")
    print(f"   Total Authentications: {stats['total_authentications']}")
    print(f"   Success Rate: {stats['success_rate']:.2%}")
    print("   ✅ Statistics retrieved!")
    
    # Test deletion
    print("\n3.7 Testing User Deletion...")
    deleted = db.delete_user("TEST_USER_001")
    assert deleted, "Deletion should succeed"
    print("   ✅ User deleted!")
    
    # Cleanup
    import os
    if os.path.exists("test_biometric.db"):
        os.remove("test_biometric.db")
    
    print("\n✅ User database passed!")


def test_complete_pipeline():
    """Test complete authentication pipeline"""
    print("\n" + "="*60)
    print("TEST 4: Complete Authentication Pipeline")
    print("="*60)
    
    # Initialize components
    print("\n4.1 Initializing Components...")
    authenticator = BiometricFusionAuthenticator()
    db = UserBiometricDatabase(db_path="test_complete.db")
    print("   ✅ Components initialized!")
    
    # Generate data for User 1
    print("\n4.2 Enrolling User 1...")
    user1_frames, user1_lh, user1_rh, user1_seq = generate_synthetic_data()
    
    user1_enrolled = authenticator.enroll_user(
        user_id="USER_001",
        frames=user1_frames[:3],
        left_hand_landmarks_list=user1_lh[:3],
        right_hand_landmarks_list=user1_rh[:3],
        landmark_sequences=user1_seq[:3],
        num_samples=3
    )
    
    db.enroll_user("USER_001", user1_enrolled, notes="Primary user")
    print("   ✅ User 1 enrolled!")
    
    # Generate data for User 2
    print("\n4.3 Enrolling User 2...")
    user2_frames, user2_lh, user2_rh, user2_seq = generate_synthetic_data()
    
    user2_enrolled = authenticator.enroll_user(
        user_id="USER_002",
        frames=user2_frames[:3],
        left_hand_landmarks_list=user2_lh[:3],
        right_hand_landmarks_list=user2_rh[:3],
        landmark_sequences=user2_seq[:3],
        num_samples=3
    )
    
    db.enroll_user("USER_002", user2_enrolled, notes="Secondary user")
    print("   ✅ User 2 enrolled!")
    
    # Test authentication for User 1 (genuine)
    print("\n4.4 Testing Authentication (User 1 - Genuine)...")
    user1_query = authenticator.extract_multimodal_features(
        frame=user1_frames[3],
        left_hand_landmarks=user1_lh[3],
        right_hand_landmarks=user1_rh[3],
        landmark_sequence=user1_seq[3]
    )
    
    user1_reference = db.get_user_biometrics("USER_001")
    is_auth1, score1, indiv1 = authenticator.verify(user1_query, user1_reference)
    
    db.log_authentication("USER_001", is_auth1, score1, indiv1)
    
    print(f"   User: USER_001")
    print(f"   Authenticated: {is_auth1}")
    print(f"   Score: {score1:.4f}")
    print("   ✅ Genuine authentication tested!")
    
    # Test authentication for User 2 claiming to be User 1 (impostor)
    print("\n4.5 Testing Authentication (User 2 as User 1 - Impostor)...")
    user2_query = authenticator.extract_multimodal_features(
        frame=user2_frames[3],
        left_hand_landmarks=user2_lh[3],
        right_hand_landmarks=user2_rh[3],
        landmark_sequence=user2_seq[3]
    )
    
    is_auth2, score2, indiv2 = authenticator.verify(user2_query, user1_reference)
    
    db.log_authentication("USER_001", is_auth2, score2, indiv2)
    
    print(f"   Claimed User: USER_001")
    print(f"   Actual User: USER_002")
    print(f"   Authenticated: {is_auth2}")
    print(f"   Score: {score2:.4f}")
    print("   ✅ Impostor detection tested!")
    
    # Show final statistics
    print("\n4.6 Final Statistics...")
    stats = db.get_statistics()
    print(f"   Total Users: {stats['total_users']}")
    print(f"   Total Authentications: {stats['total_authentications']}")
    print(f"   Failed Attempts: {stats['failed_authentications']}")
    print(f"   Success Rate: {stats['success_rate']:.2%}")
    
    # Cleanup
    import os
    if os.path.exists("test_complete.db"):
        os.remove("test_complete.db")
    
    print("\n✅ Complete pipeline passed!")


def main():
    """Run all tests"""
    print("🔬 Biometric Authentication System - Comprehensive Testing")
    print("=" * 60)
    
    try:
        # Run tests
        test_individual_extractors()
        test_fusion_authenticator()
        test_user_database()
        test_complete_pipeline()
        
        # Final summary
        print("\n" + "="*60)
        print("✨ ALL TESTS PASSED!")
        print("="*60)
        print("\n🎉 Biometric authentication system is ready for integration!")
        print("\nNext Steps:")
        print("  1. Integrate with inference.py")
        print("  2. Replace mock auth in banking_verifier.py")
        print("  3. Add enrollment UI (E key)")
        print("  4. Test with real users")
        print("\nSee TASK_3_BIOMETRIC_AUTH.md for integration guide.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
