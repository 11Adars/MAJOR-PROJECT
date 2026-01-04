import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './BiometricEnrollment.css';

function BiometricEnrollment() {
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
      <h2>🔐 Biometric Enrollment</h2>
      
      <div className="info-card">
        <h3>Why Enroll Biometrics?</h3>
        <p>
          Your biometric profile (face + hand + behavioral style) enables secure 
          money transfers <strong>without requiring a PIN</strong>.
        </p>
        <ul>
          <li>✅ Multi-modal authentication (Face + Hand + Style)</li>
          <li>✅ Continuous monitoring during transactions</li>
          <li>✅ Higher security than traditional PIN</li>
          <li>✅ No password to remember</li>
        </ul>
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
      
      <div className="technical-details">
        <details>
          <summary>🔬 Technical Details (Novel Contribution)</summary>
          <div className="tech-info">
            <h4>Multi-Modal Biometric Fusion:</h4>
            <ul>
              <li><strong>Face Recognition (40%)</strong>: HOG + Histogram + Texture + Edge analysis</li>
              <li><strong>Hand Geometry (35%)</strong>: Contour analysis + Color histograms + Hu moments</li>
              <li><strong>Behavioral Style (25%)</strong>: Optical flow + Temporal motion patterns</li>
            </ul>
            <p><strong>Fusion Algorithm:</strong> Weighted score-level combination</p>
            <p><strong>Threshold:</strong> 65% match required for authentication</p>
          </div>
        </details>
      </div>
    </div>
  );
}

export default BiometricEnrollment;
