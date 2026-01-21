"""
Blockchain Logger Implementation

Manages interaction with local Ethereum blockchain for immutable audit trail storage.
Provides secure, verifiable logging of data wiping operations on local Ganache blockchain.
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Tuple
from web3 import Web3
from web3.exceptions import TransactionNotFound, BlockNotFound, ContractLogicError
from eth_account import Account
from ..utils.data_models import WipeRecord, SystemConfig


class BlockchainConnectionError(Exception):
    """Raised when blockchain connection fails."""
    pass


class TransactionError(Exception):
    """Raised when blockchain transaction fails."""
    pass


class BlockchainLogger:
    """
    Manages interaction with local Ethereum blockchain for audit trail storage.
    
    This class provides secure, immutable logging of data wiping operations
    on a local Ganache blockchain instance. It handles Web3.py integration,
    transaction management, and retry logic for reliable operation.
    """
    
    def __init__(self, web3_provider: str, contract_address: str, abi: Dict[str, Any], 
                 private_key: Optional[str] = None, max_retries: int = 3):
        """
        Initialize the blockchain logger.
        
        Args:
            web3_provider: Web3 provider URL (must be local Ganache)
            contract_address: Address of deployed WipeAuditContract
            abi: Contract ABI for interaction
            private_key: Private key for transaction signing (optional)
            max_retries: Maximum number of retry attempts for failed operations
            
        Raises:
            BlockchainConnectionError: If connection to blockchain fails
            ValueError: If invalid parameters are provided
        """
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.base_retry_delay = 1.0  # Base delay for exponential backoff
        
        # Validate inputs
        if not web3_provider:
            raise ValueError("Web3 provider URL cannot be empty")
        
        if not contract_address:
            raise ValueError("Contract address cannot be empty")
        
        if not abi:
            raise ValueError("Contract ABI cannot be empty")
        
        # Ensure only local connections are allowed (Requirement 3.4, 7.2)
        if not self._is_local_provider(web3_provider):
            raise BlockchainConnectionError(
                f"Only local blockchain connections are allowed. "
                f"Provided URL: {web3_provider}"
            )
        
        self.web3_provider = web3_provider
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.abi = abi
        
        # Initialize Web3 connection
        self.w3 = None
        self.contract = None
        self.account = None
        
        # Set up account if private key provided
        if private_key:
            try:
                self.account = Account.from_key(private_key)
                self.logger.info(f"Account initialized: {self.account.address}")
            except Exception as e:
                raise ValueError(f"Invalid private key: {e}")
        
        # Establish connection
        self._connect()
    
    def _is_local_provider(self, provider_url: str) -> bool:
        """
        Validate that provider URL is local only.
        
        Requirement 3.4: Connect to local Ganache blockchain only
        Requirement 7.2: Local infrastructure operation
        
        Args:
            provider_url: URL to validate
            
        Returns:
            bool: True if URL is local, False otherwise
        """
        local_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'  # IPv6 localhost
        ]
        
        provider_lower = provider_url.lower()
        return any(pattern in provider_lower for pattern in local_patterns)
    
    def _connect(self) -> None:
        """
        Establish connection to Ganache blockchain.
        
        Raises:
            BlockchainConnectionError: If connection fails
        """
        try:
            self.logger.info(f"Connecting to blockchain at {self.web3_provider}")
            
            # Initialize Web3 connection
            self.w3 = Web3(Web3.HTTPProvider(self.web3_provider))
            
            # Test connection
            if not self.w3.is_connected():
                raise BlockchainConnectionError("Failed to connect to blockchain")
            
            # Initialize contract
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.abi
            )
            
            # Verify contract is accessible
            try:
                # Try to call a read-only function to verify contract
                self.contract.functions.getContractInfo().call()
                self.logger.info("Contract connection verified")
            except Exception as e:
                raise BlockchainConnectionError(f"Contract not accessible: {e}")
            
            self.logger.info("Blockchain connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to blockchain: {e}")
            raise BlockchainConnectionError(f"Connection failed: {e}")
    
    def connect_to_ganache(self) -> bool:
        """
        Test connection to Ganache blockchain.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._connect()
            return True
        except BlockchainConnectionError:
            return False
    
    def record_wipe(self, device_id: str, wipe_hash: str) -> str:
        """
        Record a wipe operation on the blockchain.
        
        Requirement 3.1: Record operation hash on local blockchain
        Requirement 3.2: Create immutable audit entries with timestamps
        
        Args:
            device_id: Unique identifier of the wiped device
            wipe_hash: SHA-256 hash of the wiping operation
            
        Returns:
            str: Transaction hash of the recorded operation
            
        Raises:
            TransactionError: If transaction fails after all retries
            ValueError: If invalid parameters provided
        """
        if not device_id or not device_id.strip():
            raise ValueError("Device ID cannot be empty")
        
        if not wipe_hash or not wipe_hash.strip():
            raise ValueError("Wipe hash cannot be empty")
        
        # Validate hash format (should be 64 hex characters for SHA-256)
        wipe_hash = wipe_hash.strip().lower()
        if len(wipe_hash) != 64 or not all(c in '0123456789abcdef' for c in wipe_hash):
            raise ValueError("Invalid wipe hash format. Expected 64 hex characters.")
        
        # Convert hash to bytes32 for smart contract
        wipe_hash_bytes = Web3.to_bytes(hexstr=wipe_hash)
        
        self.logger.info(f"Recording wipe for device {device_id} with hash {wipe_hash}")
        
        # Implement retry logic (Requirement 3.5)
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return self._execute_record_transaction(device_id, wipe_hash_bytes, attempt)
                
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Record attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.base_retry_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed")
        
        # All retries failed
        raise TransactionError(f"Failed to record wipe after {self.max_retries} attempts: {last_exception}")
    
    def _execute_record_transaction(self, device_id: str, wipe_hash_bytes: bytes, attempt: int) -> str:
        """
        Execute the record wipe transaction.
        
        Args:
            device_id: Device identifier
            wipe_hash_bytes: Hash as bytes32
            attempt: Current attempt number (for logging)
            
        Returns:
            str: Transaction hash
            
        Raises:
            TransactionError: If transaction fails
        """
        try:
            # Check if we have an account for signing
            if not self.account:
                raise TransactionError("No account configured for transaction signing")
            
            # Build transaction
            function_call = self.contract.functions.recordWipe(device_id, wipe_hash_bytes)
            
            # Estimate gas
            try:
                gas_estimate = function_call.estimate_gas({'from': self.account.address})
                gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
            except Exception as e:
                self.logger.warning(f"Gas estimation failed: {e}. Using default gas limit.")
                gas_limit = 300000  # Default gas limit
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            self.logger.info(f"Transaction sent: {tx_hash_hex}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                self.logger.info(f"Transaction successful: {tx_hash_hex}")
                return tx_hash_hex
            else:
                raise TransactionError(f"Transaction failed with status: {receipt.status}")
                
        except Exception as e:
            self.logger.error(f"Transaction execution failed on attempt {attempt + 1}: {e}")
            raise TransactionError(f"Transaction failed: {e}")
    
    def get_wipe_record(self, device_id: str) -> WipeRecord:
        """
        Retrieve wipe record by device ID.
        
        Requirement 3.3: Retrieve audit trails by device ID
        
        Args:
            device_id: Unique identifier of the device
            
        Returns:
            WipeRecord: Complete wipe record from blockchain
            
        Raises:
            ValueError: If device_id is invalid
            TransactionError: If record retrieval fails
        """
        if not device_id or not device_id.strip():
            raise ValueError("Device ID cannot be empty")
        
        device_id = device_id.strip()
        
        try:
            self.logger.info(f"Retrieving wipe record for device: {device_id}")
            
            # Call smart contract function
            record_data = self.contract.functions.getWipeRecord(device_id).call()
            
            # Parse the returned data
            # Smart contract returns: (deviceId, wipeHash, timestamp, operator, exists)
            device_id_returned = record_data[0]
            wipe_hash_bytes = record_data[1]
            timestamp = record_data[2]
            operator_address = record_data[3]
            exists = record_data[4]
            
            if not exists:
                raise TransactionError(f"No record found for device: {device_id}")
            
            # Convert bytes32 hash back to hex string
            wipe_hash = wipe_hash_bytes.hex()
            
            # Create WipeRecord object
            wipe_record = WipeRecord(
                device_id=device_id_returned,
                wipe_hash=wipe_hash,
                timestamp=timestamp,
                operator_address=operator_address
            )
            
            self.logger.info(f"Retrieved record for device {device_id}")
            return wipe_record
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve wipe record for {device_id}: {e}")
            raise TransactionError(f"Record retrieval failed: {e}")
    
    def get_wipe_record_by_transaction(self, tx_hash: str) -> Optional[WipeRecord]:
        """
        Retrieve wipe record by transaction hash.
        
        Requirement 3.3: Retrieve audit trails by transaction hash
        
        Args:
            tx_hash: Transaction hash to look up
            
        Returns:
            WipeRecord: Wipe record if found, None otherwise
            
        Raises:
            ValueError: If tx_hash is invalid
        """
        if not tx_hash or not tx_hash.strip():
            raise ValueError("Transaction hash cannot be empty")
        
        try:
            self.logger.info(f"Retrieving wipe record by transaction: {tx_hash}")
            
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Parse logs to find WipeRecorded event
            wipe_recorded_events = self.contract.events.WipeRecorded().process_receipt(receipt)
            
            if not wipe_recorded_events:
                self.logger.warning(f"No WipeRecorded event found in transaction {tx_hash}")
                return None
            
            # Get the first (should be only) event
            event = wipe_recorded_events[0]
            event_args = event['args']
            
            # Create WipeRecord from event data
            wipe_record = WipeRecord(
                device_id=event_args['deviceId'],
                wipe_hash=event_args['wipeHash'].hex(),
                timestamp=event_args['timestamp'],
                operator_address=event_args['operator'],
                transaction_hash=tx_hash,
                block_number=receipt['blockNumber'],
                gas_used=receipt['gasUsed']
            )
            
            self.logger.info(f"Retrieved record from transaction {tx_hash}")
            return wipe_record
            
        except TransactionNotFound:
            self.logger.warning(f"Transaction not found: {tx_hash}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve record by transaction {tx_hash}: {e}")
            raise TransactionError(f"Transaction lookup failed: {e}")
    
    def verify_transaction(self, tx_hash: str) -> bool:
        """
        Verify that a transaction exists and was successful.
        
        Args:
            tx_hash: Transaction hash to verify
            
        Returns:
            bool: True if transaction exists and was successful
        """
        if not tx_hash or not tx_hash.strip():
            return False
        
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return receipt.status == 1
        except TransactionNotFound:
            return False
        except Exception as e:
            self.logger.error(f"Transaction verification failed for {tx_hash}: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current blockchain connection.
        
        Returns:
            Dict containing connection information
        """
        if not self.w3 or not self.w3.is_connected():
            return {
                'connected': False,
                'provider': self.web3_provider,
                'error': 'Not connected'
            }
        
        try:
            latest_block = self.w3.eth.get_block('latest')
            chain_id = self.w3.eth.chain_id
            
            return {
                'connected': True,
                'provider': self.web3_provider,
                'contract_address': self.contract_address,
                'chain_id': chain_id,
                'latest_block': latest_block.number,
                'account_address': self.account.address if self.account else None,
                'account_balance': self.w3.eth.get_balance(self.account.address) if self.account else None
            }
        except Exception as e:
            return {
                'connected': False,
                'provider': self.web3_provider,
                'error': str(e)
            }
    
    def check_device_processed(self, device_id: str) -> bool:
        """
        Check if a device has already been processed.
        
        Args:
            device_id: Device identifier to check
            
        Returns:
            bool: True if device has been processed, False otherwise
        """
        if not device_id or not device_id.strip():
            return False
        
        try:
            return self.contract.functions.deviceProcessed(device_id.strip()).call()
        except Exception as e:
            self.logger.error(f"Failed to check device status for {device_id}: {e}")
            return False
    
    def get_total_records(self) -> int:
        """
        Get the total number of wipe records stored on the blockchain.
        
        Returns:
            int: Total number of records
        """
        try:
            return self.contract.functions.getTotalRecords().call()
        except Exception as e:
            self.logger.error(f"Failed to get total records: {e}")
            return 0
    
    def disconnect(self) -> None:
        """
        Clean up blockchain connection.
        """
        self.logger.info("Disconnecting from blockchain")
        self.w3 = None
        self.contract = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def create_blockchain_logger_from_config(config: SystemConfig, private_key: Optional[str] = None) -> BlockchainLogger:
    """
    Create BlockchainLogger from system configuration.
    
    Args:
        config: System configuration object
        private_key: Optional private key for transaction signing
        
    Returns:
        BlockchainLogger: Configured blockchain logger instance
        
    Raises:
        ValueError: If configuration is invalid
        BlockchainConnectionError: If connection fails
    """
    if not config.contract_address:
        raise ValueError("Contract address not configured")
    
    # Load contract ABI (this would typically be loaded from a file)
    # For now, we'll need to load it from the deployment artifacts
    try:
        # This is a placeholder - in practice, ABI would be loaded from deployment artifacts
        with open('config/contract_abi.json', 'r') as f:
            abi = json.load(f)
    except FileNotFoundError:
        raise ValueError("Contract ABI file not found. Ensure contract is deployed.")
    
    return BlockchainLogger(
        web3_provider=config.ganache_url,
        contract_address=config.contract_address,
        abi=abi,
        private_key=private_key,
        max_retries=config.max_retry_attempts
    )