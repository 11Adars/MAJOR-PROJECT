from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import insightface
import os
import io 
import torch 
from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.inference import EncoderClassifier  
import logging 
import torchaudio
import soundfile as sf
import librosa
from scipy.stats import skew, kurtosis
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Load ArcFace face model
face_model = insightface.app.FaceAnalysis(name='buffalo_l')
face_model.prepare(ctx_id=0, det_size=(640, 640))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load ECAPA-TDNN voice model
try:
   # Use SpeakerRecognition model specifically for speaker verification
    voice_model = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb"
    )
except Exception as e:
    logger.error(f"Model initialization error: {str(e)}")
    raise

def extract_voice_features(waveform, sample_rate):
    """Extract comprehensive voice features for speaker verification"""
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





# ---------------- FACE EMBEDDING ROUTE ------------------
@app.route('/embed', methods=['POST'])
def get_face_embedding():
    if 'image' not in request.files:
        return jsonify({'error': 'Image file missing'}), 400

    file = request.files['image']
    img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    faces = face_model.get(img)
    if not faces:
        return jsonify({'error': 'No face detected'}), 400

    embedding = faces[0].embedding.tolist()
    return jsonify({'embedding': embedding})


# ---------------- VOICE VERIFICATION ROUTE ------------------



@app.route('/voice-verify', methods=['POST'])
def verify_voice():
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
        waveform = np.concatenate(voiced_segments)
        
        # Normalize audio
        waveform = librosa.util.normalize(waveform)
        
        # Get speaker embedding
        waveform_tensor = torch.FloatTensor(waveform).unsqueeze(0)
        with torch.no_grad():
            embedding = voice_model.encode_batch(waveform_tensor)
            embedding_vector = embedding.squeeze().cpu().numpy()
            
        # Extract biometric features
        voice_features, success = extract_voice_features(waveform, sample_rate)
        if not success:
            return jsonify({'error': 'Failed to extract voice features'}), 400
            
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
    app.run(host='127.0.0.1', port=5001, debug=True)