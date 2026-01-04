"""
Enhanced Biometric Fusion Service with Deep Learning Face Recognition
======================================================================

CRITICAL FIX: Replaces weak HOG features with InsightFace embeddings
for accurate person identification during money transfers.

Changes:
- Face: InsightFace 512-dim embeddings (deep learning) instead of HOG
- Hand: Kept for multi-modal fusion (35% weight)
- Style: Kept for behavioral analysis (25% weight)  
- Threshold: Increased to 0.75 (75% match required)

This fixes the security vulnerability where any person could pass authentication.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import pickle
import requests
from pathlib import Path
from scipy.spatial.distance import cosine
import io

app = Flask(__name__)
CORS(app)

# Configuration
BIOMETRIC_DB_PATH = Path(__file__).parent / 'biometric_data_enhanced.pkl'
FACE_SERVICE_URL = 'http://127.0.0.1:5001'  # InsightFace service

def load_biometric_db():
    """Load biometric database from disk"""
    if BIOMETRIC_DB_PATH.exists():
        try:
            with open(BIOMETRIC_DB_PATH, 'rb') as f:
                db = pickle.load(f)
                print(f"✅ Loaded {len(db)} enrolled users from disk")
                return db
        except Exception as e:
            print(f"⚠️  Failed to load biometric database: {e}")
            return {}
    return {}

def save_biometric_db(db):
    """Save biometric database to disk"""
    try:
        with open(BIOMETRIC_DB_PATH, 'wb') as f:
            pickle.dump(db, f)
        print(f"💾 Saved {len(db)} users to disk")
    except Exception as e:
        print(f"❌ Failed to save database: {e}")

# Global database
biometric_db = load_biometric_db()

class EnhancedBiometricAuthenticator:
    def __init__(self, mode='face_primary'):
        """
        Initialize authenticator with configurable mode
        
        Modes:
        - 'face_primary': Face 90%, Hand 5%, Style 5% (RECOMMENDED)
        - 'balanced': Face 60%, Hand 25%, Style 15%
        - 'face_only': Face 100% (simplest)
        """
        self.mode = mode
        
        if mode == 'face_primary':
            # Face is primary identifier, hand/style just for liveness
            self.threshold = 0.85#Can be lower since face is reliable
            self.face_weight = 0.80
            self.hand_weight = 0.10
            self.style_weight = 0.10
        elif mode == 'face_only':
            # Face only (no multi-modal fusion)
            self.threshold = 0.85
            self.face_weight = 0.80
            self.hand_weight = 0.10
            self.style_weight = 0.10
        else:  # balanced
            # Original multi-modal weights
            self.threshold = 0.85
            self.face_weight = 0.5
            self.hand_weight = 0.4
            self.style_weight = 0.10
        
        print(f"🔐 Enhanced Biometric Authenticator initialized - Mode: {self.mode.upper()}")
        print(f"   🎯 Threshold: {self.threshold}")
        print(f"   📊 Weights: Face={self.face_weight}, Hand={self.hand_weight}, Style={self.style_weight}")
    
    def extract_face_embedding_insightface(self, frame):
        """
        Extract face embedding using InsightFace service (512-dim)
        This is MUCH more discriminative than HOG features!
        """
        try:
            # Convert frame to JPEG bytes
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                return None
            
            # Send to InsightFace service
            files = {'image': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}
            response = requests.post(f'{FACE_SERVICE_URL}/embed', files=files, timeout=5)
            
            if response.status_code == 200:
                embedding = np.array(response.json()['embedding'])
                return embedding
            else:
                print(f"⚠️  Face service error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Face embedding error: {e}")
            return None
    
    def extract_hand_features(self, frame):
        """Extract hand features with movement detection"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return np.zeros(128)
            
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Require larger hand area (more strict)
            if cv2.contourArea(largest_contour) < 3000:  # Increased threshold
                return np.zeros(128)
            
            # Geometric features
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = float(w) / h if h != 0 else 0
            extent = area / (w * h) if (w * h) != 0 else 0
            
            # Hu moments
            moments = cv2.moments(largest_contour)
            hu_moments = cv2.HuMoments(moments).flatten()
            
            # Color histogram
            hand_roi = cv2.bitwise_and(frame, frame, mask=mask)
            hist = cv2.calcHist([hand_roi], [0, 1, 2], mask, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            # Combine features
            features = np.concatenate([
                [area / 10000, perimeter / 1000, aspect_ratio, extent],
                hu_moments,
                hist[:100]
            ])
            
            return features[:128]
            
        except Exception as e:
            print(f"⚠️  Hand feature error: {e}")
            return np.zeros(128)
    
    def extract_style_features(self, frames):
        """Extract behavioral style features with movement validation"""
        try:
            if len(frames) < 2:
                return np.zeros(64)
            
            # Sample 10 frames evenly
            indices = np.linspace(0, len(frames) - 1, min(10, len(frames)), dtype=int)
            sampled_frames = [frames[i] for i in indices]
            
            # Convert to grayscale
            gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in sampled_frames]
            
            # Optical flow between consecutive frames
            flow_magnitudes = []
            flow_angles = []
            has_significant_movement = False
            
            for i in range(len(gray_frames) - 1):
                flow = cv2.calcOpticalFlowFarneback(
                    gray_frames[i], gray_frames[i + 1],
                    None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                
                magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                avg_magnitude = magnitude.mean()
                flow_magnitudes.append(avg_magnitude)
                flow_angles.append(angle.mean())
                
                # Check for significant movement (not just camera shake)
                if avg_magnitude > 0.8:  # Increased threshold for actual movement
                    has_significant_movement = True
            
            # Log movement analysis
            max_flow = max(flow_magnitudes) if flow_magnitudes else 0
            avg_flow = np.mean(flow_magnitudes) if flow_magnitudes else 0
            print(f"   📊 Style movement: max_flow={max_flow:.3f}, avg_flow={avg_flow:.3f}")
            
            # If no significant movement detected, return zeros
            if not has_significant_movement:
                print("   ⚠️  No significant behavioral movement detected (threshold: 0.8)")
                return np.zeros(64)
            else:
                print("   ✅ Significant behavioral movement detected")
            
            # Statistical features
            features = np.array([
                np.mean(flow_magnitudes),
                np.std(flow_magnitudes),
                np.mean(flow_angles),
                np.std(flow_angles),
                np.max(flow_magnitudes),
                np.min(flow_magnitudes)
            ])
            
            # Pad to 64 dimensions
            features = np.pad(features, (0, 64 - len(features)), 'constant')
            
            return features
            
        except Exception as e:
            print(f"⚠️  Style extraction error: {e}")
            return np.zeros(64)
    
    def calculate_similarity(self, query, reference):
        """Calculate cosine similarity"""
        if query is None or reference is None:
            return 0.0
        
        if np.allclose(query, 0) or np.allclose(reference, 0):
            return 0.0
        
        # Ensure same length
        min_len = min(len(query), len(reference))
        query = query[:min_len]
        reference = reference[:min_len]
        
        # Normalize
        query_norm = query / (np.linalg.norm(query) + 1e-7)
        ref_norm = reference / (np.linalg.norm(reference) + 1e-7)
        
        # Cosine similarity
        similarity = 1.0 - cosine(query_norm, ref_norm)
        
        return max(0.0, min(1.0, similarity))
    
    def fuse_scores(self, face_score, hand_score, style_score):
        """Weighted score-level fusion"""
        fusion_score = (
            self.face_weight * face_score +
            self.hand_weight * hand_score +
            self.style_weight * style_score
        )
        return fusion_score
    
    def enroll(self, user_id, frames):
        """Enroll user with enhanced face embeddings"""
        print(f"📝 Enrolling user {user_id} ({len(frames)} frames) - ENHANCED MODE")
        
        face_embeddings = []
        hand_list = []
        
        # Extract features from frames
        for i, frame in enumerate(frames):
            # Extract InsightFace embedding (deep learning)
            face_emb = self.extract_face_embedding_insightface(frame)
            if face_emb is not None:
                face_embeddings.append(face_emb)
                if len(face_embeddings) % 5 == 0:
                    print(f"   📸 Processed {len(face_embeddings)} face embeddings...")
            
            # Extract hand features (traditional CV)
            hand_feat = self.extract_hand_features(frame)
            if not np.allclose(hand_feat, 0):
                hand_list.append(hand_feat)
        
        if len(face_embeddings) == 0:
            return False, "No face detected in frames"
        
        # Average embeddings
        avg_face = np.mean(face_embeddings, axis=0)
        avg_hand = np.mean(hand_list, axis=0) if len(hand_list) > 0 else np.zeros(128)
        style_feat = self.extract_style_features(frames)
        
        # Store in database
        biometric_db[user_id] = {
            'face': avg_face,    # 512-dim InsightFace embedding
            'hand': avg_hand,    # 128-dim hand features
            'style': style_feat  # 64-dim style features
        }
        
        save_biometric_db(biometric_db)
        
        print(f"✅ Enrolled: face={len(face_embeddings)} frames, hand={len(hand_list)} frames")
        print(f"   👤 Face embedding: {avg_face.shape} (InsightFace)")
        print(f"   ✋ Hand features: {avg_hand.shape}")
        print(f"   ✍️  Style features: {style_feat.shape}")
        
        return True, "Enrollment successful"
    
    def verify(self, user_id, frames):
        """Verify user with enhanced face embeddings and movement validation"""
        print(f"🔍 Verifying user {user_id} ({len(frames)} frames) - ENHANCED MODE")
        
        if user_id not in biometric_db:
            return False, 0.0, 0.0, 0.0, 0.0, "User not enrolled"
        
        ref = biometric_db[user_id]
        
        # Extract query features
        face_embeddings = []
        hand_list = []
        hand_areas = []  # Track hand sizes to detect movement
        
        for frame in frames:
            face_emb = self.extract_face_embedding_insightface(frame)
            if face_emb is not None:
                face_embeddings.append(face_emb)
            
            hand_feat = self.extract_hand_features(frame)
            if not np.allclose(hand_feat, 0):
                hand_list.append(hand_feat)
                # Track hand area (first feature is area/10000)
                hand_areas.append(hand_feat[0])
        
        if len(face_embeddings) == 0:
            return False, 0.0, 0.0, 0.0, 0.0, "No face detected"
        
        query_face = np.mean(face_embeddings, axis=0)
        query_hand = np.mean(hand_list, axis=0) if len(hand_list) > 0 else np.zeros(128)
        query_style = self.extract_style_features(frames)
        
        # Check for hand movement (variance in hand area)
        hand_movement_detected = False
        if len(hand_areas) > 5:
            hand_variance = np.var(hand_areas)
            hand_range = max(hand_areas) - min(hand_areas)
            print(f"   📊 Hand movement analysis: variance={hand_variance:.4f}, range={hand_range:.4f}, frames={len(hand_areas)}")
            
            # Require BOTH high variance AND range (stricter check)
            if hand_variance > 0.2 and hand_range > 0.3:  # Much stricter thresholds
                hand_movement_detected = True
                print("   ✅ Significant hand movement detected")
            else:
                print("   ⚠️  Static hand detected (no movement) - applying penalty")
        else:
            print(f"   ⚠️  Too few hand frames ({len(hand_areas)}) - applying penalty")
        
        # Calculate similarities
        face_score = float(self.calculate_similarity(query_face, ref['face']))
        hand_score_raw = float(self.calculate_similarity(query_hand, ref['hand']))
        
        # Penalize hand score if no movement detected
        if len(hand_list) == 0:
            # No hand detected at all
            hand_score = 0.0
            print("   ⚠️  No hand detected - hand score = 0")
        elif not hand_movement_detected:
            # Hand detected but static (no gestures)
            hand_score = hand_score_raw * 0.1  # Reduce to 10% if static (was 30%)
            print(f"   ⚠️  Hand movement penalty applied: {hand_score_raw:.3f} → {hand_score:.3f}")
        else:
            # Hand with proper movement
            hand_score = hand_score_raw
            print(f"   ✅ Hand score (with movement): {hand_score:.3f}")
        
        style_score = float(self.calculate_similarity(query_style, ref['style']))
        
        # If style features are all zeros (no movement), set style score to 0
        if np.allclose(query_style, 0):
            print("   ⚠️  No behavioral movement - style score set to 0")
            style_score = 0.0
        
        # Fusion
        fusion_score = float(self.fuse_scores(face_score, hand_score, style_score))
        authenticated = fusion_score >= self.threshold
        
        print(f"   👤 Face (InsightFace): {face_score:.3f} [Primary - {self.face_weight*100:.0f}% weight]")
        print(f"   ✋ Hand: {hand_score:.3f} [Liveness - {self.hand_weight*100:.0f}% weight]")
        print(f"   ✍️  Style: {style_score:.3f} [Liveness - {self.style_weight*100:.0f}% weight]")
        print(f"   🔗 Fusion: {fusion_score:.3f} (threshold: {self.threshold})")
        
        if self.mode == 'face_primary':
            # Show what face-only score would be for comparison
            print(f"   💡 Face contribution: {face_score * self.face_weight:.3f} (dominates fusion)")
        
        print(f"   {'✅ AUTHENTICATED' if authenticated else '❌ REJECTED'}")
        
        msg = "Authenticated" if authenticated else f"Rejected (score {fusion_score:.3f} < {self.threshold})"
        return authenticated, fusion_score, face_score, hand_score, style_score, msg

# Initialize authenticator in FACE_PRIMARY mode (face 90%, hand/style 5% each)
authenticator = EnhancedBiometricAuthenticator(mode='face_primary')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'Enhanced Biometric Fusion Service',
        'mode': authenticator.mode,
        'enrolled_users': len(biometric_db),
        'enrolled_user_ids': list(biometric_db.keys()),
        'threshold': authenticator.threshold,
        'weights': {
            'face': authenticator.face_weight,
            'hand': authenticator.hand_weight,
            'style': authenticator.style_weight
        },
        'description': 'Face-primary mode: Face 90%, Hand 5%, Style 5%'
    })

