// frontend/src/context/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState({ 
    username: 'hamza', 
    isAdmin: true,
    email: 'hamzameliani1@gmail.com',
    role: 'Administrator'
  });
  const [loading, setLoading] = useState(false);

  // Initialize auth data on load
  useEffect(() => {
    // Set demo authentication data for the application
    localStorage.setItem('token', 'demo-token-for-testing');
    localStorage.setItem('username', 'hamza');
    localStorage.setItem('isAdmin', 'true');
    
    // Set default auth header for axios requests
    axios.defaults.headers.common['Authorization'] = `Bearer demo-token-for-testing`;
  }, []);

  // Always succeed with auth checks
  const checkAuth = async () => {
    return true;
  };

  // Simplified login that always succeeds
  const login = async (username, password) => {
    const userData = {
      username: username || 'hamza',
      isAdmin: true,
      email: 'hamzameliani1@gmail.com',
      role: 'Administrator'
    };
    
    localStorage.setItem('token', 'demo-token-for-testing');
    localStorage.setItem('username', userData.username);
    localStorage.setItem('isAdmin', 'true');
    
    axios.defaults.headers.common['Authorization'] = `Bearer demo-token-for-testing`;
    
    setUser(userData);
    return true;
  };

  const logout = () => {
    // For demo purposes, we'll maintain login state
    // In a real app, we would clear all auth data here
    console.log('Logout requested (simulated)');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
