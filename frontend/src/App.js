import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/Home';
import Register from './components/Register';
import Login from './components/Login';
import MultiAuthRegister from './components/MultiAuthRegister';
import MultiAuthLogin from './components/MultiAuthLogin';
import Dashboard from './components/Dashboard';
import OTPLogin from './components/OTPLogin';
import Beneficiaries from './components/Beneficiaries';
import AddBeneficiary from './components/AddBeneficiary';
import Transfer from './components/Transfer';
import TransactionHistory from './components/TransactionHistory';
import SignRecognition from './components/SignRecognition';
import SupportTickets from './components/SupportTickets';
import SetPin from './components/SetPin';
import Order from './components/AddMoney';
import BiometricEnrollment from './components/BiometricEnrollment';
import SplashScreen from './components/SplashScreen'; // Import the splash screen

function App() {
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 3000); // Splash screen duration: 3 seconds
    return () => clearTimeout(timer);
  }, []);

  // Check for token changes (e.g., after login/logout)
  useEffect(() => {
    const checkAuth = () => {
      setIsAuthenticated(!!localStorage.getItem('token'));
    };
    
    // Listen for storage changes
    window.addEventListener('storage', checkAuth);
    
    // Check auth on mount and interval (for same-tab changes)
    const interval = setInterval(checkAuth, 1000);
    
    return () => {
      window.removeEventListener('storage', checkAuth);
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return <SplashScreen />;
  }

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Home />} />
        
        {/* Multi-Auth Routes (Face + Voice + OTP) */}
        <Route path="/register" element={<MultiAuthRegister />} />
        <Route path="/login" element={<MultiAuthLogin />} />
        
        {/* Legacy Single-Auth Routes (kept for backwards compatibility) */}
        <Route path="/register-face" element={<Register mode="face" />} />
        <Route path="/login-face" element={<Login mode="face" />} />
        <Route path="/voice/register" element={<Register mode="voice" />} />
        <Route path="/voice/login" element={<Login mode="voice" />} />
        <Route path="/otp-login" element={<OTPLogin />} />

        {/* Protected Routes */}
        <Route 
          path="/dashboard" 
          element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} 
        />
        <Route 
          path="/beneficiaries" 
          element={isAuthenticated ? <Beneficiaries /> : <Navigate to="/dashboard" />} 
        />
        <Route 
          path="/add-beneficiary" 
          element={isAuthenticated ? <AddBeneficiary /> : <Navigate to="/dashboard" />} 
        />
        <Route 
          path="/transfer" 
          element={isAuthenticated ? <Transfer /> : <Navigate to="/dashboard" />} 
        />
        <Route 
          path="/biometric-enrollment" 
          element={isAuthenticated ? <BiometricEnrollment /> : <Navigate to="/dashboard" />} 
        />
        <Route 
          path="/history" 
          element={isAuthenticated ? <TransactionHistory /> : <Navigate to="/dashboard" />} 
        />
        {/* <Route 
          path="/profile" 
          element={isAuthenticated ? <Profile /> : <Navigate to="/login" />} 
        /> */}
        <Route 
          path="/set-pin" 
          element={isAuthenticated ? <SetPin /> : <Navigate to="/dashboard" />} 
        />
        <Route 
          path="/order" 
          element={isAuthenticated ? <Order /> : <Navigate to="/dashboard" />}
        />
        <Route
          path="/sign-recognition"
          element={isAuthenticated ? <SignRecognition /> : <Navigate to="/login" />}
        />
        <Route
          path="/support-tickets"
          element={isAuthenticated ? <SupportTickets /> : <Navigate to="/login" />}
        />

        {/* Fallback route */}
        <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/"} />} />
      </Routes>
    </Router>
  );
}

export default App;