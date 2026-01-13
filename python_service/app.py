# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import numpy as np
# import cv2
# import insightface
# import os
# import io 
# import torch 
# from speechbrain.inference.speaker import SpeakerRecognition
# from speechbrain.inference import EncoderClassifier  
# import logging 
# import torchaudio
# import soundfile as sf
# import librosa
# from scipy.stats import skew, kurtosis
# import warnings
# warnings.filterwarnings('ignore')

# app = Flask(__name__)
# CORS(app)

# # Load ArcFace face model
# face_model = insightface.app.FaceAnalysis(name='buffalo_l')
# face_model.prepare(ctx_id=0, det_size=(640, 640))

# # Setup logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # Load ECAPA-TDNN voice model
# try:
#    # Use SpeakerRecognition model specifically for speaker verification
#     voice_model = SpeakerRecognition.from_hparams(
#         source="speechbrain/spkrec-ecapa-voxceleb",
#         savedir="pretrained_models/spkrec-ecapa-voxceleb"
#     )
# except Exception as e:
#     logger.error(f"Model initialization error: {str(e)}")
#     raise

# def extract_voice_features(waveform, sample_rate):
#     """Extract comprehensive voice features for speaker verification"""
#     try:
#         # Fundamental frequency features
#         f0, voiced_flag, voiced_probs = librosa.pyin(
#             waveform, 
#             fmin=librosa.note_to_hz('C2'), 
#             fmax=librosa.note_to_hz('C7')
#         )
        
#         # Spectral features
#         spectral_centroids = librosa.feature.spectral_centroid(y=waveform, sr=sample_rate)[0]
#         spectral_rolloff = librosa.feature.spectral_rolloff(y=waveform, sr=sample_rate)[0]
        
#         # MFCC features with deltas
#         mfccs = librosa.feature.mfcc(y=waveform, sr=sample_rate, n_mfcc=20)
#         mfcc_deltas = librosa.feature.delta(mfccs)
#         mfcc_delta2s = librosa.feature.delta(mfccs, order=2)
        
#         # Vocal tract features
#         formants = librosa.effects.preemphasis(waveform)
        
#         features = {
#             'f0_stats': {
#                 'mean': float(np.nanmean(f0)),
#                 'std': float(np.nanstd(f0)),
#                 'skew': float(skew(f0[~np.isnan(f0)])),
#                 'kurtosis': float(kurtosis(f0[~np.isnan(f0)]))
#             },
#             'spectral_stats': {
#                 'centroid_mean': float(np.mean(spectral_centroids)),
#                 'centroid_std': float(np.std(spectral_centroids)),
#                 'rolloff_mean': float(np.mean(spectral_rolloff))
#             },
#             'mfcc_stats': {
#                 'mean': float(np.mean(mfccs)),
#                 'std': float(np.std(mfccs)),
#                 'delta_mean': float(np.mean(mfcc_deltas)),
#                 'delta2_mean': float(np.mean(mfcc_delta2s))
#             },
#             'voice_characteristics': {
#                 'formant_mean': float(np.mean(formants)),
#                 'formant_std': float(np.std(formants)),
#                 'voiced_probability': float(np.mean(voiced_probs))
#             }
#         }
        
#         return features, True
        
#     except Exception as e:
#         logger.error(f"Feature extraction error: {str(e)}")
#         return None, False





# # ---------------- FACE EMBEDDING ROUTE ------------------
# @app.route('/embed', methods=['POST'])
# def get_face_embedding():
#     if 'image' not in request.files:
#         return jsonify({'error': 'Image file missing'}), 400

#     file = request.files['image']
#     img = np.frombuffer(file.read(), np.uint8)
#     img = cv2.imdecode(img, cv2.IMREAD_COLOR)

#     faces = face_model.get(img)
#     if not faces:
#         return jsonify({'error': 'No face detected'}), 400

#     embedding = faces[0].embedding.tolist()
#     return jsonify({'embedding': embedding})


