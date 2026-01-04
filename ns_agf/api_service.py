"""
NS-AGF REST API Service
========================

Flask REST API wrapper for the NS-AGF Sign Language Recognition System.
Provides endpoints for:
- Sign language recognition (customer support queries)
- Biometric enrollment (during user registration)
- Biometric verification (during secure transactions)

This bridges the Python-based NS-AGF system with the Node.js backend.

Usage:
    python api_service.py

Endpoints:
    GET  /api/health                - Health check
    POST /api/sign/recognize        - Recognize sign language from video frames
    POST /api/biometric/enroll      - Enroll user biometrics
    POST /api/biometric/verify      - Verify user biometrics

Author: NS-AGF Team
Date: January 2026
"""

import os
import sys
import cv2
import numpy as np
import base64
import pickle
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import NS-AGF inference system
from inference import SignLanguageInference
from src.auth import BiometricFusionAuthenticator, UserBiometricDatabase

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global inference system (initialized once)
inference_system = None
bio_authenticator = None
bio_database = None


def initialize_system():
    """Initialize NS-AGF inference system and biometric modules"""
    global inference_system, bio_authenticator, bio_database
    
    print("=" * 70)
    print("🚀 Initializing NS-AGF API Service")
    print("=" * 70)
    
    # Find model and label files
    model_dir = Path(__file__).parent / 'models'
    model_path = model_dir / 'ns_agcn.pth'
    label_path = model_dir / 'sign_labels.txt'
    config_path = Path(__file__).parent / 'inference_config.ini'
    
    if not model_path.exists():
        print(f"❌ Model not found at: {model_path}")
        print("   Please ensure ns_agcn.pth is in the models/ directory")
        return False
    
    if not label_path.exists():
        print(f"⚠️  Label file not found at: {label_path}")
        print("   Will auto-detect from model checkpoint")
    
    try:
        # Initialize inference system
        print("\n🔧 Loading NS-AGF inference system...")
        inference_system = SignLanguageInference(
            model_path=str(model_path),
            num_classes=None,  # Auto-detect from checkpoint
            class_names=None,  # Load from label_names.npy
            confidence_threshold=0.7,
            device='cpu'
        )
        print("✅ NS-AGF inference system ready")
        
        # Initialize biometric authenticator
        print("\n🔧 Loading biometric authentication modules...")
        bio_authenticator = BiometricFusionAuthenticator(
            face_weight=0.5,
            hand_weight=0.3,
            style_weight=0.2,
            verification_threshold=0.65
        )
        bio_database = UserBiometricDatabase(db_path="data/biometric_users.db")
        print("✅ Biometric authentication ready")
        
        # Show enrolled users
        users = bio_database.get_all_users()
        if users:
            print(f"   📋 {len(users)} user(s) enrolled in biometric database")
        else:
            print("   ℹ️  No users enrolled yet")
        
        print("\n" + "=" * 70)
        print("✨ NS-AGF API Service Ready!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if inference_system is None:
        return jsonify({
            'status': 'error',
            'message': 'Inference system not initialized',
            'service': 'NS-AGF API'
        }), 500
    
    return jsonify({
        'status': 'ok',
        'service': 'NS-AGF API',
        'version': '1.0.0',
        'inference_ready': inference_system is not None,
        'biometric_ready': bio_authenticator is not None,
        'enrolled_users': len(bio_database.get_all_users()) if bio_database else 0
    })


@app.route('/api/sign/recognize', methods=['POST'])
def recognize_sign():
    """
    Recognize sign language gesture from video frames.
    
    Request body (JSON):
        {
            "frames": ["base64_encoded_image1", "base64_encoded_image2", ...],
            "return_sentence": true  // Optional: combine signs into sentence
        }
    
    Response (JSON):
        {
            "success": true,
            "signs": ["hello", "world"],
            "sentence": "hello world",
            "confidences": [0.95, 0.89],
            "intent": { ... },  // If banking-related
            "frames_processed": 50
        }
    """
    if inference_system is None:
        return jsonify({'error': 'Inference system not initialized'}), 500
    
    try:
        data = request.json
        frames_b64 = data.get('frames', [])
        return_sentence = data.get('return_sentence', True)
        
        if not frames_b64:
            return jsonify({'error': 'No frames provided'}), 400
        
        if len(frames_b64) < 10:
            return jsonify({'error': 'Minimum 10 frames required'}), 400
        
        # Decode frames from base64
        frames = []
        for frame_b64 in frames_b64:
            try:
                # Remove data URL prefix if present (data:image/jpeg;base64,...)
                if ',' in frame_b64:
                    frame_b64 = frame_b64.split(',')[1]
                
                # Decode base64 to bytes
                frame_bytes = base64.b64decode(frame_b64)
                
                # Convert bytes to numpy array
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                
                # Decode image
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    print(f"⚠️  Failed to decode frame")
                    continue
                
                frames.append(frame)
            except Exception as e:
                print(f"⚠️  Frame decode error: {e}")
                continue
        
        if len(frames) < 10:
            return jsonify({'error': 'Failed to decode sufficient frames'}), 400
        
        print(f"\n📹 Processing {len(frames)} frames for sign recognition...")
        
        # Process frames and extract landmarks
        landmarks_sequence = []
        valid_frames = []
        
        for frame in frames:
            # Extract landmarks using MediaPipe
            landmarks = inference_system.extractor.extract_landmarks(frame)
            
            if landmarks is not None:
                landmarks_sequence.append(landmarks)
                valid_frames.append(frame)
        
        if len(landmarks_sequence) < 10:
            return jsonify({
                'error': 'Insufficient valid frames with landmarks',
                'frames_processed': len(frames),
                'valid_frames': len(landmarks_sequence)
            }), 400
        
        print(f"   ✅ Extracted landmarks from {len(landmarks_sequence)} frames")
        
        # Predict sign from sequence
        prediction_result = inference_system.predict_from_sequence(landmarks_sequence)
        
        if 'error' in prediction_result:
            return jsonify({
                'success': False,
                'error': prediction_result['error'],
                'frames_processed': len(frames)
            }), 400
        
        predicted_sign = prediction_result['sign']
        confidence = prediction_result['confidence']
        
        print(f"   🎯 Predicted: {predicted_sign} (confidence: {confidence:.2f})")
        
        # Build response
        response = {
            'success': True,
            'sign': predicted_sign,
            'confidence': float(confidence),
            'frames_processed': len(frames),
            'valid_frames': len(landmarks_sequence)
        }
        
        # Add sentence if requested (for multi-sign sequences)
        if return_sentence:
            # For now, just return the single sign
            # In future, can accumulate multiple predictions into sentence
            response['sentence'] = predicted_sign
        
        # Add intent verification if banking-related
        if inference_system.banking_verifier:
            intent_result = inference_system.banking_verifier.verify_intent(predicted_sign)
            if intent_result and intent_result.get('is_banking_intent'):
                response['intent'] = {
                    'is_banking': True,
                    'intent_type': intent_result.get('intent_type'),
                    'is_valid': intent_result.get('is_valid'),
                    'slots': intent_result.get('slots', {}),
                    'warnings': intent_result.get('warnings', [])
                }
                print(f"   🏦 Banking intent detected: {intent_result.get('intent_type')}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Recognition error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/biometric/enroll', methods=['POST'])
def enroll_biometric():
    """
    Enroll user biometrics from video frames.
    
    Request (multipart/form-data):
        user_id: string
        frame_0: image file
        frame_1: image file
        ...
        frame_N: image file (minimum 10 frames)
    
    Response (JSON):
        {
            "success": true,
            "user_id": "user123",
            "face_biometric": "base64_encoded_pickle",
            "hand_biometric": "base64_encoded_pickle",
            "style_biometric": "base64_encoded_pickle",
            "fusion_score": 0.85
        }
    """
    if bio_authenticator is None or bio_database is None:
        return jsonify({'error': 'Biometric system not initialized'}), 500
    
    try:
        # Get user_id from form data
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        print(f"\n📝 Enrolling biometrics for user: {user_id}")
        
        # Check if user already enrolled
        if bio_database.user_exists(user_id):
            return jsonify({'error': f'User {user_id} already enrolled'}), 409
        
        # Get uploaded frames
        frames = []
        frame_keys = sorted([k for k in request.files.keys() if k.startswith('frame_')])
        
        if not frame_keys:
            return jsonify({'error': 'No frames uploaded'}), 400
        
        for frame_key in frame_keys:
            file = request.files[frame_key]
            file_bytes = file.read()
            frame_array = np.frombuffer(file_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is not None:
                frames.append(frame)
        
        if len(frames) < 10:
            return jsonify({'error': 'Minimum 10 frames required for enrollment'}), 400
        
        print(f"   📹 Processing {len(frames)} frames...")
        
        # Extract landmarks from all frames
        all_landmarks = []
        valid_frames = []
        
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = inference_system.extractor.extract_landmarks(frame_rgb)
            
            if landmarks is not None:
                all_landmarks.append(landmarks)
                valid_frames.append(frame)
        
        if len(all_landmarks) < 5:
            return jsonify({
                'error': 'Failed to extract sufficient landmarks for enrollment',
                'frames_processed': len(frames),
                'valid_frames': len(all_landmarks)
            }), 400
        
        print(f"   ✅ Extracted landmarks from {len(all_landmarks)} frames")
        
        # Extract multi-modal biometric features
        # Use the last frame for face and hand geometry
        latest_frame = valid_frames[-1]
        latest_frame_rgb = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2RGB)
        latest_landmarks = all_landmarks[-1]
        
        # MediaPipe format: pose (33) + left_hand (21) + right_hand (21) = 75
        left_hand = latest_landmarks[33:54]  # Indices 33-53
        right_hand = latest_landmarks[54:75]  # Indices 54-74
        
        print(f"   🔍 Extracting biometric features...")
        biometric_features = bio_authenticator.extract_multimodal_features(
            frame=latest_frame_rgb,
            left_hand=left_hand,
            right_hand=right_hand,
            sequence=all_landmarks  # For signing style analysis
        )
        
        if biometric_features is None:
            return jsonify({'error': 'Failed to extract biometric features'}), 500
        
        print(f"   ✅ Features extracted:")
        print(f"      - Face: {biometric_features['face'].shape}")
        print(f"      - Hand: {biometric_features['hand'].shape}")
        print(f"      - Style: {biometric_features['style'].shape}")
        print(f"      - Fusion: {biometric_features['fusion'].shape}")
        
        # Enroll in database
        success = bio_database.enroll_user(
            user_id=user_id,
            biometric_features=biometric_features,
            notes=f"Enrolled via API with {len(frames)} frames"
        )
        
        if not success:
            return jsonify({'error': 'Failed to save biometrics to database'}), 500
        
        print(f"   ✅ User {user_id} enrolled successfully!")
        
        # Serialize features to base64 for storage in main database (PostgreSQL)
        face_b64 = base64.b64encode(pickle.dumps(biometric_features['face'])).decode('utf-8')
        hand_b64 = base64.b64encode(pickle.dumps(biometric_features['hand'])).decode('utf-8')
        style_b64 = base64.b64encode(pickle.dumps(biometric_features['style'])).decode('utf-8')
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'face_biometric': face_b64,
            'hand_biometric': hand_b64,
            'style_biometric': style_b64,
            'message': f'User {user_id} enrolled successfully',
            'frames_processed': len(frames),
            'valid_frames': len(all_landmarks)
        })
        
    except Exception as e:
        print(f"❌ Enrollment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/biometric/verify', methods=['POST'])
def verify_biometric():
    """
    Verify user biometrics from video frames.
    
    Request (multipart/form-data):
        user_id: string
        frame_0: image file
        frame_1: image file
        ...
        frame_N: image file (minimum 10 frames)
    
    Response (JSON):
        {
            "authenticated": true,
            "fusion_score": 0.87,
            "face_score": 0.92,
            "hand_score": 0.85,
            "style_score": 0.79,
            "user_id": "user123",
            "frames_processed": 30
        }
    """
    if bio_authenticator is None or bio_database is None:
        return jsonify({'error': 'Biometric system not initialized'}), 500
    
    try:
        # Get user_id from form data
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        print(f"\n🔐 Verifying biometrics for user: {user_id}")
        
        # Get reference biometrics from database
        reference = bio_database.get_user_biometrics(user_id)
        if reference is None:
            return jsonify({
                'error': f'User {user_id} not enrolled',
                'authenticated': False
            }), 404
        
        # Get uploaded frames
        frames = []
        frame_keys = sorted([k for k in request.files.keys() if k.startswith('frame_')])
        
        if not frame_keys:
            return jsonify({'error': 'No frames uploaded'}), 400
        
        for frame_key in frame_keys:
            file = request.files[frame_key]
            file_bytes = file.read()
            frame_array = np.frombuffer(file_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is not None:
                frames.append(frame)
        
        if len(frames) < 10:
            return jsonify({'error': 'Minimum 10 frames required for verification'}), 400
        
        print(f"   📹 Processing {len(frames)} frames...")
        
        # Extract landmarks from all frames
        all_landmarks = []
        valid_frames = []
        
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = inference_system.extractor.extract_landmarks(frame_rgb)
            
            if landmarks is not None:
                all_landmarks.append(landmarks)
                valid_frames.append(frame)
        
        if len(all_landmarks) < 5:
            return jsonify({
                'error': 'Failed to extract sufficient landmarks',
                'frames_processed': len(frames),
                'valid_frames': len(all_landmarks),
                'authenticated': False
            }), 400
        
        print(f"   ✅ Extracted landmarks from {len(all_landmarks)} frames")
        
        # Extract multi-modal biometric features from query
        latest_frame = valid_frames[-1]
        latest_frame_rgb = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2RGB)
        latest_landmarks = all_landmarks[-1]
        
        left_hand = latest_landmarks[33:54]
        right_hand = latest_landmarks[54:75]
        
        print(f"   🔍 Extracting query features...")
        query_features = bio_authenticator.extract_multimodal_features(
            frame=latest_frame_rgb,
            left_hand=left_hand,
            right_hand=right_hand,
            sequence=all_landmarks
        )
        
        if query_features is None:
            return jsonify({
                'error': 'Failed to extract biometric features',
                'authenticated': False
            }), 500
        
        # Verify against reference
        print(f"   ⚖️  Comparing with reference biometrics...")
        is_authenticated, fusion_score, individual_scores = bio_authenticator.verify(
            query_features=query_features,
            reference_features=reference,
            threshold=0.65
        )
        
        # Log authentication attempt
        bio_database.log_authentication(
            user_id=user_id,
            authenticated=is_authenticated,
            fusion_score=fusion_score,
            individual_scores=individual_scores
        )
        
        result_emoji = "✅" if is_authenticated else "❌"
        print(f"   {result_emoji} Authentication: {'PASSED' if is_authenticated else 'FAILED'}")
        print(f"      - Fusion score: {fusion_score:.3f}")
        print(f"      - Face: {individual_scores.get('face', 0.0):.3f}")
        print(f"      - Hand: {individual_scores.get('hand', 0.0):.3f}")
        print(f"      - Style: {individual_scores.get('style', 0.0):.3f}")
        
        return jsonify({
            'authenticated': bool(is_authenticated),
            'fusion_score': float(fusion_score),
            'face_score': float(individual_scores.get('face', 0.0)),
            'hand_score': float(individual_scores.get('hand', 0.0)),
            'style_score': float(individual_scores.get('style', 0.0)),
            'user_id': user_id,
            'frames_processed': len(frames),
            'valid_frames': len(all_landmarks),
            'threshold': 0.65
        })
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/biometric/users', methods=['GET'])
def list_enrolled_users():
    """
    List all enrolled users in biometric database.
    
    Response (JSON):
        {
            "users": [
                {
                    "user_id": "user123",
                    "enrolled_date": "2026-01-01 10:30:00",
                    "authentication_count": 5,
                    "last_authenticated": "2026-01-01 14:20:00"
                },
                ...
            ],
            "total": 10
        }
    """
    if bio_database is None:
        return jsonify({'error': 'Biometric database not initialized'}), 500
    
    try:
        users = bio_database.get_all_users()
        return jsonify({
            'users': users,
            'total': len(users)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("NS-AGF REST API Service")
    print("=" * 70)
    print("Version: 1.0.0")
    print("Author: NS-AGF Team")
    print("Date: January 2026")
    print("=" * 70 + "\n")
    
    # Initialize system
    if not initialize_system():
        print("\n❌ Failed to initialize NS-AGF system. Exiting.")
        sys.exit(1)
    
    # Start Flask server
    print("\n🌐 Starting Flask server...")
    print("   URL: http://127.0.0.1:5002")
    print("   Endpoints:")
    print("      GET  /api/health              - Health check")
    print("      POST /api/sign/recognize      - Sign language recognition")
    print("      POST /api/biometric/enroll    - Enroll user biometrics")
    print("      POST /api/biometric/verify    - Verify user biometrics")
    print("      GET  /api/biometric/users     - List enrolled users")
    print("\n   Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5002,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down NS-AGF API Service...")
        print("=" * 70)
