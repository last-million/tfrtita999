// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './context/LanguageContext';
import { KnowledgeBaseProvider } from './context/KnowledgeBaseContext';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Components
import Header from './components/Header';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard.jsx';
import CallManager from './pages/CallManager.jsx';
import CallHistory from './pages/CallHistory.jsx';
import CallDetails from './pages/CallDetails.jsx';
import KnowledgeBase from './pages/KnowledgeBase.jsx';
import Authentication from './pages/Authentication.jsx';
import SystemConfig from './pages/SystemConfig.jsx';
import LoginPage from './pages/LoginPage.jsx';

// Styles
import './App.css';

const Layout = ({ children }) => {
  // Get current path to highlight the active link
  const location = useLocation();
  const currentPath = location.pathname;
  
  return (
    <div className="app-container">
      <div className="top-navbar">
        <div className="app-logo">
          <img src="/logo.svg" alt="Voice Call AI" style={{ height: '30px', marginRight: '10px' }} />
          Voice Call AI
        </div>
        <div className="top-nav-links">
          <Link to="/" className={`top-nav-link ${currentPath === '/' ? 'active' : ''}`}>Dashboard</Link>
          <Link to="/calls" className={`top-nav-link ${currentPath === '/calls' ? 'active' : ''}`}>Call Manager</Link>
          <Link to="/call-history" className={`top-nav-link ${currentPath === '/call-history' ? 'active' : ''}`}>Call History</Link>
          <Link to="/knowledge-base" className={`top-nav-link ${currentPath === '/knowledge-base' ? 'active' : ''}`}>Knowledge Base</Link>
          <Link to="/system-config" className={`top-nav-link ${currentPath === '/system-config' ? 'active' : ''}`}>System Config</Link>
          <Link to="/auth" className={`top-nav-link ${currentPath === '/auth' ? 'active' : ''}`}>Services</Link>
          <Link to="/login" className="top-nav-link login-link">Logout</Link>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <Header />
        </div>
      </div>
      <div className="content-wrapper">
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <LanguageProvider>
          <KnowledgeBaseProvider>
            <Router>
              <Routes>
                {/* Login page - public route */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* Protected routes */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                <Route path="/calls" element={
                  <ProtectedRoute>
                    <Layout>
                      <CallManager />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                <Route path="/call-history" element={
                  <ProtectedRoute>
                    <Layout>
                      <CallHistory />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                <Route path="/call-details/:callSid" element={
                  <ProtectedRoute>
                    <Layout>
                      <CallDetails />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                <Route path="/knowledge-base" element={
                  <ProtectedRoute>
                    <Layout>
                      <KnowledgeBase />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                <Route path="/auth" element={
                  <ProtectedRoute>
                    <Layout>
                      <Authentication />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                {/* Admin-only routes */}
                <Route path="/system-config" element={
                  <ProtectedRoute adminRequired={true}>
                    <Layout>
                      <SystemConfig />
                    </Layout>
                  </ProtectedRoute>
                } />
                
                {/* User management (admin only) */}
                <Route path="/users" element={
                  <ProtectedRoute adminRequired={true}>
                    <Layout>
                      <SystemConfig />
                    </Layout>
                  </ProtectedRoute>
                } />

                {/* Catch all route */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Router>
          </KnowledgeBaseProvider>
        </LanguageProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
