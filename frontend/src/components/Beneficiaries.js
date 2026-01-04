import React, { useEffect, useState } from 'react';
import './Beneficiaries.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Beneficiaries() {
  const [beneficiaries, setBeneficiaries] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:5000/api/account/beneficiaries', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setBeneficiaries(res.data));
  }, []);

  return (
    <div className="beneficiaries-container">
      <button className="back-btn" onClick={() => navigate('/dashboard')}>
        <span>←</span> Back
      </button>
      <div className="beneficiaries-header">
        <h2>👥 My Beneficiaries</h2>
        <button className="add-beneficiary-btn" onClick={() => navigate('/add-beneficiary')}>
          <span>+</span> Add New
        </button>
      </div>
      {beneficiaries.length === 0 ? (
        <div className="empty-state">
          <p>No beneficiaries yet</p>
          <span>Add someone to start sending money</span>
        </div>
      ) : (
        <div className="beneficiaries-grid">
          {beneficiaries.map(b => (
            <div key={b.id} className="beneficiary-card">
              <div className="beneficiary-avatar">{b.name.charAt(0).toUpperCase()}</div>
              <div className="beneficiary-info">
                <h3>{b.name}</h3>
                <p className="account-details">{b.account_number}</p>
                <p className="ifsc-code">IFSC: {b.ifsc}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Beneficiaries;