# # ---------------- VOICE VERIFICATION ROUTE ------------------



# @app.route('/voice-verify', methods=['POST'])
# def verify_voice():
#     temp_path = 'temp_audio.wav'
#     if 'audio' not in request.files:
#         return jsonify({'error': 'No audio file provided'}), 400
        
#     try:
#         audio_file = request.files['audio']
#         audio_file.save(temp_path)
        
#         # Load and preprocess audio
#         waveform, sample_rate = librosa.load(temp_path, sr=16000)
        
#         # Voice activity detection
#         intervals = librosa.effects.split(waveform, top_db=20)
#         if len(intervals) == 0:
#             return jsonify({'error': 'No voice detected'}), 400
            
#         # Extract voiced segments
#         voiced_segments = []
#         for start, end in intervals:
#             voiced_segments.append(waveform[start:end])
#         waveform = np.concatenate(voiced_segments)
        
#         # Normalize audio
#         waveform = librosa.util.normalize(waveform)
        
#         # Get speaker embedding
#         waveform_tensor = torch.FloatTensor(waveform).unsqueeze(0)
#         with torch.no_grad():
#             embedding = voice_model.encode_batch(waveform_tensor)
#             embedding_vector = embedding.squeeze().cpu().numpy()
            
#         # Extract biometric features
#         voice_features, success = extract_voice_features(waveform, sample_rate)
#         if not success:
#             return jsonify({'error': 'Failed to extract voice features'}), 400
            
#         response_data = {
#             'embedding': embedding_vector.tolist(),
#             'voice_features': voice_features,
#             'success': True
#         }
        
#         return jsonify(response_data)
        
#     except Exception as e:
#         logger.error(f"Error processing voice: {str(e)}")
#         return jsonify({'error': str(e), 'success': False}), 500
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)


# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=5001, debug=True)







# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import numpy as np
# import cv2
# import insightface
# import os
# import torch
# from speechbrain.inference.speaker import SpeakerRecognition
# # Note: Removed unused 'EncoderClassifier' import
# import logging
# # Note: Removed unused 'torchaudio', 'soundfile', and 'io' imports
# import librosa
# from scipy.stats import skew, kurtosis
# import warnings

# warnings.filterwarnings('ignore')

# app = Flask(__name__)
# CORS(app)

# # --- Configuration ---
# # CRITICAL: This threshold is empirical. You MUST tune this value.
# # Test with your camera:
# # 1. Check the log for a REAL face (e.g., "Liveness: 500.2")
# # 2. Check the log for a SPOOF face (e.g., "Liveness: 45.1")
# # 3. Set your threshold somewhere in between (e.g., 100)
# LIVENESS_THRESHOLD = 200.0

# # Load ArcFace face model
# face_model = insightface.app.FaceAnalysis(name='buffalo_l')
# face_model.prepare(ctx_id=0, det_size=(640, 640))

# # Setup logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # Load ECAPA-TDNN voice model
# try:
#     # Use SpeakerRecognition model specifically for speaker verification
#     voice_model = SpeakerRecognition.from_hparams(
#         source="speechbrain/spkrec-ecapa-voxceleb",
#         savedir="pretrained_models/spkrec-ecapa-voxceleb"
#     )
# except Exception as e:
#     logger.error(f"Model initialization error: {str(e)}")
#     raise

# def extract_voice_features(waveform, sample_rate):
#     """Extract comprehensive voice features for speaker verification"""
#     # (Function is unchanged)
#     try:
#         # Fundamental frequency features
#         f0, voiced_flag, voiced_probs = librosa.pyin(
#             waveform,
#             fmin=librosa.note_to_hz('C2'),
#             fmax=librosa.note_to_hz('C7')
#         )

#         # Spectral features
#         spectral_centroids = librosa.feature.spectral_centroid(y=waveform, sr=sample_rate)[0]
#         spectral_rolloff = librosa.feature.spectral_rolloff(y=waveform, sr=sample_rate)[0]

