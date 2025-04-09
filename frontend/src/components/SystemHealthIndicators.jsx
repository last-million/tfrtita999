import React from 'react';
import './SystemHealthIndicators.css';

const SystemHealthIndicators = ({ statuses = {} }) => {
  // Default system components and their status if none provided
  const defaultStatuses = {
    database: { status: 'healthy', lastChecked: '2 minutes ago' },
    twilio: { status: 'healthy', lastChecked: '5 minutes ago' },
    ultravox: { status: 'warning', lastChecked: '10 minutes ago', message: 'High latency detected' },
    supabase: { status: 'healthy', lastChecked: '7 minutes ago' },
    vectorization: { status: 'healthy', lastChecked: '15 minutes ago' }
  };

  const systemStatuses = { ...defaultStatuses, ...statuses };

  // Get appropriate status indicator
  const getStatusIndicator = (status) => {
    switch (status) {
      case 'healthy':
        return { icon: '✅', color: '#28a745', text: 'Healthy' };
      case 'warning':
        return { icon: '⚠️', color: '#ffc107', text: 'Warning' };
      case 'error':
        return { icon: '❌', color: '#dc3545', text: 'Error' };
      case 'inactive':
        return { icon: '⭘', color: '#6c757d', text: 'Inactive' };
      default:
        return { icon: '❓', color: '#6c757d', text: 'Unknown' };
    }
  };

  return (
    <div className="system-indicator-card">
      <h3>System Health</h3>
      <div className="system-health-grid">
        {Object.entries(systemStatuses).map(([system, info]) => {
          const statusInfo = getStatusIndicator(info.status);
          return (
            <div key={system} className="status-indicator">
              <div className="status-indicator-label">
                {system.charAt(0).toUpperCase() + system.slice(1)}
              </div>
              <div className="status-indicator-value">
                <span className={`status-dot ${info.status}`}></span>
                {statusInfo.text}
                {info.message && (
                  <span className="status-message"> - {info.message}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="card-footer">
        <span className="timestamp">Last updated: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

export default SystemHealthIndicators;
