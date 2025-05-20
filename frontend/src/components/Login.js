import React, { useRef, useState, useEffect } from 'react';
import { audioConfig, processAudio } from '../utils/audioUtils';
import Webcam from 'react-webcam';
import axios from 'axios';
import './styles.css';

function Login({ mode }) {
  // State management
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loginMode, setLoginMode] = useState(mode || 'face');

  // Face login states
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);

  // Voice login states
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioURL, setAudioURL] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (audioURL) {
        URL.revokeObjectURL(audioURL);
      }
      if (mediaRecorderRef.current && recording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [audioURL, recording]);

  // Face login handlers
  const capture = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
    setMessage('');
  };

  // Voice login handlers.

const startRecording = async () => {
  try {
    console.log('Starting audio recording...');
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        channelCount: audioConfig.channelCount,
        sampleRate: audioConfig.sampleRate,
        sampleSize: audioConfig.bitsPerSample,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      } 
    });
    
    audioChunksRef.current = [];
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 128000
    });
    
    mediaRecorderRef.current = mediaRecorder;
    
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunksRef.current.push(e.data);
      }
    };

    mediaRecorder.onstop = async () => {
      try {
        if (audioChunksRef.current.length === 0) {
          throw new Error('No audio data recorded');
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const wavBlob = await processAudio(audioBlob);
        
        setAudioBlob(wavBlob);
        const url = URL.createObjectURL(wavBlob);
        setAudioURL(url);

      } catch (err) {
        console.error('Audio processing error:', err);
        setMessage('Error processing audio: ' + err.message);
      } finally {
        stream.getTracks().forEach(track => track.stop());
      }
    };

    mediaRecorder.start(100);
    setRecording(true);
    setMessage('Recording in progress...');

    // Record for 3 seconds
    setTimeout(() => {
      if (mediaRecorderRef.current && recording) {
        mediaRecorderRef.current.stop();
        setRecording(false);
      }
    }, 3000); // Changed from 9000 to 3000 ms

  } catch (err) {
    console.error('Recording initialization error:', err);
    setMessage('Error accessing microphone: ' + err.message);
  }
};

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  
  // Form validation
  const validateInput = () => {
    if (!username.trim()) {
      setMessage('Username is required');
      return false;
    }
    return true;
  };

  // Login handler
  const loginUser = async () => {
    if (!validateInput()) return;

    setIsLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('username', username);

      if (loginMode === 'face') {
        if (!capturedImage) {
          setMessage('Please capture an image first');
          return;
        }

        const blob = await (await fetch(capturedImage)).blob();
        formData.append('image', new File([blob], 'face.jpg', { type: 'image/jpeg' }));

        const res = await axios.post('http://127.0.0.1:5000/api/login', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        localStorage.setItem('token', res.data.token);
        setMessage('Login successful!');
        window.location.href = '/dashboard';
      } else {
        if (!audioBlob) {
          setMessage('Please record your voice first');
          return;
        }

        formData.append('audio', new File([audioBlob], 'voice.wav', { type: 'audio/wav' }));

        const res = await axios.post('http://127.0.0.1:5000/api/voice/login', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        localStorage.setItem('token', res.data.token);
        setMessage('Login successful!');
        window.location.href = '/dashboard';
      }
    } catch (err) {
      console.error('Login error:', err);
      setMessage(err.response?.data?.error || 'Login failed: Invalid credentials');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      
      <div className="login-mode-buttons">
        <button 
          onClick={() => setLoginMode('face')}
          className={loginMode === 'face' ? 'active' : ''}
          disabled={isLoading}
        >
          Face Login
        </button>
        <button 
          onClick={() => setLoginMode('voice')}
          className={loginMode === 'voice' ? 'active' : ''}
          disabled={isLoading}
        >
          Voice Login
        </button>
      </div>
      
      <input 
        placeholder="Username" 
        value={username} 
        onChange={(e) => setUsername(e.target.value)}
        disabled={isLoading}
      />
      
      {loginMode === 'face' ? (
        <div className="face-login">
          <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />
          <button onClick={capture} disabled={isLoading}>
            Capture
          </button>
          {capturedImage && (
            <img src={capturedImage} alt="Captured" className="captured-image" />
          )}
        </div>
      ) : (
        <div className="voice-login">
          <button 
            onClick={startRecording} 
            disabled={recording || isLoading}
          >
            Start Recording
          </button>
          <button 
            onClick={stopRecording} 
            disabled={!recording || isLoading}
          >
            Stop Recording
          </button>
          {audioURL && (
            <div className="audio-preview">
              <p>Recorded Audio:</p>
              <audio controls src={audioURL}></audio>
            </div>
          )}
        </div>
      )}
      
      {message && (
        <p className={message.includes('successful') ? 'success' : 'error'}>
          {message}
        </p>
      )}
      
      <button 
        onClick={loginUser} 
        disabled={isLoading}
        className="login-button"
      >
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </div>
  );
}

export default Login;