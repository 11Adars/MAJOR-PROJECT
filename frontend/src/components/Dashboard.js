// import React, { useEffect, useState } from 'react';
// import { useNavigate } from 'react-router-dom';
// import axios from 'axios';
// import { FaUserCircle, FaMoneyCheckAlt, FaSignOutAlt, FaLock } from 'react-icons/fa';
// import './Dashboard.css';
// import BalanceCard from './BalanceCard'; 
// import QuickActions from './QuickActions';

// function Dashboard() {
//   // User data and authentication state
//   const [userData, setUserData] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [loginHistory, setLoginHistory] = useState([]);
//   const [showProfile, setShowProfile] = useState(false);
//   const navigate = useNavigate();

//   // Banking data state
//   const [balance, setBalance] = useState(null);
//   const [transactions, setTransactions] = useState([]);
//   const [bankLoading, setBankLoading] = useState(true);

//   useEffect(() => {
//     const token = localStorage.getItem('token');
//     if (!token) {
//       setError('Please login to continue');
//       setLoading(false);
//       return;
//     }

//     const fetchDashboardData = async () => {
//       try {
//         setLoading(true);
//         setError(null);

//         const token = localStorage.getItem('token');
//         if (!token) {
//           throw new Error('No authentication token found');
//         }

//         const config = {
//           headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
//           timeout: 5000
//         };

//         // Fetch user data
//         const userResponse = await axios.get('http://127.0.0.1:5000/api/user', config);
//         if (!userResponse.data) {
//           throw new Error('No user data received');
//         }
//         setUserData(userResponse.data);

//         // Fetch login history
//         const historyResponse = await axios.get('http://127.0.0.1:5000/api/login-history', config);
//         setLoginHistory(historyResponse.data || []);

//         // Fetch banking data
//         const [balanceRes, transactionsRes] = await Promise.all([
//           axios.get('http://127.0.0.1:5000/api/account/balance', config),
//           axios.get('http://127.0.0.1:5000/api/account/history', config)
//         ]);
        
//         setBalance(balanceRes.data.balance);
//         setTransactions(transactionsRes.data);

//       } catch (err) {
//         console.error('Dashboard data fetch error:', err);
//         const errorMessage = err.response?.data?.message || err.message || 'Failed to load dashboard';
//         setError(errorMessage);
        
//         if (err.response?.status === 401) {
//           localStorage.removeItem('token');
//           navigate('/login');
//         }
//       } finally {
//         setLoading(false);
//         setBankLoading(false);
//       }
//     };

//     fetchDashboardData();
//   }, [navigate]);

//   const handleLogout = async () => {
//     try {
//       const token = localStorage.getItem('token');
//       await axios.post('http://127.0.0.1:5000/api/logout', {}, {
//         headers: { Authorization: `Bearer ${token}` }
//       });
//     } catch (err) {
//       console.error('Logout error:', err);
//     } finally {
//       localStorage.removeItem('token');
//       navigate('/');
//     }
//   };

//   const toggleProfile = () => {
//     setShowProfile(!showProfile);
//   };

//   const getActiveAuthMethods = (userData) => {
//     const methods = [];
//     if (userData?.face_registered) methods.push('Face');
//     if (userData?.voice_registered) methods.push('Voice');
//     if (loginHistory.some(login => login.auth_method === 'otp')) methods.push('OTP');
//     return methods;
//   };

//   if (loading) {
//     return (
//       <div className="dashboard-container">
//         <div className="loading-spinner">Loading...</div>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="dashboard-container">
//         <div className="error-message">{error}</div>
//         <button onClick={() => navigate('/login')} className="login-button">
//           Go to Login
//         </button>
//       </div>
//     );
//   }

