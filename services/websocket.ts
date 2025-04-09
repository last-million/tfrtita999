/**
 * WebSocket service for real-time communication
 * This file is treated as a TypeScript module by importing the .tsx file
 */

class WebSocketService {
  constructor() {
    this.socket = null;
    this.reconnectTimer = null;
    this.url = 'wss://ajingolik.fun/ws';
    this.userId = null;
    this.authToken = null;
    this.messageListeners = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000; // 3s initial delay
    
    // Try to get URL from environment variables
    try {
      const envUrl = document.querySelector('meta[name="websocket-url"]')?.getAttribute('content');
      if (envUrl) {
        this.url = envUrl;
      }
    } catch (e) {
      console.warn('Could not get WebSocket URL from meta tag', e);
    }
  }

  /**
   * Connect to WebSocket server
   */
  connect(userId, authToken) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }
    
    this.userId = userId;
    this.authToken = authToken;
    this.reconnectAttempts = 0;
    
    this.initializeConnection();
  }
  
  /**
   * Initialize WebSocket connection
   */
  initializeConnection() {
    try {
      // Add auth token to connection URL
      const connectionUrl = `${this.url}?token=${this.authToken}`;
      this.socket = new WebSocket(connectionUrl);
      
      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }
  
  /**
   * Handle WebSocket open event
   */
  handleOpen(event) {
    console.log('WebSocket connection established');
    this.reconnectAttempts = 0;
    
    // Authenticate immediately after connection
    this.sendMessage('authenticate', { userId: this.userId });
  }
  
  /**
   * Handle WebSocket message event
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      // Notify all message listeners
      this.messageListeners.forEach(listener => {
        try {
          listener(message);
        } catch (error) {
          console.error('Error in WebSocket message listener:', error);
        }
      });
      
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }
  
  /**
   * Handle WebSocket close event
   */
  handleClose(event) {
    console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
    
    // Don't reconnect if closed normally
    if (event.code !== 1000) {
      this.scheduleReconnect();
    } else {
      this.socket = null;
    }
  }
  
  /**
   * Handle WebSocket error event
   */
  handleError(event) {
    console.error('WebSocket error:', event);
  }
  
  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectTimer !== null) {
      return; // Already attempting to reconnect
    }
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.initializeConnection();
    }, delay);
  }
  
  /**
   * Send WebSocket message
   */
  sendMessage(type, data) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message, WebSocket is not connected');
      return;
    }
    
    const message = { type, data };
    this.socket.send(JSON.stringify(message));
  }
  
  /**
   * Join a call room
   */
  joinCall(callSid) {
    this.sendMessage('join_call', { callSid });
  }
  
  /**
   * Add message listener
   */
  addMessageListener(listener) {
    this.messageListeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      this.messageListeners = this.messageListeners.filter(l => l !== listener);
    };
  }
  
  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'User disconnect');
      this.socket = null;
    }
    
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.userId = null;
    this.authToken = null;
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

export default websocketService;
