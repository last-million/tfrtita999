import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../context/LanguageContext';
import translations from '../translations';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { language } = useLanguage();

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    if (token && username) {
      navigate('/');
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Use relative URL that will work in any environment
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      const authUrl = `${baseUrl}/auth/token`;
      
      const response = await axios.post(authUrl, {
        username,
        password
      });

      if (response.data.access_token) {
        // Store auth info
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('username', response.data.username);
        localStorage.setItem('isAdmin', response.data.is_admin);
        
        // Set Authorization header for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        
        // Redirect to dashboard
        navigate('/');
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.response && err.response.status === 401) {
        setError(translations[language].invalidCredentials || 'Invalid credentials. Please try again.');
      } else {
        setError(translations[language].serverError || 'Server error. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const trans = translations[language] || {};

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-96">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">{trans.loginTitle || 'Login'}</h1>
          <p className="text-gray-400">{trans.loginSubtitle || 'Enter credentials to access the system'}</p>
        </div>
        
        {error && (
          <div className="bg-red-500 text-white p-3 rounded mb-4 text-center">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-white mb-2">{trans.username || 'Username'}</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder={trans.enterUsername || 'Enter your username'}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
              aria-label="Username"
              autoComplete="username"
              disabled={isLoading}
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-white mb-2">{trans.password || 'Password'}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder={trans.enterPassword || 'Enter your password'}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
              aria-label="Password"
              autoComplete="current-password"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            className={`w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${isLoading ? 'opacity-75 cursor-wait' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (trans.loggingIn || 'Logging in...') : (trans.login || 'Login')}
          </button>
        </form>
        
        <div className="mt-4 text-center text-gray-400 text-sm">
          <p>{trans.secureArea || 'This is a secure area. Unauthorized access is prohibited.'}</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
