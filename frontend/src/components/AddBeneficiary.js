import React, { useState } from 'react';
import './AddBeneficiary.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function AddBeneficiary() {
  const [form, setForm] = useState({ name: '', account_number: '', ifsc: '' });
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/account/beneficiaries', form, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setMessage('Beneficiary added!');
      setTimeout(() => navigate('/beneficiaries'), 1000);
    } catch (err) {
      setMessage(err.response?.data?.message || 'Error adding beneficiary');
    }
  };

  return (
    <div className="add-beneficiary-container">
      <button className="back-btn" onClick={() => navigate('/beneficiaries')}>
        <span>←</span> Back
      </button>
      <div className="add-beneficiary-card">
        <h2>➕ Add New Beneficiary</h2>
        <p className="subtitle">Save beneficiary details for quick transfers</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name</label>
            <input 
              name="name" 
              placeholder="Enter beneficiary name" 
              value={form.name} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="form-group">
            <label>Account Number</label>
            <input 
              name="account_number" 
              placeholder="Enter account number" 
              value={form.account_number} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="form-group">
            <label>IFSC Code</label>
            <input 
              name="ifsc" 
              placeholder="Enter IFSC code" 
              value={form.ifsc} 
              onChange={handleChange} 
              required 
            />
          </div>
          {message && <p className={message.includes('added') ? 'success-msg' : 'error-msg'}>{message}</p>}
          <button className="submit-btn" type="submit">Save Beneficiary</button>
        </form>
      </div>
    </div>
  );
}

export default AddBeneficiary;