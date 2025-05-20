import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './styles.css';

function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loginHistory, setLoginHistory] = useState([]);
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
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Welcome, {userData?.username}</h1>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </header>

      <div className="dashboard-content">
        <section className="user-info-section">
          <h2>Account Information</h2>
          <div className="user-details">
            <p><strong>Email:</strong> {userData?.email}</p>
            <p><strong>Authentication Methods:</strong></p>
            <ul>
              <li>Face Recognition: {userData?.face_registered ? '✅' : '❌'}</li>
              <li>Voice Recognition: {userData?.voice_registered ? '✅' : '❌'}</li>
            </ul>
          </div>
        </section>

        <section className="login-history-section">
          <h2>Recent Login Activity</h2>
          <div className="login-history">
            {loginHistory.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Method</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {loginHistory.map((login, index) => (
                    <tr key={index}>
                      <td>{new Date(login.timestamp).toLocaleDateString()}</td>
                      <td>{new Date(login.timestamp).toLocaleTimeString()}</td>
                      <td>{login.auth_method}</td>
                      <td>{login.success ? 'Success' : 'Failed'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No login history available</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;