const pool = require('../db');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const { sendOTP } = require('../utils/emailService');
const biometricService = require('../services/biometricService');

const generateToken = (id) =>
  jwt.sign({ id }, process.env.JWT_SECRET, { expiresIn: '1h' });

// Add these helper functions after the imports
const calculateBiometricMatch = (features1, features2) => {
    try {
        // Adjust weights for better accuracy
        const weights = {
            f0_stats: 0.35,        // Fundamental frequency
            spectral_stats: 0.25,   // Spectral features
            mfcc_stats: 0.25,       // MFCC features
            voice_characteristics: 0.15  // Other voice characteristics
        };

        // Normalized f0 comparison with wider tolerance
        const f0Score = Math.max(0, 1 - Math.abs(
            (features1.f0_stats.mean - features2.f0_stats.mean) / 
            (features2.f0_stats.mean * 0.3)  // 30% tolerance
        ));

        // Spectral comparison with normalized values
        const spectralScore = Math.max(0, 1 - Math.abs(
            (features1.spectral_stats.centroid_mean - features2.spectral_stats.centroid_mean) / 
            (features2.spectral_stats.centroid_mean * 0.4)  // 40% tolerance
        ));

        // MFCC comparison with wider acceptance range
        const mfccScore = Math.max(0, 1 - Math.abs(
            (features1.mfcc_stats.mean - features2.mfcc_stats.mean) / 
            (features2.mfcc_stats.mean * 0.4)
        ));

        // Voice characteristics with adaptive threshold
        const voiceScore = Math.max(0, 1 - Math.abs(
            (features1.voice_characteristics.formant_mean - features2.voice_characteristics.formant_mean) / 
            (features2.voice_characteristics.formant_mean * 0.4)
        ));

        const totalScore = (
            f0Score * weights.f0_stats +
            spectralScore * weights.spectral_stats +
            mfccScore * weights.mfcc_stats +
            voiceScore * weights.voice_characteristics
        );

        return totalScore;
    } catch (err) {
        console.error('Error calculating biometric match:', err);
        return 0;
    }
};

// ===================== FACE AUTH ===================== //

exports.registerFace = async (req, res) => {
  try {
    const { username, email } = req.body;
    const image = req.file?.path;

    // Validate input
    if (!username || !email) {
      return res.status(400).json({ error: 'Username and email are required' });
    }

    if (!image) {
      return res.status(400).json({ error: 'Face image is required' });
    }

    // Check if user already exists
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE email = $1 OR username = $2',
      [email, username]
    );

    if (existingUser.rows.length > 0) {
      // Cleanup uploaded file
      if (fs.existsSync(image)) {
        fs.unlinkSync(image);
      }
      return res.status(409).json({ error: 'User already exists with this email or username' });
    }

    // Extract face embedding using Python service
    const formData = new FormData();
    formData.append('image', fs.createReadStream(image));

    let faceEmbedding;
    try {
      const { data } = await axios.post('http://127.0.0.1:5001/embed', formData, {
        headers: formData.getHeaders(),
      });
      faceEmbedding = data.embedding; // 512-dim array
    } catch (err) {
      // Cleanup uploaded file
      if (fs.existsSync(image)) {
        fs.unlinkSync(image);
      }
      console.error('Face embedding extraction failed:', err.message);
      return res.status(500).json({ 
        error: 'Face verification service unavailable',
        message: 'Please ensure Python face service is running on port 5001'
      });
    }

    // Store face embedding as JSON string
    const embeddingJson = JSON.stringify(faceEmbedding);

    // Insert user into database
    const result = await pool.query(
      'INSERT INTO users (username, email, face_biometric) VALUES ($1, $2, $3) RETURNING id, username, email',
      [username, email, embeddingJson]
    );

    const userId = result.rows[0].id;
    
    // Generate JWT token
    const token = generateToken(userId);

    // Cleanup uploaded file
    if (fs.existsSync(image)) {
      fs.unlinkSync(image);
    }

    console.log(`✅ User registered successfully: ${username} (ID: ${userId})`);

    res.json({
      success: true,
      token,
      user: {
        id: userId,
        username: result.rows[0].username,
        email: result.rows[0].email
      },
      message: 'User registered successfully'
    });

  } catch (err) {
    console.error('Face registration error:', err);
    
    // Cleanup uploaded file on error
    if (req.file?.path && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }

    res.status(500).json({ 
      error: 'Face registration failed', 
      message: err.message 
    });
  }
};

