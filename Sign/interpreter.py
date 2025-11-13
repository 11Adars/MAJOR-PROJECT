import cv2
import numpy as np
import tensorflow as tf
import os
import collections
import time
import mediapipe as mp
# Import from ctransformers
from ctransformers import AutoModelForCausalLM

# --- Configuration ---
SEQUENCE_LENGTH = 30
NUM_FEATURES = 300
PROCESSED_PATH = "processed_data_landmarks"
MODEL_SAVE_PATH = "saved_model_landmarks"
BEST_MODEL_FILENAME = "best_landmark_model.keras"
PREDICTION_THRESHOLD = 0.7
SENTENCE_HISTORY_LENGTH = 10

# --- SLM Configuration (NEW - TinyLlama) ---
# This is a 100% open, non-gated model. It will download without any 401 errors.
SLM_MODEL_NAME = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
# We select a small quantized file (Q4_K_M)
SLM_MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
SLM_CACHE_PATH = "slm_model_cache" # We will re-use the same cache folder
print(f"Using device: CPU (Optimized with ctransformers)")

# --- Custom Focal Loss (Needed for loading the sign model) ---
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

# --- 1. Load Sign Language Model ---
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
    print("Ensure training with '2_train_landmark_model.py' completed successfully.")
    exit()
except Exception as e:
    print(f"\n--- Error Loading Sign Model ---: {e}"); exit()

# --- 2. Load Small Language Model (SLM) ---
print(f"Loading SLM: '{SLM_MODEL_NAME}'...")
print(f"Model will be saved to/loaded from: '{SLM_CACHE_PATH}'")
# Create the cache directory if it doesn't exist
if not os.path.exists(SLM_CACHE_PATH):
    os.makedirs(SLM_CACHE_PATH)
try:
    # Use ctransformers AutoModelForCausalLM
    slm_model = AutoModelForCausalLM.from_pretrained(
        SLM_MODEL_NAME,
        model_file=SLM_MODEL_FILE, # Specify the exact file to download
        model_type="llama",         # <-- CHANGED model type to 'llama'
        local_files_only=False,     # Set to True after first download
        # gpu_layers=0              # Set to 50 if you have a GPU, 0 for CPU-only
    )
    print("SLM (GGUF) loaded successfully.")
except Exception as e:
    print(f"Error loading SLM. Do you have 'ctransformers' installed? Error: {e}")
    print("SLM will be disabled for this session.")
    slm_model = None

