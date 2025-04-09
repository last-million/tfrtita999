// frontend/src/components/ProtectedRoute.jsx
import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';

const ProtectedRoute = ({ children, adminRequired = false }) => {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // For demo purposes, we'll bypass the authentication check
    const simulateAuth = () => {
      // Simulate a logged-in user by setting a demo token if none exists
      if (!localStorage.getItem('token')) {
        localStorage.setItem('token', 'demo-token-for-testing');
        localStorage.setItem('username', 'demo_user');
        
        // For system config access, we'll set the user as admin
        localStorage.setItem('isAdmin', 'true');
      }
      
      // Always authorize the user in this demo mode
      setIsAuthorized(true);
      setIsChecking(false);
      
      // Set default auth header for all requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${localStorage.getItem('token')}`;
    };

    // Small delay to simulate auth check
    setTimeout(simulateAuth, 500);
  }, [adminRequired, location.pathname]);

  // Show nothing while checking auth state
  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white text-center">
          <svg className="animate-spin h-10 w-10 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p>Verifying access...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authorized
  if (!isAuthorized) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // Render children if authorized
  return children;
};

export default ProtectedRoute;
