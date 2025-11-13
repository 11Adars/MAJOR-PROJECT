from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import cv2
import numpy as np
import tensorflow as tf
import os
import mediapipe as mp
from ctransformers import AutoModelForCausalLM
import time
import json
import base64

app = Flask(__name__)
CORS(app)

# --- Configuration ---
SEQUENCE_LENGTH = 30
NUM_FEATURES = 300
PROCESSED_PATH = "processed_data_landmarks"
MODEL_SAVE_PATH = "saved_model_landmarks"
BEST_MODEL_FILENAME = "best_landmark_model.keras"
PREDICTION_THRESHOLD = 0.5

# --- SLM Configuration ---
SLM_MODEL_NAME = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
SLM_MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
SLM_CACHE_PATH = "slm_model_cache"

# --- Custom Focal Loss ---
import tensorflow.keras.backend as K

class FocalLoss(tf.keras.losses.Loss):
    def __init__(self, alpha=0.25, gamma=2.0, name='focal_loss'):
        super().__init__(name=name)
        self.alpha = alpha
        self.gamma = gamma
    
    def call(self, y_true, y_pred):
        epsilon = K.epsilon()
        y_pred = K.clip(y_pred, epsilon, 1. - epsilon)
        cross_entropy = -y_true * K.log(y_pred)
        loss = self.alpha * K.pow(1. - y_pred, self.gamma) * cross_entropy
        return K.sum(loss, axis=-1)

# --- Load Sign Language Model ---
print("Loading Sign Language model and labels...")
MODEL_PATH = os.path.join(MODEL_SAVE_PATH, BEST_MODEL_FILENAME)
try:
    custom_objects = {"FocalLoss": FocalLoss}
    sign_model = tf.keras.models.load_model(MODEL_PATH, custom_objects=custom_objects, compile=False)
    sign_labels = np.load(os.path.join(PROCESSED_PATH, 'sign_labels.npy'))
    print(f"Best landmark model '{BEST_MODEL_FILENAME}' and labels loaded.")
except FileNotFoundError:
    print(f"\n--- Error: Model File Not Found ---")
    print(f"Model checkpoint file not found at: {MODEL_PATH}")
    sign_model = None
    sign_labels = None
except Exception as e:
    print(f"\n--- Error Loading Sign Model ---: {e}")
    sign_model = None
    sign_labels = None

# --- Load Small Language Model (SLM) ---
print(f"Loading SLM: '{SLM_MODEL_NAME}'...")
if not os.path.exists(SLM_CACHE_PATH):
    os.makedirs(SLM_CACHE_PATH)
try:
    slm_model = AutoModelForCausalLM.from_pretrained(
        SLM_MODEL_NAME,
        model_file=SLM_MODEL_FILE,
        model_type="llama",
        local_files_only=False,
    )
    print("SLM (GGUF) loaded successfully.")
except Exception as e:
    print(f"Error loading SLM: {e}")
    slm_model = None

