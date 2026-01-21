"""
Logging Configuration

Centralized logging configuration for the secure data wiping system.
Provides comprehensive logging for debugging, audit, and compliance purposes.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class SecurityAuditFormatter(logging.Formatter):
    """
    Custom formatter for security audit logs.
    
    Ensures consistent formatting for audit trail and compliance logging.
    """
    
    def format(self, record):
        """Format log record with security audit information."""
        # Add timestamp in ISO format
        record.iso_timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        # Add security context
        record.component = getattr(record, 'component', 'UNKNOWN')
        record.operation = getattr(record, 'operation', 'GENERAL')
        record.device_id = getattr(record, 'device_id', 'N/A')
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_audit: bool = True
) -> logging.Logger:
    """
    Set up comprehensive logging for the secure data wiping system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_audit: Enable separate audit logging
        
    Returns:
        logging.Logger: Configured root logger
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler for development and debugging
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler for general application logs
    if enable_file:
        log_file = log_path / f"secure_wiping_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Audit handler for security and compliance logging
    if enable_audit:
        audit_file = log_path / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        audit_formatter = SecurityAuditFormatter(
            '%(iso_timestamp)s | %(levelname)s | %(component)s | %(operation)s | '
            '%(device_id)s | %(name)s | %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        
        # Create separate audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False  # Don't propagate to root logger
    
    # Error handler for critical errors
    error_file = log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
        'Exception: %(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Log the logging setup
    root_logger.info(f"Logging initialized - Level: {log_level}, Directory: {log_dir}")
    
    return root_logger


def get_component_logger(component_name: str) -> logging.Logger:
    """
    Get a logger for a specific component with proper naming.
    
    Args:
        component_name: Name of the component (e.g., 'wipe_engine', 'blockchain_logger')
        
    Returns:
        logging.Logger: Component-specific logger
    """
    return logging.getLogger(f"secure_wiping.{component_name}")


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    device_id: str = "N/A",
    operation_id: str = "N/A",
    level: int = logging.INFO,
    **kwargs
) -> None:
    """
    Log a security-related event with structured information.
    
    Args:
        logger: Logger instance to use
        event_type: Type of security event (WIPE_START, HASH_GENERATED, etc.)
        message: Human-readable message
        device_id: Device identifier
        operation_id: Operation identifier
        level: Logging level
        **kwargs: Additional context information
    """
    
    # Create audit logger entry
    audit_logger = logging.getLogger('audit')
    
    extra_info = {
        'component': logger.name,
        'operation': event_type,
        'device_id': device_id,
        'operation_id': operation_id,
        **kwargs
    }
    
    # Log to both main logger and audit logger
    logger.log(level, message, extra=extra_info)
    audit_logger.log(level, message, extra=extra_info)


def log_operation_start(
    logger: logging.Logger,
    operation_type: str,
    device_id: str,
    operation_id: str,
    **kwargs
) -> None:
    """Log the start of a major operation."""
    log_security_event(
        logger,
        f"{operation_type}_START",
        f"Started {operation_type.lower()} operation for device {device_id}",
        device_id=device_id,
        operation_id=operation_id,
        level=logging.INFO,
        **kwargs
    )


def log_operation_complete(
    logger: logging.Logger,
    operation_type: str,
    device_id: str,
    operation_id: str,
    success: bool = True,
    **kwargs
) -> None:
    """Log the completion of a major operation."""
    status = "SUCCESS" if success else "FAILURE"
    level = logging.INFO if success else logging.ERROR
    
    log_security_event(
        logger,
        f"{operation_type}_{status}",
        f"Completed {operation_type.lower()} operation for device {device_id} - {status}",
        device_id=device_id,
        operation_id=operation_id,
        level=level,
        success=success,
        **kwargs
    )


def log_blockchain_transaction(
    logger: logging.Logger,
    device_id: str,
    transaction_hash: str,
    block_number: int,
    operation_id: str,
    **kwargs
) -> None:
    """Log blockchain transaction details."""
    log_security_event(
        logger,
        "BLOCKCHAIN_RECORD",
        f"Recorded blockchain transaction for device {device_id}",
        device_id=device_id,
        operation_id=operation_id,
        transaction_hash=transaction_hash,
        block_number=block_number,
        level=logging.INFO,
        **kwargs
    )


def log_certificate_generated(
    logger: logging.Logger,
    device_id: str,
    certificate_path: str,
    operation_id: str,
    **kwargs
) -> None:
    """Log certificate generation."""
    log_security_event(
        logger,
        "CERTIFICATE_GENERATED",
        f"Generated certificate for device {device_id}",
        device_id=device_id,
        operation_id=operation_id,
        certificate_path=certificate_path,
        level=logging.INFO,
        **kwargs
    )


# Initialize logging when module is imported
if __name__ != "__main__":
    # Set up basic logging configuration
    setup_logging()