//   return (
//     <div className="dashboard-main">
//       <header className="dashboard-header">
//         <div className="header-left">
//           <h1>BankAssist AI</h1>
//         </div>
//         <div className="profile-section">
//           <button onClick={toggleProfile} className="profile-button">
//             <FaUserCircle size={24} className="profile-icon" />
//             <span>{userData?.username}</span>
//           </button>
//           {showProfile && (
//             <div className="profile-dropdown">
//               <div className="profile-info">
//                 <h3>{userData?.username}</h3>
//                 <p>{userData?.email}</p>
//                 <div className="auth-methods">
//                   <p>Active Authentication Methods:</p>
//                   <div className="auth-status">
//                     {getActiveAuthMethods(userData).map((method, index) => (
//                       <span key={index} className="auth-method">
//                         {method} Authentication
//                       </span>
//                     ))} 
//                   </div>
//                 </div>
                
//                 <div className="recent-activity">
//                   <h4>Recent Login Activity</h4>
//                   <div className="login-history-compact">
//                     {loginHistory.slice(0, 5).map((login, index) => (
//                       <div key={index} className={`history-item ${login.success ? 'success' : 'failed'}`}>
//                         <span className="history-date">
//                           {new Date(login.timestamp).toLocaleDateString()} {new Date(login.timestamp).toLocaleTimeString()}
//                         </span>
//                         <span className="history-method">
//                           {login.auth_method.charAt(0).toUpperCase() + login.auth_method.slice(1)} Auth
//                         </span>
//                         <span className="history-status">
//                           {login.success ? '✅' : '❌'}
//                         </span>
//                       </div>
//                     ))}
//                   </div>
//                 </div>
//               </div>
//               <div className="profile-actions">
//                 {/* <button 
//                   onClick={() => navigate('/profile')} 
//                   className="profile-action-btn"
//                 >
//                   <FaUser /> View Profile
//                 </button> */}
//                 <button 
//                   onClick={() => navigate('/set-pin')} 
//                   className="profile-action-btn"
//                 >
//                   <FaLock /> Set/Change PIN
//                 </button>
//                 <button onClick={handleLogout} className="logout-button">
//                   <FaSignOutAlt /> Logout
//                 </button>


//                   <button 
//                   onClick={() => navigate('/order')}
//                   className="profile-action-btn"
//                 >
//                   <FaMoneyCheckAlt /> Add Money
//                 </button>
//               </div>
//             </div>
//           )}
//         </div>
//       </header>

//       <main className="dashboard-content">
//         <section className="balance-section">
//           <h2>Account Balance</h2>
//           {/* <div className="balance-card">
//             <FaMoneyCheckAlt size={32} />
//             <span className="balance-amount">
//               {balance !== null ? `₹${balance.toLocaleString()}` : 'Loading...'}
//             </span>
//           </div> */}
//           <BalanceCard balance={balance} />
//         </section>

//         <section className="quick-actions">
//           <h2>Quick Actions</h2>
//           <QuickActions />
//         </section>

//         <section className="transactions-section">
//           <h2>Recent Transactions</h2>
//           {bankLoading ? (
//             <div className="loading-spinner">Loading transactions...</div>
//           ) : (
//             <ul className="transactions-list">
//               {transactions.slice(0, 5).map((txn, idx) => (
//                 <li key={idx} className={`txn-item ${txn.type === 'debit' ? 'txn-debit' : 'txn-credit'}`}>
//                   <div className="txn-amount">
//                     {txn.type === 'debit' ? '-' : '+'}₹{txn.amount}
//                   </div>
//                   <div className="txn-details">
//                     <span className="txn-account">{txn.to_account || txn.from_account}</span>
//                     <span className="txn-date">{new Date(txn.timestamp).toLocaleString()}</span>
//                   </div>
//                   <div className="txn-status">
//                     {txn.status === 'completed' ? '✓' : '...'}
//                   </div>
//                 </li>
//               ))}
//             </ul>
//           )}
//         </section>
//       </main>
//     </div>
//   );
// }

// export default Dashboard;






import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FaUserCircle, 
  FaMoneyCheckAlt, 
  FaSignOutAlt, 
  FaLock, 
  FaShieldAlt,
  FaBell,
  FaChevronRight
} from 'react-icons/fa';
import { 
  FiArrowUp, 
  FiArrowDown, 
  FiCreditCard
} from 'react-icons/fi';
import './Dashboard.css';
import BalanceCard from './BalanceCard'; 
import QuickActions from './QuickActions';

