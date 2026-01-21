#!/usr/bin/env python3
"""
Complete Blockchain Setup Script

This script provides a complete setup workflow for the secure data wiping
blockchain infrastructure:

1. Start Ganache blockchain
2. Deploy WipeAuditContract
3. Verify deployment
4. Generate configuration files
5. Run basic tests

Usage:
    python scripts/setup_blockchain.py [--skip-ganache] [--skip-tests]
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.start_ganache import GanacheManager
from scripts.deploy_contract import ContractDeployer
from secure_data_wiping.utils.logging_config import get_component_logger


class BlockchainSetup:
    """
    Complete blockchain setup orchestrator.
    
    Manages the entire workflow from Ganache startup to contract deployment
    and verification.
    """
    
    def __init__(self, skip_ganache: bool = False, skip_tests: bool = False):
        """
        Initialize the blockchain setup.
        
        Args:
            skip_ganache: Skip Ganache startup (assume already running)
            skip_tests: Skip post-deployment tests
        """
        self.logger = get_component_logger('blockchain_setup')
        self.skip_ganache = skip_ganache
        self.skip_tests = skip_tests
        
        self.ganache_manager = None
        self.contract_deployer = None
        
    def setup_ganache(self) -> bool:
        """
        Set up Ganache blockchain.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if self.skip_ganache:
            self.logger.info("Skipping Ganache startup (--skip-ganache flag)")
            return True
        
        try:
            self.logger.info("Setting up Ganache blockchain...")
            
            self.ganache_manager = GanacheManager()
            
            # Start Ganache
            if not self.ganache_manager.start_ganache():
                self.logger.error("Failed to start Ganache")
                return False
            
            # Save configuration
            if not self.ganache_manager.save_connection_config():
                self.logger.warning("Failed to save Ganache configuration")
            
            # Wait for blockchain to be ready
            self.logger.info("Waiting for blockchain to be ready...")
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ganache setup failed: {e}")
            return False
    
    def deploy_contract(self) -> bool:
        """
        Deploy the WipeAuditContract.
        
        Returns:
            bool: True if deployment successful, False otherwise
        """
        try:
            self.logger.info("Deploying WipeAuditContract...")
            
            # Get Ganache URL
            if self.ganache_manager:
                conn_info = self.ganache_manager.get_connection_info()
                ganache_url = conn_info['url']
            else:
                ganache_url = "http://localhost:8545"
            
            self.contract_deployer = ContractDeployer(ganache_url)
            
            # Execute deployment
            if not self.contract_deployer.deploy():
                self.logger.error("Contract deployment failed")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Contract deployment failed: {e}")
            return False
    
    def run_basic_tests(self) -> bool:
        """
        Run basic tests to verify the deployment.
        
        Returns:
            bool: True if tests pass, False otherwise
        """
        if self.skip_tests:
            self.logger.info("Skipping post-deployment tests (--skip-tests flag)")
            return True
        
        try:
            self.logger.info("Running basic deployment tests...")
            
            # Import web3 for testing
            from web3 import Web3
            
            # Get connection info
            if self.ganache_manager:
                conn_info = self.ganache_manager.get_connection_info()
                ganache_url = conn_info['url']
            else:
                ganache_url = "http://localhost:8545"
            
            # Connect to blockchain
            web3 = Web3(Web3.HTTPProvider(ganache_url))
            
            if not web3.is_connected():
                self.logger.error("Cannot connect to blockchain for testing")
                return False
            
            # Create contract instance
            contract = web3.eth.contract(
                address=self.contract_deployer.contract_address,
                abi=self.contract_deployer.contract_abi
            )
            
            # Test 1: Check contract owner
            owner = contract.functions.getOwner().call()
            expected_owner = web3.eth.default_account or web3.eth.accounts[0]
            
            if owner.lower() == expected_owner.lower():
                self.logger.info("✅ Test 1 PASSED: Contract owner is correct")
            else:
                self.logger.error(f"❌ Test 1 FAILED: Expected owner {expected_owner}, got {owner}")
                return False
            
            # Test 2: Check initial state
            total_records = contract.functions.getTotalRecords().call()
            if total_records == 0:
                self.logger.info("✅ Test 2 PASSED: Initial record count is zero")
            else:
                self.logger.error(f"❌ Test 2 FAILED: Expected 0 records, got {total_records}")
                return False
            
            # Test 3: Check contract info
            contract_info = contract.functions.getContractInfo().call()
            if contract_info[2] == "1.0.0":  # Version
                self.logger.info("✅ Test 3 PASSED: Contract version is correct")
            else:
                self.logger.error(f"❌ Test 3 FAILED: Expected version 1.0.0, got {contract_info[2]}")
                return False
            
            # Test 4: Check pause state
            is_paused = contract.functions.isPaused().call()
            if not is_paused:
                self.logger.info("✅ Test 4 PASSED: Contract is not paused initially")
            else:
                self.logger.error("❌ Test 4 FAILED: Contract should not be paused initially")
                return False
            
            # Test 5: Check authorization (owner should be authorized)
            is_authorized = contract.functions.isAuthorizedOperator(owner).call()
            if is_authorized:
                self.logger.info("✅ Test 5 PASSED: Contract owner is authorized operator")
            else:
                self.logger.error("❌ Test 5 FAILED: Contract owner should be authorized operator")
                return False
            
            self.logger.info("🎉 All basic tests passed!")
            return True
            
        except Exception as e:
            self.logger.error(f"Basic tests failed: {e}")
            return False
    
    def generate_summary(self) -> dict:
        """
        Generate a summary of the setup process.
        
        Returns:
            dict: Setup summary information
        """
        summary = {
            'ganache': {
                'status': 'running' if self.ganache_manager else 'skipped',
                'url': None,
                'network_id': None
            },
            'contract': {
                'status': 'deployed' if self.contract_deployer else 'failed',
                'address': None,
                'transaction_hash': None
            },
            'config_files': [],
            'next_steps': []
        }
        
        if self.ganache_manager:
            conn_info = self.ganache_manager.get_connection_info()
            summary['ganache']['url'] = conn_info['url']
            summary['ganache']['network_id'] = conn_info['network_id']
        
        if self.contract_deployer:
            summary['contract']['address'] = self.contract_deployer.contract_address
            summary['contract']['transaction_hash'] = self.contract_deployer.deployment_tx_hash
            
            # List generated config files
            config_dir = project_root / "config"
            if config_dir.exists():
                for config_file in config_dir.glob("*.json"):
                    summary['config_files'].append(str(config_file))
                for config_file in config_dir.glob("*.py"):
                    summary['config_files'].append(str(config_file))
        
        # Next steps
        summary['next_steps'] = [
            "Run property tests: python test_smart_contract_simple.py",
            "Start main application: python main.py",
            "Run full test suite: python -m pytest tests/",
            "Deploy to production blockchain (when ready)"
        ]
        
        return summary
    
    def cleanup(self):
        """Clean up resources."""
        if self.ganache_manager and not self.skip_ganache:
            self.logger.info("Cleaning up Ganache...")
            self.ganache_manager.stop_ganache()
    
    def setup(self) -> bool:
        """
        Execute the complete blockchain setup workflow.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        self.logger.info("Starting complete blockchain setup workflow")
        
        try:
            # Step 1: Setup Ganache
            if not self.setup_ganache():
                return False
            
            # Step 2: Deploy contract
            if not self.deploy_contract():
                return False
            
            # Step 3: Run basic tests
            if not self.run_basic_tests():
                return False
            
            self.logger.info("Blockchain setup completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Blockchain setup failed: {e}")
            return False


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Complete blockchain setup for secure data wiping project"
    )
    parser.add_argument(
        '--skip-ganache',
        action='store_true',
        help='Skip Ganache startup (assume already running)'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip post-deployment tests'
    )
    
    args = parser.parse_args()
    
    print("🚀 Complete Blockchain Setup")
    print("=" * 50)
    print("📋 This script will:")
    print("   1. Start Ganache blockchain (unless --skip-ganache)")
    print("   2. Deploy WipeAuditContract")
    print("   3. Verify deployment")
    print("   4. Generate configuration files")
    print("   5. Run basic tests (unless --skip-tests)")
    print("=" * 50)
    
    # Create setup manager
    setup = BlockchainSetup(
        skip_ganache=args.skip_ganache,
        skip_tests=args.skip_tests
    )
    
    try:
        # Execute setup
        success = setup.setup()
        
        # Generate summary
        summary = setup.generate_summary()
        
        print("\n" + "=" * 50)
        print("📊 SETUP SUMMARY")
        print("=" * 50)
        
        # Ganache status
        ganache_status = summary['ganache']['status']
        if ganache_status == 'running':
            print(f"🔗 Ganache: ✅ Running on {summary['ganache']['url']}")
            print(f"   Network ID: {summary['ganache']['network_id']}")
        elif ganache_status == 'skipped':
            print("🔗 Ganache: ⏭️  Skipped")
        else:
            print("🔗 Ganache: ❌ Failed")
        
        # Contract status
        contract_status = summary['contract']['status']
        if contract_status == 'deployed':
            print(f"📄 Contract: ✅ Deployed at {summary['contract']['address']}")
            print(f"   Transaction: {summary['contract']['transaction_hash']}")
        else:
            print("📄 Contract: ❌ Failed")
        
        # Config files
        if summary['config_files']:
            print("📁 Configuration Files:")
            for config_file in summary['config_files']:
                print(f"   📄 {config_file}")
        
        if success:
            print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("\n🎯 Next Steps:")
            for step in summary['next_steps']:
                print(f"   • {step}")
            
            if not args.skip_ganache:
                print("\n⚠️  Important:")
                print("   Keep Ganache running for the application to work")
                print("   Stop with: Ctrl+C or close this terminal")
            
            return 0
        else:
            print("\n❌ SETUP FAILED!")
            print("🔧 Please check the logs and try again.")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted by user")
        setup.cleanup()
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        setup.cleanup()
        return 1
    finally:
        if not args.skip_ganache:
            # Keep Ganache running if started successfully
            if setup.ganache_manager and setup.ganache_manager.ganache_process:
                try:
                    print("\n⏳ Keeping Ganache running... Press Ctrl+C to stop")
                    while setup.ganache_manager.ganache_process.poll() is None:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping Ganache...")
                    setup.cleanup()


if __name__ == "__main__":
    sys.exit(main())