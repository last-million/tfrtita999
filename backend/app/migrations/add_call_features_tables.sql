-- Migration script to add new tables for call actions and analysis
-- Created: 2025-03-02

-- First, ensure call_sid is properly indexed in calls table
CREATE INDEX IF NOT EXISTS idx_calls_call_sid ON calls (call_sid);

-- Create call_actions table to store actions performed during calls (search, weather, calendar, email)
CREATE TABLE IF NOT EXISTS call_actions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  call_sid VARCHAR(255) NOT NULL,
  action_type VARCHAR(50) NOT NULL COMMENT 'Type of action: search, weather, calendar, email, etc.',
  action_data JSON NOT NULL COMMENT 'JSON data specific to the action type',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (call_sid) REFERENCES calls(call_sid) ON DELETE CASCADE
);

-- Create index for faster lookup by call_sid
CREATE INDEX idx_call_actions_call_sid ON call_actions (call_sid);
CREATE INDEX idx_call_actions_action_type ON call_actions (action_type);

-- Create call_analysis table to store call analysis results
CREATE TABLE IF NOT EXISTS call_analysis (
  id INT AUTO_INCREMENT PRIMARY KEY,
  call_sid VARCHAR(255) NOT NULL,
  analysis JSON NOT NULL COMMENT 'JSON object with analysis results',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (call_sid) REFERENCES calls(call_sid) ON DELETE CASCADE,
  UNIQUE KEY unique_call_analysis (call_sid)
);

-- Create call_transcriptions table to store call transcripts separately from calls table
CREATE TABLE IF NOT EXISTS call_transcriptions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  call_sid VARCHAR(255) NOT NULL,
  transcription JSON NOT NULL COMMENT 'JSON array of transcription messages',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (call_sid) REFERENCES calls(call_sid) ON DELETE CASCADE,
  UNIQUE KEY unique_call_transcription (call_sid)
);

-- Update calls table to add columns for system_prompt and other configuration
ALTER TABLE calls
ADD COLUMN IF NOT EXISTS system_prompt TEXT COMMENT 'System prompt used for the call' AFTER ultravox_cost,
ADD COLUMN IF NOT EXISTS language_hint VARCHAR(10) COMMENT 'Language hint for the call' AFTER system_prompt,
ADD COLUMN IF NOT EXISTS voice VARCHAR(50) COMMENT 'Voice used for the call' AFTER language_hint,
ADD COLUMN IF NOT EXISTS temperature DECIMAL(4,2) COMMENT 'Model temperature setting' AFTER voice,
ADD COLUMN IF NOT EXISTS model VARCHAR(100) COMMENT 'AI model used for the call' AFTER temperature,
ADD COLUMN IF NOT EXISTS knowledge_base_access BOOLEAN DEFAULT FALSE COMMENT 'Whether knowledge base was accessed' AFTER model;

-- Create knowledge_base_access_logs table to track which documents were accessed during calls
CREATE TABLE IF NOT EXISTS knowledge_base_access_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  call_sid VARCHAR(255) NOT NULL,
  document_id INT NOT NULL,
  relevance_score DECIMAL(5,4) COMMENT 'Relevance score of the document',
  accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (call_sid) REFERENCES calls(call_sid) ON DELETE CASCADE,
  FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE
);

-- Add columns to service_connections table for SERP API
ALTER TABLE service_connections
ADD COLUMN IF NOT EXISTS serp_api_key VARCHAR(255) COMMENT 'SERP API key for internet search' AFTER credentials,
ADD COLUMN IF NOT EXISTS google_search_cx VARCHAR(255) COMMENT 'Google Custom Search CX' AFTER serp_api_key;

-- Create system monitor logs table
CREATE TABLE IF NOT EXISTS system_monitor_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  cpu_usage DECIMAL(5,2) COMMENT 'CPU usage percentage',
  memory_usage DECIMAL(5,2) COMMENT 'Memory usage percentage',
  disk_usage DECIMAL(5,2) COMMENT 'Disk usage percentage', 
  network_usage DECIMAL(10,2) COMMENT 'Network usage in kbps',
  active_calls INT COMMENT 'Number of active calls',
  call_capacity INT COMMENT 'Calculated call capacity',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
