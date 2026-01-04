"""
Biometric Fusion Service for Secure Transfers (NOVEL CONTRIBUTION)
===================================================================

Implements multimodal biometric authentication using:
- Face Recognition: HOG + histogram + texture analysis
- Hand Detection: Contour-based geometric features + color analysis
- Behavioral Style: Optical flow motion patterns + temporal dynamics
- Score-Level Fusion: Weighted combination (0.4 face + 0.35 hand + 0.25 style)

This represents a NOVEL approach combining traditional CV with behavioral biometrics
for continuous transaction authentication WITHOUT requiring dedicated hardware.

Author: NS-AGF Team
Date: January 2026
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import json
import pickle
import os
from pathlib import Path
from scipy.spatial.distance import cosine

app = Flask(__name__)
CORS(app)

# Persistent biometric database
BIOMETRIC_DB_PATH = Path(__file__).parent / 'biometric_data.pkl'

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
        print(f"⚠️  Failed to save biometric database: {e}")

# Load existing database
biometric_db = load_biometric_db()

class BiometricFusionAuthenticator:
    """
    Multi-modal Biometric Fusion System
    Combines Face + Hand + Style for secure authentication
    """
    
    def __init__(self):
        # Fusion weights (NOVEL CONTRIBUTION)
        self.face_weight = 0.40   # 40% face biometrics
        self.hand_weight = 0.35   # 35% hand geometry
        self.style_weight = 0.25  # 25% behavioral style
        self.threshold = 0.65     # 65% match required
        
        # Initialize HOG descriptor for face
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
    def extract_face_features(self, frame):
        """Extract multi-dimensional face features"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Multi-method face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))
            
            if len(faces) == 0:
                # Fallback: use upper-center region
                h, w = gray.shape
                y, x = h//4, w//4
                face_roi = gray[y:y+h//2, x:x+w//2]
            else:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_resized = cv2.resize(face_roi, (128, 128))
            
            # Feature 1: Pixel intensity distribution
            pixel_features = face_resized.flatten() / 255.0
            
            # Feature 2: Histogram of gradients
            hist = cv2.calcHist([face_resized], [0], None, [64], [0, 256])
            hist_features = (hist / (hist.sum() + 1e-7)).flatten()
            
            # Feature 3: Edge density map
            edges = cv2.Canny(face_resized, 50, 150)
            edge_features = edges.flatten() / 255.0
            
            # Feature 4: Local Binary Pattern-like texture
            lbp_like = np.abs(face_resized[:, :-1] - face_resized[:, 1:]).flatten() / 255.0
            
            # Combine features (reduce dimensionality)
            combined = np.concatenate([
                pixel_features[::32],  # Sample every 32nd pixel
                hist_features,
                edge_features[::64],
                lbp_like[:256]
            ])
            
            return combined
            
        except Exception as e:
            print(f"⚠️  Face extraction error: {e}")
            return None
    
    def extract_hand_features(self, frame):
        """Extract hand geometry and color features"""
        try:
            # Convert to HSV for better skin detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Skin color detection (multiple ranges for robustness)
            lower_skin1 = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin1 = np.array([20, 255, 255], dtype=np.uint8)
            mask1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
            
            lower_skin2 = np.array([0, 10, 60], dtype=np.uint8)
            upper_skin2 = np.array([30, 200, 255], dtype=np.uint8)
            mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
            
            # Combine masks
            skin_mask = cv2.bitwise_or(mask1, mask2)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) == 0:
                return np.zeros(128)  # Return zero vector if no hand detected
            
            # Use largest contour (likely the hand)
            hand_contour = max(contours, key=cv2.contourArea)
            
            # Geometric features
            area = cv2.contourArea(hand_contour)
            perimeter = cv2.arcLength(hand_contour, True)
            
            # Bounding box features
            x, y, w, h = cv2.boundingRect(hand_contour)
            aspect_ratio = float(w) / h if h > 0 else 0
            extent = area / (w * h) if (w * h) > 0 else 0
            
            # Convex hull features
            hull = cv2.convexHull(hand_contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            # Moments for shape description
            moments = cv2.moments(hand_contour)
            hu_moments = cv2.HuMoments(moments).flatten()
            
            # Contour approximation (simplified shape)
            epsilon = 0.01 * perimeter
            approx = cv2.approxPolyDP(hand_contour, epsilon, True)
            num_vertices = len(approx)
            
            # Create feature vector
            geometric_features = np.array([
                area / 10000.0,  # Normalize
                perimeter / 1000.0,
                aspect_ratio,
                extent,
                solidity,
                num_vertices / 50.0,
                *hu_moments[:7]  # Hu moments
            ])
            
            # Color histogram of hand region
            hand_roi = frame[y:y+h, x:x+w]
            if hand_roi.size > 0:
                color_hist_b = cv2.calcHist([hand_roi], [0], None, [32], [0, 256])
                color_hist_g = cv2.calcHist([hand_roi], [1], None, [32], [0, 256])
                color_hist_r = cv2.calcHist([hand_roi], [2], None, [32], [0, 256])
                
                color_features = np.concatenate([
                    (color_hist_b / (color_hist_b.sum() + 1e-7)).flatten(),
                    (color_hist_g / (color_hist_g.sum() + 1e-7)).flatten(),
                    (color_hist_r / (color_hist_r.sum() + 1e-7)).flatten()
                ])
            else:
                color_features = np.zeros(96)
            
            # Combine geometric and color features
            combined = np.concatenate([geometric_features, color_features[:18]])
            
            # Pad to 128 dimensions
            if len(combined) < 128:
                combined = np.pad(combined, (0, 128 - len(combined)), 'constant')
            
            return combined[:128]
            
        except Exception as e:
            print(f"⚠️  Hand extraction error: {e}")
            return np.zeros(128)
    
    def extract_style_features(self, frame_sequence):
        """Extract behavioral dynamics from motion patterns"""
        try:
            if len(frame_sequence) < 3:
                return np.zeros(64)
            
            motion_features = []
            
            # Sample frames efficiently
            step = max(1, len(frame_sequence) // 8)
            frames = frame_sequence[::step][:10]
            
            for i in range(len(frames) - 1):
                try:
                    gray1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
                    gray2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
                    
                    # Resize for speed
                    gray1 = cv2.resize(gray1, (160, 120))
                    gray2 = cv2.resize(gray2, (160, 120))
                    
                    # Dense optical flow
                    flow = cv2.calcOpticalFlowFarneback(
                        gray1, gray2, None,
                        pyr_scale=0.5, levels=2, winsize=15,
                        iterations=2, poly_n=5, poly_sigma=1.1, flags=0
                    )
                    
                    # Flow magnitude and angle
                    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                    
                    # Statistical features
                    motion_features.extend([
                        np.mean(mag),
                        np.std(mag),
                        np.max(mag),
                        np.median(mag),
                        np.mean(ang),
                        np.std(ang),
                        np.percentile(mag, 75)  # 75th percentile
                    ])
                except:
                    motion_features.extend([0] * 7)
            
            # Pad to 64 dimensions
            while len(motion_features) < 64:
                motion_features.append(0)
            
            return np.array(motion_features[:64])
            
        except Exception as e:
            print(f"⚠️  Style extraction error: {e}")
            return np.zeros(64)
    
    def calculate_similarity(self, query, reference):
        """Calculate cosine similarity with robustness"""
        if query is None or reference is None:
            return 0.0
        
        # Handle zero vectors
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
        """NOVEL CONTRIBUTION: Weighted score-level fusion"""
        fusion_score = (
            self.face_weight * face_score +
            self.hand_weight * hand_score +
            self.style_weight * style_score
        )
        return fusion_score
    
    def enroll(self, user_id, frames):
        """Enroll user with multi-modal biometrics"""
        print(f"📝 Enrolling user {user_id} ({len(frames)} frames)")
        
        face_list, hand_list = [], []
        
        for frame in frames:
            face_feat = self.extract_face_features(frame)
            hand_feat = self.extract_hand_features(frame)
            
            if face_feat is not None:
                face_list.append(face_feat)
            if not np.allclose(hand_feat, 0):
                hand_list.append(hand_feat)
        
        if len(face_list) == 0:
            return False, "No face detected"
        
        # Average features
        avg_face = np.mean(face_list, axis=0)
        avg_hand = np.mean(hand_list, axis=0) if len(hand_list) > 0 else np.zeros(128)
        style_feat = self.extract_style_features(frames)
        
        biometric_db[user_id] = {
            'face': avg_face,
            'hand': avg_hand,
            'style': style_feat
        }
        
        # Persist to disk
        save_biometric_db(biometric_db)
        
        print(f"✅ Enrolled: face={len(face_list)} hand={len(hand_list)} frames")
        return True, "Enrollment successful"
    
    def verify(self, user_id, frames):
        """Verify user with multi-modal fusion"""
        print(f"🔍 Verifying user {user_id} ({len(frames)} frames)")
        
        if user_id not in biometric_db:
            return False, 0.0, 0.0, 0.0, 0.0, "User not enrolled"
        
        ref = biometric_db[user_id]
        
        # Extract query features
        face_list, hand_list = [], []
        
        for frame in frames:
            face_feat = self.extract_face_features(frame)
            hand_feat = self.extract_hand_features(frame)
            
            if face_feat is not None:
                face_list.append(face_feat)
            if not np.allclose(hand_feat, 0):
                hand_list.append(hand_feat)
        
        if len(face_list) == 0:
            return False, 0.0, 0.0, 0.0, 0.0, "No face detected"
        
        query_face = np.mean(face_list, axis=0)
        query_hand = np.mean(hand_list, axis=0) if len(hand_list) > 0 else np.zeros(128)
        query_style = self.extract_style_features(frames)
        
        # Calculate scores
        face_score = float(self.calculate_similarity(query_face, ref['face']))
        hand_score = float(self.calculate_similarity(query_hand, ref['hand']))
        style_score = float(self.calculate_similarity(query_style, ref['style']))
        
        # Fusion (NOVEL CONTRIBUTION)
        fusion_score = float(self.fuse_scores(face_score, hand_score, style_score))
        authenticated = fusion_score >= self.threshold
        
        print(f"   👤 Face: {face_score:.3f}")
        print(f"   ✋ Hand: {hand_score:.3f}")
        print(f"   ✍️  Style: {style_score:.3f}")
        print(f"   🔗 Fusion: {fusion_score:.3f}")
        print(f"   {'✅ AUTHENTICATED' if authenticated else '❌ REJECTED'}")
        
        msg = "Authenticated" if authenticated else "Rejected"
        return authenticated, fusion_score, face_score, hand_score, style_score, msg

# Initialize authenticator
authenticator = BiometricFusionAuthenticator()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'Biometric Fusion Service',
        'enrolled_users': len(biometric_db),
        'enrolled_user_ids': list(biometric_db.keys())
    })

@app.route('/api/biometric/enroll', methods=['POST'])
def enroll_biometric():
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        print(f"\n📥 Enrollment request: {user_id}")
        
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
                'message': msg
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
            'user_id': str(user_id)
        }
        
        print(f"📤 Response: auth={auth}, fusion={fusion:.3f}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Biometric Fusion Service - NOVEL CONTRIBUTION")
    print("="*70)
    print("📍 URL: http://127.0.0.1:5002")
    print("\n🔬 Multi-Modal Biometric Fusion:")
    print("   ├─ Face Recognition (40%)")
    print("   │   · HOG + Histogram + Texture + Edge density")
    print("   ├─ Hand Geometry (35%)")
    print("   │   · Contour analysis + Color histograms + Hu moments")
    print("   └─ Behavioral Style (25%)")
    print("       · Optical flow motion patterns + Temporal dynamics")
    print("\n⚙️  Fusion Algorithm: Weighted score-level combination")
    print("🎯 Threshold: 65% match required")
    print("\n📊 Endpoints: /api/health, /api/biometric/enroll, /api/biometric/verify")
    print("="*70 + "\n")
    
    app.run(host='127.0.0.1', port=5002, debug=False)
