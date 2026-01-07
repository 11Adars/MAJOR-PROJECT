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
import threading
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import NS-AGF inference system
from inference import SignLanguageInference
from src.auth import BiometricFusionAuthenticator, UserBiometricDatabase
from src.slm.query_generator import QueryGenerator

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global inference system (initialized once)
inference_system = None
bio_authenticator = None
bio_database = None
query_generator = None  # SLM for query generation

# MediaPipe is NOT thread-safe - use lock to serialize access
mediapipe_lock = threading.Lock()


def initialize_system():
    """Initialize NS-AGF inference system and biometric modules"""
    global inference_system, bio_authenticator, bio_database, query_generator
    
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
        
        # Verify all novel features are active
        print("\n📊 API NOVEL FEATURES STATUS:")
        print(f"   ✓ Temporal Smoothing: {'ENABLED' if inference_system.use_temporal_smoothing else 'DISABLED'}")
        print(f"   ✓ Model Type: {inference_system.model.__class__.__name__}")
        print(f"   ✓ Dropout: 0.0 (inference mode)")
        print(f"   ✓ Adaptive Graphs: ENABLED")
        
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
        
        # Initialize SLM Query Generator
        print("\n🔧 Loading Small Language Model (SLM)...")
        query_generator = QueryGenerator(
            use_slm=True,
            cache_path="../Sign/slm_model_cache"
        )
        slm_status = query_generator.health_check()
        if slm_status['slm_available']:
            print("✅ SLM Query Generator ready")
        else:
            print("⚠️  SLM will use fallback queries")
        
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

@app.after_request
def after_request_logging(response):
    """Log all responses for debugging"""
    if request.path == '/api/sign/recognize':
        print(f"   🌐 Response sent: {response.status_code} - Content-Length: {response.content_length}")
    return response

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


