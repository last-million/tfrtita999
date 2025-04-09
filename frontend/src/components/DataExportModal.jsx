import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DataExportModal.css';
import { useLanguage } from '../context/LanguageContext';
import translations from '../translations';

const DataExportModal = ({ isOpen, onClose, callData }) => {
  const { language } = useLanguage();
  const trans = translations[language] || {};
  
  // State for the export service and UI
  const [selectedService, setSelectedService] = useState('');
  const [connectionStatus, setConnectionStatus] = useState({
    google_sheets: false,
    supabase: false,
    airtable: false
  });
  
  // Credentials state
  const [credentials, setCredentials] = useState({
    google_sheets: {},
    supabase: {},
    airtable: {}
  });
  
  // Destination state
  const [destinations, setDestinations] = useState([]);
  const [selectedDestination, setSelectedDestination] = useState('');
  const [newDestinationName, setNewDestinationName] = useState('');
  const [createNew, setCreateNew] = useState(false);
  
  // Field mapping state
  const [showFieldMapping, setShowFieldMapping] = useState(false);
  const [fieldMapping, setFieldMapping] = useState({});
  const [destinationFields, setDestinationFields] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Available source fields from call data
  const sourceFields = [
    { key: 'call_sid', label: trans.callSid || 'Call SID' },
    { key: 'from_number', label: trans.fromNumber || 'From Number' },
    { key: 'to_number', label: trans.toNumber || 'To Number' },
    { key: 'direction', label: trans.direction || 'Direction' },
    { key: 'status', label: trans.status || 'Status' },
    { key: 'start_time', label: trans.startTime || 'Start Time' },
    { key: 'end_time', label: trans.endTime || 'End Time' },
    { key: 'duration', label: trans.duration || 'Duration' },
    { key: 'recording_url', label: trans.recordingUrl || 'Recording URL' },
    { key: 'transcription', label: trans.transcription || 'Transcription' },
    { key: 'cost', label: trans.cost || 'Cost' },
    { key: 'ultravox_cost', label: trans.ultravoxCost || 'Ultravox Cost' },
    { key: 'hang_up_by', label: trans.hangUpBy || 'Hung Up By' },
    { key: 'created_at', label: trans.createdAt || 'Created At' }
  ];

  // Check connection status on mount and when service changes
  useEffect(() => {
    if (isOpen) {
      checkConnectionStatus();
    }
  }, [isOpen, selectedService]);

  // Fetch destinations when service is selected and connected
  useEffect(() => {
    if (selectedService && connectionStatus[selectedService]) {
      fetchDestinations();
    }
  }, [selectedService, connectionStatus]);

  // Fetch destination fields when a destination is selected
  useEffect(() => {
    if (selectedDestination && !createNew) {
      fetchDestinationFields();
    } else if (createNew) {
      // Set default destination fields based on service
      setDefaultDestinationFields();
    }
  }, [selectedDestination, createNew]);

  const checkConnectionStatus = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await axios.get(`${baseUrl}/credentials/status`);
      
      const status = response.data || {};
      setConnectionStatus({
        google_sheets: !!status.google_sheets?.connected,
        supabase: !!status.supabase?.connected,
        airtable: !!status.airtable?.connected
      });
      
      // If credentials exist, store them
      if (status.google_sheets?.credentials) {
        setCredentials(prev => ({ ...prev, google_sheets: status.google_sheets.credentials }));
      }
      if (status.supabase?.credentials) {
        setCredentials(prev => ({ ...prev, supabase: status.supabase.credentials }));
      }
      if (status.airtable?.credentials) {
        setCredentials(prev => ({ ...prev, airtable: status.airtable.credentials }));
      }
    } catch (error) {
      console.error('Error checking connection status:', error);
      setError(trans.connectionCheckError || 'Failed to check connection status');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDestinations = async () => {
    setIsLoading(true);
    setError('');
    setDestinations([]);
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      let endpoint = '';
      
      // Determine the endpoint based on the selected service
      switch (selectedService) {
        case 'google_sheets':
          endpoint = `${baseUrl}/google/sheets`;
          break;
        case 'supabase':
          endpoint = `${baseUrl}/supabase/tables`;
          break;
        case 'airtable':
          endpoint = `${baseUrl}/airtable/tables`;
          break;
        default:
          throw new Error('Invalid service selected');
      }
      
      const response = await axios.get(endpoint);
      setDestinations(response.data || []);
      
      // Clear selected destination when destinations change
      setSelectedDestination('');
      setCreateNew(false);
    } catch (error) {
      console.error(`Error fetching ${selectedService} destinations:`, error);
      setError(trans.destinationFetchError || 'Failed to fetch destinations');
      setDestinations([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDestinationFields = async () => {
    if (!selectedDestination) return;
    
    setIsLoading(true);
    setError('');
    setDestinationFields([]);
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      let endpoint = '';
      
      // Determine the endpoint based on the selected service
      switch (selectedService) {
        case 'google_sheets':
          endpoint = `${baseUrl}/google/sheets/${selectedDestination}/fields`;
          break;
        case 'supabase':
          endpoint = `${baseUrl}/supabase/tables/${selectedDestination}/fields`;
          break;
        case 'airtable':
          endpoint = `${baseUrl}/airtable/tables/${selectedDestination}/fields`;
          break;
        default:
          throw new Error('Invalid service selected');
      }
      
      const response = await axios.get(endpoint);
      const fields = response.data || [];
      setDestinationFields(fields);
      
      // Initialize field mapping
      const initialMapping = {};
      sourceFields.forEach((sourceField, index) => {
        const matchingField = fields.find(field => 
          field.name.toLowerCase() === sourceField.key.toLowerCase());
        
        if (matchingField) {
          initialMapping[sourceField.key] = matchingField.name;
        } else if (index < fields.length) {
          initialMapping[sourceField.key] = fields[index].name;
        }
      });
      
      setFieldMapping(initialMapping);
      setShowFieldMapping(true);
    } catch (error) {
      console.error(`Error fetching ${selectedService} fields:`, error);
      setError(trans.fieldsFetchError || 'Failed to fetch destination fields');
      setDestinationFields([]);
      setShowFieldMapping(false);
    } finally {
      setIsLoading(false);
    }
  };

  const setDefaultDestinationFields = () => {
    // Create default field names based on source fields
    const fields = sourceFields.map(field => ({
      name: field.key,
      type: getFieldType(field.key),
      label: field.label
    }));
    
    setDestinationFields(fields);
    
    // Initialize field mapping (1:1 mapping)
    const initialMapping = {};
    sourceFields.forEach(sourceField => {
      initialMapping[sourceField.key] = sourceField.key;
    });
    
    setFieldMapping(initialMapping);
    setShowFieldMapping(true);
  };
  
  const getFieldType = (fieldKey) => {
    // Determine appropriate field type based on the field key
    switch (fieldKey) {
      case 'start_time':
      case 'end_time':
      case 'created_at':
        return 'datetime';
      case 'duration':
      case 'cost':
      case 'ultravox_cost':
        return 'number';
      case 'transcription':
        return 'text';
      default:
        return 'string';
    }
  };

  const handleConnectService = async () => {
    // Redirect to the authentication page for the selected service
    window.location.href = `/auth?service=${selectedService}`;
  };

  const handleServiceChange = (e) => {
    setSelectedService(e.target.value);
    setSelectedDestination('');
    setCreateNew(false);
    setShowFieldMapping(false);
    setError('');
    setSuccess('');
  };

  const handleDestinationChange = (e) => {
    setSelectedDestination(e.target.value);
    setCreateNew(false);
    setShowFieldMapping(false);
    setError('');
    setSuccess('');
    
    // Immediately fetch fields for the selected destination
    if (e.target.value) {
      fetchDestinationFields();
    }
  };

  const handleMapFieldChange = (sourceKey, destinationField) => {
    setFieldMapping(prev => ({
      ...prev,
      [sourceKey]: destinationField
    }));
  };

  const handleCreateNewChange = () => {
    setCreateNew(prev => !prev);
    setSelectedDestination('');
    setShowFieldMapping(false);
    setNewDestinationName('');
    setError('');
    setSuccess('');
  };

  const handleExport = async () => {
    if (!selectedService) {
      setError(trans.selectServiceError || 'Please select a service');
      return;
    }

    if (createNew && !newDestinationName.trim()) {
      setError(trans.destinationNameError || 'Please enter a name for the new destination');
      return;
    }

    if (!createNew && !selectedDestination) {
      setError(trans.selectDestinationError || 'Please select a destination');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const baseUrl = import.meta.env.VITE_API_URL || '/api';
      const destination = createNew ? newDestinationName : selectedDestination;
      
      // Prepare export payload
      const payload = {
        service: selectedService,
        destination: destination,
        createNew: createNew,
        fieldMapping: fieldMapping,
        callData: callData, // Only include if exporting specific calls
        syncEnabled: true // Enable real-time sync
      };
      
      // Call the export API
      const response = await axios.post(`${baseUrl}/export/calls`, payload);
      
      if (response.data.success) {
        setSuccess(response.data.message || (trans.exportSuccess || 'Export successful!'));
        
        // If a new destination was created, refresh destinations
        if (createNew) {
          await fetchDestinations();
          setSelectedDestination(newDestinationName);
          setCreateNew(false);
        }
      } else {
        setError(response.data.message || (trans.exportError || 'Export failed'));
      }
    } catch (error) {
      console.error('Error exporting data:', error);
      setError(error.response?.data?.message || (trans.exportError || 'Failed to export data'));
    } finally {
      setIsLoading(false);
    }
  };

  const renderCredentialsForm = () => {
    if (!selectedService) return null;
    
    return (
      <div className="credentials-form">
        <h3>{trans.connectService || 'Connect to Service'}</h3>
        <p>
          {trans.serviceNotConnected || 'This service is not connected yet. Please connect your account to continue.'}
        </p>
        <button 
          className="connect-button"
          onClick={handleConnectService}
          disabled={isLoading}
        >
          {trans.connect || 'Connect'} {getServiceName(selectedService)}
        </button>
      </div>
    );
  };

  const renderDestinationSelector = () => {
    if (!selectedService || !connectionStatus[selectedService]) return null;
    
    return (
      <div className="destination-selector">
        <h3>{trans.selectDestination || 'Select Destination'}</h3>
        
        <div className="destination-options">
          <div className="radio-option">
            <input
              type="radio"
              id="existing-destination"
              name="destination-type"
              checked={!createNew}
              onChange={handleCreateNewChange}
              disabled={isLoading || destinations.length === 0}
            />
            <label htmlFor="existing-destination">
              {trans.useExisting || 'Use existing'} {getDestinationType()}
            </label>
          </div>
          
          {!createNew && destinations.length > 0 && (
            <div className="select-container">
              <select
                value={selectedDestination}
                onChange={handleDestinationChange}
                disabled={isLoading}
              >
                <option value="">{trans.selectOne || 'Select one...'}</option>
                {destinations.map((dest, index) => (
                  <option key={index} value={dest.id || dest.name || dest}>
                    {dest.name || dest}
                  </option>
                ))}
              </select>
            </div>
          )}
          
          {!createNew && destinations.length === 0 && (
            <p className="no-destinations">
              {trans.noDestinations || `No ${getDestinationType()} found. Create a new one.`}
            </p>
          )}
          
          <div className="radio-option">
            <input
              type="radio"
              id="new-destination"
              name="destination-type"
              checked={createNew}
              onChange={handleCreateNewChange}
              disabled={isLoading}
            />
            <label htmlFor="new-destination">
              {trans.createNew || 'Create new'} {getDestinationType()}
            </label>
          </div>
          
          {createNew && (
            <div className="input-container">
              <input
                type="text"
                value={newDestinationName}
                onChange={(e) => setNewDestinationName(e.target.value)}
                placeholder={trans.enterName || `Enter name for new ${getDestinationType()}`}
                disabled={isLoading}
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderFieldMapping = () => {
    if (!showFieldMapping) return null;
    
    return (
      <div className="field-mapping">
        <h3>{trans.fieldMapping || 'Map Fields'}</h3>
        <p>
          {createNew 
            ? (trans.newDestFieldsDesc || 'Fields will be created automatically based on source data, but you can customize the mapping below') 
            : (trans.mapFieldsDescription || 'Map call data fields to the existing destination fields')}
        </p>
        
        <div className="field-mapping-options">
          <div className="auto-match-option">
            <button 
              className="auto-match-button" 
              onClick={() => autoMatchFields()}
              disabled={isLoading || destinationFields.length === 0}
            >
              {trans.autoMatchFields || 'Auto-match fields'}
            </button>
            <span className="auto-match-help">
              {trans.autoMatchHelp || 'Automatically match fields with similar names'}
            </span>
          </div>
        </div>
        
        <div className="mapping-table">
          <div className="mapping-header">
            <div className="mapping-cell">{trans.sourceField || 'Source Field'}</div>
            <div className="mapping-cell">{trans.destinationField || 'Destination Field'}</div>
          </div>
          
          {/* Standard call fields */}
          <div className="mapping-section">
            <h4>{trans.callFields || 'Call Data Fields'}</h4>
            {sourceFields.map((sourceField, index) => (
              <div className="mapping-row" key={index}>
                <div className="mapping-cell source-field">
                  {sourceField.label}
                </div>
                <div className="mapping-cell">
                  <select
                    value={fieldMapping[sourceField.key] || ''}
                    onChange={(e) => handleMapFieldChange(sourceField.key, e.target.value)}
                    disabled={isLoading}
                  >
                    <option value="">{trans.doNotExport || 'Do not export'}</option>
                    {destinationFields.map((destField, idx) => (
                      <option key={idx} value={destField.name}>
                        {destField.label || destField.name}
                      </option>
                    ))}
                    {createNew && !destinationFields.some(f => f.name === sourceField.key) && (
                      <option value={sourceField.key}>
                        {`${trans.createNew || 'Create new'}: ${sourceField.label}`}
                      </option>
                    )}
                  </select>
                </div>
              </div>
            ))}
          </div>
          
          {/* Client information fields */}
          <div className="mapping-section">
            <h4>{trans.clientFields || 'Client Information Fields'}</h4>
            <p className="client-fields-info">
              {trans.clientFieldsInfo || 'These fields will be extracted from call transcriptions when available'}
            </p>
            {[
              { key: 'client_info.name', label: trans.clientName || 'Client Name' },
              { key: 'client_info.email', label: trans.clientEmail || 'Client Email' },
              { key: 'client_info.phone', label: trans.clientPhone || 'Client Phone' },
              { key: 'client_info.company', label: trans.clientCompany || 'Client Company' },
              { key: 'client_info.address', label: trans.clientAddress || 'Client Address' }
            ].map((clientField, index) => (
              <div className="mapping-row" key={`client-${index}`}>
                <div className="mapping-cell source-field">
                  {clientField.label}
                </div>
                <div className="mapping-cell">
                  <select
                    value={fieldMapping[clientField.key] || ''}
                    onChange={(e) => handleMapFieldChange(clientField.key, e.target.value)}
                    disabled={isLoading}
                  >
                    <option value="">{trans.doNotExport || 'Do not export'}</option>
                    {destinationFields.map((destField, idx) => (
                      <option key={idx} value={destField.name}>
                        {destField.label || destField.name}
                      </option>
                    ))}
                    {createNew && !destinationFields.some(f => f.name === clientField.key.split('.')[1]) && (
                      <option value={clientField.key.split('.')[1]}>
                        {`${trans.createNew || 'Create new'}: ${clientField.label}`}
                      </option>
                    )}
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };
  
  const autoMatchFields = () => {
    const newMapping = {};
    
    // Helper function to find best match
    const findBestMatch = (sourceKey, sourceLabel) => {
      // Try exact match on name
      const exactNameMatch = destinationFields.find(
        field => field.name.toLowerCase() === sourceKey.toLowerCase()
      );
      if (exactNameMatch) return exactNameMatch.name;
      
      // Try exact match on label
      const exactLabelMatch = destinationFields.find(
        field => (field.label || field.name).toLowerCase() === sourceLabel.toLowerCase()
      );
      if (exactLabelMatch) return exactLabelMatch.name;
      
      // Try contains match (name contains sourceKey or vice versa)
      const containsMatch = destinationFields.find(
        field => field.name.toLowerCase().includes(sourceKey.toLowerCase()) || 
                sourceKey.toLowerCase().includes(field.name.toLowerCase())
      );
      if (containsMatch) return containsMatch.name;
      
      // If it's a client info field, try matching without the prefix
      if (sourceKey.startsWith('client_info.')) {
        const simpleKey = sourceKey.split('.')[1];
        
        // Try simple key exact match
        const simpleExactMatch = destinationFields.find(
          field => field.name.toLowerCase() === simpleKey.toLowerCase()
        );
        if (simpleExactMatch) return simpleExactMatch.name;
        
        // Try simple key contains match
        const simpleContainsMatch = destinationFields.find(
          field => field.name.toLowerCase().includes(simpleKey.toLowerCase()) || 
                  simpleKey.toLowerCase().includes(field.name.toLowerCase())
        );
        if (simpleContainsMatch) return simpleContainsMatch.name;
      }
      
      return createNew ? sourceKey.split('.').pop() : '';
    };
    
    // Match call fields
    sourceFields.forEach(sourceField => {
      newMapping[sourceField.key] = findBestMatch(sourceField.key, sourceField.label);
    });
    
    // Match client info fields
    [
      { key: 'client_info.name', label: trans.clientName || 'Client Name' },
      { key: 'client_info.email', label: trans.clientEmail || 'Client Email' },
      { key: 'client_info.phone', label: trans.clientPhone || 'Client Phone' },
      { key: 'client_info.company', label: trans.clientCompany || 'Client Company' },
      { key: 'client_info.address', label: trans.clientAddress || 'Client Address' }
    ].forEach(clientField => {
      newMapping[clientField.key] = findBestMatch(clientField.key, clientField.label);
    });
    
    setFieldMapping(newMapping);
  };

  const getServiceName = (serviceKey) => {
    switch (serviceKey) {
      case 'google_sheets':
        return 'Google Sheets';
      case 'supabase':
        return 'Supabase';
      case 'airtable':
        return 'Airtable';
      default:
        return serviceKey;
    }
  };

  const getDestinationType = () => {
    switch (selectedService) {
      case 'google_sheets':
        return trans.sheet || 'sheet';
      case 'supabase':
      case 'airtable':
        return trans.table || 'table';
      default:
        return trans.destination || 'destination';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="data-export-modal">
      <div className="data-export-content">
        <div className="data-export-header">
          <h2>{trans.exportData || 'Export Call Data'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="data-export-body">
          {error && (
            <div className="error-message">{error}</div>
          )}
          
          {success && (
            <div className="success-message">{success}</div>
          )}
          
          <div className="service-selector">
            <h3>{trans.selectService || 'Select Export Service'}</h3>
            <select
              value={selectedService}
              onChange={handleServiceChange}
              disabled={isLoading}
            >
              <option value="">{trans.selectOne || 'Select one...'}</option>
              <option value="google_sheets">Google Sheets</option>
              <option value="supabase">Supabase</option>
              <option value="airtable">Airtable</option>
            </select>
          </div>
          
          {selectedService && !connectionStatus[selectedService] && renderCredentialsForm()}
          
          {renderDestinationSelector()}
          
          {renderFieldMapping()}
          
          {isLoading && (
            <div className="loading-indicator">
              <div className="spinner"></div>
              <p>{trans.loading || 'Loading...'}</p>
            </div>
          )}
        </div>
        
        <div className="data-export-footer">
          <button
            className="cancel-button"
            onClick={onClose}
            disabled={isLoading}
          >
            {trans.cancel || 'Cancel'}
          </button>
          
          <button
            className="export-button"
            onClick={handleExport}
            disabled={isLoading || !selectedService || (!selectedDestination && !createNew) || (createNew && !newDestinationName.trim())}
          >
            {isLoading ? (trans.exporting || 'Exporting...') : (trans.export || 'Export')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataExportModal;
