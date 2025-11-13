import React, { useEffect, useState } from 'react';
import './Transfer.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Transfer() {
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [form, setForm] = useState({ beneficiary_id: '', amount: '', pin: '' });
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:5000/api/account/beneficiaries', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setBeneficiaries(res.data));
  }, []);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/account/transfer', form, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setMessage('Transfer successful!');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err) {
      setMessage(err.response?.data?.message || 'Transfer failed');
    }
  };

  return (
    <div className="container">
      <h2>Transfer Money</h2>
      <form onSubmit={handleSubmit}>
        <select name="beneficiary_id" value={form.beneficiary_id} onChange={handleChange} required>
          <option value="">Select Beneficiary</option>
          {beneficiaries.map(b => (
            <option key={b.id} value={b.id}>{b.name} ({b.account_number})</option>
          ))}
        </select>
        <input name="amount" type="number" placeholder="Amount" value={form.amount} onChange={handleChange} required />
        <input name="pin" type="password" placeholder="PIN" value={form.pin} onChange={handleChange} required />
        <button className="action-btn" type="submit">Transfer</button>
      </form>
      {message && <p>{message}</p>}
      <button className="action-btn" onClick={() => navigate('/dashboard')}>Back</button>
    </div>
  );
}

export default Transfer;