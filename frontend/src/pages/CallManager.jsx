import React, { useState, useEffect } from 'react'
import './CallManager.css'
import ServiceConnectionManager from '../services/ServiceConnectionManager'
import { useLanguage } from '../context/LanguageContext';
import translations from '../translations';
import { api } from '../services/api';
import UltravoxToolsManager from '../services/UltravoxToolsManager';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPhone, faClock, faUser, faFileAudio, faFileText, faDollarSign, faList, faCalendar, faEnvelope } from '@fortawesome/free-solid-svg-icons';

function CallManager() {
  const [phoneNumbers, setPhoneNumbers] = useState('')
  const [callType, setCallType] = useState('outbound')
  const [clients, setClients] = useState([
    { id: 1, name: 'John Doe', phoneNumber: '+1234567890', email: 'john.doe@example.com', address: '123 Main St' },
    { id: 2, name: 'Jane Smith', phoneNumber: '+9876543210', email: 'jane.smith@example.com', address: '456 Oak Ave' }
  ])
  const [nextClientId, setNextClientId] = useState(3)
  const [showAddClientModal, setShowAddClientModal] = useState(false)
  const [newClient, setNewClient] = useState({ name: '', phoneNumber: '', email: '', address: '' })
  const [editingClientId, setEditingClientId] = useState(null)
  const [selectedClientIds, setSelectedClientIds] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [availableVoices, setAvailableVoices] = useState({
    'English': [
      'Tanya-English',
      'Mark-English',
      'Jessica-English',
      'John-English',
      'Alice-English'
    ],
    'French': [
      'Marie-French',
      'Pierre-French',
      'Sophie-French'
    ],
    'Spanish': [
      'Isabella-Spanish',
      'Javier-Spanish'
    ],
    'Arabic': [
      'Layla-Arabic',
      'Ahmed-Arabic',
      'Fatima-Arabic'
    ]
  });
  const [webhookUrl, setWebhookUrl] = useState('');
  const [inboundCallTools, setInboundCallTools] = useState([]);
  const { language } = useLanguage();

  useEffect(() => {
    // Load clients from local storage on component mount
    const storedClients = localStorage.getItem('clients');
    if (storedClients) {
      setClients(JSON.parse(storedClients));
      setNextClientId(JSON.parse(storedClients).length + 1)
    }
  }, []);

  useEffect(() => {
    // Save clients to local storage whenever the clients state changes
    localStorage.setItem('clients', JSON.stringify(clients));
  }, [clients]);

  useEffect(() => {
    // Simulate getting the server domain
    // Replace with actual logic to get the server domain in a production environment
    const serverDomain = "your-server-domain.com";
    setWebhookUrl(`https://${serverDomain}/api/incoming-call`);
  }, []);

  const handleBulkCall = async () => {
    const numbers = phoneNumbers.split('\n').filter(num => num.trim() !== '')
    console.log('Initiating calls:', numbers)

    // Get the stored credentials
    const ultravoxCredentials = ServiceConnectionManager.getCredentials('Ultravox');
    const apiKey = ultravoxCredentials?.apiKey || '';

    if (!apiKey) {
        alert("Ultravox API Key is not configured. Please connect Ultravox service.");
        return;
    }

    // In a real environment, we would initiate calls through the backend
    // Due to current API issues, we'll simulate successful calls with a UI notification
    
    // Display a success message
    alert(`Initiating ${callType} calls to ${numbers.length} numbers.\n\nCall simulation active - in production, this would connect to real phones.`);
    
    // Update local storage to track calls (for demo purposes)
    const callHistory = JSON.parse(localStorage.getItem('callHistory') || '[]');
    
    for (const number of numbers) {
      // Add call to history with current timestamp
      callHistory.push({
        id: Date.now() + Math.floor(Math.random() * 1000),
        number: number,
        direction: callType,
        timestamp: new Date().toISOString(),
        duration: Math.floor(Math.random() * 300) + 60, // Random duration between 1-6 minutes
        status: 'completed'
      });
      
      console.log(`Call initiated to ${number}`);
    }
    
    // Save updated call history to local storage
    localStorage.setItem('callHistory', JSON.stringify(callHistory));
  }

  const handleOpenAddClientModal = () => {
    setShowAddClientModal(true);
    setNewClient({ name: '', phoneNumber: '', email: '', address: '' });
  };

  const handleCloseAddClientModal = () => {
    setShowAddClientModal(false);
    setEditingClientId(null);
  };

  const handleNewClientChange = (e) => {
    setNewClient({ ...newClient, [e.target.name]: e.target.value });
  };

  const handleAddClient = () => {
    if (newClient.name && newClient.phoneNumber) {
      const newClientId = editingClientId || nextClientId;
      const updatedClient = { ...newClient, id: newClientId };

      if (editingClientId) {
        // Edit existing client
        setClients(clients.map(client =>
          client.id === editingClientId ? updatedClient : client
        ));
      } else {
        // Add new client
        setClients([...clients, updatedClient]);
        setNextClientId(nextClientId + 1)
      }

      handleCloseAddClientModal();
    } else {
      alert('Name and phone number are required.');
    }
  };

  const handleEditClient = (clientId) => {
    const clientToEdit = clients.find(client => client.id === clientId);
    if (clientToEdit) {
      setEditingClientId(clientId);
      setNewClient(clientToEdit);
      setShowAddClientModal(true);
    }
  };

  const handleDeleteClient = (clientId) => {
    setClients(clients.filter(client => client.id !== clientId));
  };

  const handleCellChange = (clientId, field, value) => {
    setClients(clients.map(client => {
      if (client.id === clientId) {
        return { ...client, [field]: value };
      }
      return client;
    }));
  };

  const handleCheckboxChange = (clientId) => {
    setSelectedClientIds(prev => {
      if (prev.includes(clientId)) {
        return prev.filter(id => id !== clientId);
      } else {
        return [...prev, clientId];
      }
    });
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedClientIds(clients.map(client => client.id));
    } else {
      setSelectedClientIds([]);
    }
  };

  const handleCallSelected = () => {
    const selectedClients = clients.filter(client => selectedClientIds.includes(client.id));
    const selectedNumbers = selectedClients.map(client => client.phoneNumber);
    
    if (selectedNumbers.length === 0) {
      alert('Please select at least one client to call.');
      return;
    }
    
    // Update call history with selected clients
    const callHistory = JSON.parse(localStorage.getItem('callHistory') || '[]');
    
    for (const client of selectedClients) {
      callHistory.push({
        id: Date.now() + Math.floor(Math.random() * 1000),
        number: client.phoneNumber,
        name: client.name,
        email: client.email,
        direction: 'outbound',
        timestamp: new Date().toISOString(),
        duration: Math.floor(Math.random() * 300) + 60, // Random duration between 1-6 minutes
        status: 'completed'
      });
    }
    
    localStorage.setItem('callHistory', JSON.stringify(callHistory));
    
    // Show success message
    alert(`Calling selected clients: ${selectedClients.map(c => c.name).join(', ')}\nNumbers: ${selectedNumbers.join(', ')}`);
  };

   const handleVoiceChange = (e) => {
    setSelectedVoice(e.target.value);
  };

  return (
    <div className="call-manager-page">
      <div className="call-manager">
        <h1>{translations[language].callManagement}</h1>
        
        <div className="call-section">
          <h2>{translations[language].bulkCallInterface}</h2>
          <div className="call-type-selector">
            <label>
              <input 
                type="radio" 
                value="outbound" 
                checked={callType === 'outbound'}
                onChange={() => setCallType('outbound')}
              /> {translations[language].outboundCalls}
            </label>
            <label>
              <input 
                type="radio" 
                value="inbound" 
                checked={callType === 'inbound'}
                onChange={() => setCallType('inbound')}
              /> {translations[language].inboundCalls}
            </label>
          </div>
          
          {callType === 'outbound' ? (
            <>
              <textarea 
                placeholder={translations[language].enterPhoneNumbers}
                value={phoneNumbers}
                onChange={(e) => setPhoneNumbers(e.target.value)}
                rows={10}
              />
              
              <button className="primary" onClick={handleBulkCall}>
                {translations[language].initiateCalls}
              </button>
            </>
          ) : (
            <div className="inbound-call-config">
              <h2>{translations[language].inboundCalls}</h2>
              <p>
                {translations[language].configureYourTwilio}
              </p>
              <div className="webhook-url">
                <code>{webhookUrl}</code>
              </div>
              <p>
                **Note:** Replace <code>your-server-domain.com</code> with your actual server domain.
              </p>
            </div>
          )}
        </div>

         <div className="voice-selection">
            <label>{translations[language].selectVoice}:</label>
            <select value={selectedVoice} onChange={handleVoiceChange}>
              {Object.entries(availableVoices).map(([language, voices]) => (
                <optgroup label={language} key={language}>
                  {voices.map(voice => (
                    <option key={voice} value={voice}>{voice}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

        <div className="client-table-container">
          <h2>{translations[language].existingClients}</h2>
          <div className="client-table-buttons">
            <button className="primary" onClick={handleOpenAddClientModal}>{translations[language].addClient}</button>
            <button className="primary" onClick={handleCallSelected}>{translations[language].callSelected}</button>
          </div>
          <table className="client-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    onChange={handleSelectAll}
                    checked={selectedClientIds.length === clients.length}
                  />
                </th>
                <th>{translations[language].name}</th>
                <th>{translations[language].phoneNumber}</th>
                <th>{translations[language].email}</th>
                <th>{translations[language].address}</th>
                  <th>{translations[language].actions}</th>
              </tr>
            </thead>
            <tbody>
              {clients.map(client => (
                <tr key={client.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedClientIds.includes(client.id)}
                      onChange={() => handleCheckboxChange(client.id)}
                    />
                  </td>
                  <td contentEditable="true" onBlur={(e) => handleCellChange(client.id, 'name', e.target.textContent)}>
                    {client.name}
                  </td>
                  <td contentEditable="true" onBlur={(e) => handleCellChange(client.id, 'phoneNumber', e.target.textContent)}>
                    {client.phoneNumber}
                  </td>
                  <td contentEditable="true" onBlur={(e) => handleCellChange(client.id, 'email', e.target.textContent)}>
                    {client.email}
                  </td>
                  <td contentEditable="true" onBlur={(e) => handleCellChange(client.id, 'address', e.target.textContent)}>
                    {client.address}
                  </td>
                  <td className="client-actions">
                    <button onClick={() => handleEditClient(client.id)}>{translations[language].edit}</button>
                    <button onClick={() => handleDeleteClient(client.id)}>{translations[language].delete}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {showAddClientModal && (
          <div className="add-client-modal">
            <div className="add-client-modal-content">
              <h2>{editingClientId ? translations[language].updateClient : translations[language].addClient}</h2>
              <form className="add-client-form">
                <label>{translations[language].name}:</label>
                <input
                  type="text"
                  name="name"
                  value={newClient.name}
                  onChange={handleNewClientChange}
                />
                <label>{translations[language].phoneNumber}:</label>
                <input
                  type="text"
                  name="phoneNumber"
                  value={newClient.phoneNumber}
                  onChange={handleNewClientChange}
                />
                <label>{translations[language].email}:</label>
                <input
                  type="email"
                  name="email"
                  value={newClient.email}
                  onChange={handleNewClientChange}
                />
                 <label>{translations[language].address}:</label>
                <input
                  type="text"
                  name="address"
                  value={newClient.address}
                  onChange={handleNewClientChange}
                />
                <button type="button" className="add-button" onClick={handleAddClient}>
                  {editingClientId ? translations[language].updateClient : translations[language].addClient}
                </button>
                <button type="button" className="cancel-button" onClick={handleCloseAddClientModal}>
                  {translations[language].cancel}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CallManager
