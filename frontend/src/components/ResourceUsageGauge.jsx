import React from 'react';
import './ResourceUsageGauge.css';

const ResourceUsageGauge = ({ usage, resourceType }) => {
  // Determine thresholds based on resource type
  let thresholds = {
    safe: 60,
    warning: 80
  };
  
  // Adjust thresholds for specific resources
  if (resourceType === 'cpu') {
    thresholds = { safe: 50, warning: 70 };
  } else if (resourceType === 'memory') {
    thresholds = { safe: 70, warning: 85 };
  }
  
  // Determine status based on usage value and thresholds
  const getStatus = (value) => {
    if (value <= thresholds.safe) return 'safe';
    if (value <= thresholds.warning) return 'warning';
    return 'critical';
  };
  
  const status = getStatus(usage);
  
  // Format resource labels
  const getResourceLabel = (type) => {
    switch (type) {
      case 'cpu': return 'CPU';
      case 'memory': return 'Memory';
      case 'network': return 'Network';
      case 'call_capacity': return 'Call Capacity';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };
  
  return (
    <div className="resource-gauge">
      <div className="gauge-info">
        <span className="gauge-label">{getResourceLabel(resourceType)}</span>
        <span className="gauge-value">{Math.round(usage)}%</span>
      </div>
      <div className="gauge-bar-container">
        <div 
          className={`gauge-bar ${status}`} 
          style={{ width: `${usage}%` }}
        >
          {/* Animated pulse effect for critical level */}
          {status === 'critical' && <div className="pulse-effect"></div>}
        </div>
      </div>
      {/* Thresholds markers */}
      <div className="threshold-markers">
        <div className="threshold-marker safe" style={{ left: `${thresholds.safe}%` }}></div>
        <div className="threshold-marker warning" style={{ left: `${thresholds.warning}%` }}></div>
      </div>
    </div>
  );
};

export default ResourceUsageGauge;
