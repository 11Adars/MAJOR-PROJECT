import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './OTPLogin.css';

function OTPLogin() {
  const [identifier, setIdentifier] = useState('');
  const [otp, setOtp] = useState('');
  const [message, setMessage] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [maskedEmail, setMaskedEmail] = useState('');
  const navigate = useNavigate();

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/otp/send', {
        email: identifier,
        username: identifier
      });
      
      setMaskedEmail(response.data.email);
      setMessage(`OTP sent successfully to ${response.data.email}`);
      setOtpSent(true);
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to send OTP');
    }
    setLoading(false);
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/otp/verify', {
        email: identifier,
        username: identifier,
        otp
      });

      localStorage.setItem('token', response.data.token);
      navigate('/dashboard');
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to verify OTP');
    }
    setLoading(false);
  };

  return (
    <div className="auth-container">
      <h2>OTP Authentication</h2>
      {!otpSent ? (
        <form onSubmit={handleSendOTP}>
          <div className="form-group">
            <input
              type="text"
              placeholder="Enter email or username"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOTP}>
          <p>Enter the OTP sent to {maskedEmail}</p>
          <div className="form-group">
            <input
              type="text"
              placeholder="Enter OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              maxLength={6}
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>
      )}
      {message && (
        <p className={message.includes('success') ? 'success' : 'error'}>
          {message}
        </p>
      )}
    </div>
  );
}

export default OTPLogin;