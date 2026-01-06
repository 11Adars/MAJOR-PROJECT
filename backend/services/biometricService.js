/**
 * Biometric Service - Node.js Wrapper for NS-AGF API
 * ====================================================
 * 
 * This service provides Node.js functions to interact with the Python-based
 * NS-AGF API service for biometric authentication and sign language recognition.
 * 
 * Features:
 * - Enroll user biometrics (face + hand + style)
 * - Verify user biometrics during transactions
 * - Recognize sign language gestures
 * - Health check for NS-AGF service
 * 
 * Author: Banking System Team
 * Date: January 2026
 */

const axios = require('axios');
const FormData = require('form-data');

// NS-AGF Python service URL (can be configured via environment variable)
const NS_AGF_SERVICE_URL = process.env.NS_AGF_SERVICE_URL || 'http://127.0.0.1:5003';

// Timeout for API requests (30 seconds for video processing)
const API_TIMEOUT = 30000;

/**
 * Check if NS-AGF API service is running and healthy
 * 
 * @returns {Promise<Object>} Health status object
 * @throws {Error} If service is not reachable
 */
async function checkHealth() {
  try {
    const response = await axios.get(`${NS_AGF_SERVICE_URL}/api/health`, {
      timeout: 5000
    });
    
    return {
      available: true,
      status: response.data.status,
      inferenceReady: response.data.inference_ready,
      biometricReady: response.data.biometric_ready,
      enrolledUsers: response.data.enrolled_users
    };
  } catch (error) {
    console.error('NS-AGF service health check failed:', error.message);
    return {
      available: false,
      error: error.message
    };
  }
}

/**
 * Enroll user biometrics by sending video frames to NS-AGF service
 * 
 * This is called during user registration to capture and store the user's
 * biometric template (face + hand geometry + signing style) for future authentication.
 * 
 * @param {Buffer[]} videoFrames - Array of image buffers (JPEG format)
 * @param {string} userId - Unique user identifier
 * @returns {Promise<Object>} Enrollment result with serialized biometric features
 * @throws {Error} If enrollment fails
 * 
 * @example
 * const frames = [buffer1, buffer2, ...]; // 30 JPEG buffers
 * const result = await enrollBiometrics(frames, 'user123');
 * // Returns: { success, user_id, face_biometric, hand_biometric, style_biometric }
 */
async function enrollBiometrics(videoFrames, userId) {
  // Validate inputs
  if (!videoFrames || !Array.isArray(videoFrames) || videoFrames.length < 10) {
    throw new Error('Minimum 10 video frames required for biometric enrollment');
  }
  
  if (!userId || typeof userId !== 'string') {
    throw new Error('Valid user ID required');
  }
  
  console.log(`📝 Enrolling biometrics for user: ${userId} (${videoFrames.length} frames)`);
  
  try {
    // Create multipart form data
    const form = new FormData();
    form.append('user_id', userId);
    
    // Append video frames
    videoFrames.forEach((frameBuffer, index) => {
      form.append(`frame_${index}`, frameBuffer, {
        filename: `frame_${index}.jpg`,
        contentType: 'image/jpeg'
      });
    });
    
    // Send request to NS-AGF API
    const response = await axios.post(
      `${NS_AGF_SERVICE_URL}/api/biometric/enroll`,
      form,
      {
        headers: form.getHeaders(),
        timeout: API_TIMEOUT,
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      }
    );
    
    if (response.data.success) {
      console.log(`   ✅ Enrollment successful for user: ${userId}`);
      console.log(`   📊 Frames processed: ${response.data.frames_processed}`);
      console.log(`   ✓ Valid frames: ${response.data.valid_frames}`);
      
      return {
        success: true,
        userId: response.data.user_id,
        faceBiometric: response.data.face_biometric,      // Base64 encoded pickle
        handBiometric: response.data.hand_biometric,      // Base64 encoded pickle
        styleBiometric: response.data.style_biometric,    // Base64 encoded pickle
        framesProcessed: response.data.frames_processed,
        validFrames: response.data.valid_frames
      };
    } else {
      throw new Error(response.data.error || 'Enrollment failed');
    }
    
  } catch (error) {
    console.error(`❌ Biometric enrollment error for ${userId}:`, error.message);
    
    if (error.response) {
      // NS-AGF API returned an error
      const apiError = error.response.data.error || error.response.statusText;
      throw new Error(`Biometric enrollment failed: ${apiError}`);
    } else if (error.code === 'ECONNREFUSED') {
      throw new Error('NS-AGF service is not running. Please start: python ns_agf/api_service.py');
    } else {
      throw new Error(`Biometric enrollment failed: ${error.message}`);
    }
  }
}

