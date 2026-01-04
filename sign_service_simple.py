"""
Simple Sign Language Recognition Service
=========================================

Lightweight Flask service for sign language recognition
that integrates with the banking frontend.

Port: 8000
Frontend endpoint: http://localhost:3000/sign-recognition
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import random

app = Flask(__name__)
CORS(app)

# Banking sign vocabulary
BANKING_SIGNS = [
    "BALANCE", "TRANSFER", "DEPOSIT", "WITHDRAW", "ACCOUNT",
    "HELP", "SUPPORT", "PROBLEM", "ISSUE", "ERROR",
    "PAY", "PAYMENT", "LOAN", "CREDIT", "DEBIT",
    "CHECK", "VERIFY", "CONFIRM", "CANCEL", "UPDATE",
    "PASSWORD", "SECURITY", "STATEMENT", "TRANSACTION", "HISTORY",
    "MONEY", "SAVE", "INVESTMENT", "INTEREST", "BANK"
]

# Intent templates
INTENT_TEMPLATES = {
    "SUPPORT_REQUEST": ["HELP", "SUPPORT", "PROBLEM", "ISSUE", "ERROR"],
    "BALANCE_INQUIRY": ["BALANCE", "CHECK", "ACCOUNT", "STATEMENT"],
    "TRANSACTION": ["TRANSFER", "PAY", "PAYMENT", "SEND", "WITHDRAW", "DEPOSIT"],
    "ACCOUNT_MANAGEMENT": ["UPDATE", "CHANGE", "MODIFY", "CANCEL"],
    "SECURITY": ["PASSWORD", "SECURITY", "VERIFY", "CONFIRM"],
}

def get_intent(sign):
    """Map sign to banking intent"""
    for intent, keywords in INTENT_TEMPLATES.items():
        if sign in keywords:
            return intent
    return "SUPPORT_REQUEST"

def generate_sentence(sign, intent):
    """Generate natural sentence from sign"""
    templates = {
        "SUPPORT_REQUEST": f"I need help with {sign.lower()}",
        "BALANCE_INQUIRY": f"I want to check my {sign.lower()}",
        "TRANSACTION": f"I would like to {sign.lower()}",
        "ACCOUNT_MANAGEMENT": f"I need to {sign.lower()} my account",
        "SECURITY": f"I have a question about {sign.lower()}",
    }
    
    return templates.get(intent, f"I want to {sign.lower()}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Sign Language Recognition',
        'version': '1.0',
        'signs_available': len(BANKING_SIGNS)
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
                'message': 'Insufficient frames (need at least 10)'
            }), 400
        
        print(f"📥 Received {len(frames)} frames for recognition")
        
        # Simulate sign recognition (replace with actual model later)
        # For now, randomly select from common banking signs
        predicted_sign = random.choice(BANKING_SIGNS)
        confidence = random.uniform(0.75, 0.95)
        
        # Get intent
        intent = get_intent(predicted_sign)
        
        # Generate sentence
        sentence = generate_sentence(predicted_sign, intent)
        
        print(f"✅ Predicted: {predicted_sign} (confidence: {confidence:.3f}, intent: {intent})")
        
        return jsonify({
            'success': True,
            'data': {
                'recognizedSign': predicted_sign,
                'sentence': sentence,
                'intent': intent,
                'confidence': float(confidence),
                'frames_processed': len(frames)
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
    print("\n" + "="*80)
    print("🚀 Sign Language Recognition Service")
    print("="*80)
    print("📍 URL: http://127.0.0.1:8000")
    print(f"📊 Signs: {len(BANKING_SIGNS)}")
    print("\n📡 Endpoints:")
    print("   GET  /health - Health check")
    print("   POST /api/biometric/recognize-sign - Recognize sign language")
    print("="*80)
    print("\n⚠️  Note: Using simplified recognition (for integration testing)")
    print("   Replace with NS-AGF model for production")
    print("\n⚠️  Press CTRL+C to quit\n")
    
    # Run Flask app
    app.run(host='127.0.0.1', port=8000, debug=False, threaded=True)
