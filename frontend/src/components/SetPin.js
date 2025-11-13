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
    <div className="container">
      <h2>Set/Change PIN</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="password"
          placeholder="Enter new PIN"
          value={pin}
          onChange={e => setPin(e.target.value)}
          minLength={4}
          maxLength={6}
          required
        />
        <button className="action-btn" type="submit">Set PIN</button>
      </form>
      {message && <p>{message}</p>}
      <button className="action-btn" onClick={() => navigate('/profile')}>Back</button>
    </div>
  );
}

export default SetPin;