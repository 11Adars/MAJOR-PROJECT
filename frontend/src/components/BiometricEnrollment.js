import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import { FaArrowLeft, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';
import './BiometricEnrollment.css';

function BiometricEnrollment() {
  const navigate = useNavigate();
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureProgress, setCaptureProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [isEnrolled, setIsEnrolled] = useState(false);
  const webcamRef = useRef(null);
  
  const startEnrollment = () => {
    setMessage('📹 Capturing biometrics... Please move your head and hands naturally');
    setIsCapturing(true);
    setCaptureProgress(0);
    
    const frames = [];
    const totalFrames = 30; // Capture 30 frames
    
    const captureInterval = setInterval(() => {
      const frame = webcamRef.current.getScreenshot();
      if (frame) {
        frames.push(frame);
        setCaptureProgress((frames.length / totalFrames) * 100);
      }
      
      if (frames.length >= totalFrames) {
        clearInterval(captureInterval);
        submitEnrollment(frames);
      }
    }, 100); // Capture at 10 fps (100ms interval)
  };
  
  const submitEnrollment = async (frames) => {
    try {
      setMessage('⏳ Processing biometric enrollment...');
      
      const response = await axios.post(
        'http://localhost:5000/api/biometric/enroll',
        { videoFrames: frames },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.data.success) {
        setMessage('✅ Biometric enrollment successful! You can now make secure transfers.');
        setIsEnrolled(true);
        setIsCapturing(false);
      } else {
        setMessage('❌ Enrollment failed. Please try again.');
        setIsCapturing(false);
      }
    } catch (error) {
      console.error('Enrollment error:', error);
      const errorMsg = error.response?.data?.message || error.message || 'Enrollment failed';
      setMessage(`❌ ${errorMsg}`);
      setIsCapturing(false);
    }
  };
  
  return (
    <div className="biometric-enrollment-container">
      {/* Back Button */}
      <button className="back-button" onClick={() => navigate('/dashboard')}>
        <FaArrowLeft /> Back to Dashboard
      </button>

      <div className="enrollment-header">
        <h2>🔐 Biometric Enrollment</h2>
        <p className="subtitle">Set up secure authentication for PIN-free transfers</p>
      </div>
      
      {/* User Guidelines */}
      <div className="guidelines-card">
        <h3>📋 Enrollment Guidelines</h3>
        <div className="guidelines-grid">
          <div className="guideline-item">
            <div className="guideline-icon">💡</div>
            <div className="guideline-content">
              <h4>Lighting Requirements</h4>
              <p>Ensure you're in a well-lit area with even lighting on your face. Avoid direct backlight or harsh shadows.</p>
            </div>
          </div>
          
          <div className="guideline-item">
            <div className="guideline-icon">📍</div>
            <div className="guideline-content">
              <h4>Camera Position</h4>
              <p>Position yourself centered in the frame with your face and hands clearly visible. Maintain 1-2 feet distance.</p>
            </div>
          </div>
          
          <div className="guideline-item">
            <div className="guideline-icon">🎭</div>
            <div className="guideline-content">
              <h4>During Capture</h4>
              <p>Make natural facial expressions, move your head slightly (left, right, up, down), and show hand movements naturally.</p>
            </div>
          </div>
          
          <div className="guideline-item">
            <div className="guideline-icon">⏱️</div>
            <div className="guideline-content">
              <h4>Capture Duration</h4>
              <p>The enrollment process takes ~3 seconds. Stay in frame and follow the on-screen instructions.</p>
            </div>
          </div>
          
          <div className="guideline-item">
            <div className="guideline-icon">✋</div>
            <div className="guideline-content">
              <h4>Hand Gestures</h4>
              <p>Show both hands clearly with natural movements. Open palms work best for accurate hand geometry capture.</p>
            </div>
          </div>
          
          <div className="guideline-item">
            <div className="guideline-icon">🔒</div>
            <div className="guideline-content">
              <h4>Privacy & Security</h4>
              <p>Your biometric data is encrypted and stored securely. It never leaves our secure servers.</p>
            </div>
          </div>
        </div>

        <div className="important-note">
          <FaExclamationTriangle className="note-icon" />
          <div>
            <strong>Important:</strong> Ensure no one else is visible in the frame during enrollment. 
            The system captures face, hand geometry, and behavioral patterns for multi-modal authentication.
          </div>
        </div>
      </div>
      
      <div className="webcam-section">
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          videoConstraints={{ width: 640, height: 480, facingMode: 'user' }}
          className="webcam-feed"
        />
        
        {isCapturing && (
          <div className="capture-overlay">
            <div className="progress-container">
              <p>Capturing: {captureProgress.toFixed(0)}%</p>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${captureProgress}%` }}
                ></div>
              </div>
              <p className="instructions">
                🎭 Make different facial expressions<br />
                ✋ Move your hands naturally<br />
                🔄 Turn your head slightly
              </p>
            </div>
          </div>
        )}
      </div>
      
      <div className="controls">
        <button
          className="enroll-btn"
          onClick={startEnrollment}
          disabled={isCapturing || isEnrolled}
        >
          {isCapturing ? '⏳ Capturing...' : isEnrolled ? '✅ Enrolled' : '🚀 Start Enrollment'}
        </button>
        
        {isEnrolled && (
          <button
            className="re-enroll-btn"
            onClick={() => {
              setIsEnrolled(false);
              setMessage('');
            }}
          >
            🔄 Re-enroll
          </button>
        )}
      </div>
      
      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : message.includes('❌') ? 'error' : 'info'}`}>
          {message}
        </div>
      )}
    </div>
  );
}

export default BiometricEnrollment;
