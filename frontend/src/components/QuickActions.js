import React from 'react';
import { FaUserFriends, FaMoneyCheckAlt, FaHistory, FaHeadset } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

function QuickActions() {
	const navigate = useNavigate();

  const openSupport = () => {
    navigate('/sign-recognition');
  };

	return (
		<div className="action-buttons">
			<button className="action-btn" onClick={() => navigate('/beneficiaries')}>
				<FaUserFriends /> Beneficiaries
			</button>
			<button className="action-btn" onClick={() => navigate('/transfer')}>
				<FaMoneyCheckAlt /> Transfer Money
			</button>
			<button className="action-btn" onClick={() => navigate('/history')}>
				<FaHistory /> Transaction History
			</button>
			<button className="action-btn" onClick={openSupport}>
				<FaHeadset /> Customer Support
			</button>
		</div>
	);
}

export default QuickActions;