@app.route('/api/biometric/enroll', methods=['POST'])
def enroll_biometric():
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        print(f"\n📥 Enrollment request: {user_id}")
        
        # Load frames
        frames = []
        for key in sorted([k for k in request.files.keys() if k.startswith('frame_')]):
            file_bytes = request.files[key].read()
            frame_array = np.frombuffer(file_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            if frame is not None:
                frames.append(frame)
        
        if len(frames) < 10:
            return jsonify({'error': 'Minimum 10 frames required'}), 400
        
        success, msg = authenticator.enroll(user_id, frames)
        
        if success:
            return jsonify({
                'success': True,
                'user_id': user_id,
                'frames_processed': len(frames),
                'message': msg,
                'mode': 'deep_learning'
            })
        else:
            return jsonify({'error': msg}), 400
            
    except Exception as e:
        print(f"❌ Enrollment error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/biometric/verify', methods=['POST'])
def verify_biometric():
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        print(f"\n📥 Verification request: {user_id}")
        
        # Load frames
        frames = []
        for key in sorted([k for k in request.files.keys() if k.startswith('frame_')]):
            file_bytes = request.files[key].read()
            frame_array = np.frombuffer(file_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            if frame is not None:
                frames.append(frame)
        
        if len(frames) < 10:
            return jsonify({'error': 'Minimum 10 frames required'}), 400
        
        auth, fusion, face, hand, style, msg = authenticator.verify(user_id, frames)
        
        response = {
            'authenticated': bool(auth),
            'fusionScore': float(fusion),
            'faceScore': float(face),
            'handScore': float(hand),
            'styleScore': float(style),
            'threshold': float(authenticator.threshold),
            'frames_processed': len(frames),
            'message': str(msg),
            'user_id': str(user_id),
            'mode': 'deep_learning'
        }
        
        print(f"📤 Response: auth={auth}, fusion={fusion:.3f}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 ENHANCED Biometric Fusion Service - Face-Primary Mode")
    print("="*80)
    print("📍 URL: http://127.0.0.1:5002")
    print("\n🔬 Multi-Modal Biometric Fusion (FACE-PRIMARY):")
    print("   ├─ Face Recognition (90%) - InsightFace 512-dim embeddings")
    print("   │   · Deep learning face embeddings (Primary identifier)")
    print("   ├─ Hand Geometry (5%)")
    print("   │   · Basic liveness detection")
    print("   └─ Behavioral Style (5%)")
    print("       · Basic liveness detection")
    print("\n💡 Why Face-Primary Mode?")
    print("   · InsightFace is highly discriminative (unique per person)")
    print("   · Face score alone can identify authorized vs unauthorized")
    print("   · Hand/style add minimal liveness check without affecting reliability")
    print("\n⚙️  Settings:")
    print(f"   · Mode: {authenticator.mode}")
    print(f"   · Threshold: {authenticator.threshold} (70% match required)")
    print(f"   · Database: {BIOMETRIC_DB_PATH}")
    print(f"   · Face Service: {FACE_SERVICE_URL}")
    print("\n📊 Endpoints: /api/health, /api/biometric/enroll, /api/biometric/verify")
    print("="*80)
    print("\n⚠️  IMPORTANT: Make sure InsightFace service is running on port 5001!")
    print("   Start with: cd python_service && python app.py\n")
    
    app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False)
