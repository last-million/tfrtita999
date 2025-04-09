import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './CallCapacityCard.css';
import './SystemHealthIndicators.css';  // Reuse similar styling
import { useLanguage } from '../context/LanguageContext';
import translations from '../translations';
import ResourceUsageGauge from './ResourceUsageGauge';

const CallCapacityCard = () => {
  const { language } = useLanguage();
  const trans = translations[language] || {};
  
  const [capacityData, setCapacityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [useLiveData, setUseLiveData] = useState(true);

  useEffect(() => {
    fetchCapacityData();
    
    // Refresh data every 60 seconds if using live data
    let intervalId;
    if (useLiveData) {
      intervalId = setInterval(fetchCapacityData, 60000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [useLiveData]);

  const fetchCapacityData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await axios.get(`${baseUrl}/dashboard/call-capacity?use_live_data=${useLiveData}`);
      setCapacityData(response.data);
    } catch (err) {
      console.error('Error fetching call capacity data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch call capacity data');
    } finally {
      setLoading(false);
    }
  };

  const toggleDataMode = () => {
    setUseLiveData(!useLiveData);
  };

  if (loading && !capacityData) {
    return (
      <div className="system-indicator-card call-capacity-card">
        <h3>{trans.callCapacity || 'Call Capacity'}</h3>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="system-indicator-card call-capacity-card error">
        <h3>{trans.callCapacity || 'Call Capacity'}</h3>
        <div className="error-message">{error}</div>
        <button onClick={fetchCapacityData} className="retry-button">
          {trans.retry || 'Retry'}
        </button>
      </div>
    );
  }

  return (
    <div className="system-indicator-card call-capacity-card">
      <div className="card-header">
        <h3>{trans.callCapacity || 'Call Capacity'}</h3>
        <div className="data-mode-toggle">
          <button 
            className={`toggle-button ${useLiveData ? 'active' : ''}`} 
            onClick={toggleDataMode}
          >
            {useLiveData ? (trans.liveData || 'Live') : (trans.theoretical || 'Theoretical')}
          </button>
        </div>
      </div>
      
      {capacityData && (
        <div className="capacity-metrics">
          <div className="capacity-metric">
            <div className="metric-value highlighted">{capacityData.recommended_outbound_concurrent}</div>
            <div className="metric-label">{trans.recommendedOutboundCalls || 'Recommended Outbound Calls'}</div>
          </div>
          
          <div className="capacity-metric">
            <div className="metric-value">{capacityData.max_inbound_concurrent}</div>
            <div className="metric-label">{trans.maxInboundCalls || 'Max Inbound Calls'}</div>
          </div>
          
          <div className="capacity-metric">
            <div className="metric-value">{capacityData.recommended_calls_per_minute}</div>
            <div className="metric-label">{trans.callsPerMinute || 'Calls Per Minute'}</div>
          </div>
          
          <div className="capacity-info">
            <div className="info-item">
              <span className="info-label">{trans.limitingFactor || 'Limiting Factor'}:</span>
              <span className="info-value">{capacityData.limiting_factor}</span>
            </div>
            
            <div className="info-item">
              <span className="info-label">{trans.maxConcurrentCalls || 'Max Concurrent Calls'}:</span>
              <span className="info-value">{capacityData.max_concurrent_calls}</span>
            </div>
            
            {useLiveData && capacityData.resource_usage && (
              <div className="resource-gauges">
                <h5>Server Resources</h5>
                
                {/* CPU Usage Gauge */}
                <ResourceUsageGauge 
                  usage={capacityData.resource_usage.cpu?.usage_percent || 0} 
                  resourceType="cpu"
                />
                
                {/* Memory Usage Gauge */}
                <ResourceUsageGauge 
                  usage={capacityData.resource_usage.memory?.usage_percent || 0} 
                  resourceType="memory"
                />
                
                {/* Call Capacity Usage Gauge */}
                <ResourceUsageGauge 
                  usage={(capacityData.max_concurrent_calls > 0 
                    ? ((capacityData.max_concurrent_calls - capacityData.recommended_outbound_concurrent) / capacityData.max_concurrent_calls) * 100 
                    : 0)} 
                  resourceType="call_capacity"
                />
              </div>
            )}
          </div>
        </div>
      )}
      
      <div className="card-footer">
        <span className="timestamp">
          {capacityData?.timestamp 
            ? new Date(capacityData.timestamp).toLocaleTimeString() 
            : ''}
        </span>
        <button onClick={fetchCapacityData} className="refresh-button">
          {trans.refresh || 'Refresh'}
        </button>
      </div>
    </div>
  );
};

export default CallCapacityCard;
