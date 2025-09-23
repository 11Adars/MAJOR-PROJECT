import React from 'react';

// Embedded Sign Language Recognition page inside authenticated app
// Uses iframe to avoid duplicating MediaPipe + model code.
// Assumes backend FastAPI service running at SIGN_RECOG_URL.
const DEFAULT_URL = process.env.REACT_APP_SIGN_RECOGNITION_URL || 'http://127.0.0.1:8000/';

function SignRecognition() {
  return (
    <div className="sign-recognition-container">
      <div className="sign-recognition-header">
        <h2>Sign Language Recognition</h2>
        <a href="/dashboard" className="back-link">← Back to Dashboard</a>
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
      <p className="sign-info-note">Camera stays active inside this page. Returning to the dashboard keeps your login session (no re-auth).</p>
    </div>
  );
}

export default SignRecognition;
