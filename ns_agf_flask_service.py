"""
NS-AGF Sign Language Recognition Flask Service
===============================================

Flask wrapper for the NS-AGF inference model.
Uses your existing inference.py implementation.

Port: 8000
"""

import os
import sys
from pathlib import Path

# CRITICAL: Change to ns_agf directory so imports work
ns_agf_dir = Path(__file__).parent / 'ns_agf'
os.chdir(ns_agf_dir)
sys.path.insert(0, str(ns_agf_dir))
sys.path.insert(0, str(ns_agf_dir / 'src'))

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import torch

# Import from your inference.py
from inference import SignLanguageInference, load_class_names

app = Flask(__name__)
CORS(app)

# Global inference system
inference_system = None
# Global MediaPipe extractor (CRITICAL: Must reuse for video tracking!)
global_extractor = None

def base64_to_frame(base64_string):
    """Convert base64 string to OpenCV frame"""
    try:
        img_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None


def process_frames_to_sequence(frames_base64, target_length=30):
    """
    Convert base64 frames to landmark sequence
    
    Args:
        frames_base64: List of base64 encoded frames
        target_length: Target sequence length (30 frames)
    
    Returns:
        Preprocessed torch tensor ready for NS-AGF model inference
    """
    global global_extractor
    
    # Convert base64 to OpenCV frames
    frames = []
    for frame_b64 in frames_base64:
        frame = base64_to_frame(frame_b64)
        if frame is not None:
            frames.append(frame)
    
    if len(frames) < 10:
        raise ValueError(f"Insufficient frames: got {len(frames)}, need at least 10")
    
    print(f"📸 Processing {len(frames)} frames...")
    
    # CRITICAL: Use GLOBAL extractor - MUST reuse same instance for video tracking!
    # This is how inference.py works - it uses ONE extractor for all frames
    extractor = global_extractor
    
    # Extract landmarks from each frame
    landmarks_sequence = []
    successful_extractions = 0
    failed_extractions = 0
    
    # Debug: Check first frame quality
    first_frame_checked = False
    
    for idx, frame in enumerate(frames):
        # CRITICAL: Convert BGR to RGB (cv2.imdecode returns BGR, MediaPipe needs RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Debug: Print detailed info for first frame
        if idx == 0 and not first_frame_checked:
            print(f"   📐 Frame 0 details:")
            print(f"      BGR shape: {frame.shape}, dtype: {frame.dtype}")
            print(f"      BGR range: [{frame.min()}, {frame.max()}]")
            print(f"      RGB shape: {frame_rgb.shape}, dtype: {frame_rgb.dtype}")
            print(f"      RGB range: [{frame_rgb.min()}, {frame_rgb.max()}]")
            print(f"      RGB mean per channel: R={frame_rgb[:,:,0].mean():.1f}, G={frame_rgb[:,:,1].mean():.1f}, B={frame_rgb[:,:,2].mean():.1f}")
            first_frame_checked = True
        
        # Extract landmarks using fresh extractor
        landmarks = extractor.extract_landmarks(frame_rgb)
        
        if landmarks is not None:
            if len(landmarks.flatten()) == 75 * 3:
                landmarks = landmarks.reshape(75, 3)  # (V, C)
                landmarks_sequence.append(landmarks)
                successful_extractions += 1
                # Debug: Check landmark values for first successful extraction
                if successful_extractions == 1:
                    print(f"   🎯 First landmark extraction (frame {idx}):")
                    print(f"      Landmarks shape: {landmarks.shape}")
                    print(f"      Nose (0): {landmarks[0]}")
                    print(f"      Left shoulder (11): {landmarks[11]}")
                    print(f"      Right shoulder (12): {landmarks[12]}")
                    print(f"      Landmark range: [{landmarks.min():.4f}, {landmarks.max():.4f}]")
            else:
                print(f"   ⚠️  Frame {idx}: Unexpected landmark shape {landmarks.shape}")
                failed_extractions += 1
        else:
            failed_extractions += 1
    
    # DO NOT close extractor - it's global and reused!
    # extractor.holistic.close()  # REMOVED - we reuse the global extractor
    
    print(f"   ✅ Successful: {successful_extractions} frames")
    print(f"   ❌ Failed: {failed_extractions} frames")
    
    if len(landmarks_sequence) < 10:
        raise ValueError(f"Insufficient landmark frames: got {len(landmarks_sequence)}, need at least 10")
    
    print(f"✅ Extracted {len(landmarks_sequence)} landmark frames from {len(frames)} input frames")
    print(f"   Detection rate: {(len(landmarks_sequence) / len(frames) * 100):.1f}%")
    
    # Pad or truncate to target_length
    if len(landmarks_sequence) < target_length:
        # Pad with last frame
        padding = np.repeat(
            landmarks_sequence[-1:], 
            target_length - len(landmarks_sequence), 
            axis=0
        )
        landmarks_sequence = np.vstack([landmarks_sequence, padding])
    elif len(landmarks_sequence) > target_length:
        # Take last target_length frames
        landmarks_sequence = landmarks_sequence[-target_length:]
    
    # Convert list to numpy array: (T, V, C)
    landmarks_sequence = np.array(landmarks_sequence)
    
    # Debug: Check landmark ranges before preprocessing
    print(f"🔍 Before preprocessing:")
    print(f"   Shape: {landmarks_sequence.shape}")
    print(f"   Range: [{landmarks_sequence.min():.3f}, {landmarks_sequence.max():.3f}]")
    print(f"   Mean: {landmarks_sequence.mean():.3f}, Std: {landmarks_sequence.std():.3f}")
    print(f"   Nose (landmark 0) avg: [{landmarks_sequence[:, 0, 0].mean():.3f}, {landmarks_sequence[:, 0, 1].mean():.3f}, {landmarks_sequence[:, 0, 2].mean():.3f}]")
    print(f"   Left shoulder (11) avg: [{landmarks_sequence[:, 11, 0].mean():.3f}, {landmarks_sequence[:, 11, 1].mean():.3f}, {landmarks_sequence[:, 11, 2].mean():.3f}]")
    print(f"   Right shoulder (12) avg: [{landmarks_sequence[:, 12, 0].mean():.3f}, {landmarks_sequence[:, 12, 1].mean():.3f}, {landmarks_sequence[:, 12, 2].mean():.3f}]")
    
    # Calculate shoulder width to verify normalization will work
    shoulder_dist = np.linalg.norm(landmarks_sequence[:, 11, :] - landmarks_sequence[:, 12, :], axis=1)
    print(f"   Shoulder width: mean={shoulder_dist.mean():.4f}, min={shoulder_dist.min():.4f}, max={shoulder_dist.max():.4f}")
    
    # CRITICAL: Use inference system's preprocessing (handles normalization and format)
    input_tensor = inference_system.preprocess_sequence(landmarks_sequence)
    
    # AFTER NORMALIZATION - check if nose is at origin
    # Get the normalized numpy data back from tensor for inspection
    tensor_np = input_tensor.cpu().numpy()  # Shape: (1, 3, 30, 75)
    # Transpose back to (T, V, C) for easier interpretation
    check_sequence = np.transpose(tensor_np[0], (1, 2, 0))  # (30, 75, 3)
    print(f"   🔍 POST-NORMALIZATION Check:")
    print(f"      Nose (landmark 0) after norm: [{check_sequence[:, 0, 0].mean():.3f}, {check_sequence[:, 0, 1].mean():.3f}, {check_sequence[:, 0, 2].mean():.3f}]")
    print(f"      Left shoulder (11) after norm: [{check_sequence[:, 11, 0].mean():.3f}, {check_sequence[:, 11, 1].mean():.3f}, {check_sequence[:, 11, 2].mean():.3f}]")
    print(f"      Right shoulder (12) after norm: [{check_sequence[:, 12, 0].mean():.3f}, {check_sequence[:, 12, 1].mean():.3f}, {check_sequence[:, 12, 2].mean():.3f}]")
    
    # Debug: Check tensor after preprocessing  
    print(f"🔍 After preprocessing:")
    print(f"   Tensor shape: {input_tensor.shape}")
    print(f"   Tensor range: [{input_tensor.min():.3f}, {input_tensor.max():.3f}]")
    print(f"   Tensor mean: {input_tensor.mean():.3f}, Std: {input_tensor.std():.3f}")
    
    # DIAGNOSTIC: Save tensor for comparison with inference.py
    # np.save('flask_tensor_debug.npy', input_tensor.cpu().numpy())
    # print(f"   💾 Saved tensor to flask_tensor_debug.npy for analysis")
    
    return input_tensor


