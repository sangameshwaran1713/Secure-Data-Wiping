"""
Pytest Configuration and Fixtures

Common test fixtures and configuration for the secure data wiping system tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import sqlite3
from datetime import datetime

from secure_data_wiping.utils.config import ConfigManager, SystemConfig
from secure_data_wiping.utils.data_models import DeviceInfo, WipeConfig, WipeMethod, DeviceType
from secure_data_wiping.database.database_manager import DatabaseManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    return SystemConfig(
        ganache_url="http://127.0.0.1:7545",
        contract_address="0x1234567890123456789012345678901234567890",
        default_operator="test_operator",
        log_level="DEBUG",
        certificate_template="test",
        max_retry_attempts=2,
        database_path=str(Path(temp_dir) / "test.db"),
        certificates_dir=str(Path(temp_dir) / "certificates"),
        logs_dir=str(Path(temp_dir) / "logs")
    )


@pytest.fixture
def config_manager(test_config, temp_dir):
    """Create a test configuration manager."""
    config_file = Path(temp_dir) / "test_config.yaml"
    manager = ConfigManager(str(config_file))
    manager._config = test_config
    return manager


@pytest.fixture
def test_database(test_config):
    """Create a test database."""
    db_manager = DatabaseManager(test_config.database_path)
    yield db_manager
    # Cleanup is handled by temp_dir fixture


@pytest.fixture
def sample_device_info():
    """Create sample device information for testing."""
    return DeviceInfo(
        device_id="TEST_DEVICE_001",
        device_type=DeviceType.SSD,
        manufacturer="Samsung",
        model="980 PRO",
        serial_number="S123456789",
        capacity=1000000000000,  # 1TB
        connection_type="NVMe",
        file_system="NTFS",
        mount_point="/dev/nvme0n1"
    )


@pytest.fixture
def sample_wipe_config():
    """Create sample wipe configuration for testing."""
    return WipeConfig(
        method=WipeMethod.NIST_CLEAR,
        passes=3,
        verify_wipe=True,
        pattern=b'\x00',
        block_size=4096,
        timeout=1800
    )


@pytest.fixture
def mock_web3():
    """Create a mock Web3 instance for blockchain testing."""
    mock_w3 = Mock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 1337  # Ganache default
    mock_w3.eth.accounts = [
        "0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e1e1",
        "0x8ba1f109551bD432803012645Hac136c5c8b3c2e1e1e1"
    ]
    mock_w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
    
    # Mock contract
    mock_contract = Mock()
    mock_contract.functions.recordWipe.return_value.transact.return_value = "0xabcd1234"
    mock_contract.functions.getWipeRecord.return_value.call.return_value = {
        'deviceId': 'TEST_DEVICE_001',
        'wipeHash': b'\x12\x34\x56\x78',
        'timestamp': int(datetime.now().timestamp()),
        'operator': '0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e1e1',
        'exists': True
    }
    
    mock_w3.eth.contract.return_value = mock_contract
    mock_w3.eth.get_transaction_receipt.return_value = {
        'transactionHash': '0xabcd1234',
        'blockNumber': 12345,
        'gasUsed': 50000,
        'status': 1
    }
    
    return mock_w3


@pytest.fixture
def mock_ganache_process():
    """Create a mock Ganache process for testing."""
    mock_process = Mock()
    mock_process.poll.return_value = None  # Process is running
    mock_process.returncode = None
    mock_process.pid = 12345
    return mock_process


@pytest.fixture
def sample_operation_data():
    """Create sample operation data for database testing."""
    return {
        'operation_id': 'test_op_001',
        'device_id': 'TEST_DEVICE_001',
        'device_type': 'ssd',
        'device_manufacturer': 'Samsung',
        'device_model': '980 PRO',
        'device_serial': 'S123456789',
        'device_capacity': 1000000000000,
        'wipe_method': 'clear',
        'start_time': datetime.now().isoformat(),
        'passes_completed': 3,
        'success': True,
        'wipe_hash': 'abc123def456',
        'operator_id': 'test_operator'
    }


@pytest.fixture
def sample_blockchain_data():
    """Create sample blockchain data for testing."""
    return {
        'operation_id': 'test_op_001',
        'device_id': 'TEST_DEVICE_001',
        'transaction_hash': '0xabcd1234567890',
        'block_number': 12345,
        'gas_used': 50000,
        'confirmation_count': 6,
        'contract_address': '0x1234567890123456789012345678901234567890',
        'operator_address': '0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e1e1'
    }


@pytest.fixture
def sample_certificate_data():
    """Create sample certificate data for testing."""
    return {
        'operation_id': 'test_op_001',
        'certificate_path': '/tmp/certificates/test_cert_001.pdf',
        'certificate_hash': 'cert_hash_123',
        'qr_code_data': 'https://verify.example.com/cert/test_op_001'
    }


# Property-based testing strategies
@pytest.fixture
def device_id_strategy():
    """Hypothesis strategy for generating device IDs."""
    from hypothesis import strategies as st
    return st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'),
        min_size=5,
        max_size=50
    ).filter(lambda x: x and not x.isspace())


@pytest.fixture
def device_type_strategy():
    """Hypothesis strategy for generating device types."""
    from hypothesis import strategies as st
    return st.sampled_from([dt.value for dt in DeviceType])


@pytest.fixture
def wipe_method_strategy():
    """Hypothesis strategy for generating wipe methods."""
    from hypothesis import strategies as st
    return st.sampled_from([wm.value for wm in WipeMethod])


@pytest.fixture
def positive_integer_strategy():
    """Hypothesis strategy for generating positive integers."""
    from hypothesis import strategies as st
    return st.integers(min_value=1, max_value=1000000)


# Test utilities
def create_test_database_with_data(db_path: str, operations_count: int = 5):
    """Create a test database with sample data."""
    db_manager = DatabaseManager(db_path)
    
    for i in range(operations_count):
        operation_data = {
            'operation_id': f'test_op_{i:03d}',
            'device_id': f'TEST_DEVICE_{i:03d}',
            'device_type': 'ssd',
            'wipe_method': 'clear',
            'start_time': datetime.now().isoformat(),
            'success': i % 2 == 0,  # Alternate success/failure
            'wipe_hash': f'hash_{i:03d}',
            'operator_id': 'test_operator'
        }
        db_manager.insert_wipe_operation(operation_data)
    
    return db_manager


def assert_valid_hash(hash_value: str, expected_length: int = 64):
    """Assert that a hash value is valid."""
    assert isinstance(hash_value, str)
    assert len(hash_value) == expected_length
    assert all(c in '0123456789abcdef' for c in hash_value.lower())


def assert_valid_device_id(device_id: str):
    """Assert that a device ID is valid."""
    assert isinstance(device_id, str)
    assert len(device_id) > 0
    assert not device_id.isspace()


def assert_valid_timestamp(timestamp_str: str):
    """Assert that a timestamp string is valid ISO format."""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {timestamp_str}")


# Cleanup utilities
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    # Cleanup any test files that might have been created
    test_files = [
        "test_*.db",
        "test_*.log",
        "test_*.pdf",
        "test_*.yaml",
        "test_*.json"
    ]
    
    import glob
    for pattern in test_files:
        for file_path in glob.glob(pattern):
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass  # Ignore cleanup errors