exports.loginFace = async (req, res) => {
  try {
    const { username } = req.body;
    const image = req.file?.path;

    if (!username) {
      return res.status(400).json({ error: 'Username is required' });
    }

    if (!image) {
      return res.status(400).json({ error: 'Face image is required' });
    }

    // Get user from database
    const userResult = await pool.query(
      'SELECT id, username, email, face_biometric FROM users WHERE username = $1',
      [username]
    );

    if (userResult.rows.length === 0) {
      if (fs.existsSync(image)) {
        fs.unlinkSync(image);
      }
      return res.status(404).json({ error: 'User not found' });
    }

    const user = userResult.rows[0];

    // Check if user has registered face
    if (!user.face_biometric) {
      if (fs.existsSync(image)) {
        fs.unlinkSync(image);
      }
      return res.status(401).json({ error: 'No face biometric registered for this user' });
    }

    // Extract face embedding from login image
    const formData = new FormData();
    formData.append('image', fs.createReadStream(image));

    let loginEmbedding;
    try {
      const { data } = await axios.post('http://127.0.0.1:5001/embed', formData, {
        headers: formData.getHeaders(),
      });
      loginEmbedding = data.embedding;
    } catch (err) {
      if (fs.existsSync(image)) {
        fs.unlinkSync(image);
      }
      console.error('Face embedding extraction failed:', err.message);
      return res.status(500).json({ 
        error: 'Face verification failed',
        message: 'Could not process face image'
      });
    }

    // Parse stored embedding
    const storedEmbedding = JSON.parse(user.face_biometric);

    // Calculate cosine similarity between embeddings
    const dot = loginEmbedding.reduce((sum, val, i) => sum + val * storedEmbedding[i], 0);
    const normA = Math.sqrt(storedEmbedding.reduce((sum, val) => sum + val * val, 0));
    const normB = Math.sqrt(loginEmbedding.reduce((sum, val) => sum + val * val, 0));
    const similarity = dot / (normA * normB);

    console.log(`Face similarity for ${username}: ${similarity.toFixed(4)}`);

    // Cleanup uploaded file
    if (fs.existsSync(image)) {
      fs.unlinkSync(image);
    }

    // Check similarity threshold (0.5 = 50% match)
    if (similarity < 0.5) {
      return res.status(401).json({ 
        error: 'Face authentication failed',
        message: 'Face does not match registered user'
      });
    }

    // Generate token
    const token = generateToken(user.id);

    // Log login attempt
    await pool.query(
      'INSERT INTO login_history (user_id, login_method, status) VALUES ($1, $2, $3)',
      [user.id, 'face', 'success']
    ).catch(err => console.log('Login history log error:', err));

    console.log(`✅ User logged in: ${username} (ID: ${user.id})`);

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email
      }
    });

  } catch (err) {
    console.error('Face login error:', err);
    
    if (req.file?.path && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }

    res.status(500).json({ 
      error: 'Face login failed', 
      message: err.message 
    });
  }
};

// ===================== VOICE AUTH ===================== //



