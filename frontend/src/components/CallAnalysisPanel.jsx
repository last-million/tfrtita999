import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import translations from '../translations';
import './CallAnalysisPanel.css';

const CallAnalysisPanel = ({ callSid }) => {
  const { language } = useLanguage();
  const trans = translations[language] || {};
  
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reAnalyzing, setReAnalyzing] = useState(false);

  useEffect(() => {
    if (callSid) {
      fetchAnalysis();
    }
  }, [callSid]);

  const fetchAnalysis = async (forceRefresh = false) => {
    if (!callSid) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      const url = `${baseUrl}/calls/${callSid}/analysis${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await api.get(url);
      
      if (response.data && response.data.success) {
        setAnalysis(response.data.analysis);
      } else {
        setError(response.data?.error || 'Failed to fetch call analysis');
        console.error('Error fetching call analysis:', response.data);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to fetch call analysis');
      console.error('Error fetching call analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReanalyze = async () => {
    if (!callSid || reAnalyzing) return;
    
    setReAnalyzing(true);
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await api.post(`${baseUrl}/calls/${callSid}/reanalyze`);
      
      if (response.data && response.data.success) {
        setAnalysis(response.data.analysis);
      } else {
        setError(response.data?.error || 'Failed to reanalyze call');
        console.error('Error reanalyzing call:', response.data);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to reanalyze call');
      console.error('Error reanalyzing call:', err);
    } finally {
      setReAnalyzing(false);
    }
  };

  // Helper to format entities
  const formatEntityList = (entities) => {
    if (!entities || entities.length === 0) return 'None detected';
    return entities.join(', ');
  };

  // Helper for sentiment color
  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'var(--success-color, #2ecc71)';
      case 'negative': return 'var(--error-color, #e74c3c)';
      default: return 'var(--text-muted, #a0a0c0)'; // neutral
    }
  };

  if (loading && !analysis) {
    return (
      <div className="call-analysis-panel loading">
        <div className="spinner"></div>
        <p>{trans.loadingAnalysis || 'Loading call analysis...'}</p>
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="call-analysis-panel error">
        <h3>{trans.analysisError || 'Analysis Error'}</h3>
        <p className="error-message">{error}</p>
        <button onClick={() => fetchAnalysis(true)} className="retry-button">
          {trans.retry || 'Retry'}
        </button>
      </div>
    );
  }

  return (
    <div className="call-analysis-panel">
      {/* Intent and Summary Section */}
      <div className="analysis-card summary-card">
        <h3 className="card-title">
          <span className="card-icon">📝</span>
          {trans.callSummary || 'Call Summary'}
        </h3>
        <div className="analysis-content">
          <div className="summary-text">
            {analysis?.summary || trans.noSummaryAvailable || 'No summary available'}
          </div>
          
          <div className="intent-container">
            <div className="primary-intent">
              <div className="intent-label">{trans.primaryIntent || 'Primary Intent'}:</div>
              <div className="intent-value">
                {analysis?.intent?.primary?.name || 'Unknown'}
                {analysis?.intent?.primary?.confidence && (
                  <span className="confidence">
                    ({Math.round(analysis.intent.primary.confidence * 100)}%)
                  </span>
                )}
              </div>
            </div>
            
            {analysis?.intent?.secondary && analysis.intent.secondary.length > 0 && (
              <div className="secondary-intents">
                <div className="intent-label">{trans.secondaryIntents || 'Secondary Intents'}:</div>
                <div className="intent-values">
                  {analysis.intent.secondary.map((intent, index) => (
                    <span key={index} className="secondary-intent">
                      {intent.name}
                      {intent.confidence && (
                        <span className="confidence">
                          ({Math.round(intent.confidence * 100)}%)
                        </span>
                      )}
                      {index < analysis.intent.secondary.length - 1 && ', '}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <div className="sentiment-container">
            <div className="sentiment-label">{trans.customerSentiment || 'Customer Sentiment'}:</div>
            <div 
              className="sentiment-value"
              style={{ color: getSentimentColor(analysis?.sentiment?.sentiment) }}
            >
              {analysis?.sentiment?.sentiment 
                ? analysis.sentiment.sentiment.charAt(0).toUpperCase() + analysis.sentiment.sentiment.slice(1)
                : 'Unknown'}
              {analysis?.sentiment?.score && (
                <span className="sentiment-score">
                  ({analysis.sentiment.score > 0 ? '+' : ''}{Math.round(analysis.sentiment.score * 100) / 100})
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Entities Section */}
      <div className="analysis-card entities-card">
        <h3 className="card-title">
          <span className="card-icon">📋</span>
          {trans.detectedEntities || 'Detected Entities'}
        </h3>
        <div className="analysis-content">
          {analysis?.entities?.order_numbers && analysis.entities.order_numbers.length > 0 && (
            <div className="entity-group">
              <div className="entity-label">{trans.orderNumbers || 'Order Numbers'}:</div>
              <div className="entity-value">{formatEntityList(analysis.entities.order_numbers)}</div>
            </div>
          )}
          
          {analysis?.entities?.product_names && analysis.entities.product_names.length > 0 && (
            <div className="entity-group">
              <div className="entity-label">{trans.productsMentioned || 'Products Mentioned'}:</div>
              <div className="entity-value">{formatEntityList(analysis.entities.product_names)}</div>
            </div>
          )}
          
          {analysis?.entities?.contact_info?.email && analysis.entities.contact_info.email.length > 0 && (
            <div className="entity-group">
              <div className="entity-label">{trans.emailAddresses || 'Email Addresses'}:</div>
              <div className="entity-value">{formatEntityList(analysis.entities.contact_info.email)}</div>
            </div>
          )}
          
          {analysis?.entities?.contact_info?.phone && analysis.entities.contact_info.phone.length > 0 && (
            <div className="entity-group">
              <div className="entity-label">{trans.phoneNumbers || 'Phone Numbers'}:</div>
              <div className="entity-value">{formatEntityList(analysis.entities.contact_info.phone)}</div>
            </div>
          )}
          
          {analysis?.entities?.contact_info?.address && analysis.entities.contact_info.address.length > 0 && (
            <div className="entity-group">
              <div className="entity-label">{trans.addresses || 'Addresses'}:</div>
              <div className="entity-value">{formatEntityList(analysis.entities.contact_info.address)}</div>
            </div>
          )}
          
          {(!analysis?.entities || 
             ((!analysis.entities.order_numbers || analysis.entities.order_numbers.length === 0) && 
              (!analysis.entities.product_names || analysis.entities.product_names.length === 0) &&
              (!analysis.entities.contact_info?.email || analysis.entities.contact_info.email.length === 0) &&
              (!analysis.entities.contact_info?.phone || analysis.entities.contact_info.phone.length === 0) &&
              (!analysis.entities.contact_info?.address || analysis.entities.contact_info.address.length === 0))) && (
            <div className="no-entities">
              {trans.noEntitiesDetected || 'No entities detected in this call'}
            </div>
          )}
        </div>
      </div>
      
      {/* Pricing Section */}
      {analysis?.prices && analysis.prices.length > 0 && (
        <div className="analysis-card prices-card">
          <h3 className="card-title">
            <span className="card-icon">💰</span>
            {trans.pricesMentioned || 'Prices Mentioned'}
          </h3>
          <div className="analysis-content">
            <div className="price-list">
              {analysis.prices.map((price, index) => (
                <div key={index} className="price-item">
                  <div className="price-amount">${price.amount.toFixed(2)}</div>
                  <div className="price-context">{price.context}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Follow-ups Section */}
      {analysis?.follow_ups && analysis.follow_ups.length > 0 && (
        <div className="analysis-card follow-ups-card">
          <h3 className="card-title">
            <span className="card-icon">📅</span>
            {trans.followUpActions || 'Follow-up Actions'}
          </h3>
          <div className="analysis-content">
            <ul className="follow-up-list">
              {analysis.follow_ups.map((action, index) => (
                <li key={index} className="follow-up-item">{action}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
      
      {/* Reanalyze Button */}
      <div className="reanalyze-container">
        <button 
          onClick={handleReanalyze} 
          disabled={reAnalyzing}
          className="reanalyze-button"
        >
          {reAnalyzing ? (
            <>
              <span className="spinner-small"></span>
              {trans.reanalyzing || 'Reanalyzing...'}
            </>
          ) : (
            <>
              <span className="refresh-icon">🔄</span>
              {trans.reanalyzeCall || 'Reanalyze Call'}
            </>
          )}
        </button>
        
        {analysis?.analyzed_at && (
          <div className="analysis-timestamp">
            {trans.analyzedAt || 'Analyzed at'}: {new Date(analysis.analyzed_at).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
};

export default CallAnalysisPanel;
