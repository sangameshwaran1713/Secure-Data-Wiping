"""
Data Models

Core data structures and models used throughout the secure data wiping system.
Defines dataclasses for device information, wipe operations, blockchain records, and certificates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid


class WipeMethod(Enum):
    """NIST 800-88 compliant wiping methods."""
    NIST_CLEAR = "clear"
    NIST_PURGE = "purge"
    NIST_DESTROY = "destroy"


class DeviceType(Enum):
    """Supported device types for secure wiping."""
    HDD = "hdd"
    SSD = "ssd"
    USB = "usb"
    NVME = "nvme"
    SD_CARD = "sd_card"
    OTHER = "other"


class OperationStatus(Enum):
    """Status of wiping operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DeviceInfo:
    """
    Information about a device to be wiped.
    
    Contains all relevant device metadata for identification and wiping procedures.
    """
    device_id: str
    device_type: DeviceType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    capacity: Optional[int] = None  # Capacity in bytes
    connection_type: Optional[str] = None  # SATA, USB, NVMe, etc.
    file_system: Optional[str] = None
    mount_point: Optional[str] = None
    
    def __post_init__(self):
        """Validate device information after initialization."""
        if not self.device_id:
            raise ValueError("Device ID cannot be empty")
        
        if isinstance(self.device_type, str):
            self.device_type = DeviceType(self.device_type.lower())


@dataclass
class WipeConfig:
    """
    Configuration for wiping operations.
    
    Defines parameters for NIST-compliant wiping procedures.
    """
    method: WipeMethod
    passes: int = 1
    verify_wipe: bool = True
    pattern: Optional[bytes] = None
    block_size: int = 4096  # Block size in bytes
    timeout: int = 3600  # Timeout in seconds
    
    def __post_init__(self):
        """Validate wiping configuration."""
        if isinstance(self.method, str):
            self.method = WipeMethod(self.method.lower())
        
        if self.passes < 1:
            raise ValueError("Number of passes must be at least 1")
        
        if self.block_size < 512:
            raise ValueError("Block size must be at least 512 bytes")


@dataclass
class WipeResult:
    """
    Result of a wiping operation.
    
    Contains all information about the completed (or failed) wiping process.
    """
    operation_id: str
    device_id: str
    method: WipeMethod
    passes_completed: int
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    verification_hash: Optional[str] = None
    bytes_wiped: Optional[int] = None
    operator_id: str = "system"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate operation duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def status(self) -> OperationStatus:
        """Get the current operation status."""
        if self.end_time is None:
            return OperationStatus.IN_PROGRESS
        elif self.success:
            return OperationStatus.COMPLETED
        else:
            return OperationStatus.FAILED


@dataclass
class HashData:
    """
    Data structure for hash generation.
    
    Contains all metadata used in cryptographic hash generation.
    """
    device_id: str
    timestamp: str
    method: str
    passes: int
    operator: str
    verification_data: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'device_id': self.device_id,
            'timestamp': self.timestamp,
            'method': self.method,
            'passes': self.passes,
            'operator': self.operator,
            'verification_data': self.verification_data,
            'device_info': self.device_info or {}
        }


@dataclass
class WipeRecord:
    """
    Blockchain record of a wiping operation.
    
    Represents the immutable audit record stored on the blockchain.
    """
    device_id: str
    wipe_hash: str
    timestamp: int
    operator_address: str
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    confirmation_count: int = 0
    
    @property
    def is_confirmed(self) -> bool:
        """Check if the transaction is confirmed on the blockchain."""
        return self.confirmation_count > 0 and self.block_number is not None


