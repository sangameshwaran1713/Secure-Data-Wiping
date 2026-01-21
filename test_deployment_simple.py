#!/usr/bin/env python3
"""
Simple test runner for contract deployment tests.
Bypasses pytest to avoid web3 import issues.
"""

import sys
from pathlib import Path
sys.path.insert(0, '.')

from tests.test_contract_deployment import TestContractDeployment, TestGanacheManager
from secure_data_wiping.utils.logging_config import get_component_logger

def run_contract_deployment_tests():
    """Run contract deployment tests manually."""
    logger = get_component_logger('test_runner')
    
    print("📄 Testing Contract Deployment Functionality")
    print("=" * 60)
    
    # Create test instance
    test_instance = TestContractDeployment()
    test_instance.setup_method()
    
    success = True
    
    # Test 1: ContractDeployer initialization
    print("\n📋 Test 1: ContractDeployer initialization")
    try:
        test_instance.test_contract_deployer_initialization()
        print("✅ PASSED: ContractDeployer initializes correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    # Test 2: Contract compilation
    print("\n📋 Test 2: Contract compilation")
    try:
        test_instance.test_compile_contract_success()
        print("✅ PASSED: Contract compiles successfully")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    # Test 3: Configuration file structure
    print("\n📋 Test 3: Configuration file generation structure")
    try:
        from scripts.deploy_contract import ContractDeployer
        deployer = ContractDeployer("http://localhost:8545")
        
        # Test that config directory path is correct
        assert deployer.config_dir.name == "config"
        
        # Test that contract source path is correct
        assert deployer.contract_source_path.name == "WipeAuditContract.sol"
        
        print("✅ PASSED: Configuration paths are correct")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    return success

def run_ganache_manager_tests():
    """Run Ganache manager tests manually."""
    print("\n🔗 Testing Ganache Manager Functionality")
    print("=" * 60)
    
    # Create test instance
    test_instance = TestGanacheManager()
    test_instance.setup_method()
    
    success = True
    
    # Test 1: GanacheManager initialization
    print("\n📋 Test 1: GanacheManager initialization")
    try:
        test_instance.test_ganache_manager_initialization()
        print("✅ PASSED: GanacheManager initializes correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    # Test 2: Ganache command building
    print("\n📋 Test 2: Ganache command building")
    try:
        test_instance.test_build_ganache_command()
        print("✅ PASSED: Ganache command builds correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    # Test 3: Connection info generation
    print("\n📋 Test 3: Connection info generation")
    try:
        test_instance.test_get_connection_info()
        print("✅ PASSED: Connection info generates correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    return success

def run_integration_tests():
    """Run integration tests for deployment workflow."""
    print("\n🔄 Testing Deployment Integration")
    print("=" * 60)
    
    success = True
    
    # Test 1: Script file existence
    print("\n📋 Test 1: Deployment script files exist")
    try:
        from pathlib import Path
        
        scripts_dir = Path("scripts")
        required_scripts = [
            "deploy_contract.py",
            "start_ganache.py",
            "setup_blockchain.py"
        ]
        
        for script in required_scripts:
            script_path = scripts_dir / script
            assert script_path.exists(), f"Script {script} not found"
            assert script_path.is_file(), f"Script {script} is not a file"
        
        print("✅ PASSED: All deployment scripts exist")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    # Test 2: Import deployment modules
    print("\n📋 Test 2: Deployment modules import correctly")
    try:
        from scripts.deploy_contract import ContractDeployer
        from scripts.start_ganache import GanacheManager
        from scripts.setup_blockchain import BlockchainSetup
        
        # Test instantiation
        deployer = ContractDeployer("http://localhost:8545")
        manager = GanacheManager()
        setup = BlockchainSetup(skip_ganache=True, skip_tests=True)
        
        print("✅ PASSED: All deployment modules import and instantiate correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    # Test 3: Contract ABI validation
    print("\n📋 Test 3: Contract ABI validation")
    try:
        from scripts.deploy_contract import ContractDeployer
        
        deployer = ContractDeployer("http://localhost:8545")
        deployer.compile_contract()
        
        # Validate ABI structure
        abi = deployer.contract_abi
        assert isinstance(abi, list), "ABI should be a list"
        assert len(abi) > 0, "ABI should not be empty"
        
        # Check for required functions
        function_names = [item['name'] for item in abi if item['type'] == 'function']
        required_functions = ['recordWipe', 'getWipeRecord', 'verifyWipe', 'getOwner']
        
        for func in required_functions:
            assert func in function_names, f"Required function {func} not found in ABI"
        
        # Check for required events
        event_names = [item['name'] for item in abi if item['type'] == 'event']
        required_events = ['WipeRecorded', 'OperatorAuthorized']
        
        for event in required_events:
            assert event in event_names, f"Required event {event} not found in ABI"
        
        print("✅ PASSED: Contract ABI is valid and complete")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        success = False
    
    return success

def main():
    """Main test runner function."""
    print("🚀 Contract Deployment Tests")
    print("=" * 60)
    
    overall_success = True
    
    # Run contract deployment tests
    if not run_contract_deployment_tests():
        overall_success = False
    
    # Run Ganache manager tests
    if not run_ganache_manager_tests():
        overall_success = False
    
    # Run integration tests
    if not run_integration_tests():
        overall_success = False
    
    print("\n" + "=" * 60)
    if overall_success:
        print("🎉 ALL DEPLOYMENT TESTS PASSED!")
        print("✅ Contract deployment functionality is working correctly")
        print("\n🎯 Next Steps:")
        print("   • Test with actual Ganache: python scripts/start_ganache.py")
        print("   • Deploy contract: python scripts/deploy_contract.py")
        print("   • Run full setup: python scripts/setup_blockchain.py")
        return 0
    else:
        print("❌ SOME DEPLOYMENT TESTS FAILED!")
        print("🔧 Contract deployment functionality needs fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())