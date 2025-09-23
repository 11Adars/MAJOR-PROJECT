import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FaUserCircle, FaMoneyCheckAlt, FaHistory, FaUserFriends, FaSignOutAlt, FaUser, FaLock}from 'react-icons/fa';
import './styles.css';
import BalanceCard from './BalanceCard'; 
import QuickActions from './QuickActions';

function Dashboard() {
  // User data and authentication state
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loginHistory, setLoginHistory] = useState([]);
  const [showProfile, setShowProfile] = useState(false);
  const navigate = useNavigate();

  // Banking data state
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [bankLoading, setBankLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Please login to continue');
      setLoading(false);
      return;
    }

    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        const config = {
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          timeout: 5000
        };

        // Fetch user data
        const userResponse = await axios.get('http://127.0.0.1:5000/api/user', config);
        if (!userResponse.data) {
          throw new Error('No user data received');
        }
        setUserData(userResponse.data);

        // Fetch login history
        const historyResponse = await axios.get('http://127.0.0.1:5000/api/login-history', config);
        setLoginHistory(historyResponse.data || []);

        // Fetch banking data
        const [balanceRes, transactionsRes] = await Promise.all([
          axios.get('http://127.0.0.1:5000/api/account/balance', config),
          axios.get('http://127.0.0.1:5000/api/account/history', config)
        ]);
        
        setBalance(balanceRes.data.balance);
        setTransactions(transactionsRes.data);

      } catch (err) {
        console.error('Dashboard data fetch error:', err);
        const errorMessage = err.response?.data?.message || err.message || 'Failed to load dashboard';
        setError(errorMessage);
        
        if (err.response?.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
        }
      } finally {
        setLoading(false);
        setBankLoading(false);
      }
    };

    fetchDashboardData();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://127.0.0.1:5000/api/logout', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('token');
      navigate('/');
    }
  };

  const toggleProfile = () => {
    setShowProfile(!showProfile);
  };

  const getActiveAuthMethods = (userData) => {
    const methods = [];
    if (userData?.face_registered) methods.push('Face');
    if (userData?.voice_registered) methods.push('Voice');
    if (loginHistory.some(login => login.auth_method === 'otp')) methods.push('OTP');
    return methods;
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/login')} className="login-button">
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-main">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>BankAssist AI</h1>
        </div>
        <div className="profile-section">
          <button onClick={toggleProfile} className="profile-button">
            <FaUserCircle size={24} className="profile-icon" />
            <span>{userData?.username}</span>
          </button>
          {showProfile && (
            <div className="profile-dropdown">
              <div className="profile-info">
                <h3>{userData?.username}</h3>
                <p>{userData?.email}</p>
                <div className="auth-methods">
                  <p>Active Authentication Methods:</p>
                  <div className="auth-status">
                    {getActiveAuthMethods(userData).map((method, index) => (
                      <span key={index} className="auth-method">
                        {method} Authentication
                      </span>
                    ))} 
                  </div>
                </div>
                
                <div className="recent-activity">
                  <h4>Recent Login Activity</h4>
                  <div className="login-history-compact">
                    {loginHistory.slice(0, 5).map((login, index) => (
                      <div key={index} className={`history-item ${login.success ? 'success' : 'failed'}`}>
                        <span className="history-date">
                          {new Date(login.timestamp).toLocaleDateString()} {new Date(login.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="history-method">
                          {login.auth_method.charAt(0).toUpperCase() + login.auth_method.slice(1)} Auth
                        </span>
                        <span className="history-status">
                          {login.success ? '✅' : '❌'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="profile-actions">
                {/* <button 
                  onClick={() => navigate('/profile')} 
                  className="profile-action-btn"
                >
                  <FaUser /> View Profile
                </button> */}
                <button 
                  onClick={() => navigate('/set-pin')} 
                  className="profile-action-btn"
                >
                  <FaLock /> Set/Change PIN
                </button>
                <button onClick={handleLogout} className="logout-button">
                  <FaSignOutAlt /> Logout
                </button>


                  <button 
                  onClick={() => navigate('/order')}
                  className="profile-action-btn"
                >
                  <FaMoneyCheckAlt /> Add Money
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="dashboard-content">
        <section className="balance-section">
          <h2>Account Balance</h2>
          {/* <div className="balance-card">
            <FaMoneyCheckAlt size={32} />
            <span className="balance-amount">
              {balance !== null ? `₹${balance.toLocaleString()}` : 'Loading...'}
            </span>
          </div> */}
          <BalanceCard balance={balance} />
        </section>

        <section className="quick-actions">
          <h2>Quick Actions</h2>
          <QuickActions />
        </section>

        <section className="transactions-section">
          <h2>Recent Transactions</h2>
          {bankLoading ? (
            <div className="loading-spinner">Loading transactions...</div>
          ) : (
            <ul className="transactions-list">
              {transactions.slice(0, 5).map((txn, idx) => (
                <li key={idx} className={`txn-item ${txn.type === 'debit' ? 'txn-debit' : 'txn-credit'}`}>
                  <div className="txn-amount">
                    {txn.type === 'debit' ? '-' : '+'}₹{txn.amount}
                  </div>
                  <div className="txn-details">
                    <span className="txn-account">{txn.to_account || txn.from_account}</span>
                    <span className="txn-date">{new Date(txn.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="txn-status">
                    {txn.status === 'completed' ? '✓' : '...'}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

export default Dashboard;