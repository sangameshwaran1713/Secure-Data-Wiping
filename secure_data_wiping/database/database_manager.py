"""
Database Manager

Handles SQLite database initialization, connections, and operations for the secure data wiping system.
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime


class DatabaseManager:
    """
    Manages SQLite database operations for the secure data wiping system.
    
    Provides methods for database initialization, connection management,
    and CRUD operations for wipe operations, blockchain records, and certificates.
    """
    
    def __init__(self, db_path: str = "secure_wiping.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Ensure the database file and schema exist."""
        try:
            # Create database directory if it doesn't exist
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize database schema
            self._initialize_schema()
            self.logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _initialize_schema(self) -> None:
        """Initialize the database schema from SQL file."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        with open(schema_path, 'r') as schema_file:
            schema_sql = schema_file.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection with automatic cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_wipe_operation(self, operation_data: Dict[str, Any]) -> str:
        """
        Insert a new wipe operation record.
        
        Args:
            operation_data: Dictionary containing operation details
            
        Returns:
            str: The operation ID of the inserted record
        """
        required_fields = ['operation_id', 'device_id', 'device_type', 'wipe_method', 'start_time']
        
        # Validate required fields
        for field in required_fields:
            if field not in operation_data:
                raise ValueError(f"Missing required field: {field}")
        
        sql = """
        INSERT INTO wipe_operations (
            operation_id, device_id, device_type, device_manufacturer, device_model,
            device_serial, device_capacity, wipe_method, start_time, end_time,
            passes_completed, success, error_message, wipe_hash, operator_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            operation_data['operation_id'],
            operation_data['device_id'],
            operation_data['device_type'],
            operation_data.get('device_manufacturer'),
            operation_data.get('device_model'),
            operation_data.get('device_serial'),
            operation_data.get('device_capacity'),
            operation_data['wipe_method'],
            operation_data['start_time'],
            operation_data.get('end_time'),
            operation_data.get('passes_completed', 0),
            operation_data.get('success', False),
            operation_data.get('error_message'),
            operation_data.get('wipe_hash'),
            operation_data.get('operator_id', 'system')
        )
        
        with self.get_connection() as conn:
            conn.execute(sql, values)
            conn.commit()
            self.logger.info(f"Inserted wipe operation: {operation_data['operation_id']}")
        
        return operation_data['operation_id']
    
    def update_wipe_operation(self, operation_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing wipe operation record.
        
        Args:
            operation_id: The operation ID to update
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update was successful
        """
        if not update_data:
            return False
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        
        for key, value in update_data.items():
            if key != 'operation_id':  # Don't allow updating the primary identifier
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(operation_id)
        
        sql = f"UPDATE wipe_operations SET {', '.join(set_clauses)} WHERE operation_id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.info(f"Updated wipe operation: {operation_id}")
                return True
            else:
                self.logger.warning(f"No wipe operation found with ID: {operation_id}")
                return False
    
    def get_wipe_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a wipe operation by ID.
        
        Args:
            operation_id: The operation ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Operation data or None if not found
        """
        sql = "SELECT * FROM wipe_operations WHERE operation_id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, (operation_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def insert_blockchain_record(self, record_data: Dict[str, Any]) -> int:
        """
        Insert a blockchain transaction record.
        
        Args:
            record_data: Dictionary containing blockchain record details
            
        Returns:
            int: The record ID of the inserted record
        """
        required_fields = ['operation_id', 'device_id', 'transaction_hash', 'block_number', 'contract_address']
        
        for field in required_fields:
            if field not in record_data:
                raise ValueError(f"Missing required field: {field}")
        
        sql = """
        INSERT INTO blockchain_records (
            operation_id, device_id, transaction_hash, block_number, gas_used,
            confirmation_count, contract_address, operator_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            record_data['operation_id'],
            record_data['device_id'],
            record_data['transaction_hash'],
            record_data['block_number'],
            record_data.get('gas_used', 0),
            record_data.get('confirmation_count', 0),
            record_data['contract_address'],
            record_data.get('operator_address', '')
        )
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            record_id = cursor.lastrowid
            self.logger.info(f"Inserted blockchain record: {record_data['transaction_hash']}")
        
        return record_id
    
    def insert_certificate_record(self, cert_data: Dict[str, Any]) -> int:
        """
        Insert a certificate generation record.
        
        Args:
            cert_data: Dictionary containing certificate details
            
        Returns:
            int: The record ID of the inserted record
        """
        required_fields = ['operation_id', 'certificate_path']
        
        for field in required_fields:
            if field not in cert_data:
                raise ValueError(f"Missing required field: {field}")
        
        sql = """
        INSERT INTO certificates (
            operation_id, certificate_path, certificate_hash, qr_code_data
        ) VALUES (?, ?, ?, ?)
        """
        
        values = (
            cert_data['operation_id'],
            cert_data['certificate_path'],
            cert_data.get('certificate_hash'),
            cert_data.get('qr_code_data')
        )
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            record_id = cursor.lastrowid
            self.logger.info(f"Inserted certificate record for operation: {cert_data['operation_id']}")
        
        return record_id
    
    def get_operations_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all wipe operations.
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        sql = """
        SELECT 
            COUNT(*) as total_operations,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_operations,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_operations,
            COUNT(DISTINCT device_type) as device_types_processed,
            MIN(start_time) as first_operation,
            MAX(start_time) as last_operation
        FROM wipe_operations
        """
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return {}
    
    def get_config_value(self, key: str) -> Optional[str]:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            
        Returns:
            Optional[str]: Configuration value or None if not found
        """
        sql = "SELECT config_value FROM system_config WHERE config_key = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, (key,))
            row = cursor.fetchone()
            
            if row:
                return row['config_value']
            return None
    
    def set_config_value(self, key: str, value: str, description: str = None) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            description: Optional description
            
        Returns:
            bool: True if successful
        """
        sql = """
        INSERT OR REPLACE INTO system_config (config_key, config_value, description, updated_at)
        VALUES (?, ?, ?, ?)
        """
        
        with self.get_connection() as conn:
            conn.execute(sql, (key, value, description, datetime.now().isoformat()))
            conn.commit()
            self.logger.info(f"Set config: {key} = {value}")
        
        return True
    
    def store_wipe_operation(self, operation) -> str:
        """
        Store a complete WipeOperation object.
        
        Args:
            operation: WipeOperation object to store
            
        Returns:
            str: The operation ID of the stored record
        """
        from ..utils.data_models import WipeOperation
        
        # Prepare operation data
        operation_data = {
            'operation_id': operation.operation_id,
            'device_id': operation.device_info.device_id if operation.device_info else 'unknown',
            'device_type': operation.device_info.device_type.value if operation.device_info else 'unknown',
            'device_manufacturer': operation.device_info.manufacturer if operation.device_info else None,
            'device_model': operation.device_info.model if operation.device_info else None,
            'device_serial': operation.device_info.serial_number if operation.device_info else None,
            'device_capacity': operation.device_info.capacity if operation.device_info else None,
            'wipe_method': operation.wipe_config.method.value if operation.wipe_config else 'unknown',
            'start_time': operation.wipe_result.start_time.isoformat() if operation.wipe_result and operation.wipe_result.start_time else datetime.now().isoformat(),
            'end_time': operation.wipe_result.end_time.isoformat() if operation.wipe_result and operation.wipe_result.end_time else None,
            'passes_completed': operation.wipe_result.passes_completed if operation.wipe_result else 0,
            'success': operation.wipe_result.success if operation.wipe_result else False,
            'error_message': operation.wipe_result.error_message if operation.wipe_result else None,
            'wipe_hash': operation.wipe_result.verification_hash if operation.wipe_result else None,
            'operator_id': operation.wipe_result.operator_id if operation.wipe_result else 'system'
        }
        
        # Insert the operation
        operation_id = self.insert_wipe_operation(operation_data)
        
        # Store blockchain record if available
        if operation.wipe_record:
            blockchain_data = {
                'operation_id': operation.operation_id,
                'device_id': operation.device_info.device_id if operation.device_info else 'unknown',
                'transaction_hash': operation.wipe_record.transaction_hash,
                'block_number': operation.wipe_record.block_number,
                'gas_used': operation.wipe_record.gas_used,
                'confirmation_count': operation.wipe_record.confirmation_count,
                'contract_address': 'unknown',  # Will be filled by blockchain logger
                'operator_address': operation.wipe_record.operator_address
            }
            self.insert_blockchain_record(blockchain_data)
        
        # Store certificate record if available
        if operation.certificate_path:
            cert_data = {
                'operation_id': operation.operation_id,
                'certificate_path': operation.certificate_path
            }
            self.insert_certificate_record(cert_data)
        
        return operation_id
    
    def initialize_database(self):
        """Initialize the database (alias for backward compatibility)."""
        self._ensure_database_exists()
    
    def close(self):
        """Close database connections (placeholder for cleanup)."""
        # SQLite connections are closed automatically in context managers
        # This method is provided for interface compatibility
        self.logger.info("Database manager closed")