#         # MFCC features with deltas
#         mfccs = librosa.feature.mfcc(y=waveform, sr=sample_rate, n_mfcc=20)
#         mfcc_deltas = librosa.feature.delta(mfccs)
#         mfcc_delta2s = librosa.feature.delta(mfccs, order=2)

#         # Vocal tract features
#         formants = librosa.effects.preemphasis(waveform)

#         features = {
#             'f0_stats': {
#                 'mean': float(np.nanmean(f0)),
#                 'std': float(np.nanstd(f0)),
#                 'skew': float(skew(f0[~np.isnan(f0)])),
#                 'kurtosis': float(kurtosis(f0[~np.isnan(f0)]))
#             },
#             'spectral_stats': {
#                 'centroid_mean': float(np.mean(spectral_centroids)),
#                 'centroid_std': float(np.std(spectral_centroids)),
#                 'rolloff_mean': float(np.mean(spectral_rolloff))
#             },
#             'mfcc_stats': {
#                 'mean': float(np.mean(mfccs)),
#                 'std': float(np.std(mfccs)),
#                 'delta_mean': float(np.mean(mfcc_deltas)),
#                 'delta2_mean': float(np.mean(mfcc_delta2s))
#             },
#             'voice_characteristics': {
#                 'formant_mean': float(np.mean(formants)),
#                 'formant_std': float(np.std(formants)),
#                 'voiced_probability': float(np.mean(voiced_probs))
#             }
#         }

#         return features, True

#     except Exception as e:
#         logger.error(f"Feature extraction error: {str(e)}")
#         return None, False


# # ---------------- FACE EMBEDDING ROUTE (UPDATED) ------------------
# @app.route('/embed', methods=['POST'])
# def get_face_embedding():
#     if 'image' not in request.files:
#         return jsonify({'error': 'Image file missing'}), 400

#     file = request.files['image']
#     img_buffer = file.read()
#     img_array = np.frombuffer(img_buffer, np.uint8)
    
#     # FIX: Removed the 'T' that was causing a SyntaxError
#     img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

#     if img is None:
#         return jsonify({'error': 'Could not decode image'}), 400

#     # --- 1. Face Detection ---
#     faces = face_model.get(img)
#     if not faces:
#         return jsonify({'error': 'No face detected'}), 400

#     # We only care about the largest face
#     face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]

#     # --- 2. Passive Liveness Check (Texture Analysis) ---
#     try:
#         # Get the bounding box of the face
#         bbox = face.bbox.astype(int)
#         # Ensure bounding box is within image bounds
#         y1, x1, y2, x2 = max(0, bbox[1]), max(0, bbox[0]), min(img.shape[0], bbox[3]), min(img.shape[1], bbox[2])

#         # Crop the face from the original image
#         face_crop = img[y1:y2, x1:x2]

#         if face_crop.size == 0:
#             logger.warning("Face crop was empty, skipping liveness check.")
#             return jsonify({'error': 'Face detection error'}), 400

#         # Convert to grayscale for texture analysis
#         gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

#         # Calculate the variance of the Laplacian (a measure of texture/blur)
#         lap_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()

#         # Log the result for tuning
#         logger.debug(f"Liveness (Laplacian Variance): {lap_var}")

#         # Check against the threshold
#         if lap_var < LIVENESS_THRESHOLD:
#             logger.warning(f"SPOOF ATTEMPT DETECTED. Liveness score: {lap_var} < {LIVENESS_THRESHOLD}")
#             return jsonify({'error': 'Liveness check failed. Please use a real face.'}), 403 # 403 Forbidden

#         logger.info(f"Liveness check passed. Score: {lap_var}")

#     except Exception as e:
#         logger.error(f"Error during liveness check: {str(e)}")
#         return jsonify({'error': 'Internal server error during liveness check'}), 500

#     # --- 3. Get Embedding (Only if Liveness Check Passed) ---
#     embedding = face.embedding.tolist()
#     return jsonify({'embedding': embedding})


