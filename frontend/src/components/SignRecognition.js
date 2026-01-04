import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import './SignRecognition.css';

function SignRecognition() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  
  const [isRecording, setIsRecording] = useState(false);
  const [recordedFrames, setRecordedFrames] = useState([]);
  const [recognizedText, setRecognizedText] = useState('');
  const [editableText, setEditableText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [progress, setProgress] = useState(0);
  
  // Enhanced features from inference.py
  const [confidence, setConfidence] = useState(0);
  const [intent, setIntent] = useState('');
  const [detectedSigns, setDetectedSigns] = useState([]);
  const [top3Predictions, setTop3Predictions] = useState([]);
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [useSmoothing, setUseSmoothing] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [smoothingWindow, setSmoothingWindow] = useState(5);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [serviceHealth, setServiceHealth] = useState(null);
  const [landmarksDetected, setLandmarksDetected] = useState(false);

  // Hand connections for drawing skeleton
  const HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4],           // Thumb
    [0, 5], [5, 6], [6, 7], [7, 8],           // Index
    [0, 9], [9, 10], [10, 11], [11, 12],      // Middle
    [0, 13], [13, 14], [14, 15], [15, 16],    // Ring
    [0, 17], [17, 18], [18, 19], [19, 20],    // Pinky
    [5, 9], [9, 13], [13, 17]                  // Palm
  ];

  // Pose connections (upper body)
  const POSE_CONNECTIONS = [
    [11, 12], // Shoulders
    [11, 13], [13, 15], // Left arm
    [12, 14], [14, 16], // Right arm
    [0, 1], [0, 4],     // Eyes
    [1, 2], [4, 5],     // Eye to ear
    [2, 3], [5, 6],     // Ear
    [11, 23], [12, 24], // Torso
    [23, 24]            // Hips
  ];

  // Draw landmarks on canvas
  const drawLandmarks = useCallback((landmarks) => {
    const canvas = canvasRef.current;
    const webcam = webcamRef.current;
    
    if (!canvas || !webcam || !webcam.video) return;
    
    const video = webcam.video;
    const ctx = canvas.getContext('2d');
    
    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (!landmarks || !landmarks.detected) {
      // Show "No pose detected" message
      ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
      ctx.font = '24px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('⚠️ No pose detected - Please stand in frame', canvas.width / 2, 40);
      return;
    }
    
    const { pose, left_hand, right_hand } = landmarks;
    
    // Mirror the x coordinates since webcam is mirrored
    const mirrorX = (x) => 1 - x;
    
    // Draw pose connections (green)
    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 3;
    POSE_CONNECTIONS.forEach(([i, j]) => {
      if (pose[i] && pose[j]) {
        const [x1, y1] = [mirrorX(pose[i][0]) * canvas.width, pose[i][1] * canvas.height];
        const [x2, y2] = [mirrorX(pose[j][0]) * canvas.width, pose[j][1] * canvas.height];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
    });
    
    // Draw pose landmarks (green dots)
    ctx.fillStyle = '#00FF00';
    pose.slice(0, 25).forEach(([x, y, z], idx) => {
      const px = mirrorX(x) * canvas.width;
      const py = y * canvas.height;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, 2 * Math.PI);
      ctx.fill();
    });
    
    // Draw left hand (cyan)
    if (left_hand && left_hand.some(lm => lm[0] !== 0 || lm[1] !== 0)) {
      ctx.strokeStyle = '#00FFFF';
      ctx.lineWidth = 2;
      HAND_CONNECTIONS.forEach(([i, j]) => {
        const [x1, y1] = [mirrorX(left_hand[i][0]) * canvas.width, left_hand[i][1] * canvas.height];
        const [x2, y2] = [mirrorX(left_hand[j][0]) * canvas.width, left_hand[j][1] * canvas.height];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      });
      
      ctx.fillStyle = '#00FFFF';
      left_hand.forEach(([x, y]) => {
        const px = mirrorX(x) * canvas.width;
        const py = y * canvas.height;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }
    
    // Draw right hand (magenta)
    if (right_hand && right_hand.some(lm => lm[0] !== 0 || lm[1] !== 0)) {
      ctx.strokeStyle = '#FF00FF';
      ctx.lineWidth = 2;
      HAND_CONNECTIONS.forEach(([i, j]) => {
        const [x1, y1] = [mirrorX(right_hand[i][0]) * canvas.width, right_hand[i][1] * canvas.height];
        const [x2, y2] = [mirrorX(right_hand[j][0]) * canvas.width, right_hand[j][1] * canvas.height];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      });
      
      ctx.fillStyle = '#FF00FF';
      right_hand.forEach(([x, y]) => {
        const px = mirrorX(x) * canvas.width;
        const py = y * canvas.height;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }
    
    // Draw detection status
    ctx.fillStyle = '#00FF00';
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('✓ Pose Detected', 10, 25);
    
    const hasLeftHand = left_hand && left_hand.some(lm => lm[0] !== 0);
    const hasRightHand = right_hand && right_hand.some(lm => lm[0] !== 0);
    
    if (hasLeftHand) ctx.fillText('✓ Left Hand', 10, 45);
    if (hasRightHand) ctx.fillText('✓ Right Hand', 10, 65);
  }, []);

  // Real-time landmark extraction
  const extractLandmarksRealtime = useCallback(async () => {
    if (!webcamRef.current || !showLandmarks) return;
    
    try {
      const screenshot = webcamRef.current.getScreenshot();
      if (!screenshot) return;
      
      const base64Frame = screenshot.split(',')[1];
      
      const response = await axios.post(
        'http://localhost:8000/api/biometric/extract-landmarks',
        { frame: base64Frame },
        { timeout: 500 }  // Quick timeout for real-time
      );
      
      if (response.data.success) {
        setLandmarksDetected(response.data.data.detected);
        drawLandmarks(response.data.data);
      }
    } catch (err) {
      // Silently ignore errors for real-time extraction
    }
  }, [showLandmarks, drawLandmarks]);

  // Real-time landmark extraction loop
  useEffect(() => {
    let intervalId;
    
    if (showLandmarks && !isProcessing) {
      intervalId = setInterval(extractLandmarksRealtime, 100);  // 10 FPS for landmarks
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [showLandmarks, isProcessing, extractLandmarksRealtime]);

  // Check service health on mount
  useEffect(() => {
    checkServiceHealth();
    const healthInterval = setInterval(checkServiceHealth, 30000); // Check every 30s
    return () => clearInterval(healthInterval);
  }, []);

  const checkServiceHealth = async () => {
    try {
      const response = await axios.get('http://localhost:8000/health');
      setServiceHealth(response.data);
    } catch (err) {
      setServiceHealth({ status: 'error', message: 'Service unavailable' });
    }
  };

  const clearHistory = () => {
    setDetectedSigns([]);
    setTop3Predictions([]);
    setMessage('🗑️ History cleared');
  };

  const handleStartRecording = () => {
    setRecordedFrames([]);
    setRecognizedText('');
    setEditableText('');
    setMessage('');
    setProgress(0);
    
    // 3 second countdown
    setCountdown(3);
    const countdownInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownInterval);
          startCapture();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const startCapture = () => {
    setIsRecording(true);
    setMessage('🎥 Recording... Please perform your signs');
    
    const frames = [];
    const totalFrames = 50; // 5 seconds of recording
    let frameCount = 0;
    
    const captureInterval = setInterval(() => {
      if (webcamRef.current) {
        const screenshot = webcamRef.current.getScreenshot();
        if (screenshot) {
          const base64Frame = screenshot.split(',')[1];
          frames.push(base64Frame);
          frameCount++;
          
          const progressPercent = Math.round((frameCount / totalFrames) * 100);
          setProgress(progressPercent);
          
          if (frameCount >= totalFrames) {
            clearInterval(captureInterval);
            setIsRecording(false);
            setRecordedFrames(frames);
            recognizeSign(frames);
          }
        }
      }
    }, 100); // Capture every 100ms (50 frames in 5 seconds)
  };

  const recognizeSign = async (frames) => {
    setIsProcessing(true);
    setMessage('🔍 Recognizing sign language...');
    
    try {
      const response = await axios.post(
        'http://localhost:5000/api/biometric/recognize-sign',
        { videoFrames: frames },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const { recognizedSign, sentence, intent, confidence, top3, frames_processed } = response.data.data;
      
      const fullText = sentence || recognizedSign || 'No sign recognized';
      setRecognizedText(fullText);
      setEditableText(fullText);
      setConfidence(confidence || 0);
      setIntent(intent || 'UNKNOWN');
      
      // Add to detected signs history
      if (recognizedSign) {
        setDetectedSigns(prev => [...prev, { 
          sign: recognizedSign, 
          confidence, 
          time: new Date().toLocaleTimeString() 
        }]);
      }
      
      // Store top 3 predictions if available
      if (top3) {
        setTop3Predictions(top3);
      }
      
      setMessage(`✅ Recognized: "${recognizedSign}" | Intent: ${intent} | Confidence: ${(confidence * 100).toFixed(1)}%`);
      setIsProcessing(false);
      
    } catch (err) {
      console.error('Sign recognition error:', err);
      setMessage('❌ ' + (err.response?.data?.message || 'Sign recognition failed'));
      setIsProcessing(false);
    }
  };

  const handleSubmitTicket = async () => {
    if (!editableText.trim()) {
      setMessage('❌ Please enter or edit the query text');
      return;
    }

    try {
      setIsProcessing(true);
      setMessage('📤 Submitting support ticket...');
      
      await axios.post(
        'http://localhost:5000/api/support/tickets',
        {
          query_text: editableText,
          query_source: 'sign_language'
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setMessage('✅ Support ticket submitted successfully!');
      
      setTimeout(() => {
        navigate('/support-tickets');
      }, 2000);
      
    } catch (err) {
      console.error('Ticket submission error:', err);
      setMessage('❌ ' + (err.response?.data?.message || 'Failed to submit ticket'));
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setRecordedFrames([]);
    setRecognizedText('');
    setEditableText('');
    setMessage('');
    setProgress(0);
    setConfidence(0);
    setIntent('');
    setTop3Predictions([]);
  };

  return (
    <div className="sign-recognition-container">
      <div className="sign-recognition-header">
        <h2>🤟 NS-AGF Sign Language Recognition</h2>
        <div className="header-controls">
          {serviceHealth && (
            <span className={`service-status ${serviceHealth.status === 'ok' ? 'online' : 'offline'}`}>
              ● {serviceHealth.status === 'ok' ? 'Service Online' : 'Service Offline'}
              {serviceHealth.num_classes && ` (${serviceHealth.num_classes} classes)`}
            </span>
          )}
          <button onClick={() => navigate('/support-tickets')} className="back-link">
            ← Back to Support
          </button>
        </div>
      </div>

      <div className="sign-main-content">
        <div className="webcam-section">
          <div className="webcam-wrapper-large" style={{ position: 'relative' }}>
            <Webcam
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              className="sign-webcam-large"
              audio={false}
              mirrored={true}
              videoConstraints={{
                width: 1280,
                height: 720,
                facingMode: "user"
              }}
            />
            
            {/* Landmark visualization canvas */}
            {showLandmarks && (
              <canvas
                ref={canvasRef}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none'
                }}
              />
            )}
            
            {countdown > 0 && (
              <div className="countdown-overlay">
                <div className="countdown-number">{countdown}</div>
              </div>
            )}
            
            {isRecording && (
              <div className="recording-indicator">
                <span className="recording-dot"></span>
                <span>Recording...</span>
              </div>
            )}
            
            {/* Landmark toggle button */}
            <button
              onClick={() => setShowLandmarks(!showLandmarks)}
              style={{
                position: 'absolute',
                bottom: '10px',
                right: '10px',
                background: showLandmarks ? '#00ff00' : '#666',
                color: '#000',
                border: 'none',
                padding: '8px 12px',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 'bold'
              }}
            >
              {showLandmarks ? '🦴 Landmarks ON' : '🦴 Landmarks OFF'}
            </button>
          </div>

          {isRecording && (
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <p className="progress-text">{progress}% Complete</p>
            </div>
          )}

          <div className="control-buttons">
            <button
              onClick={handleStartRecording}
              disabled={isRecording || isProcessing}
              className="btn-record"
            >
              {isRecording ? '🎥 Recording...' : '🎥 Start Recording (5 sec)'}
            </button>
            
            {recordedFrames.length > 0 && !isRecording && (
              <button
                onClick={handleReset}
                disabled={isProcessing}
                className="btn-reset"
              >
                🔄 Record Again
              </button>
            )}
            
            {detectedSigns.length > 0 && (
              <button
                onClick={clearHistory}
                disabled={isProcessing}
                className="btn-clear"
              >
                🗑️ Clear History
              </button>
            )}
          </div>
        </div>

        <div className="recognition-section">
          <h3>Recognition Results</h3>
          
          {/* Confidence and Intent Display */}
          {confidence > 0 && (
            <div className="metrics-display">
              <div className="metric-item">
                <span className="metric-label">Confidence:</span>
                <div className="confidence-bar-container">
                  <div 
                    className={`confidence-bar ${
                      confidence > confidenceThreshold ? 'high' :
                      confidence > 0.5 ? 'medium' : 'low'
                    }`}
                    style={{ width: `${confidence * 100}%` }}
                  >
                    {(confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
              <div className="metric-item">
                <span className="metric-label">Intent:</span>
                <span className="intent-badge">{intent}</span>
              </div>
            </div>
          )}

          {/* Top 3 Predictions */}
          {top3Predictions.length > 0 && (
            <div className="predictions-panel">
              <h4>Model Predictions (Top 3)</h4>
              {top3Predictions.map((pred, idx) => (
                <div key={idx} className={`prediction-item ${idx === 0 ? 'top-prediction' : ''}`}>
                  <span className="prediction-rank">{idx + 1}.</span>
                  <span className="prediction-sign">{pred.sign}</span>
                  <div className="prediction-bar">
                    <div 
                      className="prediction-fill"
                      style={{ width: `${pred.confidence * 100}%` }}
                    />
                  </div>
                  <span className="prediction-confidence">{(pred.confidence * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}

          {/* Detected Signs History */}
          {detectedSigns.length > 0 && (
            <div className="history-panel">
              <h4>Detected Signs History</h4>
              <div className="history-items">
                {detectedSigns.slice(-5).reverse().map((item, idx) => (
                  <div key={idx} className="history-item">
                    <span className="history-sign">{item.sign}</span>
                    <span className="history-confidence">{(item.confidence * 100).toFixed(0)}%</span>
                    <span className="history-time">{item.time}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {isProcessing && !recognizedText && (
            <div className="processing-state">
              <div className="spinner"></div>
              <p>Processing sign language...</p>
            </div>
          )}

          {recognizedText && (
            <>
              <div className="recognized-display">
                <p className="recognized-original">{recognizedText}</p>
              </div>

              <div className="edit-section">
                <label htmlFor="editQuery">Edit or confirm your query:</label>
                <textarea
                  id="editQuery"
                  value={editableText}
                  onChange={(e) => setEditableText(e.target.value)}
                  rows={6}
                  placeholder="Edit the recognized text if needed..."
                  disabled={isProcessing}
                />
              </div>

              <button
                onClick={handleSubmitTicket}
                disabled={isProcessing || !editableText.trim()}
                className="btn-submit"
              >
                {isProcessing ? '📤 Submitting...' : '📤 Submit Support Ticket'}
              </button>
            </>
          )}

          {!recognizedText && !isProcessing && (
            <div className="empty-state">
              <p>👆 Click "Start Recording" to capture your sign language query</p>
              <p className="instruction">
                The system will record for 5 seconds. Perform your signs clearly
                in front of the camera.
              </p>
            </div>
          )}
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
          <li>Click "Start Recording" button</li>
          <li>Wait for 3-second countdown</li>
          <li>Perform your sign language query (5 seconds)</li>
          <li>System will recognize and convert to text</li>
          <li>Review and edit the text if needed</li>
          <li>Submit as a support ticket</li>
        </ol>
      </div>
    </div>
  );
}

export default SignRecognition;
