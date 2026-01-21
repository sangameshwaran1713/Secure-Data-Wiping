#!/usr/bin/env python3
"""
Smart Contract Deployment Script for Ganache

This script deploys the WipeAuditContract to a local Ganache blockchain instance.
It handles contract compilation, deployment, and configuration file generation.

Requirements:
- Ganache running on localhost:8545
- Solidity compiler (solc) available
- Web3.py for blockchain interaction

Usage:
    python scripts/deploy_contract.py
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from secure_data_wiping.utils.logging_config import get_component_logger
from secure_data_wiping.utils.config import get_config


class ContractDeployer:
    """
    Handles deployment of smart contracts to Ganache blockchain.
    
    This class manages the complete deployment workflow:
    1. Connect to Ganache
    2. Compile Solidity contract
    3. Deploy contract to blockchain
    4. Generate configuration files
    5. Verify deployment
    """
    
    def __init__(self, ganache_url: str = "http://localhost:8545"):
        """
        Initialize the contract deployer.
        
        Args:
            ganache_url: URL of the Ganache blockchain instance
        """
        self.logger = get_component_logger('contract_deployer')
        self.ganache_url = ganache_url
        self.web3 = None
        self.contract_source_path = project_root / "contracts" / "WipeAuditContract.sol"
        self.config_dir = project_root / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Contract deployment results
        self.contract_address = None
        self.contract_abi = None
        self.deployment_tx_hash = None
        self.deployment_block = None
        
    def connect_to_ganache(self) -> bool:
        """
        Connect to the Ganache blockchain instance.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Import web3 here to avoid import issues during testing
            from web3 import Web3
            
            self.logger.info(f"Connecting to Ganache at {self.ganache_url}")
            self.web3 = Web3(Web3.HTTPProvider(self.ganache_url))
            
            # Test connection
            if not self.web3.is_connected():
                self.logger.error("Failed to connect to Ganache")
                return False
            
            # Get network info
            chain_id = self.web3.eth.chain_id
            block_number = self.web3.eth.block_number
            accounts = self.web3.eth.accounts
            
            self.logger.info(f"Connected to Ganache successfully")
            self.logger.info(f"Chain ID: {chain_id}")
            self.logger.info(f"Current block: {block_number}")
            self.logger.info(f"Available accounts: {len(accounts)}")
            
            if len(accounts) == 0:
                self.logger.error("No accounts available in Ganache")
                return False
            
            # Set default account for deployment
            self.web3.eth.default_account = accounts[0]
            self.logger.info(f"Using account for deployment: {accounts[0]}")
            
            return True
            
        except ImportError as e:
            self.logger.error(f"Web3 import failed: {e}")
            self.logger.error("Please install web3: pip install web3")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Ganache: {e}")
            self.logger.error("Make sure Ganache is running on localhost:8545")
            return False
    
    def compile_contract(self) -> bool:
        """
        Compile the Solidity smart contract.
        
        For this academic project, we'll use a simplified approach
        and provide the ABI and bytecode directly since we have
        the complete contract source.
        
        Returns:
            bool: True if compilation successful, False otherwise
        """
        try:
            self.logger.info("Compiling WipeAuditContract.sol using py-solc-x")

            # Use py-solc-x to compile the Solidity contract with a compatible solc version
            try:
                from solcx import compile_standard, install_solc, set_solc_version
            except Exception:
                self.logger.error("py-solc-x is not installed. Please install with: pip install py-solc-x")
                return False

            # Ensure a 0.8.x compiler is installed
            solc_version = "0.8.20"
            try:
                install_solc(solc_version)
            except Exception:
                # If install fails, continue assuming it's already available
                pass

            set_solc_version(solc_version)

            source_path = str(self.contract_source_path)
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()

            compiled = compile_standard({
                "language": "Solidity",
                "sources": {"WipeAuditContract.sol": {"content": source}},
                "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}}
            }, allow_paths=str(self.contract_source_path.parent))

            contract_data = compiled['contracts']['WipeAuditContract.sol']['WipeAuditContract']
            self.contract_abi = contract_data['abi']
            self.contract_bytecode = '0x' + contract_data['evm']['bytecode']['object']

            self.logger.info("Contract compiled successfully with solc %s", solc_version)
            return True

        except Exception as e:
            self.logger.error(f"Contract compilation failed: {e}")
            return False
    
    def deploy_contract(self) -> bool:
        """
        Deploy the compiled contract to Ganache.
        
        Returns:
            bool: True if deployment successful, False otherwise
        """
        try:
            self.logger.info("Deploying WipeAuditContract to Ganache")
            
            # Create contract instance
            contract = self.web3.eth.contract(
                abi=self.contract_abi,
                bytecode=self.contract_bytecode
            )
            
            # Get deployment account
            deployer_account = self.web3.eth.default_account
            
            # Estimate gas for deployment
            try:
                gas_estimate = contract.constructor().estimate_gas()
                self.logger.info(f"Estimated gas for deployment: {gas_estimate}")
            except Exception as e:
                self.logger.warning(f"Could not estimate gas, using default: {e}")
                gas_estimate = 3000000  # Default gas limit
            
            # Deploy contract
            tx_hash = contract.constructor().transact({
                'from': deployer_account,
                'gas': gas_estimate + 100000,  # Add buffer
                'gasPrice': self.web3.eth.gas_price
            })
            
            self.deployment_tx_hash = tx_hash.hex()
            self.logger.info(f"Deployment transaction sent: {self.deployment_tx_hash}")
            
            # Wait for transaction receipt
            self.logger.info("Waiting for deployment confirmation...")
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status == 1:
                self.contract_address = tx_receipt.contractAddress
                self.deployment_block = tx_receipt.blockNumber
                
                self.logger.info(f"Contract deployed successfully!")
                self.logger.info(f"Contract address: {self.contract_address}")
                self.logger.info(f"Deployment block: {self.deployment_block}")
                self.logger.info(f"Gas used: {tx_receipt.gasUsed}")
                
                return True
            else:
                self.logger.error("Contract deployment failed - transaction reverted")
                return False
                
        except Exception as e:
            self.logger.error(f"Contract deployment failed: {e}")
            return False
    
    def verify_deployment(self) -> bool:
        """
        Verify that the contract was deployed correctly.
        
        Returns:
            bool: True if verification successful, False otherwise
        """
        try:
            self.logger.info("Verifying contract deployment")
            
            # Create contract instance
            contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            
            # Test basic contract functions
            try:
                # Get contract owner
                owner = contract.functions.getOwner().call()
                self.logger.info(f"Contract owner: {owner}")
                
                # Get total records (should be 0 initially)
                total_records = contract.functions.getTotalRecords().call()
                self.logger.info(f"Initial total records: {total_records}")
                
                # Get contract info
                contract_info = contract.functions.getContractInfo().call()
                self.logger.info(f"Contract info: Owner={contract_info[0]}, Records={contract_info[1]}, Version={contract_info[2]}")
                
                # Check if contract is paused (should be False initially)
                is_paused = contract.functions.isPaused().call()
                self.logger.info(f"Contract paused: {is_paused}")
                
                self.logger.info("Contract verification completed successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Contract function calls failed: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Contract verification failed: {e}")
            return False
    
    def generate_config_files(self) -> bool:
        """
        Generate configuration files for the deployed contract.
        
        Returns:
            bool: True if config generation successful, False otherwise
        """
        try:
            self.logger.info("Generating configuration files")
            
            # Contract configuration
            contract_config = {
                "contract_address": self.contract_address,
                "contract_abi": self.contract_abi,
                "deployment_info": {
                    "transaction_hash": self.deployment_tx_hash,
                    "block_number": self.deployment_block,
                    "deployer_account": self.web3.eth.default_account,
                    "deployment_timestamp": int(time.time()),
                    "ganache_url": self.ganache_url,
                    "chain_id": self.web3.eth.chain_id
                }
            }
            
            # Save contract configuration
            contract_config_path = self.config_dir / "contract_config.json"
            with open(contract_config_path, 'w') as f:
                json.dump(contract_config, f, indent=2)
            
            self.logger.info(f"Contract configuration saved to: {contract_config_path}")
            
            # Blockchain configuration
            blockchain_config = {
                "ganache": {
                    "url": self.ganache_url,
                    "chain_id": self.web3.eth.chain_id,
                    "accounts": self.web3.eth.accounts[:5],  # First 5 accounts
                    "default_account": self.web3.eth.default_account
                },
                "contract": {
                    "address": self.contract_address,
                    "name": "WipeAuditContract",
                    "version": "1.0.0"
                }
            }
            
            # Save blockchain configuration
            blockchain_config_path = self.config_dir / "blockchain_config.json"
            with open(blockchain_config_path, 'w') as f:
                json.dump(blockchain_config, f, indent=2)
            
            self.logger.info(f"Blockchain configuration saved to: {blockchain_config_path}")
            
            # Generate Python configuration module
            python_config = f'''"""
Auto-generated configuration for WipeAuditContract deployment.
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

# Contract Configuration
CONTRACT_ADDRESS = "{self.contract_address}"
GANACHE_URL = "{self.ganache_url}"
CHAIN_ID = {self.web3.eth.chain_id}

# Deployment Information
DEPLOYMENT_TX_HASH = "{self.deployment_tx_hash}"
DEPLOYMENT_BLOCK = {self.deployment_block}
DEPLOYER_ACCOUNT = "{self.web3.eth.default_account}"

# Contract ABI (for Python integration)
CONTRACT_ABI = {json.dumps(self.contract_abi, indent=2)}
'''
            
            python_config_path = self.config_dir / "contract_config.py"
            with open(python_config_path, 'w') as f:
                f.write(python_config)
            
            self.logger.info(f"Python configuration saved to: {python_config_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration file generation failed: {e}")
            return False
    
    def deploy(self) -> bool:
        """
        Execute the complete deployment workflow.
        
        Returns:
            bool: True if deployment successful, False otherwise
        """
        self.logger.info("Starting smart contract deployment workflow")
        
        # Step 1: Connect to Ganache
        if not self.connect_to_ganache():
            return False
        
        # Step 2: Compile contract
        if not self.compile_contract():
            return False
        
        # Step 3: Deploy contract
        if not self.deploy_contract():
            return False
        
        # Step 4: Verify deployment
        if not self.verify_deployment():
            return False
        
        # Step 5: Generate configuration files
        if not self.generate_config_files():
            return False
        
        self.logger.info("Smart contract deployment completed successfully!")
        self.logger.info(f"Contract address: {self.contract_address}")
        self.logger.info(f"Configuration files saved in: {self.config_dir}")
        
        return True


def main():
    """Main deployment function."""
    # Avoid Unicode symbols that may not be supported in all consoles
    print("WipeAuditContract Deployment Script")
    print("=" * 50)
    
    # Check if Ganache URL is provided
    ganache_url = os.getenv('GANACHE_URL', 'http://localhost:8545')
    
    # Create deployer
    deployer = ContractDeployer(ganache_url)
    
    # Execute deployment
    success = deployer.deploy()
    
    if success:
        print("\nDeployment completed successfully!")
        print(f"Contract Address: {deployer.contract_address}")
        print(f"Transaction Hash: {deployer.deployment_tx_hash}")
        print(f"Config files saved in: {deployer.config_dir}")
        print("\nYour smart contract is ready for use.")
        return 0
    else:
        print("\nDeployment failed!")
        print("Please check the logs and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())