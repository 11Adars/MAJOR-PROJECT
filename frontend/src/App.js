import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/Home';
import Register from './components/Register';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import OTPLogin from './components/OTPLogin';
import Beneficiaries from './components/Beneficiaries';
import AddBeneficiary from './components/AddBeneficiary';
import Transfer from './components/Transfer';
import TransactionHistory from './components/TransactionHistory';
// import Profile from './components/Profile';
import SetPin from './components/SetPin';
import Order from './components/AddMoney';
import './components/styles.css';

function App() {
  const isAuthenticated = !!localStorage.getItem('token');

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Home />} />
        <Route path="/register" element={<Register mode="face" />} />
        <Route path="/login" element={<Login mode="face" />} />
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

        {/* Fallback route */}
        <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/"} />} />
      </Routes>
    </Router>
  );
}

export default App;