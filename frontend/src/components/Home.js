// frontend/src/Home.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './styles.css';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h1 className="title">BankAssist AI</h1>
      <div className="button-group">
        <button className="btn" onClick={() => navigate('/register')}>Register (Face)</button>
        <button className="btn" onClick={() => navigate('/login')}>Login (Face)</button>
        {/* Future buttons */}
        <button className="btn disabled">Register (Voice) - Coming Soon</button>
        <button className="btn disabled">Login (OTP) - Coming Soon</button>
      </div>
    </div>
  );
};

export default Home;
