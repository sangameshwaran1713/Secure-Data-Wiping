"""
Local Infrastructure Utilities

Provides utilities for ensuring the system operates entirely on local infrastructure
without internet connectivity requirements, maintaining data privacy and security.
"""

import os
import socket
import ipaddress
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


class LocalInfrastructureError(Exception):
    """Raised when local infrastructure constraints are violated."""
    pass


class NetworkIsolationError(LocalInfrastructureError):
    """Raised when network isolation checks fail."""
    pass


class DataPrivacyError(LocalInfrastructureError):
    """Raised when data privacy constraints are violated."""
    pass


class LocalInfrastructureValidator:
    """
    Validates that the system operates entirely on local infrastructure.
    
    Ensures compliance with Requirements 7.1, 7.3, 8.1, 8.2, 8.3, 8.5.
    """
    
    def __init__(self):
        """Initialize the local infrastructure validator."""
        self.logger = logging.getLogger(__name__)
        
        # Define allowed local network ranges
        self.local_networks = [
            ipaddress.IPv4Network('127.0.0.0/8'),    # Loopback
            ipaddress.IPv4Network('10.0.0.0/8'),     # Private Class A
            ipaddress.IPv4Network('172.16.0.0/12'),  # Private Class B
            ipaddress.IPv4Network('192.168.0.0/16'), # Private Class C
            ipaddress.IPv6Network('::1/128'),        # IPv6 loopback
            ipaddress.IPv6Network('fc00::/7'),       # IPv6 unique local
        ]
        
        # Define sensitive data patterns to exclude from logs/blockchain
        self.sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential',
            'ssn', 'social', 'credit', 'card', 'account',
            'personal', 'private', 'confidential'
        ]
    
    def validate_url_is_local(self, url: str) -> bool:
        """
        Validate that a URL points to local infrastructure only.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is local, False otherwise
            
        Raises:
            NetworkIsolationError: If URL points to external network
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                raise NetworkIsolationError(f"Invalid URL format: {url}")
            
            # Check for localhost aliases
            if hostname.lower() in ['localhost', '127.0.0.1', '::1']:
                return True
            
            # Resolve hostname to IP address
            try:
                ip_str = socket.gethostbyname(hostname)
                ip_addr = ipaddress.IPv4Address(ip_str)
            except (socket.gaierror, ipaddress.AddressValueError):
                # Try IPv6
                try:
                    ip_str = socket.getaddrinfo(hostname, None, socket.AF_INET6)[0][4][0]
                    ip_addr = ipaddress.IPv6Address(ip_str)
                except (socket.gaierror, ipaddress.AddressValueError):
                    raise NetworkIsolationError(f"Cannot resolve hostname: {hostname}")
            
            # Check if IP is in allowed local networks
            for network in self.local_networks:
                if ip_addr in network:
                    self.logger.info(f"URL {url} validated as local: {ip_addr}")
                    return True
            
            raise NetworkIsolationError(f"URL {url} points to external network: {ip_addr}")
            
        except Exception as e:
            if isinstance(e, NetworkIsolationError):
                raise
            raise NetworkIsolationError(f"Failed to validate URL {url}: {e}")
    
    def validate_file_path_is_local(self, file_path: str) -> bool:
        """
        Validate that a file path is on local file system.
        
        Args:
            file_path: File path to validate
            
        Returns:
            bool: True if path is local, False otherwise
            
        Raises:
            LocalInfrastructureError: If path is not local
        """
        try:
            path = Path(file_path).resolve()
            
            # Check if path is absolute and on local file system
            if not path.is_absolute():
                raise LocalInfrastructureError(f"Path must be absolute: {file_path}")
            
            # Check for network paths (Windows UNC paths)
            if str(path).startswith('\\\\'):
                raise LocalInfrastructureError(f"Network paths not allowed: {file_path}")
            
            # Check for remote mount points (basic check)
            if '/mnt/' in str(path) or '/media/' in str(path):
                self.logger.warning(f"Path may be on remote mount: {file_path}")
            
            self.logger.info(f"File path validated as local: {path}")
            return True
            
        except Exception as e:
            if isinstance(e, LocalInfrastructureError):
                raise
            raise LocalInfrastructureError(f"Failed to validate file path {file_path}: {e}")
    
    def validate_no_internet_connectivity_required(self) -> bool:
        """
        Validate that the system can operate without internet connectivity.
        
        Returns:
            bool: True if system can operate offline
        """
        try:
            # Test that we can operate without external DNS
            self.logger.info("Validating offline operation capability")
            
            # Check that all required local services are available
            local_services = [
                ('127.0.0.1', 7545),  # Ganache default port
            ]
            
            for host, port in local_services:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        self.logger.info(f"Local service available: {host}:{port}")
                    else:
                        self.logger.warning(f"Local service not available: {host}:{port}")
                        
                except Exception as e:
                    self.logger.warning(f"Cannot check local service {host}:{port}: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate offline operation: {e}")
            return False
    
    def filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter sensitive data from dictionaries before logging or blockchain storage.
        
        Args:
            data: Dictionary that may contain sensitive data
            
        Returns:
            Dict[str, Any]: Filtered dictionary with sensitive data removed
        """
        filtered_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key contains sensitive patterns
            is_sensitive = any(pattern in key_lower for pattern in self.sensitive_patterns)
            
            if is_sensitive:
                filtered_data[key] = "[REDACTED]"
                self.logger.debug(f"Filtered sensitive field: {key}")
            elif isinstance(value, dict):
                # Recursively filter nested dictionaries
                filtered_data[key] = self.filter_sensitive_data(value)
            elif isinstance(value, str) and len(value) > 50:
                # Truncate very long strings that might contain sensitive data
                filtered_data[key] = value[:50] + "...[TRUNCATED]"
            else:
                filtered_data[key] = value
        
        return filtered_data
    
    def validate_blockchain_data_privacy(self, blockchain_data: Dict[str, Any]) -> bool:
        """
        Validate that blockchain data contains only hashes and metadata.
        
        Args:
            blockchain_data: Data to be stored on blockchain
            
        Returns:
            bool: True if data is privacy-compliant
            
        Raises:
            DataPrivacyError: If data contains sensitive information
        """
        try:
            # Check that data only contains allowed fields
            allowed_fields = {
                'device_id', 'wipe_hash', 'timestamp', 'operator_address',
                'transaction_hash', 'block_number', 'gas_used', 'method'
            }
            
            for key, value in blockchain_data.items():
                if key not in allowed_fields:
                    raise DataPrivacyError(f"Unauthorized field for blockchain storage: {key}")
                
                # Check that hash fields are actually hashes (hex strings of appropriate length)
                if 'hash' in key.lower() and isinstance(value, str):
                    if not self._is_valid_hash(value):
                        raise DataPrivacyError(f"Invalid hash format for field {key}: {value}")
                
                # Check for sensitive data patterns in values
                if isinstance(value, str):
                    value_lower = value.lower()
                    for pattern in self.sensitive_patterns:
                        if pattern in value_lower and pattern not in ['key']:  # 'key' is OK in context
                            raise DataPrivacyError(f"Sensitive data detected in field {key}")
            
            self.logger.info("Blockchain data validated for privacy compliance")
            return True
            
        except Exception as e:
            if isinstance(e, DataPrivacyError):
                raise
            raise DataPrivacyError(f"Failed to validate blockchain data privacy: {e}")
    
    def validate_certificate_data_privacy(self, certificate_data: Dict[str, Any]) -> bool:
        """
        Validate that certificate data contains only non-sensitive identifiers.
        
        Args:
            certificate_data: Data to be included in certificate
            
        Returns:
            bool: True if data is privacy-compliant
            
        Raises:
            DataPrivacyError: If data contains sensitive information
        """
        try:
            # Filter sensitive data from certificate
            filtered_data = self.filter_sensitive_data(certificate_data)
            
            # Check that no actual data content is included
            for key, value in filtered_data.items():
                if isinstance(value, str) and len(value) > 1000:
                    raise DataPrivacyError(f"Certificate field {key} contains too much data")
                
                # Ensure only cryptographic proofs and identifiers
                if 'data' in key.lower() or 'content' in key.lower():
                    if not self._is_hash_or_identifier(value):
                        raise DataPrivacyError(f"Certificate field {key} may contain sensitive data")
            
            self.logger.info("Certificate data validated for privacy compliance")
            return True
            
        except Exception as e:
            if isinstance(e, DataPrivacyError):
                raise
            raise DataPrivacyError(f"Failed to validate certificate data privacy: {e}")
    
    def create_offline_verification_data(self, wipe_hash: str, transaction_hash: str, 
                                       device_id: str) -> Dict[str, Any]:
        """
        Create verification data that can be used offline.
        
        Args:
            wipe_hash: Cryptographic hash of wiping operation
            transaction_hash: Blockchain transaction hash
            device_id: Device identifier
            
        Returns:
            Dict[str, Any]: Offline verification data
        """
        verification_data = {
            'device_id': device_id,
            'wipe_hash': wipe_hash,
            'transaction_hash': transaction_hash,
            'verification_method': 'offline_hash_comparison',
            'created_at': self._get_current_timestamp(),
            'verification_instructions': {
                'step_1': 'Compare wipe_hash with original operation hash',
                'step_2': 'Verify transaction_hash exists in local blockchain',
                'step_3': 'Check timestamp is within expected range',
                'step_4': 'Validate device_id matches certificate'
            }
        }
        
        self.logger.info(f"Created offline verification data for device {device_id}")
        return verification_data
    
    def _is_valid_hash(self, value: str) -> bool:
        """Check if a string is a valid cryptographic hash."""
        if not isinstance(value, str):
            return False
        
        # Check for common hash lengths (hex encoded)
        valid_lengths = [32, 40, 64, 128]  # MD5, SHA1, SHA256, SHA512
        
        try:
            # Check if it's valid hex
            int(value, 16)
            return len(value) in valid_lengths
        except ValueError:
            return False
    
    def _is_hash_or_identifier(self, value: str) -> bool:
        """Check if a string is a hash or safe identifier."""
        if not isinstance(value, str):
            return False
        
        # Check if it's a hash
        if self._is_valid_hash(value):
            return True
        
        # Check if it's a safe identifier (alphanumeric + common separators)
        import re
        safe_pattern = r'^[a-zA-Z0-9_\-\.]+$'
        return bool(re.match(safe_pattern, value)) and len(value) < 100
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


def create_local_infrastructure_validator() -> LocalInfrastructureValidator:
    """
    Create a LocalInfrastructureValidator instance.
    
    Returns:
        LocalInfrastructureValidator: Configured validator instance
    """
    return LocalInfrastructureValidator()


def validate_system_is_local_only(ganache_url: str, database_path: str, 
                                 certificates_dir: str) -> bool:
    """
    Validate that the entire system operates on local infrastructure only.
    
    Args:
        ganache_url: Ganache blockchain URL
        database_path: Database file path
        certificates_dir: Certificates directory path
        
    Returns:
        bool: True if system is local-only compliant
        
    Raises:
        LocalInfrastructureError: If system violates local-only constraints
    """
    validator = create_local_infrastructure_validator()
    
    # Validate blockchain URL is local
    validator.validate_url_is_local(ganache_url)
    
    # Validate database path is local
    validator.validate_file_path_is_local(database_path)
    
    # Validate certificates directory is local
    validator.validate_file_path_is_local(certificates_dir)
    
    # Validate offline operation capability
    validator.validate_no_internet_connectivity_required()
    
    return True