/**
 * Verify user biometrics during a transaction
 * 
 * This is called during money transfer to authenticate the user via continuous
 * biometric monitoring (face + hand + style) without requiring a PIN.
 * 
 * @param {Buffer[]} videoFrames - Array of image buffers captured during transaction
 * @param {string} userId - User identifier to verify against
 * @returns {Promise<Object>} Verification result with authentication scores
 * @throws {Error} If verification fails
 * 
 * @example
 * const frames = [buffer1, buffer2, ...]; // 30 JPEG buffers
 * const result = await verifyBiometrics(frames, 'user123');
 * // Returns: { authenticated, fusionScore, faceScore, handScore, styleScore }
 */
async function verifyBiometrics(videoFrames, userId) {
  // Validate inputs
  if (!videoFrames || !Array.isArray(videoFrames) || videoFrames.length < 10) {
    throw new Error('Minimum 10 video frames required for biometric verification');
  }
  
  if (!userId || (typeof userId !== 'string' && typeof userId !== 'number')) {
    throw new Error('Valid user ID required');
  }
  
  // Convert userId to string if it's a number
  const userIdStr = String(userId);
  
  console.log(`🔐 Verifying biometrics for user: ${userIdStr} (${videoFrames.length} frames)`);
  
  try {
    // Create multipart form data
    const form = new FormData();
    form.append('user_id', userIdStr);
    
    // Append video frames
    videoFrames.forEach((frameBuffer, index) => {
      form.append(`frame_${index}`, frameBuffer, {
        filename: `frame_${index}.jpg`,
        contentType: 'image/jpeg'
      });
    });
    
    // Send request to NS-AGF API
    const response = await axios.post(
      `${NS_AGF_SERVICE_URL}/api/biometric/verify`,
      form,
      {
        headers: form.getHeaders(),
        timeout: API_TIMEOUT,
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      }
    );
    
    const authenticated = response.data.authenticated;
    const fusionScore = response.data.fusionScore || response.data.fusion_score || 0;
    const faceScore = response.data.faceScore || response.data.face_score || 0;
    const handScore = response.data.handScore || response.data.hand_score || 0;
    const styleScore = response.data.styleScore || response.data.style_score || 0;
    
    const resultEmoji = authenticated ? '✅' : '❌';
    console.log(`   ${resultEmoji} Authentication: ${authenticated ? 'PASSED' : 'FAILED'}`);
    console.log(`   📊 Fusion score: ${fusionScore.toFixed(3)}`);
    console.log(`   👤 Face: ${faceScore.toFixed(3)}`);
    console.log(`   ✋ Hand: ${handScore.toFixed(3)}`);
    console.log(`   ✍️  Style: ${styleScore.toFixed(3)}`);
    
    return {
      authenticated: Boolean(authenticated),
      fusionScore: Number(fusionScore),
      faceScore: Number(faceScore),
      handScore: Number(handScore),
      styleScore: Number(styleScore),
      userId: response.data.user_id,
      framesProcessed: response.data.frames_processed,
      validFrames: response.data.valid_frames || response.data.frames_processed,
      threshold: response.data.threshold || 0.65
    };
    
  } catch (error) {
    console.error(`❌ Biometric verification error for ${userIdStr}:`, error.message);
    
    if (error.response) {
      // Check if user not enrolled
      if (error.response.status === 404) {
        throw new Error(`User ${userIdStr} not enrolled in biometric system`);
      }
      
      // NS-AGF API returned an error
      const apiError = error.response.data.error || error.response.statusText;
      throw new Error(`Biometric verification failed: ${apiError}`);
    } else if (error.code === 'ECONNREFUSED') {
      throw new Error('NS-AGF service is not running. Please start: python ns_agf/api_service.py');
    } else {
      throw new Error(`Biometric verification failed: ${error.message}`);
    }
  }
}

