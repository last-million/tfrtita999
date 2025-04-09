-- Migration script to add data_sync_jobs table
-- This table tracks jobs that sync call data to external services

CREATE TABLE IF NOT EXISTS data_sync_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service VARCHAR(50) NOT NULL COMMENT 'Service type: google_sheets, supabase, airtable',
    destination VARCHAR(255) NOT NULL COMMENT 'Sheet ID, table name, or table ID',
    field_mapping JSON NOT NULL COMMENT 'Mapping between call fields and destination fields',
    last_synced DATETIME COMMENT 'When the last sync occurred',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_service_dest (user_id, service, destination)
);

-- Add index for performance
-- Using a safer approach that works with MySQL 8.0+
CREATE INDEX idx_data_sync_active ON data_sync_jobs (is_active);
