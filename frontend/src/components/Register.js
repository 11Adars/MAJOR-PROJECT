import React, { useRef, useState, useEffect } from 'react';
import { audioConfig, processAudio } from '../utils/audioUtils';
import Webcam from 'react-webcam';
import axios from 'axios';
import './styles.css';

function Register({ mode }) {
  // State management
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [registrationMode, setRegistrationMode] = useState(mode || 'face');

  // Face registration states
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);

  // Voice registration states
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

  // Face registration handlers
  const capture = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
    setMessage('');
  };

  // Voice registration handlers
 



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
    if (!email.trim()) {
      setMessage('Email is required');
      return false;
    }
    if (!email.includes('@')) {
      setMessage('Invalid email format');
      return false;
    }
    return true;
  };

  // Registration handler
  const registerUser = async () => {
    if (!validateInput()) return;

    setIsLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('email', email);

      if (registrationMode === 'face') {
        if (!capturedImage) {
          setMessage('Please capture an image first');
          return;
        }

        const blob = await (await fetch(capturedImage)).blob();
        formData.append('image', new File([blob], 'face.jpg', { type: 'image/jpeg' }));

        const res = await axios.post('http://127.0.0.1:5000/api/register', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        setMessage('Face registered successfully! Token: ' + res.data.token);
      } else {
        if (!audioBlob) {
          setMessage('Please record your voice first');
          return;
        }

        formData.append('audio', new File([audioBlob], 'voice.wav', { type: 'audio/wav' }));

        const res = await axios.post('http://127.0.0.1:5000/api/voice/register', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        setMessage(res.data.message || 'Voice registered successfully!');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setMessage(err.response?.data?.error || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Render component
  return (
    <div className="register-container">
      <h2>Register</h2>
      
      <div className="registration-mode-buttons">
        <button 
          onClick={() => setRegistrationMode('face')}
          className={registrationMode === 'face' ? 'active' : ''}
        >
          Face Registration
        </button>
        <button 
          onClick={() => setRegistrationMode('voice')}
          className={registrationMode === 'voice' ? 'active' : ''}
        >
          Voice Registration
        </button>
      </div>
      
      <input 
        placeholder="Username" 
        value={username} 
        onChange={(e) => setUsername(e.target.value)}
        disabled={isLoading}
      />
      <input 
        placeholder="Email" 
        value={email} 
        onChange={(e) => setEmail(e.target.value)}
        disabled={isLoading}
      />
      
      {registrationMode === 'face' ? (
        <div className="face-registration">
          <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />
          <button onClick={capture} disabled={isLoading}>
            Capture
          </button>
          {capturedImage && (
            <img src={capturedImage} alt="Captured" className="captured-image" />
          )}
        </div>
      ) : (
        <div className="voice-registration">
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
        <p className={message.includes('successfully') ? 'success' : 'error'}>
          {message}
        </p>
      )}
      
      <button 
        onClick={registerUser} 
        disabled={isLoading}
        className="register-button"
      >
        {isLoading ? 'Registering...' : 'Register'}
      </button>
    </div>
  );
}

export default Register;