# # ---------------- VOICE VERIFICATION ROUTE ------------------
# # (This route is unchanged, aside from fixing syntax errors)
# @app.route('/voice-verify', methods=['POST'])
# def verify_voice():
#     temp_path = 'temp_audio.wav'
#     if 'audio' not in request.files:
#         return jsonify({'error': 'No audio file provided'}), 400

#     try:
#         audio_file = request.files['audio']
#         audio_file.save(temp_path)

#         # Load and preprocess audio
#         waveform, sample_rate = librosa.load(temp_path, sr=16000)

#         # FIX: Removed the 'dot_chart_data' line that was causing a SyntaxError

#         # Voice activity detection
#         intervals = librosa.effects.split(waveform, top_db=20)
#         if len(intervals) == 0:
#             return jsonify({'error': 'No voice detected'}), 400

#         # Extract voiced segments
#         voiced_segments = []
#         for start, end in intervals:
#             voiced_segments.append(waveform[start:end])
#         waveform = np.concatenate(voiced_segments)

#         # Normalize audio
#         waveform = librosa.util.normalize(waveform)

#         # Get speaker embedding
#         waveform_tensor = torch.FloatTensor(waveform).unsqueeze(0)
#         with torch.no_grad():
#             embedding = voice_model.encode_batch(waveform_tensor)
#             embedding_vector = embedding.squeeze().cpu().numpy()

#         # Extract biometric features
#         voice_features, success = extract_voice_features(waveform, sample_rate)
#         if not success:
#             return jsonify({'error': 'Failed to extract voice features'}), 400

#         response_data = {
#             'embedding': embedding_vector.tolist(),
#             'voice_features': voice_features,
#             'success': True
#         }

#         return jsonify(response_data)

#     except Exception as e:
#         logger.error(f"Error processing voice: {str(e)}")
#         return jsonify({'error': str(e), 'success': False}), 500
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)


# if __name__ == '__main__':
#     # FIX: Removed the 'Read Me' line that was causing a SyntaxError
#     app.run(host='127.0.0.1', port=5001, debug=True)






#updated face and voice


from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import insightface
import os
import logging
import warnings
warnings.filterwarnings('ignore')

# Conditional imports for voice authentication
try:
    import torch
    from speechbrain.inference.speaker import SpeakerRecognition
    import librosa
    from scipy.stats import skew, kurtosis
    VOICE_ENABLED = True
    print("✅ Voice authentication libraries loaded successfully")
except Exception as e:
    VOICE_ENABLED = False
    print(f"⚠️ Voice authentication disabled: {str(e)}")
    print("   Face authentication will still work.")

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# Face Liveness Threshold (Tune this value)
# Lowered from 200.0 to 50.0 for webcam compatibility (typical webcam variance: 50-150)
LIVENESS_THRESHOLD = 50.0

# Voice Liveness Thresholds (Tune these values)
# These are starting guesses. You MUST tune them by checking your logs.
VOICE_LIVENESS_THRESHOLDS = {
    "f0_std_min": 1.5,      # Real voice should have pitch variation > 1.5 Hz
    "rolloff_mean_min": 1000.0, # Real voice should have frequencies > 1000 Hz
    "voiced_prob_min": 0.04    # At least 40% of frames should be "voiced"
}

# Load ArcFace face model
face_model = insightface.app.FaceAnalysis(name='buffalo_l')
# ... (rest of model loading and logging setup is unchanged) ...
face_model.prepare(ctx_id=0, det_size=(640, 640))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load ECAPA-TDNN voice model (only if voice is enabled)
voice_model = None
if VOICE_ENABLED:
    try:
        voice_model = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa-voxceleb"
        )
        logger.info("✅ Voice model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Voice model initialization error: {str(e)}")
        logger.info("   Face authentication will still work.")
        voice_model = None

