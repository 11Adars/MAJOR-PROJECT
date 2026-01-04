# BankAssist AI - Complete Model Algorithms

## Table of Contents
1. [Face Recognition Algorithm (ArcFace)](#1-face-recognition-algorithm)
2. [Voice Recognition Algorithm (ECAPA-TDNN)](#2-voice-recognition-algorithm)
3. [Sign Language Recognition Algorithm (LSTM)](#3-sign-language-recognition-algorithm)
4. [Natural Language Generation Algorithm (TinyLlama)](#4-natural-language-generation-algorithm)
5. [Authentication Algorithms](#5-authentication-algorithms)

---

## 1. FACE RECOGNITION ALGORITHM

### 1.1 Face Registration Algorithm

```
Algorithm: FACE_REGISTRATION
Input: username, email, image_file
Output: success_status, jwt_token

1. BEGIN
2.   LOAD image_file from request
3.   CREATE FormData object
4.   APPEND image to FormData
5.   
6.   SEND POST request to Python service (http://127.0.0.1:5001/embed)
7.   RECEIVE face_embedding (512-dimensional vector)
8.   
9.   IF face_embedding is NULL THEN
10.      RETURN error "No face detected"
11.  END IF
12.  
13.  EXECUTE SQL:
14.      INSERT INTO users (username, email, face_embedding) 
15.      VALUES (username, email, face_embedding)
16.      RETURNING user_id
17.  
18.  token ← GENERATE_JWT_TOKEN(user_id)
19.  RETURN {success: true, token: token}
20. END
```

### 1.2 Face Embedding Extraction Algorithm (ArcFace)

```
Algorithm: EXTRACT_FACE_EMBEDDING
Input: image (RGB format)
Output: embedding (512-dim vector) OR error

1. BEGIN
2.   IF image is NULL OR invalid THEN
3.       RETURN error "Image file missing"
4.   END IF
5.   
6.   img_buffer ← READ image file
7.   img_array ← DECODE img_buffer to numpy array (uint8)
8.   img ← DECODE img_array using cv2.imdecode()
9.   
10.  IF img is NULL THEN
11.      RETURN error "Could not decode image"
12.  END IF
13.  
14.  // Face Detection
15.  faces[] ← face_model.get(img)  // ArcFace buffalo_l model
16.  
17.  IF faces is EMPTY THEN
18.      RETURN error "No face detected"
19.  END IF
20.  
21.  // Select largest face
22.  face ← SORT faces BY (bbox_width × bbox_height) DESCENDING
23.  face ← faces[0]
24.  
25.  // Liveness Check (Texture Analysis)
26.  bbox ← face.bbox AS integer
27.  y1, x1, y2, x2 ← CLIP bbox to image bounds
28.  face_crop ← img[y1:y2, x1:x2]
29.  
30.  IF face_crop.size == 0 THEN
31.      RETURN error "Face detection error"
32.  END IF
33.  
34.  gray_face ← CONVERT face_crop to grayscale
35.  laplacian ← COMPUTE Laplacian(gray_face)
36.  lap_var ← COMPUTE variance(laplacian)
37.  
38.  LOG "Liveness Score:", lap_var
39.  
40.  IF lap_var < LIVENESS_THRESHOLD (200.0) THEN
41.      LOG "SPOOF ATTEMPT DETECTED"
42.      RETURN error "Liveness check failed"
43.  END IF
44.  
45.  // Extract ArcFace embedding
46.  embedding ← face.embedding  // 512-dimensional vector
47.  RETURN embedding AS list
48. END
```

### 1.3 Face Login Algorithm

```
Algorithm: FACE_LOGIN
Input: username, image_file
Output: success_status, jwt_token OR error

1. BEGIN
2.   EXECUTE SQL:
3.       SELECT id, face_embedding 
4.       FROM users 
5.       WHERE username = username
6.   
7.   IF no user found THEN
8.       RETURN error "User not found"
9.   END IF
10.  
11.  saved_embedding ← user.face_embedding
12.  
13.  // Get new embedding from login image
14.  login_embedding ← EXTRACT_FACE_EMBEDDING(image_file)
15.  
16.  IF login_embedding is error THEN
17.      RETURN login_embedding (propagate error)
18.  END IF
19.  
20.  // Calculate Cosine Similarity
21.  similarity ← COSINE_SIMILARITY(login_embedding, saved_embedding)
22.  
23.  IF similarity > 0.5 THEN
24.      EXECUTE SQL:
25.          INSERT INTO login_history 
26.          (user_id, auth_method, success, ip_address)
27.          VALUES (user.id, 'face', true, request_ip)
28.      
29.      token ← GENERATE_JWT_TOKEN(user.id)
30.      RETURN {success: true, token: token}
31.  ELSE
32.      RETURN error "Face authentication failed"
33.  END IF
34. END
```

### 1.4 Cosine Similarity Algorithm

```
Algorithm: COSINE_SIMILARITY
Input: vector_A[512], vector_B[512]
Output: similarity_score (range: -1 to 1)

1. BEGIN
2.   dot_product ← 0
3.   norm_A ← 0
4.   norm_B ← 0
5.   
6.   FOR i = 0 TO 511 DO
7.       dot_product ← dot_product + (vector_A[i] × vector_B[i])
8.       norm_A ← norm_A + (vector_A[i])²
9.       norm_B ← norm_B + (vector_B[i])²
10.  END FOR
11.  
12.  norm_A ← SQRT(norm_A)
13.  norm_B ← SQRT(norm_B)
14.  
15.  similarity ← dot_product / (norm_A × norm_B)
16.  RETURN similarity
17. END
```

---

## 2. VOICE RECOGNITION ALGORITHM

### 2.1 Voice Registration Algorithm

```
Algorithm: VOICE_REGISTRATION
Input: username, email, audio_file
Output: success_status

1. BEGIN
2.   audio_path ← SAVE audio_file to temporary location
3.   
4.   // Check if user exists
5.   EXECUTE SQL:
6.       SELECT id FROM users WHERE username = username
7.   
8.   CREATE FormData
9.   APPEND audio file to FormData
10.  
11.  // Send to Python ML service
12.  SEND POST to http://127.0.0.1:5001/voice-verify
13.  RECEIVE response {embedding, voice_features, success}
14.  
15.  IF response.success == false THEN
16.      RETURN error "Voice processing failed"
17.  END IF
18.  
19.  voice_data ← {
20.      embedding: response.embedding,
21.      voice_features: response.voice_features
22.  }
23.  
24.  IF user exists THEN
25.      EXECUTE SQL:
26.          UPDATE users 
27.          SET voice_data = voice_data, voice_registered = true
28.          WHERE username = username AND email = email
29.  ELSE
30.      EXECUTE SQL:
31.          INSERT INTO users 
32.          (username, email, voice_data, voice_registered)
33.          VALUES (username, email, voice_data, true)
34.  END IF
35.  
36.  DELETE temporary audio file
37.  RETURN {success: true, message: "Voice registered successfully"}
38. END
```

### 2.2 Voice Feature Extraction Algorithm

```
Algorithm: EXTRACT_VOICE_FEATURES
Input: waveform (audio samples), sample_rate
Output: features_dict OR (NULL, false)

1. BEGIN
2.   TRY
3.       // Extract Fundamental Frequency (F0)
4.       f0[], voiced_flag[], voiced_probs[] ← librosa.pyin(
5.           waveform,
6.           fmin = 65.41 Hz,    // C2 note
7.           fmax = 2093.00 Hz   // C7 note
8.       )
9.       
10.      // Extract Spectral Features
11.      spectral_centroids[] ← librosa.spectral_centroid(waveform, sample_rate)
12.      spectral_rolloff[] ← librosa.spectral_rolloff(waveform, sample_rate)
13.      
14.      // Extract MFCC (Mel-Frequency Cepstral Coefficients)
15.      mfccs[20, T] ← librosa.mfcc(
16.          y = waveform, 
17.          sr = sample_rate, 
18.          n_mfcc = 20
19.      )
20.      mfcc_deltas ← librosa.delta(mfccs, order=1)
21.      mfcc_delta2s ← librosa.delta(mfccs, order=2)
22.      
23.      // Extract Formants (Vocal Tract Features)
24.      formants[] ← librosa.preemphasis(waveform)
25.      
26.      // Compute Statistical Features
27.      f0_valid ← REMOVE NaN values from f0
28.      
29.      features ← {
30.          'f0_stats': {
31.              'mean': MEAN(f0_valid),
32.              'std': STD_DEVIATION(f0_valid),
33.              'skew': SKEWNESS(f0_valid),
34.              'kurtosis': KURTOSIS(f0_valid)
35.          },
36.          'spectral_stats': {
37.              'centroid_mean': MEAN(spectral_centroids),
38.              'centroid_std': STD_DEVIATION(spectral_centroids),
39.              'rolloff_mean': MEAN(spectral_rolloff)
40.          },
41.          'mfcc_stats': {
42.              'mean': MEAN(mfccs),
43.              'std': STD_DEVIATION(mfccs),
44.              'delta_mean': MEAN(mfcc_deltas),
45.              'delta2_mean': MEAN(mfcc_delta2s)
46.          },
47.          'voice_characteristics': {
48.              'formant_mean': MEAN(formants),
49.              'formant_std': STD_DEVIATION(formants),
50.              'voiced_probability': MEAN(voiced_probs)
51.          }
52.      }
53.      
54.      RETURN (features, true)
55.      
56.  CATCH exception
57.      LOG "Feature extraction error:", exception
58.      RETURN (NULL, false)
59.  END TRY
60. END
```

### 2.3 Voice Liveness Detection Algorithm

```
Algorithm: CHECK_VOICE_LIVENESS
Input: voice_features (dictionary)
Output: (is_live, failure_reason)

1. BEGIN
2.   // Define thresholds
3.   F0_STD_MIN ← 1.5        // Hz
4.   ROLLOFF_MIN ← 1000.0    // Hz
5.   VOICED_PROB_MIN ← 0.04  // 4%
6.   
7.   // Extract feature values
8.   f0_std ← voice_features['f0_stats']['std']
9.   rolloff_mean ← voice_features['spectral_stats']['rolloff_mean']
10.  voiced_prob ← voice_features['voice_characteristics']['voiced_probability']
11.  
12.  LOG "Voice Liveness Scores:"
13.  LOG "  F0_Std =", f0_std
14.  LOG "  Rolloff =", rolloff_mean
15.  LOG "  VoicedProb =", voiced_prob
16.  
17.  // Check 1: Pitch Variation
18.  IF f0_std < F0_STD_MIN THEN
19.      reason ← "Pitch variation too low (" + f0_std + " < " + F0_STD_MIN + ")"
20.      RETURN (false, reason)
21.  END IF
22.  
23.  // Check 2: Frequency Range
24.  IF rolloff_mean < ROLLOFF_MIN THEN
25.      reason ← "Spectral rolloff too low (" + rolloff_mean + " < " + ROLLOFF_MIN + ")"
26.      RETURN (false, reason)
27.  END IF
28.  
29.  // Check 3: Voiced Probability
30.  IF voiced_prob < VOICED_PROB_MIN THEN
31.      reason ← "Voiced probability too low (" + voiced_prob + " < " + VOICED_PROB_MIN + ")"
32.      RETURN (false, reason)
33.  END IF
34.  
35.  // All checks passed
36.  RETURN (true, "Voice appears live")
37. END
```

### 2.4 Voice Verification with ECAPA-TDNN Algorithm

```
Algorithm: VOICE_VERIFICATION
Input: audio_file
Output: {embedding[192], voice_features, success} OR error

1. BEGIN
2.   temp_path ← 'temp_audio.wav'
3.   
4.   IF audio_file is NULL THEN
5.       RETURN error "No audio file provided"
6.   END IF
7.   
8.   SAVE audio_file to temp_path
9.   
10.  // Load and preprocess audio
11.  waveform, sample_rate ← librosa.load(temp_path, sr=16000)
12.  
13.  // Voice Activity Detection (VAD)
14.  intervals[] ← librosa.split(waveform, top_db=20)
15.  
16.  IF intervals is EMPTY THEN
17.      RETURN error "No voice detected"
18.  END IF
19.  
20.  // Extract voiced segments
21.  voiced_segments[] ← EMPTY
22.  FOR each (start, end) in intervals DO
23.      APPEND waveform[start:end] to voiced_segments
24.  END FOR
25.  
26.  waveform ← CONCATENATE(voiced_segments)
27.  
28.  // Normalize audio
29.  waveform ← NORMALIZE(waveform)
30.  
31.  // Extract biometric features
32.  voice_features, success ← EXTRACT_VOICE_FEATURES(waveform, sample_rate)
33.  
34.  IF success == false THEN
35.      RETURN error "Failed to extract voice features"
36.  END IF
37.  
38.  // Check liveness
39.  is_live, failure_reason ← CHECK_VOICE_LIVENESS(voice_features)
40.  
41.  IF is_live == false THEN
42.      LOG "SPOOF ATTEMPT DETECTED (VOICE):", failure_reason
43.      RETURN error "Liveness check failed:" + failure_reason
44.  END IF
45.  
46.  LOG "Voice liveness check passed"
47.  
48.  // Get ECAPA-TDNN embedding
49.  waveform_tensor ← CONVERT waveform to torch.FloatTensor
50.  waveform_tensor ← ADD batch dimension (unsqueeze)
51.  
52.  WITH torch.no_grad() DO
53.      embedding ← voice_model.encode_batch(waveform_tensor)
54.      embedding_vector ← SQUEEZE and convert to numpy
55.  END WITH
56.  
57.  response ← {
58.      'embedding': embedding_vector AS list,  // 192-dim
59.      'voice_features': voice_features,
60.      'success': true
61.  }
62.  
63.  DELETE temp_path file
64.  RETURN response
65. END
```

### 2.5 Biometric Match Calculation Algorithm

```
Algorithm: CALCULATE_BIOMETRIC_MATCH
Input: features1, features2 (voice feature dictionaries)
Output: total_score (range: 0 to 1)

1. BEGIN
2.   // Define feature weights
3.   weights ← {
4.       f0_stats: 0.35,              // 35%
5.       spectral_stats: 0.25,        // 25%
6.       mfcc_stats: 0.25,            // 25%
7.       voice_characteristics: 0.15  // 15%
8.   }
9.   
10.  // Calculate F0 score (with 30% tolerance)
11.  f0_diff ← ABS(features1.f0_stats.mean - features2.f0_stats.mean)
12.  f0_tolerance ← features2.f0_stats.mean × 0.3
13.  f0_score ← MAX(0, 1 - (f0_diff / f0_tolerance))
14.  
15.  // Calculate Spectral score (with 40% tolerance)
16.  spectral_diff ← ABS(features1.spectral_stats.centroid_mean - 
17.                       features2.spectral_stats.centroid_mean)
18.  spectral_tolerance ← features2.spectral_stats.centroid_mean × 0.4
19.  spectral_score ← MAX(0, 1 - (spectral_diff / spectral_tolerance))
20.  
21.  // Calculate MFCC score (with 40% tolerance)
22.  mfcc_diff ← ABS(features1.mfcc_stats.mean - features2.mfcc_stats.mean)
23.  mfcc_tolerance ← features2.mfcc_stats.mean × 0.4
24.  mfcc_score ← MAX(0, 1 - (mfcc_diff / mfcc_tolerance))
25.  
26.  // Calculate Voice Characteristics score (with 40% tolerance)
27.  voice_diff ← ABS(features1.voice_characteristics.formant_mean - 
28.                    features2.voice_characteristics.formant_mean)
29.  voice_tolerance ← features2.voice_characteristics.formant_mean × 0.4
30.  voice_score ← MAX(0, 1 - (voice_diff / voice_tolerance))
31.  
32.  // Compute weighted total score
33.  total_score ← (
34.      f0_score × weights.f0_stats +
35.      spectral_score × weights.spectral_stats +
36.      mfcc_score × weights.mfcc_stats +
37.      voice_score × weights.voice_characteristics
38.  )
39.  
40.  RETURN total_score
41. END
```

### 2.6 Voice Login Algorithm

```
Algorithm: VOICE_LOGIN
Input: username, audio_file
Output: {success, token, scores} OR error

1. BEGIN
2.   // Retrieve user data
3.   EXECUTE SQL:
4.       SELECT id, voice_data, voice_registered 
5.       FROM users 
6.       WHERE username = username
7.   
8.   IF no user found THEN
9.       RETURN error "User not found"
10.  END IF
11.  
12.  IF NOT user.voice_registered OR voice_data is NULL THEN
13.      RETURN error "Voice not registered for this user"
14.  END IF
15.  
16.  // Process login audio
17.  CREATE FormData
18.  APPEND audio_file to FormData
19.  
20.  response ← SEND POST to http://127.0.0.1:5001/voice-verify
21.  
22.  IF response.status != 200 OR response.success != true THEN
23.      RETURN error "Voice verification failed"
24.  END IF
25.  
26.  login_embedding ← response.embedding
27.  login_features ← response.voice_features
28.  
29.  // Calculate similarities
30.  embedding_similarity ← COSINE_SIMILARITY(
31.      login_embedding, 
32.      user.voice_data.embedding
33.  )
34.  
35.  biometric_similarity ← CALCULATE_BIOMETRIC_MATCH(
36.      login_features, 
37.      user.voice_data.voice_features
38.  )
39.  
40.  // Compute combined score (weighted)
41.  embedding_weight ← 0.9
42.  biometric_weight ← 0.1
43.  
44.  combined_score ← (
45.      embedding_similarity × embedding_weight +
46.      biometric_similarity × biometric_weight
47.  )
48.  
49.  LOG "Authentication scores:"
50.  LOG "  Embedding:", embedding_similarity
51.  LOG "  Biometric:", biometric_similarity
52.  LOG "  Combined:", combined_score
53.  
54.  IF combined_score > 0.60 THEN
55.      EXECUTE SQL:
56.          INSERT INTO login_history 
57.          (user_id, auth_method, success, similarity_score, biometric_score)
58.          VALUES (user.id, 'voice', true, 
59.                  embedding_similarity, biometric_similarity)
60.      
61.      token ← GENERATE_JWT_TOKEN(user.id)
62.      
63.      RETURN {
64.          success: true,
65.          token: token,
66.          scores: {
67.              combined: combined_score,
68.              embedding: embedding_similarity,
69.              biometric: biometric_similarity
70.          }
71.      }
72.  ELSE
73.      EXECUTE SQL:
74.          INSERT INTO login_history 
75.          (user_id, auth_method, success, similarity_score, biometric_score)
76.          VALUES (user.id, 'voice', false, 
77.                  embedding_similarity, biometric_similarity)
78.      
79.      RETURN error "Voice authentication failed"
80.  END IF
81. END
```

---

## 3. SIGN LANGUAGE RECOGNITION ALGORITHM

### 3.1 Sign Recognition Complete Pipeline

```
Algorithm: SIGN_RECOGNITION_PIPELINE
Input: video_frames[] (sequence of images)
Output: predicted_sign, confidence OR error

1. BEGIN
2.   SEQUENCE_LENGTH ← 30
3.   PREDICTION_THRESHOLD ← 0.5
4.   
5.   recording_sequence[] ← EMPTY
6.   
7.   // Step 1: Frame Processing Loop
8.   FOR each frame in video_frames DO
9.       landmarks ← EXTRACT_LANDMARKS(frame)
10.      APPEND landmarks to recording_sequence
11.  END FOR
12.  
13.  // Step 2: Validate sequence length
14.  IF LENGTH(recording_sequence) < SEQUENCE_LENGTH / 2 THEN
15.      RETURN error "Recording too short"
16.  END IF
17.  
18.  // Step 3: Resample to fixed length
19.  sequence_to_predict ← RESAMPLE_SEQUENCE(
20.      recording_sequence, 
21.      target_length = SEQUENCE_LENGTH
22.  )
23.  
24.  // Step 4: Preprocess sequence
25.  sequence_np ← CONVERT sequence_to_predict to numpy array
26.  sequence_np ← REPLACE NaN with 0.0
27.  sequence_np ← CLIP values to valid range
28.  
29.  // Step 5: Add batch dimension
30.  input_data ← EXPAND_DIMS(sequence_np, axis=0)
31.  // Shape: (1, 30, 300)
32.  
33.  // Step 6: LSTM Prediction
34.  prediction ← sign_model.predict(input_data)
35.  // prediction shape: (1, num_classes)
36.  
37.  pred_index ← ARGMAX(prediction[0])
38.  confidence ← prediction[0][pred_index]
39.  
40.  // Step 7: Threshold check
41.  IF confidence >= PREDICTION_THRESHOLD THEN
42.      predicted_sign ← sign_labels[pred_index]
43.      RETURN {
44.          success: true,
45.          prediction: predicted_sign,
46.          confidence: confidence
47.      }
48.  ELSE
49.      RETURN {
50.          success: false,
51.          message: "Prediction uncertain",
52.          confidence: confidence
53.      }
54.  END IF
55. END
```

### 3.2 Landmark Extraction Algorithm (MediaPipe)

```
Algorithm: EXTRACT_LANDMARKS
Input: frame (RGB image)
Output: landmarks[300] (flattened feature vector)

1. BEGIN
2.   // Initialize MediaPipe Holistic
3.   mp_holistic ← MediaPipe.Holistic(
4.       min_detection_confidence = 0.5,
5.       min_tracking_confidence = 0.5
6.   )
7.   
8.   // Convert frame to RGB
9.   image_rgb ← CONVERT frame from BGR to RGB
10.  image_rgb.flags.writeable ← false
11.  
12.  // Process with MediaPipe
13.  results ← mp_holistic.process(image_rgb)
14.  
15.  // Extract Pose Landmarks (33 points × 4 features = 132)
16.  IF results.pose_landmarks exists THEN
17.      pose_array ← []
18.      FOR each landmark in results.pose_landmarks DO
19.          APPEND [landmark.x, landmark.y, landmark.z, landmark.visibility]
20.      END FOR
21.      pose ← FLATTEN(pose_array)  // 132 values
22.  ELSE
23.      pose ← ZEROS(33 × 4)  // 132 zeros
24.  END IF
25.  
26.  // Extract Left Hand Landmarks (21 points × 4 features = 84)
27.  IF results.left_hand_landmarks exists THEN
28.      lh_array ← []
29.      FOR each landmark in results.left_hand_landmarks DO
30.          APPEND [landmark.x, landmark.y, landmark.z, landmark.visibility]
31.      END FOR
32.      left_hand ← FLATTEN(lh_array)  // 84 values
33.  ELSE
34.      left_hand ← ZEROS(21 × 4)  // 84 zeros
35.  END IF
36.  
37.  // Extract Right Hand Landmarks (21 points × 4 features = 84)
38.  IF results.right_hand_landmarks exists THEN
39.      rh_array ← []
40.      FOR each landmark in results.right_hand_landmarks DO
41.          APPEND [landmark.x, landmark.y, landmark.z, landmark.visibility]
42.      END FOR
43.      right_hand ← FLATTEN(rh_array)  // 84 values
44.  ELSE
45.      right_hand ← ZEROS(21 × 4)  // 84 zeros
46.  END IF
47.  
48.  // Concatenate all landmarks
49.  landmarks ← CONCATENATE([pose, left_hand, right_hand])
50.  // Total: 132 + 84 + 84 = 300 features
51.  
52.  RETURN landmarks
53. END
```

### 3.3 Sequence Resampling Algorithm

```
Algorithm: RESAMPLE_SEQUENCE
Input: sequence[] (variable length), target_length
Output: resampled_sequence[] (fixed length)

1. BEGIN
2.   current_length ← LENGTH(sequence)
3.   
4.   // Generate interpolation indices
5.   indices[] ← LINSPACE(
6.       start = 0,
7.       stop = current_length - 1,
8.       num = target_length
9.   )
10.  
11.  // Round to nearest integer indices
12.  indices ← ROUND(indices) AS integers
13.  
14.  // Sample frames at calculated indices
15.  resampled_sequence ← []
16.  FOR each index in indices DO
17.      APPEND sequence[index] to resampled_sequence
18.  END FOR
19.  
20.  RETURN resampled_sequence
21. END
```

### 3.4 LSTM Model Architecture

```
Algorithm: LSTM_SIGN_CLASSIFIER
Input: sequence[30, 300] (30 frames × 300 features)
Output: probabilities[num_classes]

Layer Architecture:

1. INPUT LAYER
   Shape: (batch_size, 30, 300)
   
2. LSTM LAYER 1 (Bidirectional)
   Units: 128
   Return sequences: True
   Input shape: (30, 300)
   Output shape: (30, 256)  // 128 × 2 (bidirectional)
   
3. DROPOUT LAYER 1
   Rate: 0.3
   
4. LSTM LAYER 2 (Bidirectional)
   Units: 64
   Return sequences: False
   Input shape: (30, 256)
   Output shape: (128)  // 64 × 2
   
5. DROPOUT LAYER 2
   Rate: 0.3
   
6. DENSE LAYER 1
   Units: 64
   Activation: ReLU
   Input shape: (128)
   Output shape: (64)
   
7. DROPOUT LAYER 3
   Rate: 0.2
   
8. OUTPUT LAYER (Dense)
   Units: num_classes (e.g., 15)
   Activation: Softmax
   Input shape: (64)
   Output shape: (num_classes)

Loss Function: Focal Loss
   α = 0.25
   γ = 2.0
   FL(p) = -α(1-p)^γ log(p)

Optimizer: Adam
   Learning rate: 0.001
```

### 3.5 Focal Loss Algorithm

```
Algorithm: FOCAL_LOSS
Input: y_true (true labels), y_pred (predictions)
Output: loss (scalar)

Parameters:
   α ← 0.25
   γ ← 2.0
   ε ← 1e-7 (epsilon for numerical stability)

1. BEGIN
2.   // Clip predictions to avoid log(0)
3.   y_pred ← CLIP(y_pred, min=ε, max=1-ε)
4.   
5.   // Calculate cross-entropy
6.   cross_entropy ← -y_true × LOG(y_pred)
7.   
8.   // Calculate focal loss
9.   modulating_factor ← (1 - y_pred)^γ
10.  focal_loss ← α × modulating_factor × cross_entropy
11.  
12.  // Sum over all classes
13.  loss ← SUM(focal_loss, axis=-1)
14.  
15.  RETURN loss
16. END
```

---

## 4. NATURAL LANGUAGE GENERATION ALGORITHM

### 4.1 Sentence Generation from Keywords (TinyLlama)

```
Algorithm: GENERATE_SENTENCE_FROM_KEYWORDS
Input: keywords[] (list of recognized signs)
Output: natural_sentence (string)

1. BEGIN
2.   // Model: TinyLlama-1.1B-Chat (Q4_K_M quantized)
3.   
4.   IF slm_model is NOT loaded THEN
5.       RETURN "SLM NOT LOADED."
6.   END IF
7.   
8.   // Convert keywords to comma-separated string
9.   keyword_string ← JOIN(keywords, separator=", ")
10.  
11.  // Define system context
12.  system_prompt ← "You are a helpful banking assistant. " +
13.                   "Convert keyword lists into a single, complete sentence."
14.  
15.  // Build few-shot prompt with examples
16.  prompt ← CONSTRUCT_PROMPT(
17.      system: system_prompt,
18.      examples: [
19.          {
20.              user: "Keywords: [MY, CARD, MISSING]",
21.              assistant: "My card is missing."
22.          },
23.          {
24.              user: "Keywords: [HELP, ONLINE, ACCOUNT]",
25.              assistant: "I need help with my online account."
26.          },
27.          {
28.              user: "Keywords: [LOAN, STATUS]",
29.              assistant: "What is the status of my loan?"
30.          }
31.      ],
32.      current_keywords: keyword_string
33.  )
34.  
35.  // Format with chat template
36.  formatted_prompt ← 
37.      "<|system|>\n" + system_prompt + "</s>\n" +
38.      "<|user|>\nKeywords: [MY, CARD, MISSING]</s>\n" +
39.      "<|assistant|>\nMy card is missing.</s>\n" +
40.      "<|user|>\nKeywords: [HELP, ONLINE, ACCOUNT]</s>\n" +
41.      "<|assistant|>\nI need help with my online account.</s>\n" +
42.      "<|user|>\nKeywords: [LOAN, STATUS]</s>\n" +
43.      "<|assistant|>\nWhat is the status of my loan?</s>\n" +
44.      "<|user|>\nKeywords: [" + keyword_string + "]</s>\n" +
45.      "<|assistant|>\n"
46.  
47.  LOG "Sending to SLM:", formatted_prompt
48.  
49.  start_time ← CURRENT_TIME()
50.  
51.  // Generate text with model
52.  generated_text ← slm_model.generate(
53.      prompt = formatted_prompt,
54.      max_new_tokens = 50,
55.      stop_sequences = ["</s>", "<|user|>"],
56.      temperature = 0.3,  // Low temperature for deterministic output
57.      top_p = 0.9,
58.      top_k = 40
59.  )
60.  
61.  end_time ← CURRENT_TIME()
62.  generation_time ← end_time - start_time
63.  
64.  LOG "SLM generation took", generation_time, "seconds"
65.  
66.  // Clean output
67.  final_sentence ← STRIP(generated_text)
68.  
69.  LOG "SLM Output:", final_sentence
70.  
71.  RETURN final_sentence
72. END
```

### 4.2 Support Ticket Submission Algorithm

```
Algorithm: SUBMIT_TO_SUPPORT
Input: query_text, auth_token
Output: {success, ticket_id} OR error

1. BEGIN
2.   IF query_text is EMPTY THEN
3.       RETURN error "No query text provided"
4.   END IF
5.   
6.   IF auth_token is EMPTY THEN
7.       RETURN error "Authentication token required"
8.   END IF
9.   
10.  // Prepare request
11.  backend_url ← 'http://127.0.0.1:5000/api/support/tickets'
12.  
13.  headers ← {
14.      'Authorization': 'Bearer ' + auth_token,
15.      'Content-Type': 'application/json'
16.  }
17.  
18.  payload ← {
19.      'query_text': query_text,
20.      'query_source': 'sign_language'
21.  }
22.  
23.  // Send to backend
24.  TRY
25.      response ← HTTP POST(
26.          url = backend_url,
27.          headers = headers,
28.          body = JSON(payload),
29.          timeout = 10 seconds
30.      )
31.      
32.      IF response.status_code == 201 THEN
33.          result ← PARSE_JSON(response.body)
34.          ticket_id ← result.ticket.id
35.          
36.          RETURN {
37.              success: true,
38.              message: 'Query submitted successfully',
39.              ticket_id: ticket_id
40.          }
41.      ELSE
42.          error_msg ← response.body.message OR 'Failed to submit query'
43.          RETURN error error_msg
44.      END IF
45.      
46.  CATCH exception
47.      LOG "Error submitting to support:", exception
48.      RETURN error exception.message
49.  END TRY
50. END
```

---

## 5. AUTHENTICATION ALGORITHMS

### 5.1 JWT Token Generation Algorithm

```
Algorithm: GENERATE_JWT_TOKEN
Input: user_id (integer)
Output: jwt_token (string)

1. BEGIN
2.   SECRET_KEY ← ENVIRONMENT_VARIABLE('JWT_SECRET')
3.   EXPIRY_TIME ← 1 hour
4.   
5.   payload ← {
6.       'id': user_id,
7.       'iat': CURRENT_TIMESTAMP(),  // Issued at
8.       'exp': CURRENT_TIMESTAMP() + EXPIRY_TIME  // Expiration
9.   }
10.  
11.  token ← JWT.sign(
12.      payload = payload,
13.      secret = SECRET_KEY,
14.      algorithm = 'HS256'
15.  )
16.  
17.  RETURN token
18. END
```

### 5.2 JWT Token Verification Algorithm

```
Algorithm: VERIFY_JWT_TOKEN
Input: token (string)
Output: decoded_payload OR error

1. BEGIN
2.   IF token is NULL OR EMPTY THEN
3.       RETURN error "No token provided"
4.   END IF
5.   
6.   // Extract token from "Bearer <token>" format
7.   IF token STARTS_WITH "Bearer " THEN
8.       token ← SUBSTRING(token, from=7)
9.   END IF
10.  
11.  SECRET_KEY ← ENVIRONMENT_VARIABLE('JWT_SECRET')
12.  
13.  TRY
14.      decoded ← JWT.verify(
15.          token = token,
16.          secret = SECRET_KEY,
17.          algorithms = ['HS256']
18.      )
19.      
20.      // Check expiration
21.      current_time ← CURRENT_TIMESTAMP()
22.      IF decoded.exp < current_time THEN
23.          RETURN error "Token expired"
24.      END IF
25.      
26.      RETURN decoded
27.      
28.  CATCH JsonWebTokenError
29.      RETURN error "Invalid token"
30.  CATCH TokenExpiredError
31.      RETURN error "Token expired"
32.  END TRY
33. END
```

### 5.3 OTP Generation Algorithm

```
Algorithm: GENERATE_OTP
Input: None
Output: otp (6-digit string)

1. BEGIN
2.   MIN_VALUE ← 100000
3.   MAX_VALUE ← 999999
4.   
5.   random_number ← RANDOM_INTEGER(MIN_VALUE, MAX_VALUE)
6.   otp ← CONVERT random_number to STRING
7.   
8.   RETURN otp
9. END
```

### 5.4 OTP Verification and Login Algorithm

```
Algorithm: OTP_LOGIN
Input: email, username, otp
Output: {success, token} OR error

1. BEGIN
2.   // Retrieve user with matching OTP
3.   EXECUTE SQL:
4.       SELECT id, username, email, otp_expires 
5.       FROM users 
6.       WHERE (email = email OR username = username) 
7.       AND otp = otp
8.   
9.   IF no user found THEN
10.      RETURN error "Invalid OTP"
11.  END IF
12.  
13.  user ← query_result[0]
14.  
15.  // Check OTP expiration
16.  current_time ← CURRENT_TIMESTAMP()
17.  IF current_time > user.otp_expires THEN
18.      RETURN error "OTP has expired"
19.  END IF
20.  
21.  // Clear OTP after successful verification
22.  EXECUTE SQL:
23.      UPDATE users 
24.      SET otp = NULL, otp_expires = NULL 
25.      WHERE id = user.id
26.  
27.  // Log successful login
28.  EXECUTE SQL:
29.      INSERT INTO login_history 
30.      (user_id, auth_method, success)
31.      VALUES (user.id, 'otp', true)
32.  
33.  // Generate JWT token
34.  token ← GENERATE_JWT_TOKEN(user.id)
35.  
36.  RETURN {
37.      success: true,
38.      token: token,
39.      username: user.username
40.  }
41. END
```

### 5.5 Multi-Factor Authentication Decision Algorithm

```
Algorithm: MFA_AUTHENTICATION_DECISION
Input: user_id, auth_method, authentication_score
Output: authentication_result

1. BEGIN
2.   // Define thresholds
3.   FACE_THRESHOLD ← 0.50
4.   VOICE_EMBEDDING_THRESHOLD ← 0.60
5.   VOICE_COMBINED_THRESHOLD ← 0.60
6.   
7.   CASE auth_method OF
8.       
9.       WHEN 'face':
10.          IF authentication_score > FACE_THRESHOLD THEN
11.              result ← "APPROVED"
12.          ELSE
13.              result ← "DENIED"
14.          END IF
15.      
16.      WHEN 'voice':
17.          // Voice uses combined score (embedding + biometric)
18.          IF authentication_score > VOICE_COMBINED_THRESHOLD THEN
19.              result ← "APPROVED"
20.          ELSE
21.              result ← "DENIED"
22.          END IF
23.      
24.      WHEN 'otp':
25.          // OTP is binary (valid or invalid)
26.          result ← "APPROVED"
27.      
28.      OTHERWISE:
29.          result ← "DENIED"
30.  END CASE
31.  
32.  // Log authentication attempt
33.  EXECUTE SQL:
34.      INSERT INTO login_history 
35.      (user_id, auth_method, success, similarity_score, timestamp)
36.      VALUES (user_id, auth_method, result=='APPROVED', 
37.              authentication_score, CURRENT_TIMESTAMP())
38.  
39.  RETURN result
40. END
```

---

## 6. COMPLETE SYSTEM WORKFLOW ALGORITHM

### 6.1 End-to-End Sign Language Support Query Algorithm

```
Algorithm: SIGN_LANGUAGE_SUPPORT_WORKFLOW
Input: user_session (authenticated user)
Output: ticket_id OR error

1. BEGIN
2.   // Initialize
3.   keywords[] ← EMPTY
4.   
5.   // Phase 1: User performs sign gestures
6.   REPEAT
7.       // Capture video sequence
8.       video_frames[] ← CAPTURE_WEBCAM_FRAMES(duration=2-3 seconds)
9.       
10.      // Extract landmarks from each frame
11.      landmarks_sequence[] ← []
12.      FOR each frame in video_frames DO
13.          landmarks ← EXTRACT_LANDMARKS(frame)
14.          APPEND landmarks to landmarks_sequence
15.      END FOR
16.      
17.      // Predict sign
18.      result ← SIGN_RECOGNITION_PIPELINE(landmarks_sequence)
19.      
20.      IF result.success == true THEN
21.          keyword ← result.prediction
22.          confidence ← result.confidence
23.          
24.          DISPLAY "Detected: " + keyword + " (" + confidence + ")"
25.          APPEND keyword to keywords[]
26.      ELSE
27.          DISPLAY "Prediction uncertain, try again"
28.      END IF
29.      
30.  UNTIL user clicks "Generate Query" OR user cancels
31.  
32.  // Phase 2: Generate natural language sentence
33.  IF LENGTH(keywords) == 0 THEN
34.      RETURN error "No keywords detected"
35.  END IF
36.  
37.  sentence ← GENERATE_SENTENCE_FROM_KEYWORDS(keywords)
38.  DISPLAY "Generated Query: " + sentence
39.  
40.  // Phase 3: Submit to support system
41.  auth_token ← GET_USER_TOKEN(user_session)
42.  
43.  result ← SUBMIT_TO_SUPPORT(
44.      query_text = sentence,
45.      auth_token = auth_token
46.  )
47.  
48.  IF result.success == true THEN
49.      ticket_id ← result.ticket_id
50.      DISPLAY "Support ticket created: " + ticket_id
51.      RETURN ticket_id
52.  ELSE
53.      RETURN error result.error
54.  END IF
55. END
```

---

## APPENDIX: Mathematical Formulas

### A. ArcFace Loss Function
```
L = -log(e^(s·cos(θᵢ + m)) / (e^(s·cos(θᵢ + m)) + Σⱼ≠ᵢ e^(s·cos(θⱼ))))

Where:
  s = scale factor (typically 64)
  m = additive angular margin (typically 0.5)
  θᵢ = angle between feature and true class weight
  θⱼ = angle between feature and other class weights
```

### B. Focal Loss
```
FL(p) = -α(1-pₜ)^γ log(pₜ)

Where:
  pₜ = p    if y=1 (correct class)
  pₜ = 1-p  if y=0 (incorrect class)
  α = balancing factor (0.25)
  γ = focusing parameter (2.0)
```

### C. LSTM Cell Operations
```
fₜ = σ(Wf·[hₜ₋₁, xₜ] + bf)    // Forget gate
iₜ = σ(Wi·[hₜ₋₁, xₜ] + bi)    // Input gate
C̃ₜ = tanh(WC·[hₜ₋₁, xₜ] + bC) // Candidate memory
Cₜ = fₜ * Cₜ₋₁ + iₜ * C̃ₜ      // Cell state
oₜ = σ(Wo·[hₜ₋₁, xₜ] + bo)    // Output gate
hₜ = oₜ * tanh(Cₜ)            // Hidden state

Where:
  σ = sigmoid function
  * = element-wise multiplication
  W, b = learned weight matrices and biases
```

### D. Cosine Similarity
```
similarity = (A · B) / (||A|| × ||B||)

Where:
  A · B = Σᵢ(Aᵢ × Bᵢ)           // Dot product
  ||A|| = √(Σᵢ(Aᵢ²))           // Euclidean norm of A
  ||B|| = √(Σᵢ(Bᵢ²))           // Euclidean norm of B
```

### E. Weighted Score Calculation
```
Combined_Score = Σᵢ(wᵢ × scoreᵢ)

Where:
  wᵢ = weight for feature i
  scoreᵢ = similarity score for feature i
  Σᵢwᵢ = 1 (weights sum to 1)
```

---

**END OF ALGORITHM DOCUMENTATION**