exports.registerVoice = async (req, res) => {
  const { username, email } = req.body;
  const audioPath = req.file.path;
  console.log('Starting voice registration...', { username, email });

  try {
    // Check if user exists first
    const userExists = await pool.query(
      'SELECT * FROM users WHERE username = $1',
      [username]
    );

     console.log('Audio file:', {
      path: audioPath,
      size: fs.statSync(audioPath).size,
      exists: fs.existsSync(audioPath)
    });

    const formData = new FormData();
    formData.append('audio', fs.createReadStream(audioPath), {
      filename: 'voice.wav',
      contentType: 'audio/wav'
    });

    const { data } = await axios.post('http://127.0.0.1:5001/voice-verify', formData, {
      headers: {
        ...formData.getHeaders(),
        'Accept': 'application/json'
      },
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });

    if (!data.success) {
      throw new Error(data.error || 'Voice processing failed');
    }
   const voiceData = {
        embedding: data.embedding,
        voice_features: data.voice_features
    };

    if (userExists.rows.length > 0) {
      // Update existing user
      await pool.query(
        'UPDATE users SET voice_data = $1, voice_registered = true WHERE username = $2 AND email = $3',
        [voiceData, username, email]
      );
    } else {
      // Create new user
      await pool.query(
        'INSERT INTO users (username, email, voice_data, voice_registered) VALUES ($1, $2, $3, $4)',
        [username, email, voiceData, true]
      );
    }

    res.json({ 
      success: true, 
      message: 'Voice registered successfully'
    });

  } catch (err) {
    console.error('Voice registration error:', err.message);
    res.status(500).json({ 
      error: 'Voice registration failed: ' + err.message 
    });
  } finally {
    if (fs.existsSync(audioPath)) {
      fs.unlinkSync(audioPath);
    }
  }
};


// Consolidated and hardened voice login implementation
exports.loginVoice = async (req, res) => {
    const { username } = req.body;
    const audioPath = req.file.path;

    try {
        console.log('Starting voice login...', { username });

    // Check for user and voice data
        const userResult = await pool.query(
            'SELECT * FROM users WHERE username = $1',
            [username]
        );

        if (userResult.rows.length === 0) {
            return res.status(404).json({ error: 'User not found' });
        }

        const user = userResult.rows[0];
        
        // Validate voice data
        if (!user.voice_registered || !user.voice_data) {
            console.log('Voice data missing for user:', username);
            return res.status(400).json({ error: 'Voice not registered for this user' });
        }

        console.log('Voice data found:', {
            hasEmbedding: !!user.voice_data.embedding,
            hasFeatures: !!user.voice_data.voice_features
        });

        // Process login audio
        const formData = new FormData();
    formData.append('audio', fs.createReadStream(audioPath), {
      filename: 'voice.wav',
      contentType: 'audio/wav'
    });

    // Call ML service and capture both success and error responses to aid debugging
    let mlResponse;
    try {
      mlResponse = await axios.post('http://127.0.0.1:5001/voice-verify', formData, {
        headers: {
          ...formData.getHeaders(),
          Accept: 'application/json'
        },
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
        validateStatus: () => true // allow reading non-2xx responses
      });
    } catch (callErr) {
      console.error('Error calling ML service:', callErr.message);
      throw new Error('Unable to reach voice verification service');
    }

    const { status, data } = mlResponse;
    if (status !== 200) {
      console.error('ML service non-200 response:', { status, data });
      const errMsg = (data && (data.error || data.message)) || `ML service error (${status})`;
      throw new Error(errMsg);
    }

    // Defensive checks for response shape
    if (!data || typeof data !== 'object') {
      console.error('Unexpected ML response type:', typeof data);
      throw new Error('Invalid voice verification response');
    }
    if (data.success !== true) {
      console.error('ML service reported failure:', data);
      throw new Error(data.error || 'Voice verification failed');
    }
    if (!Array.isArray(data.embedding) || !data.voice_features) {
      console.error('Missing required fields in ML response:', Object.keys(data));
      throw new Error('Invalid voice verification response');
    }

        // Calculate similarities
    const loginEmbedding = data.embedding;
    const loginFeatures = data.voice_features;
        
    const embeddingSimilarity = calculateSimilarity(loginEmbedding, user.voice_data.embedding);
    const biometricSimilarity = calculateBiometricMatch(loginFeatures, user.voice_data.voice_features);

        // Calculate combined score
        const weights = {
            embedding: 0.9,
            biometric: 0.1
        };

        const combinedScore = (
            embeddingSimilarity * weights.embedding + 
            biometricSimilarity * weights.biometric
        );

        console.log('Authentication scores:', {
            embeddingSimilarity,
            biometricSimilarity,
            combinedScore,
            threshold: 0.60
        });

        if (combinedScore > 0.60) {
            await pool.query(
                `INSERT INTO login_history 
                (user_id, auth_method, success, similarity_score, biometric_score) 
                VALUES ($1, $2, $3, $4, $5)`,
                [user.id, 'voice', true, embeddingSimilarity, biometricSimilarity]
            );

            const token = generateToken(user.id);
            res.json({ 
                success: true, 
                token,
                scores: {
                    combined: combinedScore,
                    embedding: embeddingSimilarity,
                    biometric: biometricSimilarity
                }
            });
        } else {
            await pool.query(
                `INSERT INTO login_history 
                (user_id, auth_method, success, similarity_score, biometric_score) 
                VALUES ($1, $2, $3, $4, $5)`,
                [user.id, 'voice', false, embeddingSimilarity, biometricSimilarity]
            );

            res.status(401).json({ 
                error: 'Voice authentication failed',
                scores: {
                    combined: combinedScore,
                    embedding: embeddingSimilarity,
                    biometric: biometricSimilarity
                }
            });
        }

    } catch (err) {
    console.error('Voice login error:', err);
    res.status(500).json({ error: 'Voice login failed: ' + err.message });
    } finally {
        if (fs.existsSync(audioPath)) {
            fs.unlinkSync(audioPath);
        }
    }
};


