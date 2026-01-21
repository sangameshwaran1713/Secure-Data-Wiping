#!/usr/bin/env python3
"""
Unit Tests for Smart Contract Deployment

Tests the contract deployment process and verifies that the deployed
contract functions correctly.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from scripts.deploy_contract import ContractDeployer
from scripts.start_ganache import GanacheManager
from secure_data_wiping.utils.logging_config import get_component_logger


class TestContractDeployment:
    """
    Unit tests for smart contract deployment functionality.
    
    Tests Task 2.4: Write unit tests for smart contract deployment
    - Test contract deployment process and accessibility
    - Test ABI and address file generation
    - Requirements: 4.6, 9.8
    """
    
    def setup_method(self):
        """Set up test environment for each test method."""
        self.logger = get_component_logger('test_deployment')
        self.test_ganache_url = "http://localhost:8545"
        
        # Create mock Web3 instance
        self.mock_web3 = Mock()
        self.mock_web3.is_connected.return_value = True
        self.mock_web3.eth.chain_id = 1337
        self.mock_web3.eth.block_number = 1
        self.mock_web3.eth.accounts = [
            "0x742d35Cc6634C0532925a3b8D4C0C8b3C2e1e1e1",
            "0x8ba1f109551bD432803012645Hac136c9.c3e1e1",
            "0x123456789abcdef123456789abcdef123456789a"
        ]
        self.mock_web3.eth.default_account = self.mock_web3.eth.accounts[0]
        self.mock_web3.eth.gas_price = 20000000000
        
        # Mock transaction receipt
        self.mock_tx_receipt = Mock()
        self.mock_tx_receipt.status = 1
        self.mock_tx_receipt.contractAddress = "0xContractAddress123456789abcdef"
        self.mock_tx_receipt.blockNumber = 2
        self.mock_tx_receipt.gasUsed = 2500000
        
        self.mock_web3.eth.wait_for_transaction_receipt.return_value = self.mock_tx_receipt
    
    def test_contract_deployer_initialization(self):
        """Test ContractDeployer initialization."""
        deployer = ContractDeployer(self.test_ganache_url)
        
        assert deployer.ganache_url == self.test_ganache_url
        assert deployer.contract_address is None
        assert deployer.contract_abi is None
        assert deployer.deployment_tx_hash is None
        assert deployer.deployment_block is None
        
        # Check paths
        assert deployer.contract_source_path.name == "WipeAuditContract.sol"
        assert deployer.config_dir.name == "config"
    
    @patch('scripts.deploy_contract.Web3')
    def test_connect_to_ganache_success(self, mock_web3_class):
        """Test successful connection to Ganache."""
        mock_web3_class.return_value = self.mock_web3
        
        deployer = ContractDeployer(self.test_ganache_url)
        result = deployer.connect_to_ganache()
        
        assert result is True
        assert deployer.web3 == self.mock_web3
        
        # Verify Web3 was called correctly
        mock_web3_class.assert_called_once()
        self.mock_web3.is_connected.assert_called_once()
    
    @patch('scripts.deploy_contract.Web3')
    def test_connect_to_ganache_failure(self, mock_web3_class):
        """Test failed connection to Ganache."""
        self.mock_web3.is_connected.return_value = False
        mock_web3_class.return_value = self.mock_web3
        
        deployer = ContractDeployer(self.test_ganache_url)
        result = deployer.connect_to_ganache()
        
        assert result is False
    
    @patch('scripts.deploy_contract.Web3')
    def test_connect_to_ganache_no_accounts(self, mock_web3_class):
        """Test connection failure when no accounts available."""
        self.mock_web3.eth.accounts = []
        mock_web3_class.return_value = self.mock_web3
        
        deployer = ContractDeployer(self.test_ganache_url)
        result = deployer.connect_to_ganache()
        
        assert result is False
    
    def test_compile_contract_success(self):
        """Test successful contract compilation."""
        deployer = ContractDeployer(self.test_ganache_url)
        result = deployer.compile_contract()
        
        assert result is True
        assert deployer.contract_abi is not None
        assert deployer.contract_bytecode is not None
        
        # Verify ABI contains expected functions
        function_names = [item['name'] for item in deployer.contract_abi if item['type'] == 'function']
        expected_functions = [
            'recordWipe', 'getWipeRecord', 'verifyWipe', 'authorizeOperator',
            'isAuthorizedOperator', 'getOwner', 'getTotalRecords'
        ]
        
        for func_name in expected_functions:
            assert func_name in function_names, f"Function {func_name} not found in ABI"
    
    @patch('scripts.deploy_contract.Web3')
    def test_deploy_contract_success(self, mock_web3_class):
        """Test successful contract deployment."""
        # Setup mocks
        mock_web3_class.return_value = self.mock_web3
        
        mock_contract = Mock()
        mock_constructor = Mock()
        mock_constructor.estimate_gas.return_value = 2500000
        mock_constructor.transact.return_value = Mock(hex=lambda: "0xTransactionHash123")
        mock_contract.constructor.return_value = mock_constructor
        
        self.mock_web3.eth.contract.return_value = mock_contract
        
        # Test deployment
        deployer = ContractDeployer(self.test_ganache_url)
        deployer.connect_to_ganache()
        deployer.compile_contract()
        
        result = deployer.deploy_contract()
        
        assert result is True
        assert deployer.contract_address == self.mock_tx_receipt.contractAddress
        assert deployer.deployment_block == self.mock_tx_receipt.blockNumber
        assert deployer.deployment_tx_hash == "0xTransactionHash123"
    
    @patch('scripts.deploy_contract.Web3')
    def test_deploy_contract_failure(self, mock_web3_class):
        """Test contract deployment failure."""
        # Setup mocks for failure
        mock_web3_class.return_value = self.mock_web3
        
        # Make transaction receipt indicate failure
        self.mock_tx_receipt.status = 0
        
        mock_contract = Mock()
        mock_constructor = Mock()
        mock_constructor.estimate_gas.return_value = 2500000
        mock_constructor.transact.return_value = Mock(hex=lambda: "0xFailedTx")
        mock_contract.constructor.return_value = mock_constructor
        
        self.mock_web3.eth.contract.return_value = mock_contract
        
        # Test deployment
        deployer = ContractDeployer(self.test_ganache_url)
        deployer.connect_to_ganache()
        deployer.compile_contract()
        
        result = deployer.deploy_contract()
        
        assert result is False
    
    @patch('scripts.deploy_contract.Web3')
    def test_verify_deployment_success(self, mock_web3_class):
        """Test successful deployment verification."""
        # Setup mocks
        mock_web3_class.return_value = self.mock_web3
        
        mock_contract = Mock()
        mock_contract.functions.getOwner.return_value.call.return_value = self.mock_web3.eth.default_account
        mock_contract.functions.getTotalRecords.return_value.call.return_value = 0
        mock_contract.functions.getContractInfo.return_value.call.return_value = (
            self.mock_web3.eth.default_account, 0, "1.0.0"
        )
        mock_contract.functions.isPaused.return_value.call.return_value = False
        
        self.mock_web3.eth.contract.return_value = mock_contract
        
        # Test verification
        deployer = ContractDeployer(self.test_ganache_url)
        deployer.connect_to_ganache()
        deployer.compile_contract()
        deployer.contract_address = "0xTestContract"
        
        result = deployer.verify_deployment()
        
        assert result is True
    
    @patch('scripts.deploy_contract.Web3')
    def test_verify_deployment_failure(self, mock_web3_class):
        """Test deployment verification failure."""
        # Setup mocks for failure
        mock_web3_class.return_value = self.mock_web3
        
        mock_contract = Mock()
        mock_contract.functions.getOwner.return_value.call.side_effect = Exception("Contract call failed")
        
        self.mock_web3.eth.contract.return_value = mock_contract
        
        # Test verification
        deployer = ContractDeployer(self.test_ganache_url)
        deployer.connect_to_ganache()
        deployer.compile_contract()
        deployer.contract_address = "0xTestContract"
        
        result = deployer.verify_deployment()
        
        assert result is False
    
    @patch('scripts.deploy_contract.Web3')
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_generate_config_files_success(self, mock_json_dump, mock_open, mock_web3_class):
        """Test successful configuration file generation."""
        # Setup mocks
        mock_web3_class.return_value = self.mock_web3
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Test config generation
        deployer = ContractDeployer(self.test_ganache_url)
        deployer.connect_to_ganache()
        deployer.compile_contract()
        deployer.contract_address = "0xTestContract"
        deployer.deployment_tx_hash = "0xTestTx"
        deployer.deployment_block = 2
        
        result = deployer.generate_config_files()
        
        assert result is True
        
        # Verify files were written
        assert mock_open.call_count >= 3  # contract_config.json, blockchain_config.json, contract_config.py
        assert mock_json_dump.call_count >= 2  # JSON files
    
    @patch('scripts.deploy_contract.Web3')
    def test_full_deployment_workflow(self, mock_web3_class):
        """Test the complete deployment workflow."""
        # Setup comprehensive mocks
        mock_web3_class.return_value = self.mock_web3
        
        mock_contract = Mock()
        mock_constructor = Mock()
        mock_constructor.estimate_gas.return_value = 2500000
        mock_constructor.transact.return_value = Mock(hex=lambda: "0xDeploymentTx")
        mock_contract.constructor.return_value = mock_constructor
        
        # Mock contract functions for verification
        mock_contract.functions.getOwner.return_value.call.return_value = self.mock_web3.eth.default_account
        mock_contract.functions.getTotalRecords.return_value.call.return_value = 0
        mock_contract.functions.getContractInfo.return_value.call.return_value = (
            self.mock_web3.eth.default_account, 0, "1.0.0"
        )
        mock_contract.functions.isPaused.return_value.call.return_value = False
        
        self.mock_web3.eth.contract.return_value = mock_contract
        
        # Mock file operations
        with patch('builtins.open', create=True), \
             patch('json.dump'), \
             patch('pathlib.Path.mkdir'):
            
            # Test full deployment
            deployer = ContractDeployer(self.test_ganache_url)
            result = deployer.deploy()
            
            assert result is True
            assert deployer.contract_address == self.mock_tx_receipt.contractAddress
            assert deployer.deployment_tx_hash == "0xDeploymentTx"
            assert deployer.deployment_block == self.mock_tx_receipt.blockNumber


class TestGanacheManager:
    """
    Unit tests for Ganache blockchain management.
    
    Tests Ganache startup and configuration functionality.
    """
    
    def setup_method(self):
        """Set up test environment."""
        self.logger = get_component_logger('test_ganache')
    
    def test_ganache_manager_initialization(self):
        """Test GanacheManager initialization."""
        manager = GanacheManager()
        
        assert manager.ganache_process is None
        assert manager.config is not None
        
        # Check default configuration
        config = manager.config
        assert config['host'] == '127.0.0.1'
        assert config['port'] == 8545
        assert config['network_id'] == 1337
        assert config['accounts'] == 10
        assert config['ether'] == 100
    
    def test_build_ganache_command(self):
        """Test Ganache command building."""
        manager = GanacheManager()
        cmd = manager.build_ganache_command()
        
        assert 'ganache-cli' in cmd
        assert '--host' in cmd
        assert '127.0.0.1' in cmd
        assert '--port' in cmd
        assert '8545' in cmd
        assert '--networkId' in cmd
        assert '1337' in cmd
        assert '--deterministic' in cmd
    
    @patch('subprocess.run')
    def test_check_ganache_cli_installed_success(self, mock_run):
        """Test successful Ganache CLI detection."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Ganache CLI v6.12.2"
        mock_run.return_value = mock_result
        
        manager = GanacheManager()
        result = manager.check_ganache_cli_installed()
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_check_ganache_cli_installed_failure(self, mock_run):
        """Test Ganache CLI not found."""
        mock_run.side_effect = FileNotFoundError("ganache-cli not found")
        
        manager = GanacheManager()
        result = manager.check_ganache_cli_installed()
        
        assert result is False
    
    @patch('requests.post')
    def test_is_ganache_running_success(self, mock_post):
        """Test successful Ganache detection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        manager = GanacheManager()
        result = manager.is_ganache_running()
        
        assert result is True
    
    @patch('requests.post')
    def test_is_ganache_running_failure(self, mock_post):
        """Test Ganache not running detection."""
        mock_post.side_effect = Exception("Connection refused")
        
        manager = GanacheManager()
        result = manager.is_ganache_running()
        
        assert result is False
    
    def test_get_connection_info(self):
        """Test connection info generation."""
        manager = GanacheManager()
        conn_info = manager.get_connection_info()
        
        assert 'url' in conn_info
        assert 'host' in conn_info
        assert 'port' in conn_info
        assert 'network_id' in conn_info
        assert 'chain_id' in conn_info
        
        assert conn_info['url'] == "http://127.0.0.1:8545"
        assert conn_info['host'] == '127.0.0.1'
        assert conn_info['port'] == 8545
        assert conn_info['network_id'] == 1337
    
    @patch('builtins.open', create=True)
    @patch('json.dump')
    @patch('pathlib.Path.mkdir')
    def test_save_connection_config(self, mock_mkdir, mock_json_dump, mock_open):
        """Test connection configuration saving."""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        manager = GanacheManager()
        result = manager.save_connection_config()
        
        assert result is True
        mock_mkdir.assert_called_once()
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])