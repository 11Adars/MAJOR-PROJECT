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
    <div className="container">
      <h2>Add Beneficiary</h2>
      <form onSubmit={handleSubmit}>
        <input name="name" placeholder="Name" value={form.name} onChange={handleChange} required />
        <input name="account_number" placeholder="Account Number" value={form.account_number} onChange={handleChange} required />
        <input name="ifsc" placeholder="IFSC Code" value={form.ifsc} onChange={handleChange} required />
        <button className="action-btn" type="submit">Add</button>
      </form>
      {message && <p>{message}</p>}
      <button className="action-btn" onClick={() => navigate('/beneficiaries')}>Back</button>
    </div>
  );
}

export default AddBeneficiary;