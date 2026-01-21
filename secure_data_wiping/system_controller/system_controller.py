"""
System Controller Implementation

Orchestrates all components of the secure data wiping system to provide
a complete workflow from device wiping to certificate generation.
Implements sequential processing with comprehensive error handling.
"""

import os
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..wipe_engine import WipeEngine, WipeEngineError
from ..hash_generator import HashGenerator
from ..blockchain_logger import (
    BlockchainLogger,
    BlockchainConnectionError,
    TransactionError,
    create_blockchain_logger_from_config,
)
from ..certificate_generator import CertificateGenerator, CertificateGeneratorError
from ..database import DatabaseManager
from ..utils.data_models import (
    DeviceInfo,
    WipeConfig,
    WipeResult,
    WipeData,
    BlockchainData,
    WipeOperation,
    OperationStatus,
    SystemConfig,
    WipeMethod,
)
from ..utils.config import ConfigManager
from ..utils.logging_config import setup_logging
from ..utils.local_infrastructure import (
    LocalInfrastructureValidator, 
    validate_system_is_local_only,
    LocalInfrastructureError,
    NetworkIsolationError as UtilsNetworkError,
    DataPrivacyError as UtilsDataPrivacyError
)


class SystemControllerError(Exception):
    """Base exception for system controller operations."""
    pass


class WorkflowError(SystemControllerError):
    """Raised when the sequential workflow fails."""
    pass


class ComponentInitializationError(SystemControllerError):
    """Raised when component initialization fails."""
    pass


class BlockchainConnectivityError(SystemControllerError):
    """Raised when blockchain connectivity verification fails."""
    pass


@dataclass
class ProcessingResult:
    """Result of processing a single device."""
    operation_id: str
    device_id: str
    success: bool
    error_message: Optional[str] = None
    wipe_result: Optional[WipeResult] = None
    wipe_hash: Optional[str] = None
    transaction_hash: Optional[str] = None
    certificate_path: Optional[str] = None
    processing_time: Optional[float] = None


@dataclass
class SystemStatus:
    """Current status of the system."""
    blockchain_connected: bool
    components_initialized: bool
    operations_processed: int
    operations_successful: int
    operations_failed: int
    last_operation_time: Optional[datetime] = None


