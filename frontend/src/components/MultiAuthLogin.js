import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import './MultiAuth.css';

function MultiAuthLogin() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Form states
  const [username, setUsername] = useState('');
  const [authMethod, setAuthMethod] = useState('face'); // 'face', 'voice', 'otp'
  
  // Face auth states
  const [capturedFace, setCapturedFace] = useState(null);

  // Voice auth states
  const [isRecording, setIsRecording] = useState(false);
  const [voiceBlob, setVoiceBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);

  // OTP auth states
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');

  // UI states
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Recording timer
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 10) {
            stopVoiceRecording();
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  // ==================== Face Authentication ====================
  const captureFace = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCapturedFace(imageSrc);
      setMessage('✅ Face photo captured');
    }
  };

  const retakeFace = () => {
    setCapturedFace(null);
    setMessage('');
  };

  const loginWithFace = async () => {
    if (!username.trim()) {
      setMessage('❌ Username is required');
      return;
    }
    if (!capturedFace) {
      setMessage('❌ Please capture your face photo');
      return;
    }

    setIsLoading(true);
    setMessage('📤 Verifying face...');

    try {
      const blob = await (await fetch(capturedFace)).blob();
      const formData = new FormData();
      formData.append('username', username);
      formData.append('image', new File([blob], 'face.jpg', { type: 'image/jpeg' }));

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
      console.error('Face login error:', err);
      const errorMsg = err.response?.data?.error || 'Face authentication failed';
      setMessage(`❌ ${errorMsg}`);
      setIsLoading(false);
    }
  };

  // ==================== Voice Authentication ====================
  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setVoiceBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setMessage('🎤 Recording... Speak clearly');
    } catch (err) {
      console.error('Microphone error:', err);
      setMessage('❌ Microphone access denied');
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setMessage('✅ Voice recorded successfully!');
    }
  };

  const retakeVoice = () => {
    setVoiceBlob(null);
    setMessage('');
  };

  const loginWithVoice = async () => {
    if (!username.trim()) {
      setMessage('❌ Username is required');
      return;
    }
    if (!voiceBlob) {
      setMessage('❌ Please record your voice');
      return;
    }

    setIsLoading(true);
    setMessage('📤 Verifying voice...');

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('audio', new File([voiceBlob], 'voice.wav', { type: 'audio/wav' }));

      const response = await axios.post(
        'http://localhost:5000/api/voice/login',
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
      console.error('Voice login error:', err);
      const errorMsg = err.response?.data?.error || 'Voice authentication failed';
      setMessage(`❌ ${errorMsg}`);
      setIsLoading(false);
    }
  };

  // ==================== OTP Authentication ====================
  const sendOTP = async () => {
    if (!username.trim()) {
      setMessage('❌ Username or email is required');
      return;
    }

    setIsLoading(true);
    setMessage('📤 Sending OTP...');
    
    try {
      const response = await axios.post('http://localhost:5000/api/otp/send', {
        email: username,
        username: username
      });
      
      setMaskedEmail(response.data.email);
      setOtpSent(true);
      setMessage(`✅ OTP sent to ${response.data.email}`);
      setIsLoading(false);
    } catch (err) {
      console.error('OTP send error:', err);
      const errorMsg = err.response?.data?.error || 'Failed to send OTP';
      setMessage(`❌ ${errorMsg}`);
      setIsLoading(false);
    }
  };

  const loginWithOTP = async () => {
    if (!otp || otp.length !== 6) {
      setMessage('❌ Please enter valid 6-digit OTP');
      return;
    }

    setIsLoading(true);
    setMessage('📤 Verifying OTP...');

    try {
      const response = await axios.post('http://localhost:5000/api/otp/verify', {
        email: username,
        username: username,
        otp: otp
      });

      const { token } = response.data;
      localStorage.setItem('token', token);
      
      setMessage('✅ Login successful! Redirecting...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);

    } catch (err) {
      console.error('OTP verify error:', err);
      const errorMsg = err.response?.data?.error || 'OTP verification failed';
      setMessage(`❌ ${errorMsg}`);
      setIsLoading(false);
    }
  };

  // ==================== RENDER ====================
  return (
    <div className="login-container">
      <button className="back-btn" onClick={() => navigate('/')}>
        <span>←</span> Back to Home
      </button>
      
      <h1>🔐 Login</h1>
      <p className="subtitle">Choose your authentication method</p>

      {/* Username Input */}
      <div className="form-section">
        <input 
          type="text"
          placeholder="Username or Email" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
          required
        />
      </div>

      {/* Authentication Method Selector */}
      <div className="auth-method-selector">
        <button 
          className={`method-btn ${authMethod === 'face' ? 'active' : ''}`}
          onClick={() => {
            setAuthMethod('face');
            setCapturedFace(null);
            setVoiceBlob(null);
            setOtpSent(false);
            setMessage('');
          }}
          disabled={isLoading}
        >
          📷 Face
        </button>
        <button 
          className={`method-btn ${authMethod === 'voice' ? 'active' : ''}`}
          onClick={() => {
            setAuthMethod('voice');
            setCapturedFace(null);
            setVoiceBlob(null);
            setOtpSent(false);
            setMessage('');
          }}
          disabled={isLoading}
        >
          🎤 Voice
        </button>
        <button 
          className={`method-btn ${authMethod === 'otp' ? 'active' : ''}`}
          onClick={() => {
            setAuthMethod('otp');
            setCapturedFace(null);
            setVoiceBlob(null);
            setOtpSent(false);
            setMessage('');
          }}
          disabled={isLoading}
        >
          🔐 OTP
        </button>
      </div>

      {/* Face Authentication */}
      {authMethod === 'face' && (
        <div className="face-section">
          <h3>📸 Face Authentication</h3>
          <div className="webcam-container">
            <Webcam 
              ref={webcamRef} 
              screenshotFormat="image/jpeg"
              className="webcam-preview"
              mirrored={true}
            />
          </div>
          
          {!capturedFace ? (
            <button 
              onClick={captureFace} 
              disabled={isLoading}
              className="capture-btn"
            >
              📷 Capture Face
            </button>
          ) : (
            <div className="captured-preview">
              <img src={capturedFace} alt="Captured Face" />
              <div className="btn-group">
                <button onClick={retakeFace} className="retake-btn">🔄 Retake</button>
                <button onClick={loginWithFace} disabled={isLoading} className="login-button">
                  {isLoading ? '🔄 Verifying...' : '🚀 Login with Face'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Voice Authentication */}
      {authMethod === 'voice' && (
        <div className="voice-section">
          <h3>🎤 Voice Authentication</h3>
          <p className="instruction">Speak clearly for 5-10 seconds</p>
          
          {!voiceBlob ? (
            <div className="recording-controls">
              {!isRecording ? (
                <button onClick={startVoiceRecording} disabled={isLoading} className="record-btn">
                  🎤 Start Recording
                </button>
              ) : (
                <>
                  <div className="recording-indicator">
                    <span className="pulse">●</span> Recording... {recordingTime}s
                  </div>
                  <button onClick={stopVoiceRecording} className="stop-btn">
                    ⏹️ Stop Recording
                  </button>
                </>
              )}
            </div>
          ) : (
            <div className="voice-preview">
              <p>✅ Voice recorded ({recordingTime}s)</p>
              <audio controls src={URL.createObjectURL(voiceBlob)} />
              <div className="btn-group">
                <button onClick={retakeVoice} className="retake-btn">🔄 Re-record</button>
                <button onClick={loginWithVoice} disabled={isLoading} className="login-button">
                  {isLoading ? '🔄 Verifying...' : '🚀 Login with Voice'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* OTP Authentication */}
      {authMethod === 'otp' && (
        <div className="otp-section">
          <h3>🔐 OTP Authentication</h3>
          {!otpSent ? (
            <>
              <p className="instruction">We'll send a one-time password to your registered email</p>
              <button onClick={sendOTP} disabled={isLoading} className="send-otp-btn">
                {isLoading ? '📤 Sending...' : '📧 Send OTP'}
              </button>
            </>
          ) : (
            <>
              <p className="instruction">Enter the 6-digit OTP sent to {maskedEmail}</p>
              <input
                type="text"
                placeholder="Enter OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                className="otp-input"
                disabled={isLoading}
              />
              <button 
                onClick={loginWithOTP} 
                disabled={isLoading || otp.length !== 6}
                className="login-button"
              >
                {isLoading ? '🔄 Verifying...' : '🚀 Login with OTP'}
              </button>
              <button onClick={() => {setOtpSent(false); setOtp('');}} className="resend-btn">
                🔄 Resend OTP
              </button>
            </>
          )}
        </div>
      )}

      {/* Message Display */}
      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
      
      <p className="register-link">
        Don't have an account? <span onClick={() => navigate('/register')}>Register here</span>
      </p>
    </div>
  );
}

export default MultiAuthLogin;