def extract_voice_features(waveform, sample_rate):
    """Extract comprehensive voice features for speaker verification"""
    # (Function is unchanged)
    try:
        # Fundamental frequency features
        f0, voiced_flag, voiced_probs = librosa.pyin(
            waveform,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7')
        )

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=waveform, sr=sample_rate)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=waveform, sr=sample_rate)[0]

        # MFCC features with deltas
        mfccs = librosa.feature.mfcc(y=waveform, sr=sample_rate, n_mfcc=20)
        mfcc_deltas = librosa.feature.delta(mfccs)
        mfcc_delta2s = librosa.feature.delta(mfccs, order=2)

        # Vocal tract features
        formants = librosa.effects.preemphasis(waveform)

        features = {
            'f0_stats': {
                'mean': float(np.nanmean(f0)),
                'std': float(np.nanstd(f0)),
                'skew': float(skew(f0[~np.isnan(f0)])),
                'kurtosis': float(kurtosis(f0[~np.isnan(f0)]))
            },
            'spectral_stats': {
                'centroid_mean': float(np.mean(spectral_centroids)),
                'centroid_std': float(np.std(spectral_centroids)),
                'rolloff_mean': float(np.mean(spectral_rolloff))
            },
            'mfcc_stats': {
                'mean': float(np.mean(mfccs)),
                'std': float(np.std(mfccs)),
                'delta_mean': float(np.mean(mfcc_deltas)),
                'delta2_mean': float(np.mean(mfcc_delta2s))
            },
            'voice_characteristics': {
                'formant_mean': float(np.mean(formants)),
                'formant_std': float(np.std(formants)),
                'voiced_probability': float(np.mean(voiced_probs))
            }
        }

        return features, True

    except Exception as e:
        logger.error(f"Feature extraction error: {str(e)}")
        return None, False

# --- NEW: Voice Liveness Check Function ---
def check_voice_liveness(voice_features):
    """
    Analyzes extracted features to detect potential replay attacks.
    Returns (is_live, failure_reason)
    """
    try:
        f0_std = voice_features['f0_stats']['std']
        rolloff_mean = voice_features['spectral_stats']['rolloff_mean']
        voiced_prob = voice_features['voice_characteristics']['voiced_probability']

        # Log the values for tuning
        logger.debug(f"Voice Liveness Scores: F0_Std={f0_std:.2f}, Rolloff={rolloff_mean:.2f}, VoicedProb={voiced_prob:.2f}")

        # Check 1: Pitch Variation
        if f0_std < VOICE_LIVENESS_THRESHOLDS["f0_std_min"]:
            reason = f"Pitch variation too low ({f0_std:.2f} < {VOICE_LIVENESS_THRESHOLDS['f0_std_min']})"
            return False, reason

        # Check 2: Frequency Range
        if rolloff_mean < VOICE_LIVENESS_THRESHOLDS["rolloff_mean_min"]:
            reason = f"Spectral rolloff too low ({rolloff_mean:.2f} < {VOICE_LIVENESS_THRESHOLDS['rolloff_mean_min']})"
            return False, reason

        # Check 3: Voiced Probability
        if voiced_prob < VOICE_LIVENESS_THRESHOLDS["voiced_prob_min"]:
            reason = f"Voiced probability too low ({voiced_prob:.2f} < {VOICE_LIVENESS_THRESHOLDS['voiced_prob_min']})"
            return False, reason

        # If all checks pass
        return True, "Voice appears live"

    except Exception as e:
        logger.error(f"Error during voice liveness check: {str(e)}")
        return False, "Liveness check processing error"