# --- 3. MediaPipe Initialization ---
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def extract_live_landmarks(results):
    """ Helper to extract landmarks into a flat numpy array. """
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
    lh = np.array([[res.x, res.y, res.z, res.visibility] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 4)
    rh = np.array([[res.x, res.y, res.z, res.visibility] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 4)
    return np.concatenate([pose, lh, rh])

# --- 4. SLM Generation Function (NEW "FEW-SHOT" PROMPT) ---
def generate_sentence(keywords):
    """
    Uses the loaded ctransformers SLM to convert keywords into a natural sentence.
    """
    if not slm_model:
        return "SLM NOT LOADED."

    # Create the prompt for the SLM
    keyword_string = ", ".join(keywords)
    
    # --- NEW "FEW-SHOT" PROMPT ---
    # We show the model examples of what we want. This is much more effective
    # for small models than long, complex instructions.
    
    system_prompt = (
        "You are a helpful banking assistant. Convert keyword lists into a single, complete sentence."
    )
    
    # Manually create the prompt in Llama-2-Chat format (which TinyLlama uses)
    prompt = (
        f"<|system|>\n{system_prompt}</s>\n"
        f"<|user|>\nKeywords: [MY, CARD, MISSING]</s>\n"
        f"<|assistant|>\nMy card is missing.</s>\n" # Example 1
        f"<|user|>\nKeywords: [HELP, ONLINE, ACCOUNT]</s>\n"
        f"<|assistant|>\nI need help with my online account.</s>\n" # Example 2
        f"<|user|>\nKeywords: [LOAN, STATUS]</s>\n"
        f"<|assistant|>\nWhat is the status of my loan?</s>\n" # Example 3
        f"<|user|>\nKeywords: [{keyword_string}]</s>\n" # Our actual query
        f"<|assistant|>\n"
    )
    # --- END NEW PROMPT ---

    print(f"\n--- Sending to SLM (Locally via ctransformers) ---")
    print(f"Prompt: {prompt}")

    # Generate the output locally
    print("SLM is thinking... (Running on CPU, should be fast!)")
    start_time = time.time()
    
    # Generate text using the ctransformers model
    final_sentence = slm_model(
        prompt, 
        max_new_tokens=50, 
        stop=["</s>", "<|user|>"], # Stop generating when it finishes or tries to start a new turn
        temperature=0.3 # Make it less "creative" and more direct
    )

    end_time = time.time()
    print(f"SLM generation took {end_time - start_time:.2f} seconds.")
    
    final_sentence = final_sentence.strip()
    
    print(f"SLM Output: {final_sentence}")
    print("--------------------------------\n")
    return final_sentence

# --- 5. Main Application Loop (Identical to before) ---
recording_sequence = []
sentence_keywords = [] # List for keywords (e.g., ['MY', 'LOAN'])
current_prediction = ""
confidence = 0.0
is_recording = False
status_text = "Press [SPACE] to record"
slm_output_text = "" # This will hold the final generated sentence

cap = cv2.VideoCapture(0)
if not cap.isOpened(): print("Error: Could not open webcam."); exit()

print("\nStarting Interpreter...")
print("Controls:")
print("  [SPACE] : Start / Stop Recording Sign")
print("  [ENTER] : Process Keywords with SLM")
print("  [c]     : Clear Last Keyword")
print("  [x]     : Clear All Keywords")
print("  [q]     : Quit")

while True:
    ret, frame = cap.read()
    if not ret: print("Error: Failed to capture frame."); break
    display_frame = frame.copy()

    try:
        # Process with MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = holistic.process(image_rgb)
        
        # Draw landmarks
        image_rgb.flags.writeable = True
        display_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(display_frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS, landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        mp_drawing.draw_landmarks(display_frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style())
        mp_drawing.draw_landmarks(display_frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style())

        # Extract landmark vector for recording
        current_landmarks = extract_live_landmarks(results)
        
        if is_recording:
            recording_sequence.append(current_landmarks)
            status_text = "RECORDING..."

        key = cv2.waitKey(1) & 0xFF

        # --- [SPACE] Start/Stop Recording ---
        if key == ord(' '):
            if not is_recording:
                is_recording = True
                recording_sequence = []
                status_text = "RECORDING..."
                slm_output_text = "" # Clear old sentence
                print("Started recording...")
            else:
                is_recording = False
                print("Stopped recording. Processing sign...")
                if len(recording_sequence) < SEQUENCE_LENGTH // 2:
                    status_text = "Recording too short."
                else:
                    # Resample the recorded frames to match model input length
                    indices = np.linspace(0, len(recording_sequence) - 1, SEQUENCE_LENGTH, dtype=int)
                    sequence_to_predict = [recording_sequence[i] for i in indices]
                    sequence_np = np.array(sequence_to_predict)
                    sequence_np = np.nan_to_num(sequence_np, nan=0.0, posinf=1e9, neginf=-1e9)
                    input_data = np.expand_dims(sequence_np, axis=0)
                    
                    try:
                        prediction = sign_model.predict(input_data, verbose=0)[0]
                        pred_index = np.argmax(prediction)
                        confidence = prediction[pred_index]

                        if confidence >= PREDICTION_THRESHOLD:
                            current_prediction = sign_labels[pred_index]
                            sentence_keywords.append(current_prediction) # Add to keyword list
                            status_text = f"Added: {current_prediction.upper()}"
                        else:
                            status_text = "Prediction uncertain."
                        print(f"Prediction: {current_prediction} (Conf: {confidence:.2f})")
                    except Exception as e:
                        status_text = "Sign Prediction Error"
                recording_sequence = []

        # --- [ENTER] Process sentence with SLM ---
        elif key == 13: # 13 is the Enter key
            if sentence_keywords:
                print("Sending keywords to SLM...")
                status_text = "Thinking... (CPU-Optimized)"
                # This call will now be much faster
                slm_output_text = generate_sentence(sentence_keywords)
                status_text = "Query Generated."
            else:
                status_text = "No keywords to process."

        # --- [c] Clear Last Word ---
        elif key == ord('c'):
            if sentence_keywords:
                removed_word = sentence_keywords.pop()
                status_text = f"Removed '{removed_word}'"
                slm_output_text = ""
            else:
                status_text = "Keyword list empty"

        # --- [x] Clear All ---
        elif key == ord('x'):
            sentence_keywords = []
            current_prediction = ""
            slm_output_text = ""
            status_text = "All cleared. Press [SPACE]"
            
        # --- [q] Quit ---
        elif key == ord('q'):
            print("Quitting..."); break

    except Exception as e_generic:
        print(f"Generic error in loop: {e_generic}"); continue

    # --- Display UI ---
    # Display Status (RECORDING... / Press [SPACE]...)
    cv2.putText(display_frame, status_text, (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(display_frame, status_text, (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255) if is_recording else (255, 255, 255), 2, cv2.LINE_AA)

    # Display Controls
    controls_text = "[SPACE]=Rec | [ENTER]=Submit | [c]=Undo | [x]=Clear | [q]=Quit"
    cv2.putText(display_frame, controls_text, (10, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(display_frame, controls_text, (10, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    # Display Keyword list (Green text)
    sentence_display = ' '.join(sentence_keywords)
    cv2.putText(display_frame, f"Keywords: {sentence_display}", (10, display_frame.shape[0] - 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(display_frame, f"Keywords: {sentence_display}", (10, display_frame.shape[0] - 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)

    # Display Final SLM Sentence (Light blue text)
    cv2.putText(display_frame, f"Query: {slm_output_text}", (10, display_frame.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(display_frame, f"Query: {slm_output_text}", (10, display_frame.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2, cv2.LINE_AA)

    cv2.imshow('Landmark Sign Language Interpreter', display_frame)

cap.release()
cv2.destroyAllWindows()
holistic.close()
print("\nInterpreter stopped.")