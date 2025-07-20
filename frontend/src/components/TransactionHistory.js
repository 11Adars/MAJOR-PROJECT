import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function TransactionHistory() {
  const [transactions, setTransactions] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:5000/api/account/history', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setTransactions(res.data));
  }, []);

  return (
    <div className="container">
      <h2>Transaction History</h2>
      <ul className="transactions-list">
        {transactions.map((txn, idx) => (
          <li key={idx} className={txn.type === 'debit' ? 'txn-debit' : 'txn-credit'}>
            <span>{txn.type === 'debit' ? '-' : '+'}₹{txn.amount}</span>
            <span>{txn.to_account}</span>
            <span>{new Date(txn.timestamp).toLocaleString()}</span>
          </li>
        ))}
      </ul>
      <button className="action-btn" onClick={() => navigate('/dashboard')}>Back</button>
    </div>
  );
}

export default TransactionHistory;