# ---------------- FACE EMBEDDING ROUTE (UPDATED) ------------------
@app.route('/embed', methods=['POST'])
def get_face_embedding():
    # ... (This function remains unchanged from the previous version) ...
    if 'image' not in request.files:
        return jsonify({'error': 'Image file missing'}), 400

    file = request.files['image']
    img_buffer = file.read()
    # Note: Renamed to img_array to avoid confusion with 'img' variable
    img_array = np.frombuffer(img_buffer, np.uint8) 
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({'error': 'Could not decode image'}), 400

    # --- 1. Face Detection ---
    faces = face_model.get(img)
    if not faces:
        return jsonify({'error': 'No face detected'}), 400

    # We only care about the largest face
    face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]

    # --- 2. Passive Liveness Check (Texture Analysis) ---
    try:
        # Get the bounding box of the face
        bbox = face.bbox.astype(int)
        # Ensure bounding box is within image bounds
        y1, x1, y2, x2 = max(0, bbox[1]), max(0, bbox[0]), min(img.shape[0], bbox[3]), min(img.shape[1], bbox[2])

        # Crop the face from the original image
        face_crop = img[y1:y2, x1:x2]

        if face_crop.size == 0:
            logger.warning("Face crop was empty, skipping liveness check.")
            return jsonify({'error': 'Face detection error'}), 400

        # Convert to grayscale for texture analysis
        gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

        # Calculate the variance of the Laplacian (a measure of texture/blur)
        lap_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()

        # Log the result for tuning
        logger.debug(f"Liveness (Laplacian Variance): {lap_var}")

        # FIX: Removed stray '.'
        # Check against the threshold
        if lap_var < LIVENESS_THRESHOLD:
            logger.warning(f"SPOOF ATTEMPT DETECTED. Liveness score: {lap_var} < {LIVENESS_THRESHOLD}")
            return jsonify({'error': 'Liveness check failed. Please use a real face.'}), 403 # 403 Forbidden

        logger.info(f"Liveness check passed. Score: {lap_var}")

    except Exception as e:
        logger.error(f"Error during liveness check: {str(e)}")
        return jsonify({'error': 'Internal server error during liveness check'}), 500

    # --- 3. Get Embedding (Only if Liveness Check Passed) ---
    embedding = face.embedding.tolist()
    return jsonify({'embedding': embedding})


# ---------------- VOICE VERIFICATION ROUTE (UPDATED) ------------------
@app.route('/voice-verify', methods=['POST'])
def verify_voice():
    # Check if voice authentication is enabled
    if not VOICE_ENABLED or voice_model is None:
        return jsonify({
            'error': 'Voice authentication is currently disabled due to missing dependencies',
            'success': False
        }), 503
    
    temp_path = 'temp_audio.wav'
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    try:
        audio_file = request.files['audio']
        audio_file.save(temp_path)

        # Load and preprocess audio
        waveform, sample_rate = librosa.load(temp_path, sr=16000)

        # Voice activity detection
        intervals = librosa.effects.split(waveform, top_db=20)
        if len(intervals) == 0:
            return jsonify({'error': 'No voice detected'}), 400

        # Extract voiced segments
        voiced_segments = []
        for start, end in intervals:
            voiced_segments.append(waveform[start:end])
        
        if not voiced_segments:
             return jsonify({'error': 'No voiced segments found after VAD'}), 400
        
        waveform = np.concatenate(voiced_segments)

        # Normalize audio
        waveform = librosa.util.normalize(waveform)

        # --- 1. Extract Biometric Features ---
        voice_features, success = extract_voice_features(waveform, sample_rate)
        if not success:
            return jsonify({'error': 'Failed to extract voice features'}), 400

        # --- 2. Passive Liveness Check ---
        is_live, failure_reason = check_voice_liveness(voice_features)
        if not is_live:
            logger.warning(f"SPOOF ATTEMPT DETECTED (VOICE). Reason: {failure_reason}")
            return jsonify({'error': f'Liveness check failed: {failure_reason}'}), 403

        logger.info("Voice liveness check passed.")

        # --- 3. Get Speaker Embedding (Only if Liveness Check Passed) ---
        if voice_model is None:
            return jsonify({'error': 'Voice model not loaded'}), 500
            
        waveform_tensor = torch.FloatTensor(waveform).unsqueeze(0)
        with torch.no_grad():
            embedding = voice_model.encode_batch(waveform_tensor)
            embedding_vector = embedding.squeeze().cpu().numpy()

        response_data = {
            'embedding': embedding_vector.tolist(),
            'voice_features': voice_features,
            'success': True
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing voice: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)