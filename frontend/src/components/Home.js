import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './styles.css';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="container">
      <h1 className="title">BankAssist AI</h1>
      <div className="button-group">
        <button className="btn" onClick={() => navigate('/register')}>Register (Face)</button>
        <button className="btn" onClick={() => navigate('/login')}>Login (Face)</button>
        <button className="btn" onClick={() => navigate('/voice/register')}>Register (Voice)</button>
        <button className="btn" onClick={() => navigate('/voice/login')}>Login (Voice)</button>
        {/* Future buttons */}
        <button className="btn disabled">Login (OTP) - Coming Soon</button>
      </div>
    </div>
  );
};

export default Home;