// Helper function for cosine similarity
const calculateSimilarity = (vec1, vec2) => {
  const dot = vec1.reduce((sum, val, i) => sum + val * vec2[i], 0);
  const norm1 = Math.sqrt(vec1.reduce((sum, val) => sum + val * val, 0));
  const norm2 = Math.sqrt(vec2.reduce((sum, val) => sum + val * val, 0));
  return dot / (norm1 * norm2);
};




// ===================== OTP===================== //


// Generate 6-digit OTP
const generateOTP = () => {
  return Math.floor(100000 + Math.random() * 900000).toString();
};

exports.sendOtp = async (req, res) => {
  const { email, username } = req.body;

  try {
    // Check if user exists and get their registered email
    const userResult = await pool.query(
      'SELECT id, email, username FROM users WHERE email = $1 OR username = $2',
      [email, username]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({ 
        error: 'No user found with this email/username' 
      });
    }

    const user = userResult.rows[0];
    const otp = generateOTP();
    const otpExpires = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes

    // Save OTP to database
    await pool.query(
      'UPDATE users SET otp = $1, otp_expires = $2 WHERE id = $3',
      [otp, otpExpires, user.id]
    );

    // Send OTP via email
    const emailSent = await sendOTP(user.email, otp);
    if (!emailSent) {
      throw new Error('Failed to send OTP email');
    }

    // Return masked email for privacy
    const maskedEmail = user.email.replace(/(?<=.{3}).(?=.*@)/g, '*');
    
    res.json({
      success: true,
      message: 'OTP sent successfully',
      email: maskedEmail,
      username: user.username
    });

  } catch (err) {
    console.error('Send OTP error:', err);
    res.status(500).json({ error: 'Failed to send OTP: ' + err.message });
  }
};

exports.verifyOtp = async (req, res) => {
  const { email, username, otp } = req.body;

  try {
    // Check OTP for either email or username
    const userResult = await pool.query(
      'SELECT * FROM users WHERE (email = $1 OR username = $2) AND otp = $3',
      [email, username, otp]
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid OTP' });
    }

    const user = userResult.rows[0];
    
    // Check OTP expiration
    if (new Date() > new Date(user.otp_expires)) {
      return res.status(401).json({ error: 'OTP has expired' });
    }

    // Clear OTP after successful verification
    await pool.query(
      'UPDATE users SET otp = NULL, otp_expires = NULL WHERE id = $1',
      [user.id]
    );

    // Log successful login
    await pool.query(
      'INSERT INTO login_history (user_id, auth_method, success) VALUES ($1, $2, $3)',
      [user.id, 'otp', true]
    );

    const token = generateToken(user.id);
    res.json({ 
      success: true, 
      token,
      username: user.username 
    });

  } catch (err) {
    console.error('Verify OTP error:', err);
    res.status(500).json({ error: 'Failed to verify OTP: ' + err.message });
  }
};


