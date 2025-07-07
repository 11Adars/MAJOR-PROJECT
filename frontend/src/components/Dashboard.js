import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './styles.css';

function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loginHistory, setLoginHistory] = useState([]);
  const [showProfile, setShowProfile] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Please login to continue');
      setLoading(false);
      return;
    }

    const fetchDashboardData = async () => {
  try {
    // Add loading state
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Add timeout to requests
    const config = {
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      timeout: 5000
    };

    // Fetch user data with error handling
    console.log('Fetching user data...');
    const userResponse = await axios.get('http://127.0.0.1:5000/api/user', config);
    if (!userResponse.data) {
      throw new Error('No user data received');
    }
     console.log('User data received:', userResponse.data);
    setUserData(userResponse.data);

    // Fetch login history with error handling
    console.log('Fetching login history...');
    const historyResponse = await axios.get('http://127.0.0.1:5000/api/login-history', config);
    console.log('Login history received:', historyResponse.data);
    setLoginHistory(historyResponse.data || []);

  } catch (err) {
    console.error('Dashboard data fetch error:', err);
    const errorMessage = err.response?.data?.message || err.message || 'Failed to load dashboard';
    setError(errorMessage);
    
    // Handle unauthorized access
    if (err.response?.status === 401) {
      console.log('Unauthorized access, redirecting to login...');  
      localStorage.removeItem('token');
      navigate('/login');
    }
  } finally {
    setLoading(false);
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


  // Helper function to get active auth methods
  const getActiveAuthMethods = (userData) => {
    const methods = [];
    if (userData?.face_registered) methods.push('Face');
    if (userData?.voice_registered) methods.push('Voice');
    // Only add OTP if it has been used for login
    if (loginHistory.some(login => login.auth_method === 'otp')) methods.push('OTP');
    return methods;
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>BankAssist AI</h1>
        <div className="profile-section">
          <button onClick={toggleProfile} className="profile-button">
            <span className="profile-icon">👤</span>
            {userData?.username}
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
              <button onClick={handleLogout} className="logout-button">
                Logout
              </button>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}


  
export default Dashboard;