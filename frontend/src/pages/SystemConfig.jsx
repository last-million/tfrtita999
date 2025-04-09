import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './SystemConfig.css';

const SystemConfig = () => {
  const { user } = useAuth();
  const [systemStatus, setSystemStatus] = useState({
    database: 'Unknown',
    storage: 'Unknown',
    services: 'Unknown',
    apiKeys: 'Unknown'
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('status');

  useEffect(() => {
    // Simulate loading system status data
    setTimeout(() => {
      setSystemStatus({
        database: 'Connected',
        storage: 'Available (60% free)',
        services: 'All services running',
        apiKeys: 'Configured'
      });
      setLoading(false);
    }, 1000);
  }, []);

  // Handle tab changes
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  // Admin privileges are now checked in ProtectedRoute component,
  // so we don't need to check here, but keeping this as a UI element
  // to show the message for demo purposes only
  const showAccessDenied = false; // Hardcoded to false for demo
  
  if (showAccessDenied) {
    return (
      <div className="system-config-container">
        <h1>Access Denied</h1>
        <p>You need administrator privileges to access this section.</p>
      </div>
    );
  }

  return (
    <div className="system-config-container">
      <h1>System Configuration</h1>
      
      <div className="system-tabs">
        <button 
          className={activeTab === 'status' ? 'active' : ''} 
          onClick={() => handleTabChange('status')}
        >
          System Status
        </button>
        <button 
          className={activeTab === 'services' ? 'active' : ''} 
          onClick={() => handleTabChange('services')}
        >
          Services
        </button>
        <button 
          className={activeTab === 'users' ? 'active' : ''} 
          onClick={() => handleTabChange('users')}
        >
          User Management
        </button>
        <button 
          className={activeTab === 'backup' ? 'active' : ''} 
          onClick={() => handleTabChange('backup')}
        >
          Backup & Restore
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'status' && (
          <div className="status-panel">
            <h2>System Status</h2>
            {loading ? (
              <p>Loading system status...</p>
            ) : (
              <div className="status-grid">
                <div className="status-item">
                  <h3>Database</h3>
                  <p className={systemStatus.database === 'Connected' ? 'status-good' : 'status-error'}>
                    {systemStatus.database}
                  </p>
                </div>
                <div className="status-item">
                  <h3>Storage</h3>
                  <p className="status-good">{systemStatus.storage}</p>
                </div>
                <div className="status-item">
                  <h3>Services</h3>
                  <p className="status-good">{systemStatus.services}</p>
                </div>
                <div className="status-item">
                  <h3>API Keys</h3>
                  <p className="status-good">{systemStatus.apiKeys}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'services' && (
          <div className="services-panel">
            <h2>Service Configuration</h2>
            <p>Configure and monitor system services</p>
            <div className="service-list">
              <div className="service-item">
                <h3>Twilio</h3>
                <label>
                  <span>API Key:</span>
                  <input type="password" value="********" readOnly />
                </label>
                <button className="config-button">Update</button>
              </div>
              <div className="service-item">
                <h3>Database</h3>
                <p>Status: Connected</p>
                <button className="config-button">Test Connection</button>
              </div>
              <div className="service-item">
                <h3>File Storage</h3>
                <p>Status: Active</p>
                <button className="config-button">Configure</button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="users-panel">
            <h2>User Management</h2>
            <p>Manage system users and permissions</p>
            <div className="user-actions">
              <button className="primary-button">Add New User</button>
              <button className="secondary-button">Export User List</button>
            </div>
            <div className="user-list">
              <div className="user-header">
                <span>Username</span>
                <span>Role</span>
                <span>Status</span>
                <span>Actions</span>
              </div>
              <div className="user-item">
                <span>admin</span>
                <span>Administrator</span>
                <span className="status-active">Active</span>
                <span>
                  <button className="icon-button">Edit</button>
                  <button className="icon-button">Delete</button>
                </span>
              </div>
              <div className="user-item">
                <span>hamza</span>
                <span>Administrator</span>
                <span className="status-active">Active</span>
                <span>
                  <button className="icon-button">Edit</button>
                  <button className="icon-button">Delete</button>
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'backup' && (
          <div className="backup-panel">
            <h2>Backup & Restore</h2>
            <p>Manage system backups and restore points</p>
            
            <div className="backup-actions">
              <div className="action-item">
                <h3>Create Backup</h3>
                <p>Create a complete system backup including database and files</p>
                <button className="primary-button">Create Backup</button>
              </div>
              
              <div className="action-item">
                <h3>Restore System</h3>
                <p>Restore the system from a previous backup point</p>
                <button className="warning-button">Restore System</button>
              </div>
            </div>
            
            <h3>Available Backups</h3>
            <div className="backup-list">
              <div className="backup-item">
                <span>Backup_20250301_120000</span>
                <span>March 1, 2025 12:00 PM</span>
                <span>Complete</span>
                <span>
                  <button className="secondary-button">Restore</button>
                  <button className="icon-button">Delete</button>
                </span>
              </div>
              <div className="backup-item">
                <span>Backup_20250228_235900</span>
                <span>February 28, 2025 11:59 PM</span>
                <span>Complete</span>
                <span>
                  <button className="secondary-button">Restore</button>
                  <button className="icon-button">Delete</button>
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemConfig;