/**
 * Recognize sign language from video frames
 * 
 * This is used in customer support to convert sign language gestures into text queries.
 * 
 * @param {Buffer[]} videoFrames - Array of image buffers (JPEG format)
 * @param {Object} options - Recognition options
 * @param {boolean} options.returnSentence - Combine multiple signs into sentence
 * @returns {Promise<Object>} Recognition result with detected sign and confidence
 * @throws {Error} If recognition fails
 * 
 * @example
 * const frames = [buffer1, buffer2, ...]; // 30+ JPEG buffers
 * const result = await recognizeSign(frames, { returnSentence: true });
 * // Returns: { success, sign, confidence, sentence, intent }
 */
async function recognizeSign(videoFrames, options = {}) {
  // Validate inputs
  if (!videoFrames || !Array.isArray(videoFrames) || videoFrames.length < 10) {
    throw new Error('Minimum 10 video frames required for sign language recognition');
  }
  
  console.log(`🤟 Recognizing sign language (${videoFrames.length} frames)`);
  
  try {
    // Convert buffers to base64 (NS-AGF API expects JSON with base64 frames)
    const framesBase64 = videoFrames.map(buffer => {
      const base64 = buffer.toString('base64');
      return `data:image/jpeg;base64,${base64}`;
    });
    
    // Send request to NS-AGF API
    const response = await axios.post(
      `${NS_AGF_SERVICE_URL}/api/sign/recognize`,
      {
        frames: framesBase64,
        return_sentence: options.returnSentence !== false
      },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: API_TIMEOUT
      }
    );
    
    if (response.data.success) {
      console.log(`   ✅ Sign recognized: ${response.data.sign}`);
      console.log(`   📊 Confidence: ${response.data.confidence.toFixed(2)}`);
      
      if (response.data.intent && response.data.intent.is_banking) {
        console.log(`   🏦 Banking intent detected: ${response.data.intent.intent_type}`);
      }
      
      return {
        success: true,
        sign: response.data.sign,
        confidence: response.data.confidence,
        sentence: response.data.sentence,
        framesProcessed: response.data.frames_processed,
        validFrames: response.data.valid_frames,
        intent: response.data.intent || null
      };
    } else {
      throw new Error(response.data.error || 'Sign recognition failed');
    }
    
  } catch (error) {
    console.error('❌ Sign recognition error:', error.message);
    
    if (error.response) {
      const apiError = error.response.data.error || error.response.statusText;
      throw new Error(`Sign recognition failed: ${apiError}`);
    } else if (error.code === 'ECONNREFUSED') {
      throw new Error('NS-AGF service is not running. Please start: python ns_agf/api_service.py');
    } else {
      throw new Error(`Sign recognition failed: ${error.message}`);
    }
  }
}

/**
 * List all enrolled users in biometric database
 * 
 * @returns {Promise<Array>} Array of user objects with enrollment details
 * @throws {Error} If request fails
 */
async function listEnrolledUsers() {
  try {
    const response = await axios.get(`${NS_AGF_SERVICE_URL}/api/biometric/users`, {
      timeout: 5000
    });
    
    return {
      users: response.data.users,
      total: response.data.total
    };
  } catch (error) {
    console.error('Error listing enrolled users:', error.message);
    throw new Error(`Failed to list enrolled users: ${error.message}`);
  }
}

/**
 * Convert base64 image string to Buffer
 * 
 * Helper function to convert base64-encoded images from frontend
 * into Buffer objects for NS-AGF API.
 * 
 * @param {string} base64String - Base64 image string (with or without data URL prefix)
 * @returns {Buffer} Image buffer
 * 
 * @example
 * const buffer = base64ToBuffer('data:image/jpeg;base64,/9j/4AAQ...');
 */
function base64ToBuffer(base64String) {
  // Remove data URL prefix if present
  if (base64String.includes(',')) {
    base64String = base64String.split(',')[1];
  }
  
  return Buffer.from(base64String, 'base64');
}

/**
 * Convert array of base64 image strings to array of Buffers
 * 
 * @param {string[]} base64Frames - Array of base64 image strings
 * @returns {Buffer[]} Array of image buffers
 * 
 * @example
 * const buffers = base64ArrayToBuffers(['data:image/jpeg;base64,...', ...]);
 */
function base64ArrayToBuffers(base64Frames) {
  return base64Frames.map(base64ToBuffer);
}

// Export all functions
module.exports = {
  checkHealth,
  enrollBiometrics,
  verifyBiometrics,
  recognizeSign,
  listEnrolledUsers,
  base64ToBuffer,
  base64ArrayToBuffers,
  NS_AGF_SERVICE_URL
};
