// Example: AddMoney.js
import React, { useState } from 'react';
import './AddMoney.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function AddMoney() {
  const [amount, setAmount] = useState('');
  const navigate = useNavigate();

  const handleAddMoney = async () => {
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
    <div className="container">
      <input
        type="number"
        placeholder="Amount (INR)"
        value={amount}
        onChange={e => setAmount(e.target.value)}
      />
      <button onClick={handleAddMoney}>Add Money</button>
    </div>
  );
}

export default AddMoney;