exports.getUserData = async (req, res) => {
    try {
        const userId = req.userId;
        console.log('Fetching user data for ID:', userId);

        // Simplify query to only fetch needed columns
        const userResult = await pool.query(
            `SELECT 
                id, 
                username, 
                email,
                voice_registered,
                COALESCE(voice_data, '{}') as voice_data
            FROM users 
            WHERE id = $1`,
            [userId]
        );

        if (userResult.rows.length === 0) {
            return res.status(404).json({ message: 'User not found' });
        }

        // Transform data for frontend
        const userData = {
            ...userResult.rows[0],
            face_registered: false, // Default to false for now
            auth_methods: {
                voice: userResult.rows[0].voice_registered,
                face: false // Default to false for now
            }
        };

        console.log('User data fetched successfully:', {
            id: userData.id,
            username: userData.username,
            authMethods: userData.auth_methods
        });

        res.json(userData);
    } catch (err) {
        console.error('Get user data error:', err);
        res.status(500).json({ message: 'Failed to fetch user data: ' + err.message });
    }
};
exports.getLoginHistory = async (req, res) => {
    try {
        const userId = req.userId;
        const historyResult = await pool.query(
            `SELECT 
                timestamp, 
                auth_method, 
                success, 
                similarity_score,
                biometric_score
            FROM login_history 
            WHERE user_id = $1 
            ORDER BY timestamp DESC 
            LIMIT 10`,
            [userId]
        );

        res.json(historyResult.rows);
    } catch (err) {
        console.error('Get login history error:', err);
        res.status(500).json({ message: 'Failed to fetch login history' });
    }
};

// ...existing code...

exports.logout = async (req, res) => {
  try {
    const userId = req.userId;
    
    // Log the logout event
    await pool.query(
      'INSERT INTO login_history (user_id, auth_method, success, ip_address) VALUES ($1, $2, $3, $4)',
      [userId, 'logout', true, req.ip]
    );

    res.json({ 
      success: true, 
      message: 'Logged out successfully' 
    });
  } catch (err) {
    console.error('Logout error:', err);
    res.status(500).json({ 
      error: 'Logout failed', 
      message: err.message 
    });
  }
};

// ===================== BIOMETRIC ENROLLMENT ===================== //

/**
 * Enroll user biometrics (face + hand + style)
 * Called after user registers via face/OTP
 * Captures continuous video frames and extracts biometric features
 */
