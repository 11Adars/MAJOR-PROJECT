import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignRecognition.css';

// Embedded Sign Language Recognition page inside authenticated app
// Uses iframe to load the Flask-based sign language service
const DEFAULT_URL = process.env.REACT_APP_SIGN_RECOGNITION_URL || 'http://127.0.0.1:8000/';

function SignRecognition() {
  const navigate = useNavigate();
  const [serviceStatus, setServiceStatus] = useState('checking');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // Check if the sign language service is running
    const checkService = async () => {
      try {
        const response = await fetch(`${DEFAULT_URL}api/health`, {
          method: 'GET',
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'ok') {
            setServiceStatus('running');
          } else {
            setServiceStatus('error');
            setErrorMessage('Sign language service is not properly initialized.');
          }
        } else {
          setServiceStatus('error');
          setErrorMessage('Unable to connect to sign language service.');
        }
      } catch (error) {
        setServiceStatus('error');
        setErrorMessage('Sign language service is not running. Please start the service on port 8000.');
      }
    };

    checkService();
  }, []);

  useEffect(() => {
    // Send token to iframe when it loads and service is running
    if (serviceStatus === 'running') {
      const iframe = document.querySelector('.sign-recognition-iframe');
      if (iframe) {
        const token = localStorage.getItem('token');
        
        // Wait for iframe to load, then send token
        iframe.onload = () => {
          iframe.contentWindow.postMessage({ 
            type: 'AUTH_TOKEN', 
            token: token 
          }, '*');
        };
      }
    }
  }, [serviceStatus]);

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  if (serviceStatus === 'checking') {
    return (
      <div className="sign-recognition-container">
        <div className="sign-recognition-header">
          <h2>Sign Language Recognition</h2>
          <button onClick={handleBackToDashboard} className="back-link">
            ← Back to Dashboard
          </button>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Checking sign language service...</p>
        </div>
      </div>
    );
  }

  if (serviceStatus === 'error') {
    return (
      <div className="sign-recognition-container">
        <div className="sign-recognition-header">
          <h2>Sign Language Recognition</h2>
          <button onClick={handleBackToDashboard} className="back-link">
            ← Back to Dashboard
          </button>
        </div>
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h3>Service Not Available</h3>
          <p>{errorMessage}</p>
          <div className="instructions">
            <h4>To start the service:</h4>
            <ol>
              <li>Navigate to the Sign folder</li>
              <li>Run: <code>python sign_service.py</code></li>
              <li>Refresh this page</li>
            </ol>
          </div>
          <button onClick={handleBackToDashboard} className="btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="sign-recognition-container">
      <div className="sign-recognition-header">
        <h2>Sign Language Recognition</h2>
        <button onClick={handleBackToDashboard} className="back-link">
          ← Back to Dashboard
        </button>
      </div>
      <div className="sign-recognition-frame-wrapper">
        <iframe
          title="Sign Recognition"
          src={DEFAULT_URL}
          className="sign-recognition-iframe"
          allow="camera; microphone; clipboard-read; clipboard-write"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </div>
      <p className="sign-info-note">
        Camera stays active inside this page. Returning to the dashboard keeps your login session (no re-auth).
      </p>
    </div>
  );
}

export default SignRecognition;
