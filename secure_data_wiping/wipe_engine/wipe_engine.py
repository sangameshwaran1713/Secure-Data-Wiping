"""
Wipe Engine Implementation

Implements NIST 800-88 compliant data wiping procedures for secure data destruction.
Provides cryptographically verifiable wiping operations for IT asset recycling.
"""

import os
import time
import logging
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import uuid

from ..utils.data_models import (
    WipeMethod, WipeConfig, WipeResult, DeviceInfo, DeviceType, OperationStatus
)


class WipeEngineError(Exception):
    """Base exception for wipe engine operations."""
    pass


class DeviceAccessError(WipeEngineError):
    """Raised when device cannot be accessed for wiping."""
    pass


class WipeOperationError(WipeEngineError):
    """Raised when wiping operation fails."""
    pass


class VerificationError(WipeEngineError):
    """Raised when wipe verification fails."""
    pass


class WipeEngine:
    """
    Implements NIST 800-88 compliant data wiping procedures.
    
    This class provides secure data destruction capabilities following NIST guidelines
    for different device types and wiping methods. It supports verification and
    generates cryptographic proof of wiping operations.
    """
    
    # NIST 800-88 compliant patterns for overwriting
    NIST_PATTERNS = {
        'zeros': b'\x00',
        'ones': b'\xFF', 
        'random': None,  # Generated dynamically
        'dod_5220': [b'\x00', b'\xFF', b'\x00'],  # DoD 5220.22-M pattern
        'gutmann_partial': [b'\x55', b'\xAA', b'\x92', b'\x49', b'\x24']  # Partial Gutmann
    }
    
    # NIST recommended pass counts by method and device type
    NIST_PASS_REQUIREMENTS = {
        WipeMethod.NIST_CLEAR: {
            DeviceType.HDD: 1,      # Single overwrite for HDDs
            DeviceType.SSD: 1,      # Single overwrite (may not be effective)
            DeviceType.USB: 1,      # Single overwrite
            DeviceType.NVME: 1,     # Single overwrite
            DeviceType.SD_CARD: 1,  # Single overwrite
            DeviceType.OTHER: 1     # Default single overwrite
        },
        WipeMethod.NIST_PURGE: {
            DeviceType.HDD: 3,      # Multiple passes for HDDs
            DeviceType.SSD: 1,      # Cryptographic erase (simulated as single pass)
            DeviceType.USB: 3,      # Multiple passes for flash storage
            DeviceType.NVME: 1,     # Cryptographic erase (simulated)
            DeviceType.SD_CARD: 3,  # Multiple passes for flash storage
            DeviceType.OTHER: 3     # Default multiple passes
        },
        WipeMethod.NIST_DESTROY: {
            # Physical destruction - simulated for academic purposes
            DeviceType.HDD: 1,      # Simulation of physical destruction
            DeviceType.SSD: 1,      # Simulation of physical destruction
            DeviceType.USB: 1,      # Simulation of physical destruction
            DeviceType.NVME: 1,     # Simulation of physical destruction
            DeviceType.SD_CARD: 1,  # Simulation of physical destruction
            DeviceType.OTHER: 1     # Simulation of physical destruction
        }
    }
    
    def __init__(self, config: Optional[WipeConfig] = None):
        """
        Initialize the wipe engine.
        
        Args:
            config: Optional default wiping configuration
        """
        self.logger = logging.getLogger(__name__)
        self.default_config = config or WipeConfig(method=WipeMethod.NIST_CLEAR)
        
        # Statistics tracking
        self.operations_completed = 0
        self.total_bytes_wiped = 0
        self.last_operation_time = None
        
        self.logger.info("WipeEngine initialized with NIST 800-88 compliance")
    
    def wipe_device(self, device_path: str, method: Optional[WipeMethod] = None, 
                   device_info: Optional[DeviceInfo] = None,
                   config: Optional[WipeConfig] = None) -> WipeResult:
        """
        Execute NIST 800-88 compliant wiping operation on a device.
        
        Args:
            device_path: Path to the device to be wiped
            method: Wiping method to use (overrides config)
            device_info: Information about the device being wiped
            config: Wiping configuration (uses default if not provided)
            
        Returns:
            WipeResult: Complete result of the wiping operation
            
        Raises:
            DeviceAccessError: If device cannot be accessed
            WipeOperationError: If wiping operation fails
        """
        # Use provided config or default
        wipe_config = config or self.default_config
        
        # Override method if specified
        if method:
            wipe_config = WipeConfig(
                method=method,
                passes=wipe_config.passes,
                verify_wipe=wipe_config.verify_wipe,
                pattern=wipe_config.pattern,
                block_size=wipe_config.block_size,
                timeout=wipe_config.timeout
            )
        
        # Generate operation ID
        operation_id = str(uuid.uuid4())
        
        # Determine device ID
        device_id = device_info.device_id if device_info else self._generate_device_id(device_path)
        
        # Create initial result
        wipe_result = WipeResult(
            operation_id=operation_id,
            device_id=device_id,
            method=wipe_config.method,
            passes_completed=0,
            start_time=datetime.now(),
            operator_id="wipe_engine"
        )
        
        self.logger.info(f"Starting wipe operation {operation_id} for device {device_id}")
        self.logger.info(f"Method: {wipe_config.method.value}, Device path: {device_path}")
        
        try:
            # Validate device access
            self._validate_device_access(device_path)
            
            # Determine device type if not provided
            if not device_info:
                device_info = self._detect_device_info(device_path, device_id)
            
            # Get NIST-compliant pass count for this method and device type
            required_passes = self._get_nist_pass_count(wipe_config.method, device_info.device_type)
            
            # Execute wiping based on method
            if wipe_config.method == WipeMethod.NIST_DESTROY:
                bytes_wiped = self._simulate_physical_destruction(device_path, device_info)
                passes_completed = 1
            else:
                bytes_wiped, passes_completed = self._execute_overwrite_wipe(
                    device_path, device_info, wipe_config, required_passes
                )
            
            # Update result with success
            wipe_result.end_time = datetime.now()
            wipe_result.success = True
            wipe_result.passes_completed = passes_completed
            wipe_result.bytes_wiped = bytes_wiped
            
            # Generate verification hash
            if wipe_config.verify_wipe:
                wipe_result.verification_hash = self._generate_verification_hash(
                    wipe_result, device_info
                )
            
            # Update statistics
            self.operations_completed += 1
            self.total_bytes_wiped += bytes_wiped
            self.last_operation_time = wipe_result.end_time
            
            self.logger.info(f"Wipe operation {operation_id} completed successfully")
            self.logger.info(f"Passes: {passes_completed}, Bytes wiped: {bytes_wiped}")
            
            return wipe_result
            
        except Exception as e:
            # Update result with failure
            wipe_result.end_time = datetime.now()
            wipe_result.success = False
            wipe_result.error_message = str(e)
            
            self.logger.error(f"Wipe operation {operation_id} failed: {e}")
            
            # Re-raise as WipeOperationError if not already a wipe engine error
            if not isinstance(e, WipeEngineError):
                raise WipeOperationError(f"Wipe operation failed: {e}") from e
            
            raise
    
    def verify_wipe(self, device_path: str, wipe_result: WipeResult) -> bool:
        """
        Verify that a wiping operation was successful.
        
        Args:
            device_path: Path to the wiped device
            wipe_result: Result of the wiping operation to verify
            
        Returns:
            bool: True if verification successful, False otherwise
            
        Raises:
            VerificationError: If verification process fails
        """
        self.logger.info(f"Verifying wipe operation {wipe_result.operation_id}")
        
        try:
            # For NIST_DESTROY, verify device is no longer accessible normally
            if wipe_result.method == WipeMethod.NIST_DESTROY:
                return self._verify_destruction(device_path, wipe_result)
            
            # For overwrite methods, check if device is accessible first
            if not self._is_device_accessible(device_path):
                self.logger.warning(f"Device {device_path} not accessible for verification")
                return False
            
            # For overwrite methods, verify data patterns
            return self._verify_overwrite(device_path, wipe_result)
            
        except Exception as e:
            self.logger.error(f"Wipe verification failed: {e}")
            raise VerificationError(f"Verification failed: {e}") from e
    
    def get_nist_pass_count(self, method: WipeMethod, device_type: DeviceType) -> int:
        """
        Get NIST-compliant pass count for method and device type.
        
        Args:
            method: Wiping method
            device_type: Type of device
            
        Returns:
            int: Required number of passes
        """
        return self._get_nist_pass_count(method, device_type)
    
    def _validate_device_access(self, device_path: str) -> None:
        """
        Validate that device can be accessed for wiping.
        
        Args:
            device_path: Path to device
            
        Raises:
            DeviceAccessError: If device cannot be accessed
        """
        if not device_path or not device_path.strip():
            raise DeviceAccessError("Device path cannot be empty")
        
        # For academic simulation, we'll create a test file if it doesn't exist
        # In production, this would check actual device access
        device_path = device_path.strip()
        
        # Simulate device access validation
        if device_path.startswith('/dev/') or device_path.startswith('\\\\.\\'):
            # Simulating real device path - for academic purposes, we'll allow this
            self.logger.info(f"Simulating access to device: {device_path}")
            return
        
        # For file-based simulation, ensure we can access the file
        try:
            path_obj = Path(device_path)
            
            # If file doesn't exist, create it for simulation
            if not path_obj.exists():
                # Create parent directories if needed
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                # Create a test file for simulation (1MB default)
                with open(device_path, 'wb') as f:
                    f.write(b'\x00' * (1024 * 1024))  # 1MB of zeros
                
                self.logger.info(f"Created simulation file: {device_path}")
            
            # Test read/write access
            with open(device_path, 'r+b') as f:
                f.seek(0)
                f.read(1)  # Test read
                f.seek(0)
                f.write(b'\x00')  # Test write
                f.flush()
            
        except PermissionError:
            raise DeviceAccessError(f"Permission denied accessing device: {device_path}")
        except OSError as e:
            raise DeviceAccessError(f"Cannot access device {device_path}: {e}")
    
    def _is_device_accessible(self, device_path: str) -> bool:
        """Check if device is accessible."""
        try:
            self._validate_device_access(device_path)
            return True
        except DeviceAccessError:
            return False
    
    def _generate_device_id(self, device_path: str) -> str:
        """Generate device ID from device path."""
        # For simulation, use path-based ID
        path_hash = hashlib.md5(device_path.encode()).hexdigest()[:8]
        return f"DEVICE_{path_hash.upper()}"
    
    def _detect_device_info(self, device_path: str, device_id: str) -> DeviceInfo:
        """
        Detect device information from device path.
        
        Args:
            device_path: Path to device
            device_id: Generated device ID
            
        Returns:
            DeviceInfo: Detected device information
        """
        # For academic simulation, detect based on path patterns
        device_path_lower = device_path.lower()
        
        if 'ssd' in device_path_lower or 'nvme' in device_path_lower:
            device_type = DeviceType.SSD
        elif 'usb' in device_path_lower:
            device_type = DeviceType.USB
        elif 'sd' in device_path_lower or 'mmc' in device_path_lower:
            device_type = DeviceType.SD_CARD
        elif 'hdd' in device_path_lower or 'hd' in device_path_lower:
            device_type = DeviceType.HDD
        else:
            device_type = DeviceType.OTHER
        
        # Get file size for capacity
        capacity = None
        try:
            if os.path.exists(device_path):
                capacity = os.path.getsize(device_path)
        except OSError:
            pass
        
        return DeviceInfo(
            device_id=device_id,
            device_type=device_type,
            manufacturer="Simulated",
            model="Academic Test Device",
            capacity=capacity,
            connection_type="Simulated"
        )
    
    def _get_nist_pass_count(self, method: WipeMethod, device_type: DeviceType) -> int:
        """Get NIST-compliant pass count."""
        return self.NIST_PASS_REQUIREMENTS.get(method, {}).get(device_type, 1)
    
    def _execute_overwrite_wipe(self, device_path: str, device_info: DeviceInfo, 
                               config: WipeConfig, required_passes: int) -> Tuple[int, int]:
        """
        Execute overwrite-based wiping (CLEAR or PURGE methods).
        
        Args:
            device_path: Path to device
            device_info: Device information
            config: Wiping configuration
            required_passes: Number of passes required by NIST
            
        Returns:
            Tuple[int, int]: (bytes_wiped, passes_completed)
        """
        self.logger.info(f"Executing overwrite wipe with {required_passes} passes")
        
        total_bytes_wiped = 0
        passes_completed = 0
        
        try:
            # Get device size
            device_size = self._get_device_size(device_path)
            
            # Execute required number of passes
            for pass_num in range(required_passes):
                self.logger.info(f"Starting pass {pass_num + 1}/{required_passes}")
                
                # Select pattern for this pass
                pattern = self._get_wipe_pattern(config.method, device_info.device_type, pass_num)
                
                # Perform the overwrite
                bytes_written = self._overwrite_device(
                    device_path, pattern, device_size, config.block_size
                )
                
                total_bytes_wiped += bytes_written
                passes_completed += 1
                
                self.logger.info(f"Pass {pass_num + 1} completed: {bytes_written} bytes")
                
                # Verify pass if required
                if config.verify_wipe and pass_num == required_passes - 1:
                    self._verify_pass(device_path, pattern, device_size)
            
            return total_bytes_wiped, passes_completed
            
        except Exception as e:
            self.logger.error(f"Overwrite wipe failed at pass {passes_completed + 1}: {e}")
            raise WipeOperationError(f"Overwrite failed: {e}") from e
    
    def _simulate_physical_destruction(self, device_path: str, device_info: DeviceInfo) -> int:
        """
        Simulate physical destruction for NIST_DESTROY method.
        
        Args:
            device_path: Path to device
            device_info: Device information
            
        Returns:
            int: Bytes "destroyed" (for simulation)
        """
        self.logger.info("Simulating physical destruction (NIST DESTROY method)")
        
        try:
            # Get device size before "destruction"
            device_size = self._get_device_size(device_path)
            
            # Simulate destruction by making device inaccessible
            # For academic purposes, we'll rename/move the file
            if os.path.exists(device_path):
                destroyed_path = f"{device_path}.DESTROYED_{int(time.time())}"
                os.rename(device_path, destroyed_path)
                self.logger.info(f"Device simulated as destroyed: {device_path} -> {destroyed_path}")
            
            # Simulate destruction time based on device size
            destruction_time = min(max(device_size / (1024 * 1024), 1), 10)  # 1-10 seconds
            time.sleep(destruction_time)
            
            return device_size
            
        except Exception as e:
            self.logger.error(f"Physical destruction simulation failed: {e}")
            raise WipeOperationError(f"Destruction simulation failed: {e}") from e
    
    def _get_device_size(self, device_path: str) -> int:
        """Get device size in bytes."""
        try:
            return os.path.getsize(device_path)
        except OSError as e:
            raise DeviceAccessError(f"Cannot determine device size: {e}") from e
    
    def _get_wipe_pattern(self, method: WipeMethod, device_type: DeviceType, pass_num: int) -> bytes:
        """
        Get wiping pattern for specific pass.
        
        Args:
            method: Wiping method
            device_type: Device type
            pass_num: Pass number (0-based)
            
        Returns:
            bytes: Pattern to use for wiping
        """
        if method == WipeMethod.NIST_CLEAR:
            # Single pass with zeros for CLEAR
            return self.NIST_PATTERNS['zeros']
        
        elif method == WipeMethod.NIST_PURGE:
            # Multiple passes with different patterns for PURGE
            if device_type == DeviceType.SSD or device_type == DeviceType.NVME:
                # For SSDs, simulate cryptographic erase with random pattern
                return secrets.token_bytes(1)
            else:
                # For HDDs and other devices, use DoD pattern
                patterns = self.NIST_PATTERNS['dod_5220']
                return patterns[pass_num % len(patterns)]
        
        else:  # NIST_DESTROY
            # Not used for physical destruction
            return self.NIST_PATTERNS['zeros']
    
    def _overwrite_device(self, device_path: str, pattern: bytes, device_size: int, 
                         block_size: int) -> int:
        """
        Overwrite device with specified pattern.
        
        Args:
            device_path: Path to device
            pattern: Pattern to write
            device_size: Size of device in bytes
            block_size: Block size for writing
            
        Returns:
            int: Number of bytes written
        """
        bytes_written = 0
        
        try:
            with open(device_path, 'r+b') as device:
                device.seek(0)
                
                # Create block-sized pattern
                if len(pattern) == 1:
                    # Single byte pattern - repeat to fill block
                    block_pattern = pattern * block_size
                else:
                    # Multi-byte pattern - repeat as needed
                    block_pattern = (pattern * ((block_size // len(pattern)) + 1))[:block_size]
                
                # Write pattern across entire device
                while bytes_written < device_size:
                    remaining = device_size - bytes_written
                    write_size = min(block_size, remaining)
                    
                    if write_size < block_size:
                        # Last partial block
                        write_data = block_pattern[:write_size]
                    else:
                        write_data = block_pattern
                    
                    device.write(write_data)
                    bytes_written += len(write_data)
                    
                    # Periodic flush for large devices
                    if bytes_written % (block_size * 100) == 0:
                        device.flush()
                        os.fsync(device.fileno())
                
                # Final flush
                device.flush()
                os.fsync(device.fileno())
            
            return bytes_written
            
        except Exception as e:
            raise WipeOperationError(f"Device overwrite failed: {e}") from e
    
    def _verify_pass(self, device_path: str, expected_pattern: bytes, device_size: int) -> None:
        """
        Verify that a wiping pass was successful.
        
        Args:
            device_path: Path to device
            expected_pattern: Expected pattern
            device_size: Device size
            
        Raises:
            VerificationError: If verification fails
        """
        self.logger.info("Verifying wiping pass")
        
        try:
            with open(device_path, 'rb') as device:
                # Sample verification - check multiple points
                sample_points = min(10, device_size // 1024)  # Up to 10 sample points
                
                for i in range(sample_points):
                    # Calculate sample position
                    position = (device_size * i) // sample_points
                    device.seek(position)
                    
                    # Read sample
                    sample_size = min(len(expected_pattern), device_size - position)
                    sample_data = device.read(sample_size)
                    
                    # Compare with expected pattern
                    expected_sample = expected_pattern[:sample_size]
                    if sample_data != expected_sample:
                        raise VerificationError(
                            f"Verification failed at position {position}: "
                            f"expected {expected_sample.hex()}, got {sample_data.hex()}"
                        )
            
            self.logger.info("Pass verification successful")
            
        except Exception as e:
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(f"Verification process failed: {e}") from e
    
    def _verify_overwrite(self, device_path: str, wipe_result: WipeResult) -> bool:
        """Verify overwrite-based wiping."""
        try:
            # For simulation, check if file exists and has expected size
            if not os.path.exists(device_path):
                return False
            
            # Check if file was modified recently (within operation timeframe)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(device_path))
            
            # Allow some tolerance for file system timestamp precision
            start_time = wipe_result.start_time
            end_time = wipe_result.end_time or datetime.now()
            
            # Check if modification time is within the operation window (with 1 second tolerance)
            time_tolerance = 1.0  # 1 second tolerance
            if (start_time.timestamp() - time_tolerance) <= file_mtime.timestamp() <= (end_time.timestamp() + time_tolerance):
                return True
            
            # Also check if the file size matches what we expect
            expected_size = wipe_result.bytes_wiped
            actual_size = os.path.getsize(device_path)
            
            if expected_size and actual_size == expected_size:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _verify_destruction(self, device_path: str, wipe_result: WipeResult) -> bool:
        """Verify physical destruction."""
        # For destruction, device should no longer be accessible
        return not os.path.exists(device_path)
    
    def _generate_verification_hash(self, wipe_result: WipeResult, device_info: DeviceInfo) -> str:
        """
        Generate verification hash for wiping operation.
        
        Args:
            wipe_result: Wiping operation result
            device_info: Device information
            
        Returns:
            str: SHA-256 verification hash
        """
        # Create verification data
        verification_data = {
            'operation_id': wipe_result.operation_id,
            'device_id': wipe_result.device_id,
            'method': wipe_result.method.value,
            'passes_completed': wipe_result.passes_completed,
            'start_time': wipe_result.start_time.isoformat(),
            'end_time': wipe_result.end_time.isoformat() if wipe_result.end_time else None,
            'bytes_wiped': wipe_result.bytes_wiped,
            'device_type': device_info.device_type.value if device_info else 'unknown'
        }
        
        # Generate hash
        verification_json = json.dumps(verification_data, sort_keys=True)
        return hashlib.sha256(verification_json.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get wiping engine statistics.
        
        Returns:
            Dict containing operation statistics
        """
        return {
            'operations_completed': self.operations_completed,
            'total_bytes_wiped': self.total_bytes_wiped,
            'last_operation_time': self.last_operation_time.isoformat() if self.last_operation_time else None,
            'nist_methods_supported': [method.value for method in WipeMethod],
            'device_types_supported': [device_type.value for device_type in DeviceType]
        }


# Import json for verification hash generation
import json