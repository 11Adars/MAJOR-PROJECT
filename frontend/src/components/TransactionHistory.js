import React, { useEffect, useState } from 'react';
import './TransactionHistory.css';
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
    <div className="transaction-history-container">
      <button className="back-btn" onClick={() => navigate('/dashboard')}>
        <span>←</span> Back
      </button>
      <div className="history-header">
        <h2>📊 Transaction History</h2>
        <p className="subtitle">View all your past transactions</p>
      </div>
      {transactions.length === 0 ? (
        <div className="empty-state">
          <p>No transactions yet</p>
          <span>Your transaction history will appear here</span>
        </div>
      ) : (
        <div className="transactions-list">
          {transactions.map((txn, idx) => (
            <div key={idx} className={`transaction-card ${txn.type}`}>
              <div className="txn-icon">
                {txn.type === 'debit' ? '↗️' : '↙️'}
              </div>
              <div className="txn-details">
                <h3>{txn.to_account || 'N/A'}</h3>
                <p className="txn-date">{new Date(txn.timestamp).toLocaleString()}</p>
              </div>
              <div className={`txn-amount ${txn.type}`}>
                {txn.type === 'debit' ? '-' : '+'}₹{txn.amount}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TransactionHistory;