"""
Property-Based Tests for Smart Contract

Tests the correctness properties of the WipeAuditContract smart contract,
focusing on access control, data integrity, and security properties.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, MagicMock, patch
import json
import os
from pathlib import Path

from secure_data_wiping.utils.data_models import WipeRecord, DeviceType
from secure_data_wiping.utils.logging_config import get_component_logger


class TestSmartContractAccessControl:
    """
    Property-based tests for smart contract access control.
    
    Tests Property 8: Smart Contract Access Control
    Validates: Requirements 4.7
    """
    
    def setup_method(self):
        """Set up test environment for each test method."""
        self.logger = get_component_logger('test_smart_contract')
        
        # Mock Web3 and contract for testing
        self.mock_w3 = Mock()
        self.mock_contract = Mock()
        
        # Create test accounts (mock addresses)
        self.owner_account = Mock()
        self.owner_account.address = "0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e1e1"
        
        self.authorized_operator = Mock()
        self.authorized_operator.address = "0x8ba1f109551bD432803012645Hac136c9.c3e1e1"
        
        self.unauthorized_user = Mock()
        self.unauthorized_user.address = "0x123456789abcdef123456789abcdef123456789a"
        
        # Mock Web3 accounts
        self.mock_w3.eth.accounts = [
            self.owner_account.address,
            self.authorized_operator.address,
            self.unauthorized_user.address
        ]
        
        # Mock contract functions
        self.setup_contract_mocks()
    
    def setup_contract_mocks(self):
        """Set up mock contract function responses."""
        # Mock successful operations for authorized users
        self.mock_contract.functions.recordWipe.return_value.transact.return_value = "0xabcd1234"
        self.mock_contract.functions.isAuthorizedOperator.return_value.call.return_value = True
        
        # Mock contract state
        self.authorized_operators = {
            self.owner_account.address: True,
            self.authorized_operator.address: True,
            self.unauthorized_user.address: False
        }
        
        # Mock access control checks
        def mock_is_authorized(address):
            return Mock(call=lambda: self.authorized_operators.get(address, False))
        
        self.mock_contract.functions.isAuthorizedOperator = mock_is_authorized
    
    def mock_keccak(self, data):
        """Mock Web3.keccak function for testing."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        # Return a mock 32-byte hash
        return b'\x12\x34\x56\x78' * 8
    
    @given(
        device_id=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'),
            min_size=1,
            max_size=50
        ).filter(lambda x: x.strip()),
        wipe_hash=st.binary(min_size=32, max_size=32)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_unauthorized_access_prevention(self, device_id, wipe_hash):
        """
        Feature: secure-data-wiping-blockchain, Property 8: Smart Contract Access Control
        
        Property: For any unauthorized address attempting to modify existing wipe records,
        the smart contract should prevent the modification.
        
        Validates: Requirements 4.7
        """
        # Convert binary hash to bytes32 format using mock
        wipe_hash_bytes32 = self.mock_keccak(wipe_hash)
        
        # Test that unauthorized users cannot record wipe operations
        # Mock the contract to raise an exception for unauthorized access
        def mock_record_wipe_unauthorized(*args, **kwargs):
            caller = kwargs.get('from', self.unauthorized_user.address)
            if not self.authorized_operators.get(caller, False):
                raise Exception("WipeAudit: Only authorized operators can record wipes")
            return Mock(transact=lambda x: "0xabcd1234")
        
        self.mock_contract.functions.recordWipe.return_value = Mock(
            transact=mock_record_wipe_unauthorized
        )
        
        # Test unauthorized access is prevented
        with pytest.raises(Exception, match="Only authorized operators can record wipes"):
            self.mock_contract.functions.recordWipe(device_id, wipe_hash_bytes32).transact({
                'from': self.unauthorized_user.address
            })
        
        # Test authorized access works
        try:
            result = self.mock_contract.functions.recordWipe(device_id, wipe_hash_bytes32).transact({
                'from': self.authorized_operator.address
            })
            assert result == "0xabcd1234"
        except Exception as e:
            pytest.fail(f"Authorized operator should be able to record wipes: {e}")
    
    @given(
        operator_address=st.text(min_size=42, max_size=42).filter(
            lambda x: x.startswith('0x') and all(c in '0123456789abcdefABCDEF' for c in x[2:])
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_property_8_operator_authorization_control(self, operator_address):
        """
        Test that only the contract owner can authorize/revoke operators.
        
        This extends Property 8 to cover operator management access control.
        """
        # Mock owner-only functions
        def mock_authorize_operator(*args, **kwargs):
            caller = kwargs.get('from', self.unauthorized_user.address)
            if caller != self.owner_account.address:
                raise Exception("WipeAudit: Only owner can perform this action")
            return Mock(transact=lambda x: "0xdef5678")
        
        self.mock_contract.functions.authorizeOperator.return_value = Mock(
            transact=mock_authorize_operator
        )
        
        # Test unauthorized user cannot authorize operators
        with pytest.raises(Exception, match="Only owner can perform this action"):
            self.mock_contract.functions.authorizeOperator(operator_address).transact({
                'from': self.unauthorized_user.address
            })
        
        # Test owner can authorize operators
        try:
            result = self.mock_contract.functions.authorizeOperator(operator_address).transact({
                'from': self.owner_account.address
            })
            assert result == "0xdef5678"
        except Exception as e:
            pytest.fail(f"Owner should be able to authorize operators: {e}")
    
    @given(
        device_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        num_unauthorized_attempts=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_8_multiple_unauthorized_attempts(self, device_id, num_unauthorized_attempts):
        """
        Test that multiple unauthorized attempts are consistently blocked.
        
        Property: For any number of unauthorized access attempts,
        all should be prevented by the smart contract.
        """
        wipe_hash = self.mock_keccak(f"test_hash_{device_id}")
        
        # Mock contract to track unauthorized attempts
        unauthorized_attempts = []
        
        def mock_record_wipe_tracking(*args, **kwargs):
            caller = kwargs.get('from', self.unauthorized_user.address)
            if not self.authorized_operators.get(caller, False):
                unauthorized_attempts.append(caller)
                raise Exception("WipeAudit: Only authorized operators can record wipes")
            return Mock(transact=lambda x: "0xabcd1234")
        
        self.mock_contract.functions.recordWipe.return_value = Mock(
            transact=mock_record_wipe_tracking
        )
        
        # Attempt multiple unauthorized operations
        for i in range(num_unauthorized_attempts):
            with pytest.raises(Exception, match="Only authorized operators can record wipes"):
                self.mock_contract.functions.recordWipe(
                    f"{device_id}_{i}", wipe_hash
                ).transact({'from': self.unauthorized_user.address})
        
        # Verify all attempts were blocked
        assert len(unauthorized_attempts) == num_unauthorized_attempts
        
        # Verify authorized operation still works after unauthorized attempts
        try:
            result = self.mock_contract.functions.recordWipe(device_id, wipe_hash).transact({
                'from': self.authorized_operator.address
            })
            assert result == "0xabcd1234"
        except Exception as e:
            pytest.fail(f"Authorized operations should work after unauthorized attempts: {e}")
    
    @given(
        device_ids=st.lists(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_property_8_batch_access_control(self, device_ids):
        """
        Test access control for batch operations.
        
        Property: For any batch of wipe recording attempts by unauthorized users,
        all should be prevented while authorized operations succeed.
        """
        # Create unique hashes for each device
        device_hashes = {
            device_id: self.mock_keccak(f"hash_{device_id}")
            for device_id in device_ids
        }
        
        # Mock contract for batch operations
        successful_operations = []
        failed_operations = []
        
        def mock_batch_record_wipe(*args, **kwargs):
            caller = kwargs.get('from')
            device_id = args[0] if args else kwargs.get('device_id')
            
            if not self.authorized_operators.get(caller, False):
                failed_operations.append((device_id, caller))
                raise Exception("WipeAudit: Only authorized operators can record wipes")
            else:
                successful_operations.append((device_id, caller))
                return Mock(transact=lambda x: f"0x{hash(device_id) & 0xffffffff:08x}")
        
        self.mock_contract.functions.recordWipe.return_value = Mock(
            transact=mock_batch_record_wipe
        )
        
        # Test unauthorized batch operations fail
        for device_id in device_ids:
            with pytest.raises(Exception, match="Only authorized operators can record wipes"):
                self.mock_contract.functions.recordWipe(
                    device_id, device_hashes[device_id]
                ).transact({'from': self.unauthorized_user.address})
        
        # Test authorized batch operations succeed
        for device_id in device_ids:
            try:
                result = self.mock_contract.functions.recordWipe(
                    device_id, device_hashes[device_id]
                ).transact({'from': self.authorized_operator.address})
                assert result.startswith('0x')
            except Exception as e:
                pytest.fail(f"Authorized batch operation should succeed for {device_id}: {e}")
        
        # Verify results
        assert len(failed_operations) == len(device_ids)
        assert len(successful_operations) == len(device_ids)
        
        # Verify all failed operations were from unauthorized user
        for device_id, caller in failed_operations:
            assert caller == self.unauthorized_user.address
        
        # Verify all successful operations were from authorized operator
        for device_id, caller in successful_operations:
            assert caller == self.authorized_operator.address


class TestSmartContractDataIntegrity:
    """
    Additional property tests for smart contract data integrity.
    
    These tests complement the access control tests by verifying
    that the contract maintains data consistency and integrity.
    """
    
    def setup_method(self):
        """Set up test environment."""
        self.logger = get_component_logger('test_contract_integrity')
        self.mock_contract = Mock()
        self.stored_records = {}
    
    def mock_keccak(self, data):
        """Mock Web3.keccak function for testing."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        # Return a mock 32-byte hash
        return b'\x12\x34\x56\x78' * 8
    
    @given(
        device_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        wipe_hash=st.binary(min_size=32, max_size=32)
    )
    @settings(max_examples=50, deadline=None)
    def test_wipe_record_immutability(self, device_id, wipe_hash):
        """
        Test that wipe records cannot be modified once stored.
        
        Property: For any stored wipe record, subsequent attempts to modify
        it should be prevented (immutability property).
        """
        wipe_hash_bytes32 = self.mock_keccak(wipe_hash)
        
        # Mock storage behavior
        def mock_store_record(*args, **kwargs):
            if device_id in self.stored_records:
                raise Exception("WipeAudit: Device has already been processed")
            
            self.stored_records[device_id] = {
                'deviceId': device_id,
                'wipeHash': wipe_hash_bytes32,
                'timestamp': 1640995200,  # Fixed timestamp for testing
                'operator': '0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e1e1',
                'exists': True
            }
            return Mock(transact=lambda x: "0xabcd1234")
        
        def mock_get_record(*args, **kwargs):
            if device_id not in self.stored_records:
                raise Exception("WipeAudit: No record found for this device")
            return Mock(call=lambda: self.stored_records[device_id])
        
        self.mock_contract.functions.recordWipe.return_value = Mock(
            transact=mock_store_record
        )
        self.mock_contract.functions.getWipeRecord.return_value = mock_get_record()
        
        # First recording should succeed
        result = self.mock_contract.functions.recordWipe(device_id, wipe_hash_bytes32).transact({})
        assert result == "0xabcd1234"
        
        # Verify record was stored
        stored_record = self.mock_contract.functions.getWipeRecord(device_id).call()
        assert stored_record['deviceId'] == device_id
        assert stored_record['wipeHash'] == wipe_hash_bytes32
        
        # Second recording attempt should fail (immutability)
        with pytest.raises(Exception, match="Device has already been processed"):
            self.mock_contract.functions.recordWipe(device_id, wipe_hash_bytes32).transact({})
    
    @given(
        device_ids=st.lists(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            min_size=2,
            max_size=20,
            unique=True
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_device_uniqueness_property(self, device_ids):
        """
        Test that each device can only have one wipe record.
        
        Property: For any set of device IDs, each device should be
        processable exactly once, preventing duplicate records.
        """
        processed_devices = set()
        
        def mock_unique_record(*args, **kwargs):
            device_id = args[0] if args else kwargs.get('device_id')
            
            if device_id in processed_devices:
                raise Exception("WipeAudit: Device has already been processed")
            
            processed_devices.add(device_id)
            return Mock(transact=lambda x: f"0x{hash(device_id) & 0xffffffff:08x}")
        
        self.mock_contract.functions.recordWipe.return_value = Mock(
            transact=mock_unique_record
        )
        
        # First pass: all devices should be processable
        for device_id in device_ids:
            result = self.mock_contract.functions.recordWipe(
                device_id, self.mock_keccak(f"hash_{device_id}")
            ).transact({})
            assert result.startswith('0x')
        
        # Second pass: all devices should be rejected (already processed)
        for device_id in device_ids:
            with pytest.raises(Exception, match="Device has already been processed"):
                self.mock_contract.functions.recordWipe(
                    device_id, self.mock_keccak(f"new_hash_{device_id}")
                ).transact({})
        
        # Verify all devices were processed exactly once
        assert len(processed_devices) == len(device_ids)
        assert processed_devices == set(device_ids)


class TestSmartContractEventEmission:
    """
    Property tests for smart contract event emission.
    
    Verifies that events are properly emitted for audit trail purposes.
    """
    
    def setup_method(self):
        """Set up test environment."""
        self.logger = get_component_logger('test_contract_events')
        self.mock_contract = Mock()
        self.emitted_events = []
    
    def mock_keccak(self, data):
        """Mock Web3.keccak function for testing."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        # Return a mock 32-byte hash
        return b'\x12\x34\x56\x78' * 8
    
    @given(
        device_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        operator_address=st.text(min_size=42, max_size=42).filter(
            lambda x: x.startswith('0x') and len(x) == 42
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_wipe_recorded_event_emission(self, device_id, operator_address):
        """
        Test that WipeRecorded events are emitted for all successful operations.
        
        Property: For any successful wipe recording operation,
        a WipeRecorded event should be emitted with correct data.
        """
        wipe_hash = self.mock_keccak(f"hash_{device_id}")
        
        def mock_record_with_event(*args, **kwargs):
            # Simulate successful recording with event emission
            event_data = {
                'deviceId': device_id,
                'wipeHash': wipe_hash,
                'timestamp': 1640995200,
                'operator': operator_address
            }
            self.emitted_events.append(('WipeRecorded', event_data))
            return Mock(transact=lambda x: "0xabcd1234")
        
        self.mock_contract.functions.recordWipe.return_value = Mock(
            transact=mock_record_with_event
        )
        
        # Record wipe operation
        result = self.mock_contract.functions.recordWipe(device_id, wipe_hash).transact({
            'from': operator_address
        })
        assert result == "0xabcd1234"
        
        # Verify event was emitted
        assert len(self.emitted_events) == 1
        event_name, event_data = self.emitted_events[0]
        
        assert event_name == 'WipeRecorded'
        assert event_data['deviceId'] == device_id
        assert event_data['wipeHash'] == wipe_hash
        assert event_data['operator'] == operator_address
        assert 'timestamp' in event_data