function Dashboard() {
  // User data and authentication state
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loginHistory, setLoginHistory] = useState([]);
  const [showProfile, setShowProfile] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();

  // Banking data state
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [bankLoading, setBankLoading] = useState(true);
  const [biometricEnrolled, setBiometricEnrolled] = useState(false);
  const [showEnrollmentBanner, setShowEnrollmentBanner] = useState(false);
  const [stats, setStats] = useState({
    monthlySpent: 0,
    monthlyReceived: 0,
    activeCards: 1
  });

  // Calculate stats from transactions if API is not available
  const calculateStatsFromTransactions = (transactions) => {
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    
    const monthlyData = transactions.filter(txn => {
      const txnDate = new Date(txn.timestamp);
      return txnDate.getMonth() === currentMonth && txnDate.getFullYear() === currentYear;
    });

    const monthlySpent = monthlyData
      .filter(txn => txn.type === 'debit')
      .reduce((sum, txn) => sum + txn.amount, 0);

    const monthlyReceived = monthlyData
      .filter(txn => txn.type === 'credit')
      .reduce((sum, txn) => sum + txn.amount, 0);

    return { monthlySpent, monthlyReceived, activeCards: 1 };
  };

  // Generate mock notifications
  const generateMockNotifications = () => {
    return [
      {
        id: 1,
        title: 'Welcome to BankAssist AI',
        message: 'Your account is now active with enhanced security features.',
        timestamp: new Date().toISOString(),
        read: false,
        type: 'info'
      },
      {
        id: 2,
        title: 'Security Update',
        message: 'Face authentication is now available for your account.',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        read: true,
        type: 'security'
      }
    ];
  };

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

        // Check biometric enrollment status
        const biometricStatus = userResponse.data.biometric_enrolled || 
                                userResponse.data.biometricEnrolled ||
                                false;
        setBiometricEnrolled(biometricStatus);
        setShowEnrollmentBanner(!biometricStatus);

        // Fetch login history (handle potential 404)
        let loginHistoryData = [];
        try {
          const historyResponse = await axios.get('http://127.0.0.1:5000/api/login-history', config);
          loginHistoryData = historyResponse.data || [];
        } catch (historyError) {
          console.warn('Login history endpoint not available, using empty array');
          loginHistoryData = [];
        }
        setLoginHistory(loginHistoryData);

        // Use mock notifications since endpoint doesn't exist
        setNotifications(generateMockNotifications());

        // Fetch banking data
        try {
          const [balanceRes, transactionsRes] = await Promise.all([
            axios.get('http://127.0.0.1:5000/api/account/balance', config),
            axios.get('http://127.0.0.1:5000/api/account/history', config)
          ]);
          
          setBalance(balanceRes.data.balance);
          setTransactions(transactionsRes.data || []);
          
          // Calculate stats from transactions since stats endpoint doesn't exist
          const calculatedStats = calculateStatsFromTransactions(transactionsRes.data || []);
          setStats(calculatedStats);

        } catch (bankingError) {
          console.error('Banking data fetch error:', bankingError);
          // Set default values if banking endpoints fail
          setBalance(0);
          setTransactions([]);
          setStats({ monthlySpent: 0, monthlyReceived: 0, activeCards: 0 });
        }

      } catch (err) {
        console.error('Dashboard data fetch error:', err);
        const errorMessage = err.response?.data?.message || err.message || 'Failed to load dashboard';
        
        // Don't show error for missing optional endpoints
        if (err.response?.status === 404 && err.config?.url.includes('/api/notifications')) {
          console.warn('Notifications endpoint not available, using mock data');
        } else {
          setError(errorMessage);
        }
        
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
      // Try to call logout endpoint, but don't fail if it doesn't exist
      await axios.post('http://127.0.0.1:5000/api/logout', {}, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 3000
      }).catch(() => {
        console.log('Logout endpoint not available, proceeding with client-side logout');
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
    
    // Default to OTP if no methods detected
    if (methods.length === 0) methods.push('OTP');
    
    return methods;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const unreadNotificationsCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-container">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading your dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <h3>Unable to Load Dashboard</h3>
            <p>{error}</p>
            <div className="error-actions">
              <button onClick={() => window.location.reload()} className="btn btn-outline">
                Try Again
              </button>
              <button onClick={() => navigate('/login')} className="btn btn-primary">
                Go to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-main">
      {/* Enhanced Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <div className="brand">
              <div className="brand-mark">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                  <path d="M16 0C7.164 0 0 7.164 0 16C0 24.836 7.164 32 16 32C24.836 32 32 24.836 32 16C32 7.164 24.836 0 16 0Z" fill="url(#gradient-primary)"/>
                  <path d="M21.333 10.667H10.667V21.333H21.333V10.667Z" fill="white"/>
                  <path d="M13.333 13.333H18.667V18.667H13.333V13.333Z" fill="url(#gradient-primary)"/>
                </svg>
              </div>
              <div className="brand-name">
                BankAssist <span>AI</span>
              </div>
            </div>
          </div>
          
          <div className="header-right">
            <div className="notification-bell">
              <FaBell size={20} />
              {unreadNotificationsCount > 0 && (
                <span className="notification-badge">{unreadNotificationsCount}</span>
              )}
            </div>
            
            <div className="profile-section">
              <button onClick={toggleProfile} className="profile-button">
                <div className="profile-avatar">
                  <FaUserCircle size={32} />
                </div>
                <div className="profile-info">
                  <span className="profile-name">{userData?.username || 'User'}</span>
                  <span className="profile-status">Online</span>
                </div>
                <FaChevronRight size={14} className={`dropdown-arrow ${showProfile ? 'open' : ''}`} />
              </button>
              
              {showProfile && (
                <div className="profile-dropdown">
                  <div className="dropdown-header">
                    <div className="user-avatar">
                      <FaUserCircle size={48} />
                    </div>
                    <div className="user-info">
                      <h3>{userData?.username || 'User'}</h3>
                      <p>{userData?.email || 'user@example.com'}</p>
                    </div>
                  </div>
                  
                  <div className="dropdown-section">
                    <h4>Security Status</h4>
                    <div className="auth-methods">
                      {getActiveAuthMethods(userData).map((method, index) => (
                        <div key={index} className="auth-method-item">
                          <FaShieldAlt size={16} />
                          <span>{method} Authentication</span>
                          <div className="status-indicator active"></div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="dropdown-section">
                    <h4>Recent Activity</h4>
                    <div className="activity-list">
                      {loginHistory.slice(0, 3).map((login, index) => (
                        <div key={index} className="activity-item">
                          <div className="activity-icon">
                            {login.success ? '✅' : '❌'}
                          </div>
                          <div className="activity-details">
                            <span className="activity-method">
                              {login.auth_method?.charAt(0)?.toUpperCase() + login.auth_method?.slice(1) || 'OTP'} Login
                            </span>
                            <span className="activity-time">
                              {new Date(login.timestamp).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))}
                      {loginHistory.length === 0 && (
                        <div className="activity-item">
                          <div className="activity-icon">🔒</div>
                          <div className="activity-details">
                            <span className="activity-method">Current Session</span>
                            <span className="activity-time">Just now</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="dropdown-actions">
                    <button 
                      onClick={() => navigate('/set-pin')} 
                      className="dropdown-btn"
                    >
                      <FaLock /> Security Settings
                    </button>
                    <button 
                      onClick={() => navigate('/order')}
                      className="dropdown-btn"
                    >
                      <FaMoneyCheckAlt /> Add Funds
                    </button>
                    <button onClick={handleLogout} className="dropdown-btn logout">
                      <FaSignOutAlt /> Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Enhanced Main Content */}
      <main className="dashboard-content">
        {/* Welcome Section */}
        <section className="welcome-section">
          <div className="welcome-content">
            <h1>Welcome back, {userData?.username || 'User'}!</h1>
            <p>Here's your financial overview for today</p>
          </div>
          <div className="date-display">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </div>
        </section>

        {/* Biometric Enrollment Banner */}
        {showEnrollmentBanner && (
          <section className="enrollment-banner">
            <div className="banner-content">
              <div className="banner-icon">
                <FaShieldAlt size={40} />
              </div>
              <div className="banner-text">
                <h3>🔐 Secure Your Transfers with Biometric Authentication</h3>
                <p>
                  Enroll your biometrics (face + hand + behavioral style) to enable 
                  PIN-free secure transfers with our advanced multi-modal authentication system.
                </p>
              </div>
              <div className="banner-actions">
                <button 
                  className="btn-enroll"
                  onClick={() => navigate('/biometric-enrollment')}
                >
                  Enroll Now <FaChevronRight />
                </button>
                <button 
                  className="btn-dismiss"
                  onClick={() => setShowEnrollmentBanner(false)}
                >
                  Maybe Later
                </button>
              </div>
            </div>
          </section>
        )}

        {/* Stats Overview */}
        <section className="stats-overview">
          <div className="stat-card">
            <div className="stat-icon income">
              <FiArrowDown size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-label">Monthly Income</span>
              <span className="stat-value">{formatCurrency(stats.monthlyReceived)}</span>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon expense">
              <FiArrowUp size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-label">Monthly Expenses</span>
              <span className="stat-value">{formatCurrency(stats.monthlySpent)}</span>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon cards">
              <FiCreditCard size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-label">Active Cards</span>
              <span className="stat-value">{stats.activeCards}</span>
            </div>
          </div>
        </section>

        {/* Balance and Quick Actions */}
        <div className="main-grid">
          <section className="balance-section">
            <div className="section-header">
              <h2>Account Balance</h2>
              <button className="view-all">View Details</button>
            </div>
            <BalanceCard balance={balance} />
          </section>

          <section className="quick-actions-section">
            <div className="section-header">
              <h2>Quick Actions</h2>
            </div>
            <QuickActions />
          </section>
        </div>

        {/* Transactions Section */}
        <section className="transactions-section">
          <div className="section-header">
            <h2>Recent Transactions</h2>
            <button className="view-all" onClick={() => navigate('/history')}>
              View All
            </button>
          </div>
          
          {bankLoading ? (
            <div className="loading-transactions">
              <div className="loading-spinner-small"></div>
              <span>Loading transactions...</span>
            </div>
          ) : transactions.length > 0 ? (
            <div className="transactions-container">
              <div className="transactions-list">
                {transactions.slice(0, 6).map((txn, idx) => (
                  <div key={idx} className="transaction-item">
                    <div className="transaction-icon">
                      {txn.type === 'debit' ? (
                        <FiArrowUp size={20} className="debit" />
                      ) : (
                        <FiArrowDown size={20} className="credit" />
                      )}
                    </div>
                    <div className="transaction-details">
                      <span className="transaction-description">
                        {txn.description || (txn.type === 'debit' ? 'Payment Sent' : 'Payment Received')}
                      </span>
                      <span className="transaction-account">
                        {txn.to_account || txn.from_account || 'Bank Transfer'}
                      </span>
                      <span className="transaction-date">
                        {new Date(txn.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="transaction-amount">
                      <span className={`amount ${txn.type === 'debit' ? 'debit' : 'credit'}`}>
                        {txn.type === 'debit' ? '-' : '+'}{formatCurrency(txn.amount)}
                      </span>
                      <span className={`status ${txn.status || 'completed'}`}>
                        {txn.status === 'completed' ? 'Completed' : 'Pending'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="no-transactions">
              <div className="no-data-icon">💳</div>
              <h3>No transactions yet</h3>
              <p>Your transaction history will appear here</p>
              <button 
                onClick={() => navigate('/transfer')} 
                className="btn btn-primary"
              >
                Make your first transfer
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default Dashboard;