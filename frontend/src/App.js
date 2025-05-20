import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import Register from './components/Register';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        {/* Authentication Routes */}
        <Route path="/register" element={<Register mode="face" />} />
        <Route path="/login" element={<Login mode="face" />} />
        <Route path="/voice/register" element={<Register mode="voice" />} />
        <Route path="/voice/login" element={<Login mode="voice" />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;