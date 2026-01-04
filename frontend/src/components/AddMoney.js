// Example: AddMoney.js
import React, { useState } from 'react';
import './AddMoney.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function AddMoney() {
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleAddMoney = async () => {
    if (!amount || Number(amount) <= 0) {
      alert('Please enter a valid amount');
      return;
    }
    setLoading(true);
    // 1. Create order from backend
    const res = await axios.post('http://127.0.0.1:5000/api/razorpay/order', { amount :Number(amount)}, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    });
    const order = res.data;

    // 2. Open Razorpay Checkout
    const options = {
      key: 'rzp_test_vpCwG1s5IJZOwG', // Replace with your Razorpay key_id
      amount: order.amount,
      currency: order.currency,
      order_id: order.id,
      name: 'Your Bank App',
      // handler: function (response) {
      //   alert('Payment successful! Razorpay Payment ID: ' + response.razorpay_payment_id);
      //   // Optionally, call backend to verify payment and update balance
      // }
      handler: async function (response) {
  // Send payment details to backend for verification and wallet update
  try {
    await axios.post('http://127.0.0.1:5000/api/razorpay/verify', {
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_order_id: response.razorpay_order_id,
      amount: amount // in INR
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    });
    alert('Money added to your wallet!');
      navigate('/dashboard'); 
    // Optionally, refresh balance here
  } catch (err) {
    alert('Payment verification failed!');
  }
}
    };
    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  return (
    <div className="add-money-container">
      <button className="back-btn" onClick={() => navigate('/dashboard')}>
        <span>←</span> Back
      </button>
      <div className="add-money-card">
        <h2>💰 Add Money</h2>
        <p className="subtitle">Top up your wallet instantly</p>
        <div className="amount-input-group">
          <span className="currency-symbol">₹</span>
          <input
            type="number"
            placeholder="Enter amount"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            min="1"
            disabled={loading}
          />
        </div>
        <button 
          className="add-money-btn" 
          onClick={handleAddMoney}
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Add Money via Razorpay'}
        </button>
      </div>
    </div>
  );
}

export default AddMoney;