# --- MediaPipe Initialization ---
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def extract_live_landmarks(results):
    """Extract landmarks into a flat numpy array."""
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
    lh = np.array([[res.x, res.y, res.z, res.visibility] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 4)
    rh = np.array([[res.x, res.y, res.z, res.visibility] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 4)
    return np.concatenate([pose, lh, rh])

def generate_sentence(keywords):
    """Uses the loaded ctransformers SLM to convert keywords into a natural sentence."""
    if not slm_model:
        return "SLM NOT LOADED."

    keyword_string = ", ".join(keywords)
    
    system_prompt = "You are a helpful banking assistant. Convert keyword lists into a single, complete sentence."
    
    prompt = (
        f"<|system|>\n{system_prompt}</s>\n"
        f"<|user|>\nKeywords: [MY, CARD, MISSING]</s>\n"
        f"<|assistant|>\nMy card is missing.</s>\n"
        f"<|user|>\nKeywords: [HELP, ONLINE, ACCOUNT]</s>\n"
        f"<|assistant|>\nI need help with my online account.</s>\n"
        f"<|user|>\nKeywords: [LOAN, STATUS]</s>\n"
        f"<|assistant|>\nWhat is the status of my loan?</s>\n"
        f"<|user|>\nKeywords: [{keyword_string}]</s>\n"
        f"<|assistant|>\n"
    )

    print(f"\n--- Sending to SLM ---")
    print(f"Prompt: {prompt}")
    
    start_time = time.time()
    final_sentence = slm_model(
        prompt, 
        max_new_tokens=50, 
        stop=["</s>", "<|user|>"],
        temperature=0.3
    )
    end_time = time.time()
    
    print(f"SLM generation took {end_time - start_time:.2f} seconds.")
    final_sentence = final_sentence.strip()
    print(f"SLM Output: {final_sentence}")
    
    return final_sentence

# Global state for recording
recording_state = {
    'recording_sequence': [],
    'sentence_keywords': [],
    'is_recording': False,
    'current_prediction': '',
    'confidence': 0.0,
    'status_text': 'Press [SPACE] to record',
    'slm_output_text': ''
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict_sign():
    """Process recorded sequence and predict sign."""
    if sign_model is None or sign_labels is None:
        return jsonify({'error': 'Sign model not loaded'}), 500
    
    data = request.json
    recording_sequence = data.get('sequence', [])
    
    if len(recording_sequence) < SEQUENCE_LENGTH // 2:
        return jsonify({'error': 'Recording too short', 'success': False})
    
    try:
        # Resample the recorded frames to match model input length
        indices = np.linspace(0, len(recording_sequence) - 1, SEQUENCE_LENGTH, dtype=int)
        sequence_to_predict = [recording_sequence[i] for i in indices]
        sequence_np = np.array(sequence_to_predict)
        sequence_np = np.nan_to_num(sequence_np, nan=0.0, posinf=1e9, neginf=-1e9)
        input_data = np.expand_dims(sequence_np, axis=0)
        
        prediction = sign_model.predict(input_data, verbose=0)[0]
        pred_index = np.argmax(prediction)
        confidence = float(prediction[pred_index])
        
        if confidence >= PREDICTION_THRESHOLD:
            current_prediction = sign_labels[pred_index]
            return jsonify({
                'success': True,
                'prediction': current_prediction,
                'confidence': confidence
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Prediction uncertain',
                'confidence': confidence
            })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/generate-sentence', methods=['POST'])
def generate_sentence_api():
    """Generate sentence from keywords using SLM."""
    data = request.json
    keywords = data.get('keywords', [])
    
    if not keywords:
        return jsonify({'error': 'No keywords provided', 'success': False})
    
    try:
        sentence = generate_sentence(keywords)
        return jsonify({
            'success': True,
            'sentence': sentence
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/submit-to-support', methods=['POST'])
def submit_to_support():
    """Submit generated query to backend support system."""
    data = request.json
    query_text = data.get('query_text', '')
    auth_token = data.get('token', '')
    
    if not query_text:
        return jsonify({'error': 'No query text provided', 'success': False}), 400
    
    if not auth_token:
        return jsonify({'error': 'Authentication token required', 'success': False}), 401
    
    try:
        import requests
        
        # Forward to backend API
        backend_url = 'http://127.0.0.1:5000/api/support/tickets'
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'query_text': query_text,
            'query_source': 'sign_language'
        }
        
        response = requests.post(backend_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            result = response.json()
            return jsonify({
                'success': True,
                'message': 'Query submitted successfully',
                'ticket_id': result.get('ticket', {}).get('id')
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('message', 'Failed to submit query')
            }), response.status_code
            
    except Exception as e:
        print(f"Error submitting to support: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/process-frame', methods=['POST'])
def process_frame():
    """Process a single frame and extract landmarks."""
    data = request.json
    frame_data = data.get('frame', '')
    
    try:
        # Decode base64 image
        frame_bytes = base64.b64decode(frame_data.split(',')[1])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Process with MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = holistic.process(image_rgb)
        
        # Extract landmarks
        landmarks = extract_live_landmarks(results)
        
        # Draw landmarks on frame
        image_rgb.flags.writeable = True
        display_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(
            display_frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
        mp_drawing.draw_landmarks(
            display_frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style()
        )
        mp_drawing.draw_landmarks(
            display_frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style()
        )
        
        # Encode processed frame back to base64
        _, buffer = cv2.imencode('.jpg', display_frame)
        processed_frame = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'landmarks': landmarks.tolist(),
            'processed_frame': f'data:image/jpeg;base64,{processed_frame}'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'sign_model_loaded': sign_model is not None,
        'slm_model_loaded': slm_model is not None
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
