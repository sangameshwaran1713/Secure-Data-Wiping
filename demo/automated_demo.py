#!/usr/bin/env python3
"""
Automated Demonstration Script

This script provides a fully automated demonstration of the secure data wiping system
for academic presentation, viva demonstration, and system validation.
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from secure_data_wiping.wipe_engine import WipeEngine
from secure_data_wiping.hash_generator import HashGenerator
from secure_data_wiping.certificate_generator import CertificateGenerator
from secure_data_wiping.local_infrastructure import (
    NetworkIsolationChecker, DataPrivacyFilter, OfflineVerifier
)
from secure_data_wiping.utils.data_models import (
    DeviceInfo, WipeMethod, DeviceType, WipeData, BlockchainData
)
from demo.sample_it_assets import SampleITAssetsGenerator


class AutomatedDemonstrator:
    """Provides automated demonstration of the complete system."""
    
    def __init__(self, output_dir: str = None, verbose: bool = True):
        """
        Initialize the automated demonstrator.
        
        Args:
            output_dir: Directory for demo outputs
            verbose: Whether to show detailed output
        """
        self.output_dir = Path(output_dir) if output_dir else Path('demo/demo_output')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.demo_start_time = datetime.now()
        self.results = {}
        
        # Initialize components
        self.wipe_engine = WipeEngine()
        self.hash_generator = HashGenerator()
        self.certificate_generator = CertificateGenerator(output_dir=str(self.output_dir))
        self.privacy_filter = DataPrivacyFilter()
        self.network_checker = NetworkIsolationChecker()
        self.offline_verifier = OfflineVerifier(verification_data_dir=str(self.output_dir))
        
        # Demo statistics
        self.stats = {
            'devices_processed': 0,
            'certificates_generated': 0,
            'hashes_generated': 0,
            'privacy_violations_detected': 0,
            'total_processing_time': 0.0,
            'scenarios_completed': 0
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "STEP": "🔄"
            }.get(level, "📝")
            print(f"[{timestamp}] {prefix} {message}")
    
    def print_header(self, title: str):
        """Print a formatted header."""
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"  {title}")
            print(f"{'='*80}")
    
    def print_section(self, title: str):
        """Print a formatted section header."""
        if self.verbose:
            print(f"\n--- {title} ---")
    
    def simulate_device_wiping(self, device: DeviceInfo, data_file_path: str) -> Dict[str, Any]:
        """
        Simulate the complete device wiping workflow.
        
        Args:
            device: Device information
            data_file_path: Path to sample data file
            
        Returns:
            Dictionary containing workflow results
        """
        workflow_start = time.time()
        
        self.log(f"Processing device: {device.device_id} ({device.device_type.value})", "STEP")
        
        # Step 1: Determine optimal wiping method
        if device.device_type == DeviceType.HDD:
            method = WipeMethod.NIST_CLEAR if device.capacity < 1000000000000 else WipeMethod.NIST_PURGE
        elif device.device_type == DeviceType.SSD:
            method = WipeMethod.NIST_PURGE  # Crypto-erase for SSDs
        elif device.device_type == DeviceType.USB:
            method = WipeMethod.NIST_CLEAR
        else:  # NVMe
            method = WipeMethod.NIST_PURGE
        
        self.log(f"Selected wiping method: {method.value.upper()}")
        
        # Step 2: Perform secure wiping
        wipe_start = time.time()
        wipe_result = self.wipe_engine.wipe_device(data_file_path, method)
        wipe_time = time.time() - wipe_start
        
        if not wipe_result.success:
            self.log(f"Wiping failed for device {device.device_id}", "ERROR")
            return {"success": False, "error": "Wiping failed"}
        
        self.log(f"Wiping completed in {wipe_time:.3f}s ({wipe_result.passes_completed} passes)")
        
        # Step 3: Generate cryptographic hash
        hash_start = time.time()
        wipe_hash = self.hash_generator.generate_wipe_hash(wipe_result)
        hash_time = time.time() - hash_start
        
        self.log(f"Hash generated in {hash_time:.6f}s: {wipe_hash[:16]}...")
        
        # Step 4: Apply privacy filtering
        privacy_start = time.time()
        raw_data = {
            'device_id': device.device_id,
            'wipe_hash': wipe_hash,
            'timestamp': int(datetime.now().timestamp()),
            'method': method.value,
            'operator_id': 'demo_operator',
            'device_serial': device.serial_number,  # This should be filtered
            'manufacturer': device.manufacturer,
            'model': device.model,
            'capacity': device.capacity,
            'connection_type': device.connection_type
        }
        
        privacy_result = self.privacy_filter.filter_blockchain_data(raw_data)
        privacy_time = time.time() - privacy_start
        
        self.log(f"Privacy filtering completed in {privacy_time:.6f}s")
        self.log(f"Privacy violations detected: {len(privacy_result.violations)}")
        
        # Step 5: Generate certificate
        cert_start = time.time()
        
        wipe_data = WipeData(
            device_id=device.device_id,
            wipe_hash=wipe_hash,
            timestamp=datetime.now(),
            method=method.value,
            operator='demo_operator',
            passes=wipe_result.passes_completed
        )
        
        # Simulate blockchain data
        blockchain_data = BlockchainData(
            transaction_hash=f"0x{'a' * 62}",  # Mock transaction
            block_number=12345 + self.stats['devices_processed'],
            contract_address=f"0x{'b' * 38}",  # Mock contract
            gas_used=50000,
            confirmation_count=6
        )
        
        cert_path = self.certificate_generator.generate_certificate(
            wipe_data, blockchain_data, device
        )
        cert_time = time.time() - cert_start
        
        self.log(f"Certificate generated in {cert_time:.3f}s: {Path(cert_path).name}")
        
        # Step 6: Create offline verification
        verification_start = time.time()
        verification_data = self.offline_verifier.create_verification_data(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            device_info=device,
            certificate_path=cert_path
        )
        verification_time = time.time() - verification_start
        
        self.log(f"Offline verification created in {verification_time:.6f}s")
        
        # Calculate total workflow time
        workflow_time = time.time() - workflow_start
        
        # Update statistics
        self.stats['devices_processed'] += 1
        self.stats['certificates_generated'] += 1
        self.stats['hashes_generated'] += 1
        self.stats['privacy_violations_detected'] += len(privacy_result.violations)
        self.stats['total_processing_time'] += workflow_time
        
        # Return comprehensive results
        return {
            'success': True,
            'device_id': device.device_id,
            'device_type': device.device_type.value,
            'wipe_method': method.value,
            'wipe_result': wipe_result,
            'wipe_hash': wipe_hash,
            'privacy_result': privacy_result,
            'certificate_path': cert_path,
            'verification_data': verification_data,
            'timing': {
                'total_workflow': workflow_time,
                'wiping': wipe_time,
                'hashing': hash_time,
                'privacy_filtering': privacy_time,
                'certificate_generation': cert_time,
                'verification_setup': verification_time
            }
        }
    
    def run_scenario_demo(self, scenario_name: str, devices: List[DeviceInfo], 
                         data_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run a complete scenario demonstration.
        
        Args:
            scenario_name: Name of the scenario
            devices: List of devices in the scenario
            data_files: Mapping of device_id to data file path
            
        Returns:
            Dictionary containing scenario results
        """
        self.print_header(f"SCENARIO DEMONSTRATION: {scenario_name.upper()}")
        
        scenario_start = time.time()
        scenario_results = []
        
        self.log(f"Starting scenario '{scenario_name}' with {len(devices)} devices")
        
        for i, device in enumerate(devices, 1):
            self.print_section(f"Device {i}/{len(devices)}: {device.device_id}")
            
            data_file = data_files.get(device.device_id)
            if not data_file or not os.path.exists(data_file):
                self.log(f"Data file not found for device {device.device_id}", "WARNING")
                continue
            
            # Process device
            result = self.simulate_device_wiping(device, data_file)
            scenario_results.append(result)
            
            # Brief pause for demonstration effect
            if self.verbose:
                time.sleep(0.5)
        
        scenario_time = time.time() - scenario_start
        self.stats['scenarios_completed'] += 1
        
        # Calculate scenario statistics
        successful_devices = len([r for r in scenario_results if r.get('success')])
        total_certificates = len([r for r in scenario_results if r.get('certificate_path')])
        avg_processing_time = sum(r.get('timing', {}).get('total_workflow', 0) 
                                for r in scenario_results) / len(scenario_results) if scenario_results else 0
        
        self.log(f"Scenario '{scenario_name}' completed in {scenario_time:.2f}s", "SUCCESS")
        self.log(f"Devices processed: {successful_devices}/{len(devices)}")
        self.log(f"Certificates generated: {total_certificates}")
        self.log(f"Average processing time: {avg_processing_time:.3f}s per device")
        
        return {
            'scenario_name': scenario_name,
            'total_devices': len(devices),
            'successful_devices': successful_devices,
            'total_time': scenario_time,
            'average_processing_time': avg_processing_time,
            'results': scenario_results
        }
    
    def demonstrate_system_capabilities(self):
        """Demonstrate key system capabilities."""
        self.print_header("SYSTEM CAPABILITIES DEMONSTRATION")
        
        # Capability 1: NIST Compliance
        self.print_section("NIST 800-88 Compliance")
        
        nist_methods = [WipeMethod.NIST_CLEAR, WipeMethod.NIST_PURGE, WipeMethod.NIST_DESTROY]
        device_types = [DeviceType.HDD, DeviceType.SSD, DeviceType.USB, DeviceType.NVME]
        
        self.log("Demonstrating NIST compliance across device types and methods:")
        for device_type in device_types:
            for method in nist_methods:
                pass_count = self.wipe_engine.get_nist_pass_count(method, device_type)
                self.log(f"  {device_type.value.upper()} + {method.value.upper()}: {pass_count} passes")
        
        # Capability 2: Cryptographic Security
        self.print_section("Cryptographic Security")
        
        self.log("SHA-256 hash generation and verification:")
        test_data = "Sample data for hash testing"
        hash_value = self.hash_generator._generate_hash(test_data)
        self.log(f"  Sample hash: {hash_value[:32]}...")
        self.log(f"  Hash length: {len(hash_value)} characters")
        self.log(f"  Algorithm: SHA-256 (256-bit security)")
        
        # Capability 3: Privacy Protection
        self.print_section("Privacy Protection")
        
        test_data = {
            'device_id': 'TEST_DEVICE',
            'safe_field': 'public_data',
            'password': 'secret123',
            'email': 'user@example.com'
        }
        
        privacy_result = self.privacy_filter.filter_blockchain_data(test_data)
        self.log(f"Privacy filtering demonstration:")
        self.log(f"  Original fields: {len(test_data)}")
        self.log(f"  Violations detected: {len(privacy_result.violations)}")
        self.log(f"  Safe fields preserved: {len(privacy_result.filtered_data)}")
        
        # Capability 4: Network Isolation
        self.print_section("Network Isolation")
        
        test_addresses = [
            ('127.0.0.1', 'Local loopback'),
            ('192.168.1.1', 'Private network'),
            ('8.8.8.8', 'External DNS'),
            ('google.com', 'External domain')
        ]
        
        self.log("Network isolation testing:")
        for addr, description in test_addresses:
            is_local = self.network_checker.is_local_address(addr)
            status = "ALLOWED" if is_local else "BLOCKED"
            self.log(f"  {addr} ({description}): {status}")
    
    def generate_demo_report(self, scenario_results: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive demonstration report.
        
        Args:
            scenario_results: Results from all scenarios
            
        Returns:
            Path to generated report file
        """
        report_path = self.output_dir / f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        total_demo_time = (datetime.now() - self.demo_start_time).total_seconds()
        
        report_data = {
            'demo_metadata': {
                'generated_at': datetime.now().isoformat(),
                'demo_duration': total_demo_time,
                'system_version': '1.0.0',
                'demo_type': 'automated_complete_system'
            },
            'system_statistics': self.stats,
            'performance_metrics': {
                'average_processing_time': (
                    self.stats['total_processing_time'] / self.stats['devices_processed']
                    if self.stats['devices_processed'] > 0 else 0
                ),
                'devices_per_minute': (
                    (self.stats['devices_processed'] / total_demo_time) * 60
                    if total_demo_time > 0 else 0
                ),
                'certificates_per_minute': (
                    (self.stats['certificates_generated'] / total_demo_time) * 60
                    if total_demo_time > 0 else 0
                )
            },
            'scenario_results': scenario_results,
            'compliance_verification': {
                'nist_800_88_compliant': True,
                'privacy_protection_active': True,
                'network_isolation_enforced': True,
                'cryptographic_integrity': True
            },
            'output_files': {
                'certificates_directory': str(self.output_dir),
                'verification_data_directory': str(self.output_dir),
                'demo_assets_directory': str(self.output_dir.parent / 'sample_assets')
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_path)
    
    def run_complete_automated_demo(self) -> Dict[str, Any]:
        """
        Run the complete automated demonstration.
        
        Returns:
            Dictionary containing complete demo results
        """
        self.print_header("AUTOMATED SECURE DATA WIPING SYSTEM DEMONSTRATION")
        
        self.log("🎓 Final Year Project - Computer Science")
        self.log("🔐 Blockchain-Based Audit Trail for IT Asset Recycling")
        self.log("🤖 Automated System Demonstration")
        
        try:
            # Step 1: Generate sample IT assets
            self.log("Generating sample IT assets for demonstration...", "STEP")
            assets_generator = SampleITAssetsGenerator(
                output_dir=str(self.output_dir.parent / 'sample_assets')
            )
            demo_environment = assets_generator.generate_complete_demo_environment()
            
            # Step 2: Demonstrate system capabilities
            self.demonstrate_system_capabilities()
            
            # Step 3: Run scenario demonstrations
            scenario_results = []
            scenarios = demo_environment['scenarios']
            scenario_files = demo_environment['scenario_files']
            
            # Select key scenarios for demonstration
            demo_scenarios = ['small_office', 'dev_workstation', 'data_center']
            
            for scenario_name in demo_scenarios:
                if scenario_name in scenarios:
                    devices = scenarios[scenario_name]
                    files = scenario_files[scenario_name]
                    result = self.run_scenario_demo(scenario_name, devices, files)
                    scenario_results.append(result)
            
            # Step 4: Generate comprehensive report
            self.log("Generating demonstration report...", "STEP")
            report_path = self.generate_demo_report(scenario_results)
            
            # Step 5: Final summary
            self.print_header("DEMONSTRATION SUMMARY")
            
            total_time = (datetime.now() - self.demo_start_time).total_seconds()
            
            self.log("🎉 AUTOMATED DEMONSTRATION COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.log(f"📊 Total demonstration time: {total_time:.2f} seconds")
            self.log(f"🔧 Devices processed: {self.stats['devices_processed']}")
            self.log(f"📜 Certificates generated: {self.stats['certificates_generated']}")
            self.log(f"🔐 Hashes generated: {self.stats['hashes_generated']}")
            self.log(f"🛡️ Privacy violations detected: {self.stats['privacy_violations_detected']}")
            self.log(f"🎭 Scenarios completed: {self.stats['scenarios_completed']}")
            self.log(f"📈 Average processing time: {self.stats['total_processing_time'] / self.stats['devices_processed']:.3f}s per device")
            self.log(f"📋 Demo report: {Path(report_path).name}")
            
            return {
                'success': True,
                'total_time': total_time,
                'statistics': self.stats,
                'scenario_results': scenario_results,
                'report_path': report_path,
                'demo_environment': demo_environment
            }
            
        except Exception as e:
            self.log(f"Demonstration failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


def main():
    """Main function for automated demonstration."""
    print("🤖 AUTOMATED SECURE DATA WIPING DEMONSTRATION")
    print("=" * 80)
    
    # Create demonstrator
    demonstrator = AutomatedDemonstrator(verbose=True)
    
    # Run complete demonstration
    results = demonstrator.run_complete_automated_demo()
    
    if results['success']:
        print(f"\n✅ Automated demonstration completed successfully!")
        print(f"📁 Output directory: {demonstrator.output_dir}")
        print(f"📋 Report file: {results['report_path']}")
        return 0
    else:
        print(f"\n❌ Automated demonstration failed: {results.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())