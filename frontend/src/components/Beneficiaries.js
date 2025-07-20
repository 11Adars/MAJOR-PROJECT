import React, { useEffect, useState } from 'react';
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
    <div className="container">
      <h2>Beneficiaries</h2>
      <button className="action-btn" onClick={() => navigate('/add-beneficiary')}>Add Beneficiary</button>
      <ul className="beneficiaries-list">
        {beneficiaries.map(b => (
          <li key={b.id}>
            <strong>{b.name}</strong> — {b.account_number} ({b.ifsc})
          </li>
        ))}
      </ul>
      <button className="action-btn" onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
    </div>
  );
}

export default Beneficiaries;