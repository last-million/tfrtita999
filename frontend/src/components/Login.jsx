// frontend/src/components/Login.jsx
import React, { useState, useEffect } from "react";
import { api } from "../services/api.js"; // Revert to named import

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);

  // Test connection on component mount
  useEffect(() => {
    testConnection();
  }, []);

  // Function to test API connectivity
  const testConnection = async () => {
    try {
      setMessage("Testing API connection...");
      const response = await api.health();
      setMessage(`API connection successful: ${response.data.status}`);
    } catch (err) {
      console.error("API connection error:", err);
      setMessage(`API connection error: ${err.message}`);
    }
  };

  // Test the availability of routes
  const testRoutes = async () => {
    try {
      setDebugInfo("Loading routes...");
      const response = await api.auth.testConnection();
      setDebugInfo(JSON.stringify(response.data, null, 2));
    } catch (err) {
      setDebugInfo(`Error fetching routes: ${err.message}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // First try with the regular endpoint
      console.log("Attempting login with main endpoint...");
      const response = await api.auth.login({ username, password });
      handleLoginSuccess(response);
    } catch (mainError) {
      console.error("Main login error:", mainError);
      
      try {
        // If that fails, try the simplified endpoint
        console.log("Attempting login with simple endpoint...");
        const response = await api.auth.loginSimple({ username, password });
        handleLoginSuccess(response);
      } catch (simpleError) {
        console.error("Simple login error:", simpleError);
        
        try {
          // If both methods fail, try the direct URL approach
          console.log("Attempting login with direct endpoint...");
          const response = await api.auth.loginDirect({ username, password });
          handleLoginSuccess(response);
        } catch (directError) {
          console.error("Direct login error:", directError);
          
          // Show detailed error info from all three attempts
          setError(
            `Login failed with all methods. Main error: ${mainError.message || 'Unknown error'}. 
            Direct error: ${directError.message || 'Unknown error'}.
            Response status: ${mainError.response?.status || 'N/A'}.`
          );
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSuccess = (response) => {
    const { access_token } = response.data;
    // Save token to localStorage or cookie
    localStorage.setItem("token", access_token);
    localStorage.setItem("auth_token", access_token);

    // Redirect or reload
    window.location.href = "/";
  };

  return (
    <div className="login-container" style={{ maxWidth: "600px", margin: "0 auto" }}>
      <h2>Login</h2>
      
      {/* Connection status */}
      {message && (
        <div style={{ padding: "10px", background: "#f0f0f0", marginBottom: "10px", borderRadius: "4px" }}>
          {message}
        </div>
      )}
      
      {/* Error message */}
      {error && (
        <div style={{ color: "red", marginBottom: "10px", padding: "10px", background: "#fff0f0", borderRadius: "4px" }}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
        <div>
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            style={{ display: "block", width: "100%", padding: "8px", marginTop: "5px" }}
            disabled={isLoading}
          />
        </div>
        <div style={{ marginTop: "10px" }}>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            style={{ display: "block", width: "100%", padding: "8px", marginTop: "5px" }}
            disabled={isLoading}
          />
        </div>
        <button 
          type="submit" 
          style={{ 
            marginTop: "15px", 
            padding: "8px 16px", 
            backgroundColor: "#4CAF50", 
            color: "white", 
            border: "none", 
            borderRadius: "4px", 
            cursor: isLoading ? "not-allowed" : "pointer",
            opacity: isLoading ? 0.7 : 1
          }}
          disabled={isLoading}
        >
          {isLoading ? "Logging in..." : "Login"}
        </button>
        
        {/* Debug tools */}
        <div style={{ marginTop: "40px", padding: "15px", background: "#f8f8f8", borderRadius: "4px" }}>
          <h3>Debug Tools</h3>
          <button 
            type="button" 
            onClick={testConnection}
            style={{ 
              marginRight: "10px", 
              padding: "5px 10px", 
              backgroundColor: "#007bff", 
              color: "white", 
              border: "none", 
              borderRadius: "4px"
            }}
          >
            Test API Connection
          </button>
          <button 
            type="button" 
            onClick={testRoutes}
            style={{ 
              padding: "5px 10px", 
              backgroundColor: "#007bff", 
              color: "white", 
              border: "none", 
              borderRadius: "4px"
            }}
          >
            Show Available Routes
          </button>
          
          {debugInfo && (
            <div style={{ 
              marginTop: "15px", 
              padding: "10px", 
              background: "#efefef", 
              maxHeight: "200px", 
              overflowY: "auto",
              fontSize: "12px",
              fontFamily: "monospace",
              whiteSpace: "pre-wrap"
            }}>
              {debugInfo}
            </div>
          )}
        </div>
      </form>
    </div>
  );
};

export default Login;