class SystemController:
    """
    Main system controller that orchestrates all components.
    
    Implements the complete secure data wiping workflow:
    1. Device wiping using NIST 800-88 compliant procedures
    2. Cryptographic hash generation of wiping operation
    3. Blockchain logging for immutable audit trail
    4. Certificate generation with blockchain verification
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the system controller.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.system_config = self.config_manager.get_config()
        
        # Initialize components
        self.wipe_engine: Optional[WipeEngine] = None
        self.hash_generator: Optional[HashGenerator] = None
        self.blockchain_logger: Optional[BlockchainLogger] = None
        self.certificate_generator: Optional[CertificateGenerator] = None
        self.database_manager: Optional[DatabaseManager] = None
        self.local_validator: Optional[LocalInfrastructureValidator] = None
        
        # System status tracking
        self.status = SystemStatus(
            blockchain_connected=False,
            components_initialized=False,
            operations_processed=0,
            operations_successful=0,
            operations_failed=0
        )
        
        # Processing statistics
        self.start_time = datetime.now()
        self.processing_history: List[ProcessingResult] = []
        
        self.logger.info("SystemController initialized")
    
    def initialize_system(self) -> bool:
        """
        Initialize all system components and verify connectivity.
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Raises:
            ComponentInitializationError: If component initialization fails
            BlockchainConnectivityError: If blockchain connectivity fails
        """
        self.logger.info("Initializing system components...")
        
        try:
            # Initialize local infrastructure validator first
            self._initialize_local_validator()
            
            # Validate system is local-only compliant
            self._validate_local_infrastructure()
            
            # Initialize database manager
            self._initialize_database()
            
            # Initialize core components
            self._initialize_wipe_engine()
            self._initialize_hash_generator()
            self._initialize_certificate_generator()
            
            # Initialize blockchain logger (requires connectivity check)
            self._initialize_blockchain_logger()
            
            # Verify blockchain connectivity
            self._verify_blockchain_connectivity()
            
            # Mark system as initialized
            self.status.components_initialized = True
            self.status.blockchain_connected = True
            
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            self.status.components_initialized = False
            self.status.blockchain_connected = False
            raise ComponentInitializationError(f"Failed to initialize system: {e}") from e
    
    def process_device(self, device_info: DeviceInfo, wipe_config: WipeConfig,
                      custom_certificate_name: Optional[str] = None) -> ProcessingResult:
        """
        Process a single device through the complete workflow.
        
        Args:
            device_info: Information about the device to wipe
            wipe_config: Configuration for the wiping operation
            custom_certificate_name: Optional custom certificate filename
            
        Returns:
            ProcessingResult: Result of the processing operation
            
        Raises:
            WorkflowError: If any step in the workflow fails and halts processing
        """
        if not self.status.components_initialized:
            raise WorkflowError("System not initialized. Call initialize_system() first to prevent processing.")
        
        operation_id = f"OP_{int(time.time())}_{device_info.device_id}"
        start_time = time.time()
        
        self.logger.info(f"Starting processing for device {device_info.device_id} (Operation: {operation_id})")
        
        # Create operation record
        operation = WipeOperation(
            operation_id=operation_id,
            device_info=device_info,
            wipe_config=wipe_config
        )
        
        try:
            # Step 1: Wipe the device
            self.logger.info(f"Step 1: Wiping device {device_info.device_id}")
            wipe_result = self._execute_wiping(device_info, wipe_config, operation_id)
            operation.wipe_result = wipe_result
            
            if not wipe_result.success:
                raise WorkflowError(f"Device wiping failed: {wipe_result.error_message}. Processing halted to prevent subsequent steps from executing.")
            
            # Step 2: Generate cryptographic hash
            self.logger.info(f"Step 2: Generating hash for operation {operation_id}")
            wipe_hash = self._generate_hash(wipe_result)
            
            # Step 3: Log to blockchain
            self.logger.info(f"Step 3: Recording to blockchain for device {device_info.device_id}")
            transaction_hash = self._record_to_blockchain(device_info.device_id, wipe_hash)
            
            # Step 4: Generate certificate
            self.logger.info(f"Step 4: Generating certificate for device {device_info.device_id}")
            certificate_path = self._generate_certificate(
                wipe_result, wipe_hash, transaction_hash, device_info, custom_certificate_name
            )
            
            # Step 5: Store operation in database
            operation.certificate_path = certificate_path
            operation.update_timestamp()
            self._store_operation(operation)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create successful result
            result = ProcessingResult(
                operation_id=operation_id,
                device_id=device_info.device_id,
                success=True,
                wipe_result=wipe_result,
                wipe_hash=wipe_hash,
                transaction_hash=transaction_hash,
                certificate_path=certificate_path,
                processing_time=processing_time
            )
            
            # Update statistics
            self.status.operations_processed += 1
            self.status.operations_successful += 1
            self.status.last_operation_time = datetime.now()
            self.processing_history.append(result)
            
            self.logger.info(f"Successfully processed device {device_info.device_id} in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            # Calculate processing time even for failures
            processing_time = time.time() - start_time
            
            # Create failure result
            result = ProcessingResult(
                operation_id=operation_id,
                device_id=device_info.device_id,
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
            
            # Update statistics
            self.status.operations_processed += 1
            self.status.operations_failed += 1
            self.status.last_operation_time = datetime.now()
            self.processing_history.append(result)
            
            self.logger.error(f"Failed to process device {device_info.device_id}: {e}")
            
            # Store failed operation in database
            operation.wipe_result = WipeResult(
                operation_id=operation_id,
                device_id=device_info.device_id,
                method=wipe_config.method,
                passes_completed=0,
                start_time=datetime.now(),
                success=False,
                error_message=str(e)
            )
            operation.update_timestamp()
            self._store_operation(operation)
            
            raise WorkflowError(f"Device processing failed: {e}. Processing halted to prevent subsequent operations.") from e
    
    def process_batch(self, devices: List[Tuple[DeviceInfo, WipeConfig]],
                     continue_on_error: bool = True) -> List[ProcessingResult]:
        """
        Process multiple devices in batch.
        
        Args:
            devices: List of (device_info, wipe_config) tuples
            continue_on_error: Whether to continue processing if one device fails
            
        Returns:
            List[ProcessingResult]: Results for all processed devices
        """
        if not self.status.components_initialized:
            raise WorkflowError("System not initialized. Call initialize_system() first to prevent batch processing.")
        
        self.logger.info(f"Starting batch processing of {len(devices)} devices")
        results = []
        
        for i, (device_info, wipe_config) in enumerate(devices, 1):
            self.logger.info(f"Processing device {i}/{len(devices)}: {device_info.device_id}")
            
            try:
                result = self.process_device(device_info, wipe_config)
                results.append(result)
                
            except WorkflowError as e:
                self.logger.error(f"Failed to process device {device_info.device_id}: {e}")
                
                # Create failure result
                result = ProcessingResult(
                    operation_id=f"BATCH_FAIL_{int(time.time())}_{device_info.device_id}",
                    device_id=device_info.device_id,
                    success=False,
                    error_message=str(e)
                )
                results.append(result)
                
                if not continue_on_error:
                    self.logger.error("Stopping batch processing due to error - halting processing to prevent further failures")
                    break
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.logger.info(f"Batch processing completed: {successful} successful, {failed} failed")
        return results
    
    def get_system_status(self) -> SystemStatus:
        """Get current system status."""
        return self.status
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive processing summary.
        
        Returns:
            Dict containing processing statistics and history
        """
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'system_status': {
                'blockchain_connected': self.status.blockchain_connected,
                'components_initialized': self.status.components_initialized,
                'uptime_seconds': total_time
            },
            'processing_statistics': {
                'operations_processed': self.status.operations_processed,
                'operations_successful': self.status.operations_successful,
                'operations_failed': self.status.operations_failed,
                'success_rate': (self.status.operations_successful / max(1, self.status.operations_processed)) * 100,
                'last_operation_time': self.status.last_operation_time.isoformat() if self.status.last_operation_time else None
            },
            'performance_metrics': {
                'average_processing_time': self._calculate_average_processing_time(),
                'total_devices_processed': len(self.processing_history),
                'processing_rate_per_hour': self._calculate_processing_rate()
            },
            'recent_operations': [
                {
                    'operation_id': r.operation_id,
                    'device_id': r.device_id,
                    'success': r.success,
                    'processing_time': r.processing_time,
                    'error_message': r.error_message
                }
                for r in self.processing_history[-10:]  # Last 10 operations
            ]
        }
    
    def shutdown_system(self) -> bool:
        """
        Gracefully shutdown the system.
        
        Returns:
            bool: True if shutdown successful
        """
        self.logger.info("Shutting down system...")
        
        try:
            # Close database connections
            if self.database_manager:
                self.database_manager.close()
            
            # Log final statistics
            summary = self.get_processing_summary()
            self.logger.info(f"Final statistics: {summary['processing_statistics']}")
            
            self.logger.info("System shutdown completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            return False
    
    # Private helper methods
    
    def _initialize_local_validator(self):
        """Initialize local infrastructure validator."""
        try:
            self.local_validator = LocalInfrastructureValidator()
            self.logger.info("Local infrastructure validator initialized")
        except Exception as e:
            raise ComponentInitializationError(f"Failed to initialize local validator: {e}")
    
    def _validate_local_infrastructure(self):
        """Validate that system operates on local infrastructure only."""
        try:
            validate_system_is_local_only(
                ganache_url=self.system_config.ganache_url,
                database_path=self.system_config.database_path,
                certificates_dir=self.system_config.certificates_dir
            )
            self.logger.info("Local infrastructure validation passed")
        except LocalInfrastructureError as e:
            raise ComponentInitializationError(f"Local infrastructure validation failed: {e}")
    
    def _initialize_database(self):
        """Initialize database manager."""
        try:
            from ..database import DatabaseManager
            self.database_manager = DatabaseManager(self.system_config.database_path)
            self.database_manager.initialize_database()
            self.logger.info("Database manager initialized")
        except Exception as e:
            raise ComponentInitializationError(f"Failed to initialize database: {e}")
    
    def _initialize_wipe_engine(self):
        """Initialize wipe engine."""
        try:
            self.wipe_engine = WipeEngine()
            self.logger.info("Wipe engine initialized")
        except Exception as e:
            raise ComponentInitializationError(f"Failed to initialize wipe engine: {e}")
    
    def _initialize_hash_generator(self):
        """Initialize hash generator."""
        try:
            self.hash_generator = HashGenerator()
            self.logger.info("Hash generator initialized")
        except Exception as e:
            raise ComponentInitializationError(f"Failed to initialize hash generator: {e}")
    
    def _initialize_certificate_generator(self):
        """Initialize certificate generator."""
        try:
            self.certificate_generator = CertificateGenerator(
                output_dir=self.system_config.certificates_dir
            )
            self.logger.info("Certificate generator initialized")
        except Exception as e:
            raise ComponentInitializationError(f"Failed to initialize certificate generator: {e}")
    
    def _initialize_blockchain_logger(self):
        """Initialize blockchain logger."""
        try:
            # Use the factory function to ensure the logger is configured
            # consistently with the SystemConfig (including ABI loading).
            self.blockchain_logger = create_blockchain_logger_from_config(
                self.system_config
            )
            self.logger.info("Blockchain logger initialized")
        except Exception as e:
            raise ComponentInitializationError(f"Failed to initialize blockchain logger: {e}")
    
    def _verify_blockchain_connectivity(self):
        """Verify blockchain connectivity."""
        try:
            if not self.blockchain_logger.connect_to_ganache():
                raise BlockchainConnectivityError("Failed to connect to Ganache blockchain")
            
            # Test blockchain connection with a simple call
            connection_info = self.blockchain_logger.get_connection_info()
            self.logger.info(f"Blockchain connectivity verified: {connection_info}")
            
        except Exception as e:
            raise BlockchainConnectivityError(f"Blockchain connectivity verification failed: {e}")
    
    def _execute_wiping(self, device_info: DeviceInfo, wipe_config: WipeConfig, operation_id: str) -> WipeResult:
        """Execute device wiping."""
        try:
            # For demonstration purposes, we'll create a test file to wipe
            # In production, this would wipe actual device paths
            test_file_path = f"test_device_{device_info.device_id}.tmp"
            
            # Create test file with some data
            with open(test_file_path, 'w') as f:
                f.write("Test data for secure wiping demonstration\n" * 100)
            
            # Execute wiping
            wipe_result = self.wipe_engine.wipe_device(test_file_path, wipe_config.method)
            wipe_result.operation_id = operation_id
            
            return wipe_result
            
        except Exception as e:
            raise WorkflowError(f"Wiping execution failed: {e}")
    
    def _generate_hash(self, wipe_result: WipeResult) -> str:
        """Generate cryptographic hash of wiping operation."""
        try:
            wipe_hash = self.hash_generator.generate_wipe_hash(wipe_result)
            return wipe_hash
        except Exception as e:
            raise WorkflowError(f"Hash generation failed: {e}")
    
    def _record_to_blockchain(self, device_id: str, wipe_hash: str) -> str:
        """Record wiping operation to blockchain."""
        try:
            # Validate data privacy before blockchain storage
            blockchain_data = {
                'device_id': device_id,
                'wipe_hash': wipe_hash,
                'timestamp': int(time.time()),
                'method': 'secure_wipe'
            }
            
            # Validate privacy compliance
            if self.local_validator:
                self.local_validator.validate_blockchain_data_privacy(blockchain_data)
            
            transaction_hash = self.blockchain_logger.record_wipe(device_id, wipe_hash)
            return transaction_hash
        except Exception as e:
            raise WorkflowError(f"Blockchain recording failed: {e}")
    
    def _generate_certificate(self, wipe_result: WipeResult, wipe_hash: str, 
                            transaction_hash: str, device_info: DeviceInfo,
                            custom_filename: Optional[str] = None) -> str:
        """Generate PDF certificate."""
        try:
            # Get blockchain record for certificate
            wipe_record = self.blockchain_logger.get_wipe_record_by_transaction(transaction_hash)
            
            # Create certificate data
            wipe_data = WipeData(
                device_id=device_info.device_id,
                wipe_hash=wipe_hash,
                timestamp=wipe_result.start_time,
                method=wipe_result.method.value,
                operator=wipe_result.operator_id,
                passes=wipe_result.passes_completed
            )
            
            blockchain_data = BlockchainData(
                transaction_hash=transaction_hash,
                block_number=wipe_record.block_number,
                contract_address=self.blockchain_logger.contract_address,
                gas_used=wipe_record.gas_used,
                confirmation_count=wipe_record.confirmation_count
            )
            
            # Validate certificate data privacy
            if self.local_validator:
                certificate_data = {
                    'device_id': device_info.device_id,
                    'wipe_hash': wipe_hash,
                    'transaction_hash': transaction_hash,
                    'method': wipe_result.method.value,
                    'operator': wipe_result.operator_id
                }
                self.local_validator.validate_certificate_data_privacy(certificate_data)
            
            # Generate certificate
            certificate_path = self.certificate_generator.generate_certificate(
                wipe_data=wipe_data,
                blockchain_data=blockchain_data,
                device_info=device_info,
                custom_filename=custom_filename
            )
            
            # Create offline verification data
            if self.local_validator:
                try:
                    from ..local_infrastructure import create_offline_verification_data
                    offline_verification = create_offline_verification_data(
                        wipe_data=wipe_data,
                        blockchain_data=blockchain_data,
                        device_info=device_info,
                        certificate_path=certificate_path
                    )
                    self.logger.info(f"Offline verification data created for device {device_info.device_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to create offline verification data: {e}")
            
            return certificate_path
            
        except Exception as e:
            raise WorkflowError(f"Certificate generation failed: {e}")
    
    def _store_operation(self, operation: WipeOperation):
        """Store operation in database."""
        try:
            self.database_manager.store_wipe_operation(operation)
        except Exception as e:
            self.logger.warning(f"Failed to store operation in database: {e}")
            # Don't raise exception as this is not critical for the main workflow
    
    def _calculate_average_processing_time(self) -> float:
        """Calculate average processing time."""
        if not self.processing_history:
            return 0.0
        
        times = [r.processing_time for r in self.processing_history if r.processing_time is not None]
        return sum(times) / len(times) if times else 0.0
    
    def generate_offline_verification(self, device_id: str, wipe_hash: str, 
                                    transaction_hash: str) -> Dict[str, Any]:
        """
        Generate offline verification data for certificates.
        
        Args:
            device_id: Device identifier
            wipe_hash: Cryptographic hash of wiping operation
            transaction_hash: Blockchain transaction hash
            
        Returns:
            Dict[str, Any]: Offline verification data
        """
        if not self.local_validator:
            raise SystemControllerError("Local validator not initialized")
        
        return self.local_validator.create_offline_verification_data(
            wipe_hash=wipe_hash,
            transaction_hash=transaction_hash,
            device_id=device_id
        )
    
    def _calculate_processing_rate(self) -> float:
        """Calculate processing rate per hour."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        if total_time == 0:
            return 0.0
        
        return (self.status.operations_processed / total_time) * 3600  # Per hour


def create_system_controller_from_config(config_path: str) -> SystemController:
    """
    Create SystemController from configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        SystemController: Configured system controller instance
    """
    return SystemController(config_path=config_path)