exports.enrollBiometrics = async (req, res) => {
  try {
    const userId = req.userId; // From authMiddleware JWT
    const { videoFrames } = req.body; // Array of base64-encoded frames from frontend

    console.log('Biometric enrollment started for user ID:', userId);

    // Validate input
    if (!videoFrames || !Array.isArray(videoFrames)) {
      return res.status(400).json({ 
        error: 'Missing required field: videoFrames (array of base64 strings)' 
      });
    }

    if (videoFrames.length < 20) {
      return res.status(400).json({ 
        error: 'Insufficient frames for enrollment. Please provide at least 20 frames.' 
      });
    }

    // Check if user exists
    const userCheck = await pool.query('SELECT id, username FROM users WHERE id = $1', [userId]);
    if (userCheck.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const username = userCheck.rows[0].username;
    console.log(`Enrolling biometrics for user: ${username} (ID: ${userId})`);

    // CRITICAL: Call biometric service to extract and enroll features
    console.log(`📞 Calling biometric service to enroll user ${userId} with ${videoFrames.length} frames`);
    
    // Convert base64 frames to buffers
    const frameBuffers = videoFrames.map(frame => {
      // Remove data URL prefix if present (data:image/jpeg;base64,...)
      const base64Data = frame.includes(',') ? frame.split(',')[1] : frame;
      return Buffer.from(base64Data, 'base64');
    });

    // Call biometric service enrollment endpoint
    const enrollmentResult = await biometricService.enrollBiometrics(frameBuffers, userId.toString());
    
    if (!enrollmentResult.success) {
      console.error('❌ Biometric service enrollment failed:', enrollmentResult.error);
      return res.status(500).json({ 
        error: 'Failed to enroll biometrics in service',
        details: enrollmentResult.error 
      });
    }

    console.log(`✅ Biometric service enrolled user ${userId} successfully`);
    console.log(`📊 Enrollment stats: ${enrollmentResult.framesProcessed} frames processed`);
    
    // The biometric service stores features in its own database (in-memory + pickle)
    // We just mark the user as enrolled in PostgreSQL with enrollment markers
    // IMPORTANT: Do NOT overwrite face_biometric (used for face login)
    // Use separate columns for transfer biometrics
    const transferEnrollmentMarker = `enrolled_${userId}_${Date.now()}`;
    
    console.log(`💾 Marking user ${userId} as biometrically enrolled in PostgreSQL`);

    // Store enrollment marker in database
    // Keep face_biometric intact (used for face login with port 5001)
    const updateResult = await pool.query(
      `UPDATE users 
       SET hand_biometric = $1, 
           style_biometric = $2, 
           biometric_registered_at = NOW()
       WHERE id = $3
       RETURNING id, username, biometric_registered_at`,
      [transferEnrollmentMarker, transferEnrollmentMarker, userId]
    );

    console.log('Biometric enrollment successful:', {
      userId,
      username: updateResult.rows[0].username,
      registeredAt: updateResult.rows[0].biometric_registered_at
    });

    // Log enrollment event
    await pool.query(
      `INSERT INTO biometric_auth_log 
       (user_id, auth_type, face_score, hand_score, style_score, fusion_score, authenticated, ip_address, user_agent)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [userId, 'enrollment', 1.0, 1.0, 1.0, 1.0, true, req.ip, req.headers['user-agent']]
    );

    res.json({
      success: true,
      message: 'Biometric enrollment completed successfully',
      data: {
        userId: updateResult.rows[0].id,
        username: updateResult.rows[0].username,
        enrolledAt: updateResult.rows[0].biometric_registered_at,
        biometricsEnrolled: {
          face: true,
          hand: true,
          style: true
        }
      }
    });

  } catch (err) {
    console.error('Biometric enrollment error:', err);
    
    // Handle specific errors
    if (err.message && err.message.includes('ECONNREFUSED')) {
      return res.status(503).json({ 
        error: 'Biometric service unavailable', 
        message: 'NS-AGF API service is not running. Please start it with: python ns_agf/api_service.py' 
      });
    }

    res.status(500).json({ 
      error: 'Biometric enrollment failed', 
      message: err.message 
    });
  }
};

// ===================== SIGN LANGUAGE RECOGNITION ===================== //

/**
 * Recognize sign language from video frames
 * Used for customer support queries
 */
exports.recognizeSignLanguage = async (req, res) => {
  try {
    const { videoFrames } = req.body;

    console.log('Sign language recognition started');

    // Validate input
    if (!videoFrames || !Array.isArray(videoFrames)) {
      return res.status(400).json({ 
        error: 'Missing required field: videoFrames (array of base64 strings)' 
      });
    }

    if (videoFrames.length < 20) {
      return res.status(400).json({ 
        error: 'Insufficient frames for recognition. Please provide at least 20 frames.' 
      });
    }

    console.log(`Processing ${videoFrames.length} frames for sign recognition`);

    // Call biometric service to recognize sign
    const recognitionResult = await biometricService.recognizeSign(videoFrames, {
      returnSentence: true,
      returnIntent: true
    });

    if (!recognitionResult.success) {
      console.error('Sign recognition failed:', recognitionResult.message);
      return res.status(500).json({ 
        error: 'Sign recognition failed', 
        message: recognitionResult.message 
      });
    }

    const { recognizedSign, sentence, intent } = recognitionResult.data;

    console.log('Sign recognition successful:', {
      recognizedSign,
      sentence,
      intent
    });

    res.json({
      success: true,
      message: 'Sign language recognized successfully',
      data: {
        recognizedSign,
        sentence,
        intent
      }
    });

  } catch (err) {
    console.error('Sign language recognition error:', err);
    
    // Handle specific errors
    if (err.message && err.message.includes('ECONNREFUSED')) {
      return res.status(503).json({ 
        error: 'Sign recognition service unavailable', 
        message: 'NS-AGF API service is not running. Please start it with: python ns_agf/api_service.py' 
      });
    }

    res.status(500).json({ 
      error: 'Sign language recognition failed', 
      message: err.message 
    });
  }
};