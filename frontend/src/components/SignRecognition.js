import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import './SignRecognition.css';

function SignRecognition() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const captureIntervalRef = useRef(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const processingRef = useRef(false); // Track if request is in flight
  
  const [isRecording, setIsRecording] = useState(false);
  const [currentFrames, setCurrentFrames] = useState([]);
  const [recognizedWords, setRecognizedWords] = useState([]); // Array of recognized words
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [lastRecognition, setLastRecognition] = useState('');
  const [landmarksDetected, setLandmarksDetected] = useState(false);
  const [skeletonEnabled, setSkeletonEnabled] = useState(true);
  
  // Intent verification states for banking security
  const [detectedIntent, setDetectedIntent] = useState(null);
  const [showIntentConfirmation, setShowIntentConfirmation] = useState(false);
  const [pendingSign, setPendingSign] = useState(null);
  const [intentHistory, setIntentHistory] = useState([]); // Track all detected intents

  // High-risk intents that require confirmation
  const HIGH_RISK_INTENTS = ['delete_account', 'transfer', 'alert_fraud', 'report_missing'];

  // MediaPipe Holistic pose connections for skeleton drawing
  const POSE_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 7], [0, 4], [4, 5], [5, 6], [6, 8],
    [9, 10], [11, 12], [11, 13], [13, 15], [15, 17], [15, 19], [15, 21],
    [17, 19], [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], [18, 20],
    [11, 23], [12, 24], [23, 24], [23, 25], [24, 26], [25, 27], [26, 28],
    [27, 29], [28, 30], [29, 31], [30, 32], [27, 31], [28, 32]
  ];

  const HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8],
    [5, 9], [9, 10], [10, 11], [11, 12], [9, 13], [13, 14], [14, 15], [15, 16],
    [13, 17], [17, 18], [18, 19], [19, 20], [0, 17]
  ];

  // Draw skeleton overlay on canvas
  useEffect(() => {
    // Don't draw skeleton when disabled
    if (!skeletonEnabled) {
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
      return;
    }

    const drawSkeleton = async () => {
      // Check ref immediately - stops skeleton during recognition
      if (processingRef.current) {
        const canvas = canvasRef.current;
        if (canvas) {
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        // Keep checking but don't make API calls
        animationRef.current = requestAnimationFrame(drawSkeleton);
        return;
      }
      
      const video = webcamRef.current?.video;
      const canvas = canvasRef.current;
      
      if (!video || !canvas || video.readyState !== 4) {
        animationRef.current = requestAnimationFrame(drawSkeleton);
        return;
      }

      const ctx = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Capture current frame for landmark detection
      const screenshot = webcamRef.current.getScreenshot();
      if (!screenshot) {
        animationRef.current = requestAnimationFrame(drawSkeleton);
        return;
      }

      try {
        // Send frame to backend for landmark extraction
        const base64Frame = screenshot.split(',')[1];
        const response = await axios.post(
          'http://localhost:5003/api/sign/extract-landmarks',
          { frame: base64Frame },
          { timeout: 100 }
        );

        if (response.data.success && response.data.landmarks) {
          setLandmarksDetected(true);
          const landmarks = response.data.landmarks; // Array of {x, y, z}

          // Draw pose landmarks (0-32)
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 2;
          POSE_CONNECTIONS.forEach(([start, end]) => {
            if (start < 33 && end < 33 && landmarks[start] && landmarks[end]) {
              ctx.beginPath();
              ctx.moveTo(landmarks[start].x * canvas.width, landmarks[start].y * canvas.height);
              ctx.lineTo(landmarks[end].x * canvas.width, landmarks[end].y * canvas.height);
              ctx.stroke();
            }
          });

          // Draw left hand landmarks (33-53)
          ctx.strokeStyle = '#FF0000';
          HAND_CONNECTIONS.forEach(([start, end]) => {
            const leftStart = 33 + start;
            const leftEnd = 33 + end;
            if (landmarks[leftStart] && landmarks[leftEnd]) {
              ctx.beginPath();
              ctx.moveTo(landmarks[leftStart].x * canvas.width, landmarks[leftStart].y * canvas.height);
              ctx.lineTo(landmarks[leftEnd].x * canvas.width, landmarks[leftEnd].y * canvas.height);
              ctx.stroke();
            }
          });

          // Draw right hand landmarks (54-74)
          ctx.strokeStyle = '#0000FF';
          HAND_CONNECTIONS.forEach(([start, end]) => {
            const rightStart = 54 + start;
            const rightEnd = 54 + end;
            if (landmarks[rightStart] && landmarks[rightEnd]) {
              ctx.beginPath();
              ctx.moveTo(landmarks[rightStart].x * canvas.width, landmarks[rightStart].y * canvas.height);
              ctx.lineTo(landmarks[rightEnd].x * canvas.width, landmarks[rightEnd].y * canvas.height);
              ctx.stroke();
            }
          });

          // Draw landmark points
          ctx.fillStyle = '#FFFFFF';
          landmarks.forEach((lm, idx) => {
            if (lm) {
              ctx.beginPath();
              ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 3, 0, 2 * Math.PI);
              ctx.fill();
            }
          });
        } else {
          setLandmarksDetected(false);
        }
      } catch (err) {
        // Silently fail for real-time drawing
        setLandmarksDetected(false);
      }

      animationRef.current = requestAnimationFrame(drawSkeleton);
    };

    animationRef.current = requestAnimationFrame(drawSkeleton);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [skeletonEnabled]); // Only depends on skeletonEnabled, processingRef is checked inside

  // Start recording frames
  const handleStartRecording = () => {
    if (isRecording) return;
    
    setMessage('🎥 Recording... Perform ONE sign clearly');
    setIsRecording(true);
    setProgress(0);
    setCurrentFrames([]);
    
    const frames = [];
    const totalFrames = 50;
    let frameCount = 0;
    
    captureIntervalRef.current = setInterval(() => {
      if (webcamRef.current) {
        const screenshot = webcamRef.current.getScreenshot();
        if (screenshot) {
          const base64Frame = screenshot.split(',')[1];
          frames.push(base64Frame);
          frameCount++;
          
          const progressPercent = Math.round((frameCount / totalFrames) * 100);
          setProgress(progressPercent);
          setCurrentFrames(frames);
          
          if (frameCount >= totalFrames) {
            clearInterval(captureIntervalRef.current);
            setIsRecording(false);
            setMessage('✅ Recording complete! Click "Stop & Recognize" to process.');
          }
        }
      }
    }, 100);
  };

  // Stop recording and recognize the sign
  const handleStopRecording = async () => {
    // Prevent multiple simultaneous recognitions using ref (faster than state)
    if (processingRef.current) {
      console.log('⏳ Already processing, ignoring click...');
      return;
    }
    
    // Prevent multiple simultaneous recognitions
    if (isProcessing) {
      console.log('⏳ Already processing (state), please wait...');
      return;
    }
    
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
    }
    setIsRecording(false);
    
    if (currentFrames.length < 10) {
      setMessage('❌ Not enough frames captured. Try again.');
      return;
    }
    
    // Set both ref and state
    processingRef.current = true;
    setIsProcessing(true);
    setMessage('🔍 Recognizing sign...');
    
    try {
      console.log('📤 Sending', currentFrames.length, 'frames to API...');
      // Call NS-AGF API directly for single sign recognition (no ticket creation)
      const response = await axios.post(
        'http://localhost:5003/api/sign/recognize',
        { frames: currentFrames },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000 //ncreased to 30 seconds for MediaPipe processing
        }
      );

      const recognizedSign = response.data.sign || 'Unknown';
      const confidence = response.data.confidence || 0;
      const intentData = response.data.intent || null;
      
      console.log('✅ Received response:', recognizedSign, confidence);
      console.log('🏦 Intent data:', intentData);
      
      // Check if this is a HIGH-RISK banking intent that requires confirmation
      if (intentData && HIGH_RISK_INTENTS.includes(intentData.type)) {
        // HIGH-RISK intent detected - ALWAYS show confirmation dialog
        // Let the user decide whether to proceed, even with lower confidence
        const confidenceWarning = !intentData.is_valid 
          ? `⚠️ Low confidence detected (${(confidence * 100).toFixed(0)}%). ` 
          : '';
        
        setPendingSign({ 
          sign: recognizedSign, 
          confidence, 
          intent: intentData,
          hasConfidenceWarning: !intentData.is_valid
        });
        setDetectedIntent(intentData);
        setShowIntentConfirmation(true);
        setMessage(`⚠️ HIGH-RISK ACTION DETECTED: ${intentData.description || intentData.type}`);
        setCurrentFrames([]);
        setProgress(0);
        return; // Don't add to sentence yet - wait for user confirmation
      }
      
      // Regular intent or no intent - add to sentence directly
      if (intentData) {
        setIntentHistory(prev => [...prev, { sign: recognizedSign, intent: intentData.type, confidence }]);
        setDetectedIntent(intentData);
      }
      
      // Add word to sentence
      setRecognizedWords(prev => [...prev, recognizedSign]);
      setLastRecognition(`${recognizedSign} (${(confidence * 100).toFixed(1)}%)`);
      
      // Show intent information if detected
      const intentMsg = intentData ? ` | 🏦 Intent: ${intentData.type}` : '';
      setMessage(`✅ Recognized: "${recognizedSign}" with ${(confidence * 100).toFixed(0)}% confidence${intentMsg}`);
      setCurrentFrames([]);
      setProgress(0);
      
    } catch (err) {
      console.error('Sign recognition error:', err);
      console.log('Error response:', err.response);
      const errorMsg = err.response?.data?.error || err.response?.data?.message || err.message || 'Recognition failed';
      setMessage(`❌ ${errorMsg}`);
    } finally {
      processingRef.current = false;  // Clear ref
      setIsProcessing(false);
    }
  };

  // Handle confirmation of high-risk intent
  const handleConfirmIntent = () => {
    if (pendingSign) {
      // User confirmed the high-risk action
      setRecognizedWords(prev => [...prev, pendingSign.sign]);
      setLastRecognition(`${pendingSign.sign} (${(pendingSign.confidence * 100).toFixed(1)}%) ✅ CONFIRMED`);
      setIntentHistory(prev => [...prev, { 
        sign: pendingSign.sign, 
        intent: pendingSign.intent.type, 
        confidence: pendingSign.confidence,
        confirmed: true 
      }]);
      setMessage(`✅ HIGH-RISK ACTION CONFIRMED: ${pendingSign.intent.type} - "${pendingSign.sign}" added to query`);
    }
    setShowIntentConfirmation(false);
    setPendingSign(null);
  };

  // Handle rejection of high-risk intent
  const handleRejectIntent = () => {
    setMessage(`❌ Action cancelled. "${pendingSign?.sign}" was NOT added to your query.`);
    setShowIntentConfirmation(false);
    setPendingSign(null);
    setDetectedIntent(null);
  };

  // Clear last word from sentence
  const handleClearLastWord = () => {
    if (recognizedWords.length > 0) {
      setRecognizedWords(prev => prev.slice(0, -1));
      setMessage('🗑️ Last word removed');
      setLastRecognition('');
    }
  };

  // Reset entire sentence
  const handleReset = () => {
    setRecognizedWords([]);
    setCurrentFrames([]);
    setProgress(0);
    setMessage('');
    setLastRecognition('');
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
    }
    setIsRecording(false);
  };

  // Submit sentence for intent analysis and ticket creation
  const handlePredict = async () => {
    if (recognizedWords.length === 0) {
      setMessage('❌ No signs captured. Please record at least one sign.');
      return;
    }

    setIsProcessing(true);
    setMessage('🔍 Analyzing sentence with Intent + SLM...');
    
    try {
      const sentence = recognizedWords.join(' ');
      console.log('📝 Sending to backend:');
      console.log('   Sentence:', sentence);
      console.log('   Words:', recognizedWords);
      
      // Call backend hybrid endpoint with the sentence
      const response = await axios.post(
        'http://localhost:5000/api/support/tickets/hybrid-sign-sentence',
        { 
          sentence: sentence,
          words: recognizedWords,
          use_slm: true
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('✅ Backend response received:');
      console.log('   Full response:', response.data);
      console.log('   sign_language_data:', response.data.sign_language_data);

      const { sign_language_data } = response.data;
      const generatedQuery = sign_language_data?.query_generated || sentence;
      const intent = sign_language_data?.intent || 'general';
      
      console.log('📊 Extracted values:');
      console.log('   Generated Query:', generatedQuery);
      console.log('   Intent:', intent);
      console.log('   SLM Used:', sign_language_data?.slm_used);
      
      setMessage(`✅ Ticket created! Intent: ${intent} | Query: "${generatedQuery}"`);
      
      // Navigate to tickets after 2 seconds
      setTimeout(() => {
        navigate('/support-tickets');
      }, 2000);
      
    } catch (err) {
      console.error('Prediction error:', err);
      console.error('   Error message:', err.message);
      console.error('   Response data:', err.response?.data);
      const errorMsg = err.response?.data?.message || 'Prediction failed';
      setMessage(`❌ ${errorMsg}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="sign-recognition-container">
      {/* HIGH-RISK INTENT CONFIRMATION MODAL */}
      {showIntentConfirmation && pendingSign && (
        <div className="intent-confirmation-overlay">
          <div className="intent-confirmation-modal">
            <div className="intent-warning-icon">⚠️</div>
            <h3>High-Risk Banking Action Detected</h3>
            <div className="intent-details">
              <p><strong>Sign Recognized:</strong> "{pendingSign.sign}"</p>
              <p><strong>Confidence:</strong> {(pendingSign.confidence * 100).toFixed(1)}%</p>
              <p><strong>Banking Intent:</strong> <span className="intent-type">{pendingSign.intent.type}</span></p>
              <p><strong>Description:</strong> {pendingSign.intent.description || 'Sensitive banking operation'}</p>
            </div>
            
            {/* Show warning if confidence is below threshold */}
            {pendingSign.hasConfidenceWarning && (
              <div className="confidence-warning">
                <p>⚠️ <strong>Low Confidence Warning:</strong></p>
                <p>The recognition confidence ({(pendingSign.confidence * 100).toFixed(1)}%) is below the recommended threshold for this high-risk action.</p>
                <p>Please ensure this is the correct sign before confirming.</p>
              </div>
            )}
            
            <div className="intent-warning-message">
              <p>🔒 This action requires your confirmation before proceeding.</p>
              <p>Please verify this is the action you intended to perform.</p>
            </div>
            <div className="intent-confirmation-buttons">
              <button 
                className="confirm-btn" 
                onClick={handleConfirmIntent}
              >
                ✅ Yes, I Confirm This Action
              </button>
              <button 
                className="reject-btn" 
                onClick={handleRejectIntent}
              >
                ❌ Cancel - This Was a Mistake
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="sign-recognition-header">
        <h2>🤟 Sign Language Recognition - Build Your Query</h2>
        <button onClick={() => navigate('/support-tickets')} className="back-link">
          ← Back to Support
        </button>
      </div>

      <div className="sign-main-content">
        <div className="webcam-section">
          <div className="webcam-wrapper">
            <Webcam
              ref={webcamRef}
              screenshotFormat="image/png"
              className="sign-webcam"
              audio={false}
              mirrored={false}
            />
            <canvas 
              ref={canvasRef} 
              className="skeleton-overlay"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none'
              }}
            />
            
            {!landmarksDetected && skeletonEnabled && (
              <div className="landmark-warning">
                ⚠️ No landmarks detected - adjust position/lighting
              </div>
            )}
            
            {isRecording && (
              <div className="recording-indicator">
                <span className="recording-dot"></span>
                <span>Recording...</span>
              </div>
            )}
          </div>

          {isRecording && (
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <p className="progress-text">{progress}% ({currentFrames.length}/50 frames)</p>
            </div>
          )}

          <div className="control-buttons">
            <button
              onClick={() => setSkeletonEnabled(!skeletonEnabled)}
              className="btn-toggle-skeleton"
            >
              {skeletonEnabled ? '👁️ Hide Skeleton' : '👁️‍🗨️ Show Skeleton'}
            </button>
            
            <button
              onClick={handleStartRecording}
              disabled={isRecording || isProcessing}
              className="btn-record"
            >
              🎥 Start Recording
            </button>
            
            <button
              onClick={handleStopRecording}
              disabled={!isRecording && currentFrames.length === 0 || isProcessing}
              className="btn-stop"
            >
              ⏹️ Stop & Recognize
            </button>
            
            <button
              onClick={handleClearLastWord}
              disabled={recognizedWords.length === 0 || isProcessing}
              className="btn-clear-word"
            >
              ⬅️ Clear Last Word
            </button>
            
            <button
              onClick={handleReset}
              disabled={isProcessing}
              className="btn-reset"
            >
              🔄 Reset All
            </button>
          </div>
        </div>

        <div className="recognition-section">
          <h3>📝 Your Sentence</h3>
          
          <div className="sentence-builder">
            {recognizedWords.length === 0 ? (
              <p className="empty-sentence">No words captured yet. Start recording!</p>
            ) : (
              <div className="words-container">
                {recognizedWords.map((word, index) => (
                  <span key={index} className="word-badge">
                    {word}
                  </span>
                ))}
              </div>
            )}
          </div>

          {lastRecognition && (
            <div className="last-recognition">
              <strong>Last recognized:</strong> {lastRecognition}
            </div>
          )}

          <div className="sentence-preview">
            <label>Complete Sentence:</label>
            <div className="sentence-text">
              {recognizedWords.length > 0 ? recognizedWords.join(' ') : 'Build your sentence by recording signs...'}
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={recognizedWords.length === 0 || isProcessing}
            className="btn-predict"
          >
            {isProcessing ? '⏳ Processing...' : '🚀 Predict & Submit Ticket'}
          </button>
        </div>
      </div>

      {message && (
        <div className={`message-box ${message.includes('✅') ? 'success' : message.includes('❌') ? 'error' : 'info'}`}>
          {message}
        </div>
      )}

      <div className="instructions-panel">
        <h3>📋 Instructions</h3>
        <ol>
          <li><strong>Start Recording:</strong> Click to begin capturing frames for one sign</li>
          <li><strong>Perform Sign:</strong> Make your sign clearly (records for 5 seconds)</li>
          <li><strong>Stop & Recognize:</strong> Processes the captured sign and adds to sentence</li>
          <li><strong>Repeat:</strong> Record more signs to build your complete sentence</li>
          <li><strong>Clear Last Word:</strong> Remove the most recent word if incorrect</li>
          <li><strong>Reset All:</strong> Clear entire sentence and start over</li>
          <li><strong>Predict & Submit:</strong> Sends sentence to Intent + SLM for analysis and creates ticket</li>
        </ol>
        <p className="tip">💡 <strong>Tip:</strong> Build complete sentences like "I need help with loan" or "Check account balance"</p>
      </div>
    </div>
  );
}

export default SignRecognition;
