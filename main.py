#!/usr/bin/env python3
"""
Secure Data Wiping System - Main Application Entry Point

This is the main entry point for the secure data wiping system.
Provides both CLI interface and programmatic access to the system.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from secure_data_wiping.cli import main as cli_main
from secure_data_wiping.system_controller import SystemController
from secure_data_wiping.utils.data_models import DeviceInfo, WipeConfig, DeviceType, WipeMethod
from secure_data_wiping.utils.logging_config import setup_logging


def demo_single_device():
    """
    Demonstrate processing a single device.
    
    This function shows how to use the SystemController programmatically
    for processing individual devices.
    """
    print("=== Secure Data Wiping System - Single Device Demo ===\n")
    
    # Set up logging
    setup_logging(log_level="INFO")
    
    try:
        # Create sample device info
        device_info = DeviceInfo(
            device_id="DEMO_DEVICE_001",
            device_type=DeviceType.HDD,
            manufacturer="Seagate",
            model="ST1000DM003",
            serial_number="DEMO123456",
            capacity=1000000000000  # 1TB
        )
        
        # Create wipe configuration
        wipe_config = WipeConfig(
            method=WipeMethod.NIST_CLEAR,
            passes=1,
            verify_wipe=True
        )
        
        print(f"Processing device: {device_info.device_id}")
        print(f"Device type: {device_info.device_type.value}")
        print(f"Wipe method: {wipe_config.method.value}")
        print(f"Passes: {wipe_config.passes}")
        print()
        
        # Initialize system controller
        controller = SystemController()
        
        # Initialize system
        print("Initializing system...")
        if not controller.initialize_system():
            # Avoid Unicode symbols that may not be supported in all consoles
            print("FAILED: Could not initialize system")
            return False
        
        print("System initialized successfully")
        
        # Process the device
        print("Processing device...")
        result = controller.process_device(device_info, wipe_config)
        
        # Display results
        if result.success:
            print("Device processed successfully!")
            print(f"   Operation ID: {result.operation_id}")
            print(f"   Wipe Hash: {result.wipe_hash}")
            print(f"   Transaction Hash: {result.transaction_hash}")
            print(f"   Certificate: {result.certificate_path}")
            print(f"   Processing Time: {result.processing_time:.2f} seconds")
        else:
            print(f"Device processing failed: {result.error_message}")
        
        # Get system status
        status = controller.get_system_status()
        summary = controller.get_processing_summary()
        
        print(f"\nSystem Status:")
        print(f"   Operations Processed: {status.operations_processed}")
        print(f"   Success Rate: {summary['processing_statistics']['success_rate']:.1f}%")
        
        # Shutdown system
        controller.shutdown_system()
        
        return result.success
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Main entry point for the application.
    
    If command line arguments are provided, use CLI interface.
    Otherwise, run the single device demo.
    """
    if len(sys.argv) > 1:
        # Use CLI interface
        return cli_main()
    else:
        # Run demo
        print("No command line arguments provided. Running single device demo...")
        print("For CLI usage, run: python main.py --help")
        print()
        
        success = demo_single_device()
        
        print("\n" + "="*60)
        if success:
            print("Demo completed successfully!")
            print("\nTo process multiple devices, use the CLI interface:")
            print("  python main.py create-sample sample_devices.csv")
            print("  python main.py batch-process sample_devices.csv")
        else:
            print("Demo failed. Check the logs for more information.")
        
        print("\nFor full CLI help, run: python main.py --help")
        print("="*60)
        
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())