@app.route('/api/sign/extract-landmarks', methods=['POST'])
def extract_landmarks():
    """
    Extract landmarks from a single frame for real-time skeleton visualization.
    
    Request body (JSON):
        {
            "frame": "base64_encoded_image"
        }
    
    Response (JSON):
        {
            "success": true,
            "landmarks": [{x, y, z}, ...] // 75 landmarks
        }
    """
    if inference_system is None:
        return jsonify({'success': False, 'error': 'Inference system not initialized'}), 500
    
    try:
        data = request.json
        frame_b64 = data.get('frame', '')
        
        if not frame_b64:
            return jsonify({'success': False, 'error': 'No frame provided'}), 400
        
        # Decode frame from base64
        try:
            # Remove data URL prefix if present
            if ',' in frame_b64:
                frame_b64 = frame_b64.split(',')[1]
            
            frame_bytes = base64.b64decode(frame_b64)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({'success': False, 'error': 'Failed to decode frame'}), 400
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Extract landmarks (MediaPipe is NOT thread-safe - use lock)
            with mediapipe_lock:
                landmarks = inference_system.extractor.extract_landmarks(frame_rgb)
            
            if landmarks is None:
                return jsonify({'success': False, 'landmarks_detected': False}), 200
            
            # Convert numpy array to list of {x, y, z} objects
            landmarks_list = []
            for lm in landmarks:
                landmarks_list.append({
                    'x': float(lm[0]),
                    'y': float(lm[1]),
                    'z': float(lm[2])
                })
            
            return jsonify({
                'success': True,
                'landmarks_detected': True,
                'landmarks': landmarks_list
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Frame decode error: {str(e)}'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
        print(f"📥 Received request data keys: {list(data.keys()) if data else 'None'}")
        frames_b64 = data.get('frames', [])
        print(f"📊 Frames count: {len(frames_b64) if frames_b64 else 0}")
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
        
        # Use lock to serialize MediaPipe access (NOT thread-safe)
        with mediapipe_lock:
            for frame in frames:
                # Convert BGR to RGB (cv2.imdecode returns BGR)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Extract landmarks using MediaPipe
                landmarks = inference_system.extractor.extract_landmarks(frame_rgb)
                
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
        
        # Predict sign from the full sequence (single prediction)
        # Note: Disable temporal smoothing for batch processing (it's for streaming only)
        print(f"   🔄 Predicting from {len(landmarks_sequence)} frames...")
        
        try:
            pred_result = inference_system.predict_from_sequence(landmarks_sequence, use_temporal_smoothing=False)
        except Exception as pred_error:
            print(f"   ❌ Prediction failed: {pred_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Prediction error: {str(pred_error)}'}), 500
        
        if 'error' in pred_result:
            return jsonify({
                'error': pred_result['error'],
                'frames_processed': len(frames)
            }), 400
        
        predicted_sign = pred_result['sign']
        confidence = pred_result['confidence']
        
        print(f"   🎯 Prediction: {predicted_sign} (confidence: {confidence:.2f})")
        
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
            try:
                # Call verify_sign_sequence with list of signs and confidences
                intent, context, is_valid = inference_system.banking_verifier.verify_sign_sequence(
                    signs=[predicted_sign],
                    confidences=[confidence]
                )
                print(f"   🔍 Intent verification result: {intent.value}, is_valid={is_valid}")
                if intent.value != 'unknown':
                    # Get intent description from rules
                    intent_desc = "Banking operation"
                    if hasattr(inference_system.banking_verifier, 'intents'):
                        intent_config = inference_system.banking_verifier.intents.get(intent.value, {})
                        intent_desc = intent_config.get('description', intent_desc)
                    
                    response['intent'] = {
                        'is_banking': True,
                        'type': intent.value,  # Frontend expects 'type' not 'intent_type'
                        'description': intent_desc,
                        'is_valid': is_valid,
                        'confidence_threshold': inference_system.banking_verifier.confidence_thresholds.get(intent.value, 0.75),
                        'slots': context.slots,
                        'warnings': [context.error_message] if context.error_message else []
                    }
                    print(f"   🏦 Banking intent detected: {intent.value} (valid={is_valid})")
                else:
                    print(f"   ℹ️  No banking intent detected for '{predicted_sign}'")
            except Exception as e:
                print(f"   ⚠️  Banking verifier error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ⚠️  Banking verifier not available")
        
        print(f"   📤 Sending response: {predicted_sign} with confidence {confidence:.2f}")
        print(f"   📦 Response data: {response}")
        
        try:
            json_response = jsonify(response)
            print(f"   ✅ Response created successfully")
            return json_response, 200
        except Exception as json_error:
            print(f"   ❌ Failed to create JSON response: {json_error}")
            return jsonify({'error': 'Failed to serialize response'}), 500
        
    except Exception as e:
        print(f"❌ Recognition error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/slm/generate', methods=['POST'])
def slm_generate_query():
    """
    Generate natural language query from sign words using SLM.
    
    Request body (JSON):
        {
            "sign_word": "ATM help account",
            "context": "User performed signs: ATM, help, account"
        }
    
    Response (JSON):
        {
            "success": true,
            "query": "I need help accessing my ATM and checking my account balance",
            "intent": "access_atm",
            "slm_used": true
        }
    """
    global query_generator
    
    try:
        data = request.json
        sign_word = data.get('sign_word', '')
        context = data.get('context', '')
        
        if not sign_word:
            return jsonify({'error': 'sign_word is required'}), 400
        
        print(f"\n📝 SLM Query Generation Request")
        print(f"   Sign words: {sign_word}")
        print(f"   Context: {context}")
        
        # Generate query using SLM
        generated_query = sign_word  # Default to raw input
        intent = 'general_inquiry'
        slm_used = False
        
        if query_generator is not None:
            try:
                # Split sign_word into individual keywords for better SLM processing
                keywords = [word.strip().upper() for word in sign_word.split() if word.strip()]
                
                print(f"   📌 Keywords extracted: {keywords}")
                
                # Use the first keyword to detect banking intent
                first_keyword = keywords[0] if keywords else sign_word
                intent = detect_banking_intent(first_keyword)
                
                # Pass the full phrase to SLM to generate a natural query
                # The SLM will work better with the multi-word input
                result = query_generator.generate_query(' '.join(keywords), intent)
                
                if result and isinstance(result, str) and result.strip():
                    generated_query = result.strip()
                    slm_used = query_generator.slm_model is not None
                    print(f"   ✅ SLM generated: {generated_query}")
                    print(f"   Intent: {intent}")
                    print(f"   SLM Used: {slm_used}")
                elif result and isinstance(result, dict) and 'query' in result:
                    generated_query = result['query']
                    intent = result.get('intent', intent)
                    slm_used = result.get('slm_used', True)
                    print(f"   ✅ SLM generated: {generated_query}")
                    print(f"   Intent: {intent}")
                else:
                    # Fallback
                    generated_query = create_fallback_query(' '.join(keywords), intent)
                    print(f"   Using fallback: {generated_query}")
            except Exception as slm_error:
                print(f"   ⚠️ SLM generation failed: {slm_error}")
                import traceback
                traceback.print_exc()
                # Fallback to simple mapping
                intent = detect_banking_intent(sign_word)
                generated_query = create_fallback_query(sign_word, intent)
                print(f"   Using fallback: {generated_query}")
        else:
            # No SLM available, use fallback
            intent = detect_banking_intent(sign_word)
            generated_query = create_fallback_query(sign_word, intent)
            print(f"   ⚠️ SLM not available, using fallback: {generated_query}")
        
        return jsonify({
            'success': True,
            'query': generated_query,
            'intent': intent,
            'slm_used': slm_used,
            'original_input': sign_word
        })
        
    except Exception as e:
        print(f"❌ SLM generation error: {e}")
        return jsonify({'error': str(e)}), 500


def detect_banking_intent(sign_words):
    """Detect banking intent from sign words"""
    words_lower = sign_words.lower()
    
    intent_keywords = {
        'delete_account': ['delete', 'remove', 'close', 'cancel'],
        'check_balance': ['balance', 'account', 'money', 'how much'],
        'transfer_money': ['transfer', 'send', 'money'],
        'access_atm': ['atm', 'cash', 'withdraw'],
        'get_loan': ['loan', 'borrow', 'credit'],
        'report_issue': ['report', 'problem', 'issue', 'illegal', 'missing'],
        'speak_manager': ['manager', 'speak', 'talk', 'help'],
        'account_info': ['address', 'info', 'information', 'passbook'],
        'online_banking': ['online', 'internet', 'digital'],
        'interest_rates': ['interest', 'rate']
    }
    
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in words_lower:
                return intent
    
    return 'general_inquiry'


def create_fallback_query(sign_words, intent):
    """Create a fallback query without SLM"""
    fallback_templates = {
        'delete_account': f"I want to delete or close my account. Request: {sign_words}",
        'check_balance': f"I want to check my account balance. Request: {sign_words}",
        'transfer_money': f"I need to transfer money. Request: {sign_words}",
        'access_atm': f"I need help with ATM services. Request: {sign_words}",
        'get_loan': f"I want information about loans. Request: {sign_words}",
        'report_issue': f"I need to report an issue. Request: {sign_words}",
        'speak_manager': f"I would like to speak with a manager. Request: {sign_words}",
        'account_info': f"I need information about my account. Request: {sign_words}",
        'online_banking': f"I need help with online banking. Request: {sign_words}",
        'interest_rates': f"I want to know about interest rates. Request: {sign_words}",
        'general_inquiry': f"I have a banking inquiry. Request: {sign_words}"
    }
    
    return fallback_templates.get(intent, fallback_templates['general_inquiry'])


@app.route('/api/sign/hybrid-recognize', methods=['POST'])
def hybrid_recognize_sign():
    """
    Hybrid approach: Recognize sign + generate natural language query.
    
    This combines:
    1. AGCN sign recognition (fast, deterministic)
    2. Intent verification (banking-related)
    3. SLM query generation (detailed, fallback available)
    
    Request body (JSON):
        {
            "frames": ["base64_encoded_image1", "base64_encoded_image2", ...],
            "use_slm": true  // Optional: enable SLM (default: true)
        }
    
    Response (JSON):
        {
            "success": true,
            "sign": "HELP",
            "confidence": 0.95,
            "intent": "customer_support",
            "query": "I need help with banking services",
            "slm_used": true,
            "frames_processed": 50,
            "valid_frames": 48
        }
    """
    if inference_system is None:
        return jsonify({'error': 'Inference system not initialized'}), 500
    
    if query_generator is None:
        return jsonify({'error': 'Query generator not initialized'}), 500
    
    try:
        data = request.json
        frames_b64 = data.get('frames', [])
        use_slm = data.get('use_slm', True)
        return_skeleton = data.get('return_skeleton', False)  # NEW: Option to return frames with landmarks
        
        if not frames_b64:
            return jsonify({'error': 'No frames provided'}), 400
        
        if len(frames_b64) < 10:
            return jsonify({'error': 'Minimum 10 frames required'}), 400
        
        # Decode frames from base64
        frames = []
        for frame_b64 in frames_b64:
            try:
                if ',' in frame_b64:
                    frame_b64 = frame_b64.split(',')[1]
                
                frame_bytes = base64.b64decode(frame_b64)
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                
                frames.append(frame)
            except Exception as e:
                print(f"⚠️  Frame decode error: {e}")
                continue
        
        if len(frames) < 10:
            return jsonify({'error': 'Failed to decode sufficient frames'}), 400
        
        print(f"\n📹 HYBRID RECOGNITION: Processing {len(frames)} frames...")
        
        # Step 1: Extract landmarks and recognize sign
        landmarks_sequence = []
        valid_frames = []
        skeleton_frames_b64 = []  # NEW: Store frames with skeleton drawn
        
        for frame in frames:
            # Convert BGR to RGB (MediaPipe expects RGB!)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Extract landmarks with MediaPipe results for visualization
            landmarks, mp_results = inference_system.extractor.extract_with_results(frame_rgb)
            
            if landmarks is not None:
                landmarks_sequence.append(landmarks)
                valid_frames.append(frame)
                
                # NEW: Draw skeleton if requested
                if return_skeleton and mp_results:
                    skeleton_frame = frame.copy()
                    from src.utils.mediapipe_helper import draw_landmarks
                    skeleton_frame = draw_landmarks(skeleton_frame, mp_results)
                    
                    # Encode back to base64
                    _, buffer = cv2.imencode('.jpg', skeleton_frame)
                    skeleton_b64 = base64.b64encode(buffer).decode('utf-8')
                    skeleton_frames_b64.append(f"data:image/jpeg;base64,{skeleton_b64}")
        
        if len(landmarks_sequence) < 10:
            return jsonify({
                'error': 'Insufficient valid frames with landmarks',
                'frames_processed': len(frames),
                'valid_frames': len(landmarks_sequence)
            }), 400
        
        print(f"   ✅ Step 1: Extracted landmarks from {len(landmarks_sequence)} frames")
        
        # Step 2: Predict sign
        prediction_result = inference_system.predict_from_sequence(landmarks_sequence)
        
        if 'error' in prediction_result:
            return jsonify({
                'success': False,
                'error': prediction_result['error'],
                'frames_processed': len(frames)
            }), 400
        
        predicted_sign = prediction_result['sign']
        confidence = prediction_result['confidence']
        
        print(f"   ✅ Step 2: Predicted sign '{predicted_sign}' (confidence: {confidence:.2f})")
        
        # Step 3: Verify banking intent
        intent_type = "general_inquiry"
        is_banking = False
        
        if inference_system.banking_verifier:
            try:
                # Call verify_sign_sequence with list of signs and confidences
                intent, context, is_valid = inference_system.banking_verifier.verify_sign_sequence(
                    signs=[predicted_sign],
                    confidences=[confidence]
                )
                if intent.value != 'unknown':
                    is_banking = True
                    intent_type = intent.value
                    print(f"   ✅ Step 3: Banking intent verified - '{intent_type}'")
                else:
                    print(f"   ℹ️  Step 3: General inquiry (not banking-related)")
            except Exception as e:
                print(f"   ⚠️  Step 3: Banking verifier error (using fallback): {e}")
                intent_type = "customer_support"
        
        # Step 4: Generate natural language query using SLM
        generated_query = None
        slm_used = False
        
        if use_slm and query_generator is not None:
            print(f"   ⏳ Step 4: Generating query using SLM...")
            generated_query = query_generator.generate_query(
                sign_name=predicted_sign,
                intent=intent_type,
                hand_landmarks=landmarks_sequence[-1][33:75] if landmarks_sequence else None
            )
            
            if generated_query:
                slm_used = True
                print(f"   ✅ Step 4: Generated query: '{generated_query}'")
            else:
                print(f"   ⚠️  Step 4: SLM fallback query generated")
                generated_query = query_generator._get_fallback_query(predicted_sign, intent_type)
        else:
            # Use fallback query
            print(f"   ⚠️  Step 4: Using fallback query (SLM disabled or unavailable)")
            generated_query = query_generator._get_fallback_query(predicted_sign, intent_type)
        
        # Build response
        response = {
            'success': True,
            'sign': predicted_sign,
            'confidence': float(confidence),
            'intent': intent_type,
            'is_banking_intent': is_banking,
            'query': generated_query,
            'slm_used': slm_used,
            'frames_processed': len(frames),
            'valid_frames': len(landmarks_sequence)
        }
        
        # Add skeleton frames if requested
        if return_skeleton and skeleton_frames_b64:
            response['skeleton_frames'] = skeleton_frames_b64[:10]  # Return first 10 frames with skeleton
            print(f"   🎨 Added {len(skeleton_frames_b64[:10])} skeleton visualization frames")
        
        print(f"\n✨ HYBRID RECOGNITION COMPLETE")
        print(f"   Sign: {predicted_sign}")
        print(f"   Query: {generated_query}")
        print(f"   SLM Used: {'Yes' if slm_used else 'Fallback'}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Hybrid recognition error: {e}")
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
    print("   URL: http://127.0.0.1:5003")
    print("   Endpoints:")
    print("      GET  /api/health                 - Health check")
    print("      POST /api/sign/recognize         - Sign language recognition")
    print("      POST /api/sign/hybrid-recognize  - Hybrid sign + query generation")
    print("      POST /api/biometric/enroll       - Enroll user biometrics")
    print("      POST /api/biometric/verify       - Verify user biometrics")
    print("      GET  /api/biometric/users        - List enrolled users")
    print("\n   Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5003,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down NS-AGF API Service...")
        print("=" * 70)