def generate_sentence(sign, intent):
    """Generate natural language sentence"""
    templates = {
        "SUPPORT_REQUEST": f"I need help with {sign.lower()}",
        "BALANCE_INQUIRY": f"I want to check my {sign.lower()}",
        "TRANSACTION": f"I would like to {sign.lower()}",
        "ACCOUNT_MANAGEMENT": f"I need to update my {sign.lower()}",
        "SECURITY": f"I have a question about {sign.lower()}",
    }
    return templates.get(intent, f"I want to {sign.lower()}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'NS-AGF Sign Language Recognition',
        'model_loaded': inference_system is not None,
        'num_classes': inference_system.num_classes if inference_system else 0
    })


@app.route('/api/biometric/recognize-sign', methods=['POST'])
def recognize_sign():
    """
    Recognize sign language from video frames
    
    Request:
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
                'message': f'Insufficient frames: got {len(frames)}, need at least 10'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"📥 Received {len(frames)} frames for recognition")
        
        # Convert frames to landmark sequence
        try:
            data_tensor = process_frames_to_sequence(frames, target_length=30)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Landmark extraction failed: {str(e)}'
            }), 400
        
        # Run inference
        print("🤖 Running NS-AGF inference...")
        data_tensor = data_tensor.to(inference_system.device)
        
        with torch.no_grad():
            output = inference_system.model(data_tensor)
            probabilities = torch.softmax(output, dim=1)
            confidence, predicted_class = probabilities.max(1)
        
        # Get prediction
        confidence = confidence.item()
        predicted_class = predicted_class.item()
        predicted_sign = inference_system.class_names[predicted_class]
        
        # Calculate prediction entropy (measure of uncertainty)
        probs_np = probabilities[0].cpu().numpy()
        entropy = -np.sum(probs_np * np.log(probs_np + 1e-10))
        max_entropy = np.log(len(probs_np))
        normalized_entropy = entropy / max_entropy
        
        # Get top 3 predictions
        top3_probs, top3_classes = torch.topk(probabilities[0], k=min(3, inference_system.num_classes))
        top3_list = [
            {
                'sign': inference_system.class_names[top3_classes[i].item()],
                'confidence': float(top3_probs[i].item())
            }
            for i in range(len(top3_classes))
        ]
        
        print(f"✅ Predicted: {predicted_sign} (confidence: {confidence:.3f})")
        top3_str = ", ".join([f"{item['sign']} ({item['confidence']:.2f})" for item in top3_list])
        print(f"   Top 3: {top3_str}")
        
        # Banking Intent Verification
        intent = "UNKNOWN"
        intent_info = None
        
        if hasattr(inference_system, 'banking_verifier') and inference_system.banking_verifier:
            try:
                intent_obj, context, is_valid = inference_system.banking_verifier.verify_sign_sequence(
                    signs=[predicted_sign],
                    confidences=[confidence]
                )
                
                intent = intent_obj.value
                intent_info = {
                    'intent': intent,
                    'intent_valid': is_valid,
                    'requires_confirmation': context.pending_confirmation,
                    'missing_slots': context.missing_slots,
                    'error_message': context.error_message if not is_valid else None,
                    'slots': context.slots,
                    'is_authenticated': context.is_authenticated
                }
                
                print(f"🎯 Intent: {intent} (valid: {is_valid})")
                if not is_valid and context.error_message:
                    print(f"   ⚠️  {context.error_message}")
                    
            except Exception as e:
                print(f"⚠️ Intent verification error: {e}")
                intent = "SUPPORT_REQUEST"  # Fallback
        else:
            intent = "SUPPORT_REQUEST"  # Default fallback
        
        # Generate sentence
        sentence = generate_sentence(predicted_sign, intent)
        
        print(f"📝 Sentence: {sentence}")
        print(f"{'='*60}\n")
        
        # Build response
        response_data = {
            'recognizedSign': predicted_sign,
            'sentence': sentence,
            'intent': intent,
            'confidence': float(confidence),
            'top3': top3_list,
            'frames_processed': len(frames),
            'entropy': float(normalized_entropy)
        }
        
        # Add intent verification details if available
        if intent_info:
            response_data['intent_info'] = intent_info
        
        return jsonify({
            'success': True,
            'data': response_data
        })
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Recognition failed: {str(e)}'
        }), 500


def initialize_service():
    """Initialize NS-AGF inference system matching inference.py EXACTLY"""
    global inference_system
    global global_extractor
    
    print("\n" + "="*80)
    print("🚀 Initializing NS-AGF Sign Language Recognition Service")
    print("="*80)
    
    model_path = './models/ns_agcn.pth'  # Relative to ns_agf/ directory (we already changed dir)
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        print("⚠️  Service will not work without model!")
        return False
    
    try:
        # CRITICAL: Load model with SAME parameters as inference.py
        # No manual num_classes - let it auto-detect from checkpoint
        inference_system = SignLanguageInference(
            model_path=model_path,
            confidence_threshold=0.5,  # Lower for Flask (0.7 in inference.py was for real-time)
            device='cpu'
        )
        
        # CRITICAL: Create GLOBAL MediaPipe extractor - MUST reuse for all frames!
        # This is EXACTLY how inference.py works - one extractor instance for entire session
        print("🔧 Creating GLOBAL MediaPipe extractor (video tracking mode)...")
        from src.utils.mediapipe_helper import MediaPipeExtractor
        global_extractor = MediaPipeExtractor(
            static_image_mode=False,  # Video mode for continuous tracking
            model_complexity=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        print("✅ Global MediaPipe extractor created (MATCHES inference.py)")
        
        # Also update inference system's extractor
        inference_system.extractor = global_extractor
        
        print("\n✅ NS-AGF inference system initialized successfully!")
        print(f"📊 Classes: {inference_system.num_classes}")
        print(f"🏷️  Labels: {inference_system.class_names[:5]}...")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to initialize inference system: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Initialize inference system
    if not initialize_service():
        print("\n❌ Service initialization failed!")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("🌐 Starting Flask Server")
    print("="*80)
    print("📍 URL: http://127.0.0.1:8000")
    print("\n📡 Endpoints:")
    print("   GET  /health - Health check")
    print("   POST /api/biometric/recognize-sign - Recognize sign language")
    print("="*80)
    print("\n⚠️  Press CTRL+C to quit\n")
    
    # Run Flask app
    app.run(host='127.0.0.1', port=8000, debug=False, threaded=True)
