import React, { useEffect, useState, useRef } from 'react';
import './Transfer.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';

function Transfer() {
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [form, setForm] = useState({ beneficiary_id: '', amount: '' });
  const [message, setMessage] = useState('');
  const [isTransferring, setIsTransferring] = useState(false);
  const [showBiometricAuth, setShowBiometricAuth] = useState(false);
  const [authProgress, setAuthProgress] = useState(0);
  const [biometricScores, setBiometricScores] = useState(null);
  const navigate = useNavigate();
  const webcamRef = useRef(null);

  useEffect(() => {
    axios.get('http://localhost:5000/api/account/beneficiaries', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setBeneficiaries(res.data))
      .catch(err => setMessage('Failed to load beneficiaries'));
  }, []);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    
    if (!form.beneficiary_id || !form.amount) {
      setMessage('Please select beneficiary and enter amount');
      return;
    }

    // Start biometric authentication
    setShowBiometricAuth(true);
    setMessage('🔐 Starting biometric authentication...');
    
    // Capture frames for authentication
    await captureAndTransfer();
  };

  const captureAndTransfer = async () => {
    setIsTransferring(true);
    setAuthProgress(0);
    
    try {
      // Capture 30 frames over 3 seconds
      const frames = [];
      const totalFrames = 30;
      
      setMessage('📹 Please look at the camera...');
      
      for (let i = 0; i < totalFrames; i++) {
        if (webcamRef.current) {
          const screenshot = webcamRef.current.getScreenshot();
          if (screenshot) {
            // Remove data:image/jpeg;base64, prefix
            const base64Frame = screenshot.split(',')[1];
            frames.push(base64Frame);
            
            // Update progress
            const progress = Math.round(((i + 1) / totalFrames) * 100);
            setAuthProgress(progress);
          }
        }
        
        // Wait 100ms between captures
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      if (frames.length < 20) {
        setMessage('❌ Insufficient frames captured. Please try again.');
        setIsTransferring(false);
        setShowBiometricAuth(false);
        return;
      }

      setMessage('🔐 Authenticating with biometrics...');

      // Call secure transfer endpoint
      const response = await axios.post(
        'http://localhost:5000/api/account/secure-transfer',
        {
          amount: parseFloat(form.amount),
          beneficiary_id: parseInt(form.beneficiary_id),
          videoFrames: frames
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );

      const { data } = response.data;
      setBiometricScores(data.biometricScores);
      
      setMessage(`✅ Transfer successful! New balance: ₹${data.newBalance}`);
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => navigate('/dashboard'), 3000);

    } catch (err) {
      console.error('Transfer error:', err);
      const errorData = err.response?.data;
      
      if (errorData?.enrollmentRequired) {
        setMessage('❌ Biometric enrollment required. Please enroll from settings.');
      } else if (errorData?.scores) {
        setBiometricScores(errorData.scores);
        setMessage(`❌ Authentication failed (Score: ${errorData.scores.fusionScore?.toFixed(2) || 'N/A'}). Please try again.`);
      } else {
        setMessage(`❌ ${errorData?.message || 'Transfer failed'}`);
      }
      
      setIsTransferring(false);
      setShowBiometricAuth(false);
    }
  };

  return (
    <div className="container">
      <h2>💸 Transfer Money</h2>
      
      {!showBiometricAuth ? (
        <form onSubmit={handleSubmit}>
          <select 
            name="beneficiary_id" 
            value={form.beneficiary_id} 
            onChange={handleChange} 
            required
            disabled={isTransferring}
          >
            <option value="">Select Beneficiary</option>
            {beneficiaries.map(b => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.account_number})
              </option>
            ))}
          </select>
          
          <input 
            name="amount" 
            type="number" 
            placeholder="Amount (₹)" 
            value={form.amount} 
            onChange={handleChange} 
            required
            disabled={isTransferring}
            min="1"
            step="0.01"
          />
          
          <button 
            className="action-btn transfer-btn" 
            type="submit"
            disabled={isTransferring}
          >
            {isTransferring ? 'Processing...' : '🔐 Transfer with Biometric Auth'}
          </button>
        </form>
      ) : (
        <div className="biometric-auth-container">
          <h3>🔐 Biometric Authentication</h3>
          <p className="auth-instruction">Please stay still and look at the camera</p>
          
          <div className="webcam-wrapper">
            <Webcam
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              className="transfer-webcam"
              audio={false}
              mirrored={true}
            />
          </div>
          
          <div className="auth-progress-container">
            <div className="auth-progress-bar">
              <div 
                className="auth-progress-fill" 
                style={{ width: `${authProgress}%` }}
              />
            </div>
            <p className="auth-progress-text">{authProgress}% Complete</p>
          </div>
          
          {biometricScores && (
            <div className="biometric-scores">
              <h4>Authentication Scores:</h4>
              <div className="score-grid">
                <div className="score-item">
                  <span className="score-label">👤 Face:</span>
                  <span className="score-value">{(biometricScores.face * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span className="score-label">✋ Hand:</span>
                  <span className="score-value">{(biometricScores.hand * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span className="score-label">✍️ Style:</span>
                  <span className="score-value">{(biometricScores.style * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item fusion-score">
                  <span className="score-label">🔒 Overall:</span>
                  <span className="score-value">{(biometricScores.fusion * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {message && (
        <p className={message.includes('✅') ? 'success-message' : 'error-message'}>
          {message}
        </p>
      )}
      
      <button 
        className="action-btn back-btn" 
        onClick={() => navigate('/dashboard')}
        disabled={isTransferring}
      >
        ← Back to Dashboard
      </button>
    </div>
  );
}

export default Transfer;