@dataclass
class WipeData:
    """
    Data for certificate generation.
    
    Contains wiping operation information for certificate creation.
    """
    device_id: str
    wipe_hash: str
    timestamp: datetime
    method: str
    operator: str
    passes: int
    device_info: Optional[DeviceInfo] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for certificate generation."""
        return {
            'device_id': self.device_id,
            'wipe_hash': self.wipe_hash,
            'timestamp': self.timestamp.isoformat(),
            'method': self.method,
            'operator': self.operator,
            'passes': self.passes,
            'device_info': self.device_info.__dict__ if self.device_info else {}
        }


@dataclass
class BlockchainData:
    """
    Blockchain transaction data for certificates.
    
    Contains blockchain-specific information for certificate verification.
    """
    transaction_hash: str
    block_number: int
    contract_address: str
    gas_used: int
    confirmation_count: int = 0
    network_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for certificate generation."""
        return {
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'contract_address': self.contract_address,
            'gas_used': self.gas_used,
            'confirmation_count': self.confirmation_count,
            'network_id': self.network_id
        }


@dataclass
class WipeOperation:
    """
    Complete wiping operation with all associated data.
    
    Combines device info, wipe config, results, and blockchain data.
    """
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_info: Optional[DeviceInfo] = None
    wipe_config: Optional[WipeConfig] = None
    wipe_result: Optional[WipeResult] = None
    wipe_record: Optional[WipeRecord] = None
    certificate_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def status(self) -> OperationStatus:
        """Get the current operation status."""
        if self.wipe_result:
            return self.wipe_result.status
        return OperationStatus.PENDING
    
    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()


@dataclass
class SystemConfig:
    """
    System configuration settings.
    
    Contains configuration parameters for the entire system.
    """
    ganache_url: str = "http://127.0.0.1:7545"
    contract_address: Optional[str] = None
    default_operator: str = "system"
    log_level: str = "INFO"
    certificate_template: str = "default"
    max_retry_attempts: int = 3
    database_path: str = "secure_wiping.db"
    certificates_dir: str = "certificates"
    logs_dir: str = "logs"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ganache_url': self.ganache_url,
            'contract_address': self.contract_address,
            'default_operator': self.default_operator,
            'log_level': self.log_level,
            'certificate_template': self.certificate_template,
            'max_retry_attempts': self.max_retry_attempts,
            'database_path': self.database_path,
            'certificates_dir': self.certificates_dir,
            'logs_dir': self.logs_dir
        }


# Utility functions for data model operations

def create_device_info_from_dict(data: Dict[str, Any]) -> DeviceInfo:
    """
    Create DeviceInfo from dictionary data.
    
    Args:
        data: Dictionary containing device information
        
    Returns:
        DeviceInfo: Created device info object
    """
    return DeviceInfo(
        device_id=data['device_id'],
        device_type=DeviceType(data.get('device_type', 'other').lower()),
        manufacturer=data.get('manufacturer'),
        model=data.get('model'),
        serial_number=data.get('serial_number'),
        capacity=data.get('capacity'),
        connection_type=data.get('connection_type'),
        file_system=data.get('file_system'),
        mount_point=data.get('mount_point')
    )


def create_wipe_config_from_dict(data: Dict[str, Any]) -> WipeConfig:
    """
    Create WipeConfig from dictionary data.
    
    Args:
        data: Dictionary containing wipe configuration
        
    Returns:
        WipeConfig: Created wipe configuration object
    """
    return WipeConfig(
        method=WipeMethod(data.get('method', 'clear').lower()),
        passes=data.get('passes', 1),
        verify_wipe=data.get('verify_wipe', True),
        pattern=data.get('pattern'),
        block_size=data.get('block_size', 4096),
        timeout=data.get('timeout', 3600)
    )


def validate_operation_data(operation: WipeOperation) -> List[str]:
    """
    Validate a complete wipe operation for consistency.
    
    Args:
        operation: Wipe operation to validate
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    
    if not operation.operation_id:
        errors.append("Operation ID is required")
    
    if not operation.device_info:
        errors.append("Device information is required")
    elif not operation.device_info.device_id:
        errors.append("Device ID is required")
    
    if not operation.wipe_config:
        errors.append("Wipe configuration is required")
    elif operation.wipe_config.passes < 1:
        errors.append("Number of passes must be at least 1")
    
    if operation.wipe_result:
        if operation.wipe_result.operation_id != operation.operation_id:
            errors.append("Operation ID mismatch between operation and result")
        
        if operation.device_info and operation.wipe_result.device_id != operation.device_info.device_id:
            errors.append("Device ID mismatch between device info and result")
    
    return errors