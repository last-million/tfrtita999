import React from 'react';
import './CallActionsList.css';
import { useLanguage } from '../context/LanguageContext';
import translations from '../translations';

const CallActionsList = ({ actions, showTitle = true }) => {
  const { language } = useLanguage();
  const trans = translations[language] || {};
  
  if (!actions || actions.length === 0) {
    return (
      <div className="call-actions-list empty">
        <p className="no-actions">{trans.noActionsRecorded || 'No actions were recorded during this call'}</p>
      </div>
    );
  }
  
  // Group actions by type for better organization
  const searchActions = actions.filter(action => action.action_type === 'search');
  const weatherActions = actions.filter(action => action.action_type === 'weather');
  const calendarActions = actions.filter(action => action.action_type === 'calendar');
  const emailActions = actions.filter(action => action.action_type === 'email');
  const otherActions = actions.filter(action => 
    !['search', 'weather', 'calendar', 'email'].includes(action.action_type)
  );

  // Format date for display
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return dateString;
    }
  };
  
  return (
    <div className="call-actions-list">
      {showTitle && (
        <h3 className="actions-title">{trans.callActions || 'Call Actions'}</h3>
      )}
      
      {/* Calendar Events Section */}
      {calendarActions.length > 0 && (
        <div className="action-section">
          <h4 className="section-title">
            <span className="icon">📅</span> 
            {trans.scheduledEvents || 'Scheduled Events'}
          </h4>
          <div className="actions-container">
            {calendarActions.map((action, index) => (
              <div key={`calendar-${action.id || index}`} className="action-item calendar-action">
                <div className="action-time">{formatDate(action.created_at)}</div>
                <div className="action-content">
                  <div className="action-header">
                    <strong>{action.action_data?.summary || 'Meeting'}</strong>
                  </div>
                  <div className="action-details">
                    <div className="detail-row">
                      <span className="detail-label">{trans.start || 'Start'}:</span>
                      <span className="detail-value">
                        {new Date(action.action_data?.start_time).toLocaleString()}
                      </span>
                    </div>
                    {action.action_data?.hangout_link && (
                      <div className="detail-row">
                        <span className="detail-label">{trans.meetLink || 'Meet'}:</span>
                        <a 
                          href={action.action_data.hangout_link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="detail-value link"
                        >
                          {trans.joinMeeting || 'Join Meeting'}
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Email Section */}
      {emailActions.length > 0 && (
        <div className="action-section">
          <h4 className="section-title">
            <span className="icon">✉️</span> 
            {trans.sentEmails || 'Sent Emails'}
          </h4>
          <div className="actions-container">
            {emailActions.map((action, index) => (
              <div key={`email-${action.id || index}`} className="action-item email-action">
                <div className="action-time">{formatDate(action.created_at)}</div>
                <div className="action-content">
                  <div className="action-header">
                    <strong>{action.action_data?.subject || 'Email'}</strong>
                  </div>
                  <div className="action-details">
                    <div className="detail-row">
                      <span className="detail-label">{trans.to || 'To'}:</span>
                      <span className="detail-value">
                        {Array.isArray(action.action_data?.to) 
                          ? action.action_data?.to.join(', ')
                          : action.action_data?.to || 'No recipients'
                        }
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Weather Section */}
      {weatherActions.length > 0 && (
        <div className="action-section">
          <h4 className="section-title">
            <span className="icon">🌤️</span> 
            {trans.weatherInfo || 'Weather Information'}
          </h4>
          <div className="actions-container">
            {weatherActions.map((action, index) => (
              <div key={`weather-${action.id || index}`} className="action-item weather-action">
                <div className="action-time">{formatDate(action.created_at)}</div>
                <div className="action-content">
                  <div className="action-header">
                    <strong>{trans.weatherIn || 'Weather in'} {action.action_data?.location}</strong>
                  </div>
                  <div className="action-details">
                    <p className="weather-details">{action.action_data?.details}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Search Section */}
      {searchActions.length > 0 && (
        <div className="action-section">
          <h4 className="section-title">
            <span className="icon">🔍</span> 
            {trans.searches || 'Web Searches'}
          </h4>
          <div className="actions-container">
            {searchActions.map((action, index) => (
              <div key={`search-${action.id || index}`} className="action-item search-action">
                <div className="action-time">{formatDate(action.created_at)}</div>
                <div className="action-content">
                  <div className="action-header">
                    <strong>"{action.action_data?.query}"</strong>
                  </div>
                  {action.action_data?.results && action.action_data.results.length > 0 && (
                    <div className="search-results">
                      <div className="result-item">
                        <a 
                          href={action.action_data.results[0].link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="result-title"
                        >
                          {action.action_data.results[0].title}
                        </a>
                        <p className="result-snippet">{action.action_data.results[0].snippet}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Other Actions Section */}
      {otherActions.length > 0 && (
        <div className="action-section">
          <h4 className="section-title">
            <span className="icon">🔄</span> 
            {trans.otherActions || 'Other Actions'}
          </h4>
          <div className="actions-container">
            {otherActions.map((action, index) => (
              <div key={`other-${action.id || index}`} className="action-item other-action">
                <div className="action-time">{formatDate(action.created_at)}</div>
                <div className="action-content">
                  <div className="action-header">
                    <strong>{action.action_type}</strong>
                  </div>
                  <div className="action-details">
                    <pre className="action-data">{JSON.stringify(action.action_data, null, 2)}</pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CallActionsList;
