const pool = require('../db');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

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
  const { username, email } = req.body;
  const image = req.file.path;

  const form = new FormData();
  form.append('image', fs.createReadStream(image));

  try {
    const { data } = await axios.post('http://127.0.0.1:5001/embed', form, {
      headers: form.getHeaders(),
    });

    const embedding = data.embedding;

    const result = await pool.query(
      'INSERT INTO users (username, email, face_embedding) VALUES ($1, $2, $3) RETURNING id',
      [username, email, embedding]
    );

    const token = generateToken(result.rows[0].id);
    res.json({ success: true, token });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Face registration failed' });
  } finally {
    fs.unlinkSync(image);
  }
};

exports.loginFace = async (req, res) => {
  const { username } = req.body;
  const image = req.file.path;

  const userResult = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
  if (userResult.rows.length === 0)
    return res.status(404).json({ error: 'User not found' });

  const savedEmbedding = userResult.rows[0].face_embedding;

  const form = new FormData();
  form.append('image', fs.createReadStream(image));

  try {
    const { data } = await axios.post('http://127.0.0.1:5001/embed', form, {
      headers: form.getHeaders(),
    });

    const loginEmbedding = data.embedding;

    const dot = loginEmbedding.reduce((sum, val, i) => sum + val * savedEmbedding[i], 0);
    const normA = Math.sqrt(savedEmbedding.reduce((sum, val) => sum + val * val, 0));
    const normB = Math.sqrt(loginEmbedding.reduce((sum, val) => sum + val * val, 0));
    const similarity = dot / (normA * normB);

    if (similarity > 0.5) {
      await pool.query(
        'INSERT INTO login_history (user_id, auth_method, success, ip_address) VALUES ($1, $2, $3, $4)',
        [userResult.rows[0].id, 'face', true, req.ip]
      );

      const token = generateToken(userResult.rows[0].id);
      res.json({ success: true, token });
    } else {
      res.status(401).json({ error: 'Face authentication failed' });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Face login failed' });
  } finally {
    fs.unlinkSync(image);
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


exports.loginVoice = async (req, res) => {
    const { username } = req.body;
    const audioPath = req.file.path;

    try {
        console.log('Starting voice login...', { username });

        const userResult = await pool.query(
            'SELECT * FROM users WHERE username = $1 AND voice_registered = true',
            [username]
        );

        if (userResult.rows.length === 0) {
            return res.status(404).json({ error: 'User not found or voice not registered' });
        }

        const formData = new FormData();
        formData.append('audio', fs.createReadStream(audioPath));

        const { data } = await axios.post('http://127.0.0.1:5001/voice-verify', formData, {
            headers: {
                ...formData.getHeaders(),
                'Accept': 'application/json'
            }
        });

        if (!data.success) {
            throw new Error(data.error || 'Voice verification failed');
        }

        const loginFeatures = data.voice_features;
        const loginEmbedding = data.embedding;
        const savedData = userResult.rows[0].voice_data;

        // Calculate embedding similarity
        const embeddingSimilarity = calculateSimilarity(loginEmbedding, savedData.embedding);
        
        // Calculate biometric feature similarity
        const biometricSimilarity = calculateBiometricMatch(loginFeatures, savedData.voice_features);

        console.log('Voice verification scores:', {
            embeddingSimilarity,
            biometricSimilarity
        });

        // Use stricter thresholds for authentication
        if (embeddingSimilarity > 0.75) {
            await pool.query(
                'INSERT INTO login_history (user_id, auth_method, success, similarity_score) VALUES ($1, $2, $3, $4)',
                [userResult.rows[0].id, 'voice', true, embeddingSimilarity]
            );

            const token = generateToken(userResult.rows[0].id);
            res.json({ 
                success: true, 
                token,
                scores: {
                    embedding: embeddingSimilarity,
                    biometric: biometricSimilarity
                }
            });
        } else {

            await pool.query(
        'INSERT INTO login_history (user_id, auth_method, success, similarity_score) VALUES ($1, $2, $3, $4)',
        [userResult.rows[0].id, 'voice', false, embeddingSimilarity]
    );
            res.status(401).json({ 
                error: 'Voice authentication failed',
                scores: {
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
        formData.append('audio', fs.createReadStream(audioPath));

        const { data } = await axios.post('http://127.0.0.1:5001/voice-verify', formData, {
            headers: {
                ...formData.getHeaders(),
                'Accept': 'application/json'
            }
        });

        if (!data.success || !data.embedding || !data.voice_features) {
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