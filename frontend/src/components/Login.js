import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  
  // Form states
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Face login states
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);

  // Capture face photo
  const captureFace = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCapturedImage(imageSrc);
      setMessage('✅ Face photo captured');
    }
  };

  // Form validation
  const validateForm = () => {
    if (!username.trim()) {
      setMessage('❌ Username is required');
      return false;
    }
    if (!capturedImage) {
      setMessage('❌ Please capture your face photo');
      return false;
    }
    return true;
  };

  // Login with face + password
  const loginUser = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setMessage('📤 Logging in...');

    try {
      // Convert base64 image to blob
      const blob = await (await fetch(capturedImage)).blob();
      
      // Create FormData
      const formData = new FormData();
      formData.append('username', username);
      formData.append('image', new File([blob], 'face.jpg', { type: 'image/jpeg' }));

      // Login with backend
      const response = await axios.post(
        'http://localhost:5000/api/login',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      const { token } = response.data;
      localStorage.setItem('token', token);
      
      setMessage('✅ Login successful! Redirecting...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);

    } catch (err) {
      console.error('Login error:', err);
      const errorMsg = err.response?.data?.error || 'Login failed';
      setMessage(`❌ ${errorMsg}`);
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <button className="back-btn" onClick={() => navigate('/')}>
        <span>←</span> Back to Home
      </button>
      
      <h1>🔐 Login</h1>
      
      <div className="form-section">
        <input 
          type="text"
          placeholder="Username" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
          required
        />
      </div>
      
      <div className="face-section">
        <h3>📸 Capture Face Photo</h3>
        <div className="webcam-container">
          <Webcam 
            ref={webcamRef} 
            screenshotFormat="image/jpeg"
            className="webcam-preview"
          />
        </div>
        
        <button 
          onClick={captureFace} 
          disabled={isLoading}
          className="capture-btn"
        >
          📷 Capture Face
        </button>
        
        {capturedImage && (
          <div className="captured-preview">
            <img src={capturedImage} alt="Captured Face" />
            <p>✅ Face captured successfully</p>
          </div>
        )}
      </div>
      
      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
      
      <button 
        onClick={loginUser} 
        disabled={isLoading || !capturedImage}
        className="login-button"
      >
        {isLoading ? '🔄 Logging in...' : '🚀 Login'}
      </button>
      
      <p className="register-link">
        Don't have an account? <span onClick={() => navigate('/register')}>Register here</span>
      </p>
    </div>
  );
}

export default Login;