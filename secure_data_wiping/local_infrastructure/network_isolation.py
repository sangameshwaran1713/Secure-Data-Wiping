"""
Network Isolation Module

Implements network isolation checks to ensure the system operates only
on local infrastructure without external network connectivity.
"""

import ipaddress
import socket
import urllib.parse
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


class NetworkIsolationError(Exception):
    """Raised when network isolation constraints are violated."""
    pass


@dataclass
class NetworkCheck:
    """Result of a network connectivity check."""
    address: str
    is_local: bool
    is_reachable: bool
    error_message: Optional[str] = None


class NetworkIsolationChecker:
    """
    Checks and enforces network isolation constraints.
    
    Ensures that all network operations are restricted to local infrastructure
    and prevents connections to external networks.
    """
    
    def __init__(self):
        """Initialize the network isolation checker."""
        self.logger = logging.getLogger(__name__)
        
        # Define local address ranges
        self.local_ranges = [
            ipaddress.IPv4Network('127.0.0.0/8'),    # Loopback
            ipaddress.IPv4Network('10.0.0.0/8'),     # Private Class A
            ipaddress.IPv4Network('172.16.0.0/12'),  # Private Class B
            ipaddress.IPv4Network('192.168.0.0/16'), # Private Class C
            ipaddress.IPv4Network('169.254.0.0/16'), # Link-local
        ]
        
        # Define allowed local hostnames
        self.local_hostnames = [
            'localhost',
            '127.0.0.1',
            '::1',
            'ganache',
            'local-ganache'
        ]
    
    def is_local_address(self, address: str) -> bool:
        """
        Check if an address is considered local.
        
        Args:
            address: IP address or hostname to check
            
        Returns:
            bool: True if address is local, False otherwise
        """
        try:
            # Check if it's a known local hostname
            if address.lower() in self.local_hostnames:
                return True
            
            # Try to parse as IP address
            try:
                ip = ipaddress.IPv4Address(address)
                
                # Check if IP is in any local range
                for local_range in self.local_ranges:
                    if ip in local_range:
                        return True
                
                return False
                
            except ipaddress.AddressValueError:
                # Not a valid IP, try to resolve hostname
                try:
                    resolved_ip = socket.gethostbyname(address)
                    return self.is_local_address(resolved_ip)
                except socket.gaierror:
                    # Cannot resolve hostname
                    return False
                    
        except Exception as e:
            self.logger.warning(f"Error checking address {address}: {e}")
            return False
    
    def validate_url(self, url: str) -> NetworkCheck:
        """
        Validate that a URL points to local infrastructure.
        
        Args:
            url: URL to validate
            
        Returns:
            NetworkCheck: Result of the validation
            
        Raises:
            NetworkIsolationError: If URL points to external network
        """
        try:
            parsed = urllib.parse.urlparse(url)
            
            if not parsed.hostname:
                raise NetworkIsolationError(f"Invalid URL: {url}")
            
            is_local = self.is_local_address(parsed.hostname)
            
            if not is_local:
                raise NetworkIsolationError(
                    f"External network access denied: {parsed.hostname} is not a local address"
                )
            
            # Test connectivity
            is_reachable = self._test_connectivity(parsed.hostname, parsed.port or 80)
            
            return NetworkCheck(
                address=parsed.hostname,
                is_local=is_local,
                is_reachable=is_reachable
            )
            
        except NetworkIsolationError:
            raise
        except Exception as e:
            error_msg = f"Error validating URL {url}: {e}"
            self.logger.error(error_msg)
            return NetworkCheck(
                address=url,
                is_local=False,
                is_reachable=False,
                error_message=error_msg
            )
    
    def validate_ganache_connection(self, ganache_url: str) -> bool:
        """
        Validate that Ganache URL is local and accessible.
        
        Args:
            ganache_url: Ganache blockchain URL
            
        Returns:
            bool: True if connection is valid and local
            
        Raises:
            NetworkIsolationError: If connection is not local
        """
        self.logger.info(f"Validating Ganache connection: {ganache_url}")
        
        check = self.validate_url(ganache_url)
        
        if not check.is_local:
            raise NetworkIsolationError(
                f"Ganache connection must be local: {ganache_url}"
            )
        
        # Additional Ganache-specific checks
        parsed = urllib.parse.urlparse(ganache_url)
        
        # Check for common Ganache ports
        ganache_ports = [7545, 8545, 9545]
        if parsed.port and parsed.port not in ganache_ports:
            self.logger.warning(
                f"Unusual port for Ganache: {parsed.port}. "
                f"Common ports are: {ganache_ports}"
            )
        
        self.logger.info(f"Ganache connection validated: {ganache_url}")
        return True
    
    def check_system_isolation(self) -> Dict[str, Any]:
        """
        Perform comprehensive system isolation check.
        
        Returns:
            Dict containing isolation status and details
        """
        results = {
            'isolated': True,
            'checks': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check for internet connectivity (should fail in isolated environment)
            internet_check = self._check_internet_connectivity()
            results['checks'].append({
                'name': 'Internet Connectivity',
                'result': 'ISOLATED' if not internet_check else 'CONNECTED',
                'isolated': not internet_check
            })
            
            if internet_check:
                results['warnings'].append(
                    "Internet connectivity detected - system may not be properly isolated"
                )
            
            # Check local network interfaces
            local_interfaces = self._get_local_interfaces()
            results['checks'].append({
                'name': 'Local Interfaces',
                'result': f"Found {len(local_interfaces)} local interfaces",
                'interfaces': local_interfaces
            })
            
            # Check for external DNS servers
            dns_check = self._check_dns_configuration()
            results['checks'].append({
                'name': 'DNS Configuration',
                'result': dns_check['status'],
                'external_dns': dns_check.get('external_servers', [])
            })
            
            if dns_check.get('external_servers'):
                results['warnings'].append(
                    f"External DNS servers configured: {dns_check['external_servers']}"
                )
            
        except Exception as e:
            error_msg = f"Error during isolation check: {e}"
            results['errors'].append(error_msg)
            results['isolated'] = False
            self.logger.error(error_msg)
        
        return results
    
    def _test_connectivity(self, hostname: str, port: int, timeout: int = 5) -> bool:
        """Test connectivity to a host and port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((hostname, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_internet_connectivity(self) -> bool:
        """Check if internet connectivity is available."""
        # Try to connect to common external services
        external_hosts = [
            ('8.8.8.8', 53),      # Google DNS
            ('1.1.1.1', 53),      # Cloudflare DNS
            ('google.com', 80),   # Google
            ('github.com', 443)   # GitHub
        ]
        
        for host, port in external_hosts:
            if self._test_connectivity(host, port, timeout=2):
                return True
        
        return False
    
    def _get_local_interfaces(self) -> List[str]:
        """Get list of local network interfaces."""
        interfaces = []
        
        try:
            # Get hostname and local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            interfaces.append(f"{hostname} ({local_ip})")
            
            # Add loopback
            interfaces.append("localhost (127.0.0.1)")
            
        except Exception as e:
            self.logger.warning(f"Error getting local interfaces: {e}")
        
        return interfaces
    
    def _check_dns_configuration(self) -> Dict[str, Any]:
        """Check DNS configuration for external servers."""
        result = {
            'status': 'LOCAL',
            'external_servers': []
        }
        
        try:
            # This is a simplified check - in a real implementation,
            # you would check system DNS configuration files
            # For now, we'll assume local DNS if we can't reach external servers
            
            external_dns_servers = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
            
            for dns_server in external_dns_servers:
                if self._test_connectivity(dns_server, 53, timeout=1):
                    result['external_servers'].append(dns_server)
            
            if result['external_servers']:
                result['status'] = 'EXTERNAL_DNS_DETECTED'
            
        except Exception as e:
            self.logger.warning(f"Error checking DNS configuration: {e}")
            result['status'] = 'ERROR'
        
        return result


def is_local_address(address: str) -> bool:
    """
    Convenience function to check if an address is local.
    
    Args:
        address: IP address or hostname to check
        
    Returns:
        bool: True if address is local, False otherwise
    """
    checker = NetworkIsolationChecker()
    return checker.is_local_address(address)


def validate_local_only_operation(url: str) -> bool:
    """
    Validate that an operation uses only local infrastructure.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if operation is local-only
        
    Raises:
        NetworkIsolationError: If operation uses external network
    """
    checker = NetworkIsolationChecker()
    check = checker.validate_url(url)
    return check.is_local and check.is_reachable