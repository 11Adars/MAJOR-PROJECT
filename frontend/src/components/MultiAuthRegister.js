import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import './MultiAuth.css';

function MultiAuthRegister() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Form states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  
  // Authentication modes
  const [activeAuthMethods, setActiveAuthMethods] = useState({
    face: true,
    voice: true,
    otp: true
  });

  // Face auth states
  const [capturedFace, setCapturedFace] = useState(null);
  const [faceStatus, setFaceStatus] = useState(''); // 'captured', 'pending', 'completed'

  // Voice auth states
  const [isRecording, setIsRecording] = useState(false);
  const [voiceBlob, setVoiceBlob] = useState(null);
  const [voiceStatus, setVoiceStatus] = useState(''); // 'recorded', 'pending', 'completed'
  const [recordingTime, setRecordingTime] = useState(0);

  // UI states
  const [currentStep, setCurrentStep] = useState(1); // 1: Basic Info, 2: Face, 3: Voice, 4: Complete
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [registrationData, setRegistrationData] = useState(null);

  // Recording timer
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  // ==================== STEP 1: Basic Information ====================
  const validateBasicInfo = () => {
    if (!username.trim()) {
      setMessage('❌ Username is required');
      return false;
    }
    if (!email.trim() || !email.includes('@')) {
      setMessage('❌ Valid email is required');
      return false;
    }
    if (!phone.trim() || phone.length < 10) {
      setMessage('❌ Valid phone number is required');
      return false;
    }
    return true;
  };

  const handleBasicInfoNext = () => {
    if (validateBasicInfo()) {
      setCurrentStep(2);
      setMessage('');
    }
  };

  // ==================== STEP 2: Face Authentication ====================
  const captureFace = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCapturedFace(imageSrc);
      setFaceStatus('captured');
      setMessage('✅ Face photo captured successfully!');
    }
  };

  const retakeFace = () => {
    setCapturedFace(null);
    setFaceStatus('');
    setMessage('');
  };

  const handleFaceNext = async () => {
    if (!capturedFace) {
      setMessage('❌ Please capture your face photo first');
      return;
    }
    setCurrentStep(3);
    setMessage('');
  };

  // ==================== STEP 3: Voice Authentication ====================
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
        setVoiceStatus('recorded');
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setMessage('🎤 Recording... Please speak for 5-10 seconds');
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
    setVoiceStatus('');
    setMessage('');
  };

  const handleVoiceNext = () => {
    // Voice is optional, proceed to registration even without voice
    registerUser();
  };

  const skipVoice = () => {
    setMessage('ℹ️ Voice authentication skipped. You can still login with Face or OTP.');
    registerUser();
  };

  // ==================== STEP 4: Final Registration ====================
  const registerUser = async () => {
    if (!capturedFace) {
      setMessage('❌ Please capture your face photo first');
      return;
    }
    // Voice is optional, continue even if not recorded

    setIsLoading(true);
    setMessage('📤 Registering your account...');

    try {
      // Create FormData for multipart request
      const formData = new FormData();
      formData.append('username', username);
      formData.append('email', email);
      formData.append('phone', phone);

      // Add face image
      if (capturedFace) {
        const faceBlob = await (await fetch(capturedFace)).blob();
        formData.append('face', new File([faceBlob], 'face.jpg', { type: 'image/jpeg' }));
      }

      // Add voice recording
      if (voiceBlob) {
        formData.append('voice', new File([voiceBlob], 'voice.wav', { type: 'audio/wav' }));
      }

      // Register with backend
      const response = await axios.post(
        'http://localhost:5000/api/auth/register-multi',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      const { token, user } = response.data;
      localStorage.setItem('token', token);
      
      const authMethods = ['Face'];
      if (voiceBlob) authMethods.push('Voice');
      setMessage(`✅ Registration successful with ${authMethods.join(' + ')}! Redirecting...`);
      setCurrentStep(4);
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

  // ==================== RENDER ====================
  const renderStepIndicator = () => (
    <div className="step-indicator">
      <div className={`step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
        <span>1</span> Basic Info
      </div>
      <div className={`step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
        <span>2</span> Face
      </div>
      <div className={`step ${currentStep >= 3 ? 'active' : ''} ${currentStep > 3 ? 'completed' : ''}`}>
        <span>3</span> Voice
      </div>
    </div>
  );

  return (
    <div className="register-container">
      <button className="back-btn" onClick={() => navigate('/')}>
        <span>←</span> Back to Home
      </button>
      
      <h2>🔐 Multi-Factor Registration</h2>
      <p className="subtitle">Register with Face (required) & Voice (optional)</p>

      {renderStepIndicator()}
      
      <div className="register-form">
        
        {/* STEP 1: Basic Information */}
        {currentStep === 1 && (
          <div className="step-content">
            <h3>📝 Basic Information</h3>
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
            <input
              type="tel"
              placeholder="Phone Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={isLoading}
            />
            <button onClick={handleBasicInfoNext} className="next-btn">
              Next: Face Authentication →
            </button>
          </div>
        )}

        {/* STEP 2: Face Authentication */}
        {currentStep === 2 && (
          <div className="step-content">
            <h3>📷 Face Authentication</h3>
            <div className="webcam-section">
              {!capturedFace ? (
                <>
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    className="webcam"
                    mirrored={true}
                  />
                  <button onClick={captureFace} className="capture-btn">
                    📸 Capture Face
                  </button>
                </>
              ) : (
                <>
                  <img src={capturedFace} alt="Captured" className="captured-image" />
                  <div className="btn-group">
                    <button onClick={retakeFace} className="retake-btn">
                      🔄 Retake
                    </button>
                    <button onClick={handleFaceNext} className="next-btn">
                      Next: Voice →
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* STEP 3: Voice Authentication */}
        {currentStep === 3 && (
          <div className="step-content">
            <h3>🎤 Voice Authentication (Optional)</h3>
            <p className="instruction">Voice is optional - you can skip this step</p>
            
            <div className="voice-section">
              <p className="note">Voice authentication is optional. You can skip this step.</p>
              {!voiceBlob ? (
                <>
                  <div className="recording-controls">
                    {!isRecording ? (
                      <button onClick={startVoiceRecording} className="record-btn">
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
                  <button onClick={skipVoice} className="skip-btn" disabled={isLoading}>
                    ⏭️ Skip Voice (Register with Face only)
                  </button>
                </>
              ) : (
                <>
                  <div className="voice-preview">
                    <p>✅ Voice recorded ({recordingTime}s)</p>
                    <audio controls src={URL.createObjectURL(voiceBlob)} />
                  </div>
                  <div className="btn-group">
                    <button onClick={retakeVoice} className="retake-btn" disabled={isLoading}>
                      🔄 Re-record
                    </button>
                    <button onClick={handleVoiceNext} className="register-button" disabled={isLoading}>
                      {isLoading ? '⏳ Registering...' : '✅ Complete Registration'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* STEP 4: Success */}
        {currentStep === 4 && (
          <div className="step-content success-screen">
            <div className="success-icon">✅</div>
            <h3>Registration Successful!</h3>
            <p>Your account has been created with:</p>
            <ul className="auth-methods-list">
              <li>✅ Face Recognition</li>
              {voiceBlob && <li>✅ Voice Authentication</li>}
            </ul>
            <p className="instruction">You can now login using Face{voiceBlob ? ', Voice,' : ''} or OTP</p>
          </div>
        )}

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

export default MultiAuthRegister;
