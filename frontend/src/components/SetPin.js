import React, { useState } from 'react';
import './SetPin.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function SetPin() {
  const [pin, setPin] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/account/set-pin', { pin }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setMessage('PIN set successfully!');
      setTimeout(() => navigate('/profile'), 1000);
    } catch (err) {
      setMessage(err.response?.data?.message || 'Failed to set PIN');
    }
  };

  return (
    <div className="set-pin-container">
      <button className="back-btn" onClick={() => navigate('/profile')}>
        <span>←</span> Back
      </button>
      <div className="set-pin-card">
        <h2>🔐 Set/Change PIN</h2>
        <p className="subtitle">Create a secure PIN for transactions</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>New PIN (4-6 digits)</label>
            <input
              type="password"
              placeholder="Enter new PIN"
              value={pin}
              onChange={e => setPin(e.target.value)}
              minLength={4}
              maxLength={6}
              required
            />
          </div>
          {message && <p className={message.includes('success') ? 'success-msg' : 'error-msg'}>{message}</p>}
          <button className="submit-btn" type="submit">Set PIN</button>
        </form>
      </div>
    </div>
  );
}

export default SetPin;