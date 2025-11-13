import React from 'react';
import './BalanceCard.css';

import { FaMoneyCheckAlt } from 'react-icons/fa';

function BalanceCard({ balance }) {
  return (
    <div className="balance-card">
      <FaMoneyCheckAlt size={32} />
      <span className="balance-amount">
        {balance !== null ? `₹${balance.toLocaleString()}` : 'Loading...'}
      </span>
    </div>
  );
}

export default BalanceCard;
