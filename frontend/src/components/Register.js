import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import './Register.css';

function Register() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);

  // Form states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  
  // UI states
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);

  // Capture face photo
  const captureFace = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCapturedImage(imageSrc);
      setMessage('Photo captured! Click Register to continue.');
    }
  };

  // Retake photo
  const retake = () => {
    setCapturedImage(null);
    setMessage('');
  };

  // Form validation
  const validateForm = () => {
    if (!username.trim()) {
      setMessage('❌ Username is required');
      return false;
    }
    if (!email.trim() || !email.includes('@')) {
      setMessage('❌ Valid email is required');
      return false;
    }
    if (!capturedImage) {
      setMessage('❌ Please capture your face photo');
      return false;
    }
    return true;
  };

  // Register user
  const registerUser = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setMessage('📤 Registering user...');

    try {
      // Convert base64 image to blob
      const blob = await (await fetch(capturedImage)).blob();
      
      // Create FormData
      const formData = new FormData();
      formData.append('username', username);
      formData.append('email', email);
      formData.append('image', new File([blob], 'face.jpg', { type: 'image/jpeg' }));

      // Register with backend
      const response = await axios.post(
        'http://localhost:5000/api/register',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      const { token } = response.data;
      localStorage.setItem('token', token);
      
      setMessage('✅ Registration successful! Redirecting to dashboard...');
      setIsLoading(false);
      
      // Redirect to dashboard
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);

    } catch (err) {
      console.error('Registration error:', err);
      const errorMsg = err.response?.data?.error || 'Registration failed';
      setMessage(`❌ ${errorMsg}`);
      setIsLoading(false);
    }
  };

  return (
    <div className="register-container">
      <button className="back-btn" onClick={() => navigate('/')}>
        <span>←</span> Back to Home
      </button>
      
      <h2>🔐 Register New Account</h2>
      
      <div className="register-form">
        {/* Form Inputs */}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
        />
            
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />

            {/* Webcam Section */}
            <div className="webcam-section">"

              <h3>📷 Capture Your Face</h3>
              
              {!capturedImage ? (
                <>
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    className="webcam"
                    mirrored={true}
                  />
                  <button 
                    onClick={captureFace} 
                    disabled={isLoading}
                    className="capture-btn"
                  >
                    📸 Capture Photo
                  </button>
                </>
              ) : (
                <>
                  <img src={capturedImage} alt="Captured" className="captured-image" />
                  <button onClick={retake} disabled={isLoading} className="retake-btn">
                    🔄 Retake Photo
                  </button>
                </>
              )}
            </div>

            {/* Register Button */}
            <button 
              onClick={registerUser} 
              disabled={isLoading || !capturedImage}
              className="register-button"
            >
              {isLoading ? '⏳ Registering...' : '✅ Register'}
            </button>

        {/* Message Display */}
        {message && (
          <p className={`message ${message.includes('✅') || message.includes('success') ? 'success' : 'error'}`}>
            {message}
          </p>
        )}
      </div>

      <p className="login-link">
        Already have an account? <span onClick={() => navigate('/login')}>Login</span>
      </p>
    </div>
  );
}

export default Register;
