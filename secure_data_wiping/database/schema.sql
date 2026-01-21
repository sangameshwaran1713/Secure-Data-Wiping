-- Secure Data Wiping System Database Schema
-- SQLite database for local storage of operations, blockchain records, and certificates

-- Table for storing wipe operations
CREATE TABLE IF NOT EXISTS wipe_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT UNIQUE NOT NULL,
    device_id TEXT NOT NULL,
    device_type TEXT NOT NULL,
    device_manufacturer TEXT,
    device_model TEXT,
    device_serial TEXT,
    device_capacity INTEGER,
    wipe_method TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    passes_completed INTEGER DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT 0,
    error_message TEXT,
    wipe_hash TEXT,
    operator_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing blockchain transaction records
CREATE TABLE IF NOT EXISTS blockchain_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    transaction_hash TEXT UNIQUE NOT NULL,
    block_number INTEGER NOT NULL,
    gas_used INTEGER NOT NULL,
    confirmation_count INTEGER DEFAULT 0,
    contract_address TEXT NOT NULL,
    operator_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operation_id) REFERENCES wipe_operations(operation_id)
);

-- Table for storing generated certificates
CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL,
    certificate_path TEXT NOT NULL,
    certificate_hash TEXT,
    qr_code_data TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operation_id) REFERENCES wipe_operations(operation_id)
);

-- Table for storing system configuration
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_wipe_operations_device_id ON wipe_operations(device_id);
CREATE INDEX IF NOT EXISTS idx_wipe_operations_operation_id ON wipe_operations(operation_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_records_device_id ON blockchain_records(device_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_records_tx_hash ON blockchain_records(transaction_hash);
CREATE INDEX IF NOT EXISTS idx_certificates_operation_id ON certificates(operation_id);

-- Insert default system configuration
INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES
('ganache_url', 'http://127.0.0.1:7545', 'Local Ganache blockchain URL'),
('contract_address', '', 'Deployed smart contract address'),
('default_operator', 'system', 'Default operator identifier'),
('log_level', 'INFO', 'System logging level'),
('certificate_template', 'default', 'Certificate template to use'),
('max_retry_attempts', '3', 'Maximum retry attempts for blockchain operations');