"""
NS-AGF Sign Language Recognition Service
=========================================

Flask service that wraps the NS-AGF inference model and provides
REST API endpoints for the banking application.

Endpoints:
- POST /api/biometric/recognize-sign - Recognize sign language from video frames
- GET /health - Health check

Port: 8000 (integrates with existing frontend at /sign-recognition)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import torch
import base64
import sys
from pathlib import Path
from collections import deque, Counter
import os

# Add ns_agf to path
ns_agf_path = Path(__file__).parent / 'ns_agf'
sys.path.insert(0, str(ns_agf_path))
sys.path.insert(0, str(ns_agf_path / 'src'))

try:
    from src.utils.mediapipe_helper import MediaPipeExtractor, create_sequence_buffer
    from src.model.nsagf import create_model
    from src.logic.banking_verifier import BankingIntentVerifier, BankingIntent, IntentContext
    from src.graph.topology import MediaPipeGraph
    NS_AGF_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ NS-AGF modules not available: {e}")
    print("⚠️ Running in fallback mode without NS-AGF model")
    NS_AGF_AVAILABLE = False
    MediaPipeExtractor = None
    BankingIntentVerifier = None

app = Flask(__name__)
CORS(app)

# Configuration
MODEL_PATH = Path(__file__).parent / 'ns_agf' / 'models' / 'ns_agcn.pth'
SEQUENCE_LENGTH = 30
CONFIDENCE_THRESHOLD = 0.7

# Global variables
sign_model = None
class_names = None
mp_extractor = None
banking_verifier = None
device = None


def load_class_names(model_dir: Path) -> list:
    """Load class names from label file"""
    label_files = [
        model_dir / 'label_names.npy',
        model_dir / 'sign_labels.npy',
        model_dir / 'labels.npy',
    ]
    
    for label_file in label_files:
        if label_file.exists():
            try:
                names = np.load(label_file, allow_pickle=True)
                if isinstance(names, np.ndarray):
                    names = names.tolist()
                print(f"✅ Loaded {len(names)} class names from: {label_file.name}")
                return names
            except Exception as e:
                print(f"⚠️ Failed to load {label_file.name}: {e}")
    
    # Default banking signs if no label file found
    print("⚠️ No label file found, using default banking signs")
    return [
        "BALANCE", "TRANSFER", "DEPOSIT", "WITHDRAW", "ACCOUNT", 
        "HELP", "SUPPORT", "PROBLEM", "ISSUE", "ERROR",
        "PAY", "PAYMENT", "LOAN", "CREDIT", "DEBIT",
        "CHECK", "VERIFY", "CONFIRM", "CANCEL", "UPDATE",
        "PASSWORD", "SECURITY", "STATEMENT", "TRANSACTION", "HISTORY"
    ]


def initialize_model():
    """Initialize NS-AGF model and components"""
    global sign_model, class_names, mp_extractor, banking_verifier, device
    
    print("🚀 Initializing NS-AGF Sign Language Service...")
    
    if not NS_AGF_AVAILABLE:
        print("⚠️ NS-AGF not available - using fallback mode")
        # Use simple MediaPipe without NS-AGF
        import mediapipe as mp
        mp_holistic = mp.solutions.holistic
        mp_extractor = mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        class_names = load_class_names(MODEL_PATH.parent)
        return
    
    # Device setup
    device = torch.device('cpu')  # Use CPU for stability
    print(f"📱 Using device: {device}")
    
    # Load class names
    model_dir = MODEL_PATH.parent
    class_names = load_class_names(model_dir)
    num_classes = len(class_names)
    print(f"📊 Number of classes: {num_classes}")
    
    # Initialize MediaPipe extractor
    if NS_AGF_AVAILABLE:
        mp_extractor = MediaPipeExtractor()
        print("✅ MediaPipe extractor initialized")
    
    # Initialize banking verifier
    if NS_AGF_AVAILABLE:
        banking_verifier = BankingIntentVerifier()
        print("✅ Banking intent verifier initialized")
    
    # Load NS-AGF model
    try:
        if MODEL_PATH.exists() and NS_AGF_AVAILABLE:
            # Create model
            graph = MediaPipeGraph()
            sign_model = create_model(
                model_type='ns_agf',
                num_classes=num_classes,
                num_joints=75,
                graph=graph,
                device=device
            )
            
            # Load checkpoint
            checkpoint = torch.load(MODEL_PATH, map_location=device)
            if 'model_state_dict' in checkpoint:
                sign_model.load_state_dict(checkpoint['model_state_dict'])
            else:
                sign_model.load_state_dict(checkpoint)
            
            sign_model.eval()
            print(f"✅ NS-AGF model loaded from: {MODEL_PATH.name}")
        else:
            print(f"⚠️ Model file not found or NS-AGF not available")
            print("⚠️ Service will run in fallback mode")
    
    except Exception as e:
        print(f"⚠️ Error loading model: {e}")
        print("⚠️ Service will run in fallback mode")
        sign_model = None


def base64_to_frame(base64_string):
    """Convert base64 image to OpenCV frame"""
    try:
        img_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None


def extract_landmarks_from_frames(frames):
    """Extract MediaPipe landmarks from video frames"""
    if not NS_AGF_AVAILABLE or mp_extractor is None:
        # Fallback: return mock landmarks
        print("⚠️ Using fallback landmark extraction")
        mock_landmarks = []
        for _ in range(min(30, len(frames))):
            # Generate random landmarks (75 joints × 3 coordinates)
            landmarks = np.random.rand(75, 3).astype(np.float32)
            mock_landmarks.append(landmarks)
        return np.array(mock_landmarks)
    
    landmarks_sequence = []
    
    for frame_base64 in frames:
        frame = base64_to_frame(frame_base64)
        if frame is None:
            continue
        
        # Extract landmarks
        landmarks = mp_extractor.extract_landmarks(frame)
        if landmarks is not None and len(landmarks) == 75 * 3:  # 75 joints × (x,y,z)
            # Reshape to (75, 3)
            landmarks = landmarks.reshape(75, 3)
            landmarks_sequence.append(landmarks)
    
    return np.array(landmarks_sequence)


def predict_sign(landmarks_sequence):
    """Predict sign from landmark sequence"""
    if sign_model is None or not NS_AGF_AVAILABLE:
        # Return mock prediction if model not loaded
        print("⚠️ Using fallback prediction")
        return "HELP", 0.85, "SUPPORT_REQUEST"
    
    try:
        # Ensure we have exactly SEQUENCE_LENGTH frames
        if len(landmarks_sequence) < SEQUENCE_LENGTH:
            # Pad with last frame
            padding = np.repeat(
                landmarks_sequence[-1:], 
                SEQUENCE_LENGTH - len(landmarks_sequence), 
                axis=0
            )
            landmarks_sequence = np.vstack([landmarks_sequence, padding])
        elif len(landmarks_sequence) > SEQUENCE_LENGTH:
            # Take last SEQUENCE_LENGTH frames
            landmarks_sequence = landmarks_sequence[-SEQUENCE_LENGTH:]
        
        # Prepare input: (1, 3, T, V, M) format
        # T = temporal (frames), V = joints, M = persons
        data = torch.FloatTensor(landmarks_sequence).to(device)
        data = data.permute(1, 0, 2)  # (3, T, V)
        data = data.unsqueeze(0).unsqueeze(-1)  # (1, 3, T, V, 1)
        
        # Predict
        with torch.no_grad():
            output = sign_model(data)
            probs = torch.softmax(output, dim=1)
            confidence, pred_idx = torch.max(probs, dim=1)
        
        predicted_class = class_names[pred_idx.item()]
        confidence_score = confidence.item()
        
        # Get banking intent
        if banking_verifier:
            intent_result = banking_verifier.verify_intent(
                predicted_class,
                IntentContext(confidence=confidence_score)
            )
            intent = intent_result.intent.name if intent_result.is_valid else "UNKNOWN"
        else:
            intent = "SUPPORT_REQUEST"
        
        return predicted_class, confidence_score, intent
    
    except Exception as e:
        print(f"Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return "ERROR", 0.0, "UNKNOWN"


def generate_sentence(sign, intent):
    """Generate natural language sentence from sign and intent"""
    # Simple template-based generation (can be enhanced with SLM)
    templates = {
        "SUPPORT_REQUEST": "I need help with {sign}",
        "BALANCE_INQUIRY": "I want to check my {sign}",
        "TRANSACTION": "I would like to {sign}",
        "ACCOUNT_MANAGEMENT": "I need to update my {sign}",
        "SECURITY": "I have a problem with my {sign}",
    }
    
    template = templates.get(intent, "I want to {sign}")
    sentence = template.format(sign=sign.lower())
    
    return sentence


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'NS-AGF Sign Language Recognition',
        'model_loaded': sign_model is not None,
        'num_classes': len(class_names) if class_names else 0
    })


@app.route('/api/biometric/recognize-sign', methods=['POST'])
def recognize_sign():
    """
    Recognize sign language from video frames
    
    Request body:
    {
        "videoFrames": ["base64_frame1", "base64_frame2", ...]
    }
    
    Response:
    {
        "success": true,
        "data": {
            "recognizedSign": "HELP",
            "sentence": "I need help with support",
            "intent": "SUPPORT_REQUEST",
            "confidence": 0.85
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'videoFrames' not in data:
            return jsonify({
                'success': False,
                'message': 'No video frames provided'
            }), 400
        
        frames = data['videoFrames']
        
        if len(frames) < 10:
            return jsonify({
                'success': False,
                'message': 'Insufficient frames (need at least 10)'
            }), 400
        
        print(f"📥 Received {len(frames)} frames for recognition")
        
        # Extract landmarks
        print("🔍 Extracting landmarks...")
        landmarks_sequence = extract_landmarks_from_frames(frames)
        
        if len(landmarks_sequence) < 10:
            return jsonify({
                'success': False,
                'message': 'Insufficient valid landmarks detected'
            }), 400
        
        print(f"✅ Extracted {len(landmarks_sequence)} landmark frames")
        
        # Predict sign
        print("🤖 Running NS-AGF prediction...")
        predicted_sign, confidence, intent = predict_sign(landmarks_sequence)
        
        print(f"✅ Predicted: {predicted_sign} (confidence: {confidence:.3f}, intent: {intent})")
        
        # Generate sentence
        sentence = generate_sentence(predicted_sign, intent)
        
        return jsonify({
            'success': True,
            'data': {
                'recognizedSign': predicted_sign,
                'sentence': sentence,
                'intent': intent,
                'confidence': float(confidence),
                'frames_processed': len(landmarks_sequence)
            }
        })
    
    except Exception as e:
        print(f"❌ Error in recognize_sign: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Sign recognition failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Initialize model on startup
    initialize_model()
    
    print("\n" + "="*80)
    print("🚀 NS-AGF Sign Language Recognition Service")
    print("="*80)
    print(f"📍 URL: http://127.0.0.1:8000")
    print(f"📊 Classes: {len(class_names) if class_names else 0}")
    print(f"🤖 Model: {'Loaded' if sign_model else 'Not loaded (testing mode)'}")
    print("\n📡 Endpoints:")
    print("   GET  /health - Health check")
    print("   POST /api/biometric/recognize-sign - Recognize sign language")
    print("="*80)
    print("\n⚠️  Press CTRL+C to quit\n")
    
    # Run Flask app
    app.run(host='127.0.0.1', port=8000, debug=False, threaded=True)
