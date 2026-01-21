#!/usr/bin/env python3
"""
Command Line Interface for Secure Data Wiping System

Provides CLI commands for batch processing of IT assets through the complete
secure data wiping workflow.
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

from .system_controller import SystemController
from .utils.data_models import DeviceInfo, WipeConfig, DeviceType, WipeMethod
from .utils.logging_config import setup_logging


def setup_cli_logging(log_level: str = "INFO"):
    """Set up logging for CLI operations."""
    setup_logging(log_level=log_level)
    return logging.getLogger(__name__)


def parse_device_csv(csv_path: str) -> List[Tuple[DeviceInfo, WipeConfig]]:
    """
    Parse device information from CSV file.
    
    Expected CSV format:
    device_id,device_type,manufacturer,model,serial_number,capacity,wipe_method,passes
    
    Args:
        csv_path: Path to CSV file containing device information
        
    Returns:
        List of (DeviceInfo, WipeConfig) tuples
    """
    devices = []
    
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Create DeviceInfo
            device_info = DeviceInfo(
                device_id=row['device_id'],
                device_type=DeviceType(row.get('device_type', 'other').lower()),
                manufacturer=row.get('manufacturer'),
                model=row.get('model'),
                serial_number=row.get('serial_number'),
                capacity=int(row['capacity']) if row.get('capacity') else None
            )
            
            # Create WipeConfig
            wipe_config = WipeConfig(
                method=WipeMethod(row.get('wipe_method', 'clear').lower()),
                passes=int(row.get('passes', 1)),
                verify_wipe=row.get('verify_wipe', 'true').lower() == 'true'
            )
            
            devices.append((device_info, wipe_config))
    
    return devices


def parse_device_json(json_path: str) -> List[Tuple[DeviceInfo, WipeConfig]]:
    """
    Parse device information from JSON file.
    
    Expected JSON format:
    {
        "devices": [
            {
                "device_id": "DEV_001",
                "device_type": "hdd",
                "manufacturer": "Seagate",
                "model": "ST1000DM003",
                "serial_number": "ABC123",
                "capacity": 1000000000000,
                "wipe_method": "clear",
                "passes": 1,
                "verify_wipe": true
            }
        ]
    }
    
    Args:
        json_path: Path to JSON file containing device information
        
    Returns:
        List of (DeviceInfo, WipeConfig) tuples
    """
    devices = []
    
    with open(json_path, 'r') as jsonfile:
        data = json.load(jsonfile)
        
        for device_data in data.get('devices', []):
            # Create DeviceInfo
            device_info = DeviceInfo(
                device_id=device_data['device_id'],
                device_type=DeviceType(device_data.get('device_type', 'other').lower()),
                manufacturer=device_data.get('manufacturer'),
                model=device_data.get('model'),
                serial_number=device_data.get('serial_number'),
                capacity=device_data.get('capacity')
            )
            
            # Create WipeConfig
            wipe_config = WipeConfig(
                method=WipeMethod(device_data.get('wipe_method', 'clear').lower()),
                passes=device_data.get('passes', 1),
                verify_wipe=device_data.get('verify_wipe', True)
            )
            
            devices.append((device_info, wipe_config))
    
    return devices


def create_sample_device_file(output_path: str, format_type: str = "csv"):
    """
    Create a sample device file for demonstration.
    
    Args:
        output_path: Path where to create the sample file
        format_type: Format type ('csv' or 'json')
    """
    if format_type.lower() == "csv":
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'device_id', 'device_type', 'manufacturer', 'model', 
                'serial_number', 'capacity', 'wipe_method', 'passes', 'verify_wipe'
            ])
            writer.writerow([
                'DEV_001', 'hdd', 'Seagate', 'ST1000DM003', 
                'ABC123', '1000000000000', 'clear', '1', 'true'
            ])
            writer.writerow([
                'DEV_002', 'ssd', 'Samsung', '850 EVO', 
                'XYZ789', '500000000000', 'purge', '3', 'true'
            ])
            writer.writerow([
                'DEV_003', 'usb', 'SanDisk', 'Ultra', 
                'USB001', '32000000000', 'destroy', '1', 'false'
            ])
    
    elif format_type.lower() == "json":
        sample_data = {
            "devices": [
                {
                    "device_id": "DEV_001",
                    "device_type": "hdd",
                    "manufacturer": "Seagate",
                    "model": "ST1000DM003",
                    "serial_number": "ABC123",
                    "capacity": 1000000000000,
                    "wipe_method": "clear",
                    "passes": 1,
                    "verify_wipe": True
                },
                {
                    "device_id": "DEV_002",
                    "device_type": "ssd",
                    "manufacturer": "Samsung",
                    "model": "850 EVO",
                    "serial_number": "XYZ789",
                    "capacity": 500000000000,
                    "wipe_method": "purge",
                    "passes": 3,
                    "verify_wipe": True
                },
                {
                    "device_id": "DEV_003",
                    "device_type": "usb",
                    "manufacturer": "SanDisk",
                    "model": "Ultra",
                    "serial_number": "USB001",
                    "capacity": 32000000000,
                    "wipe_method": "destroy",
                    "passes": 1,
                    "verify_wipe": False
                }
            ]
        }
        
        with open(output_path, 'w') as jsonfile:
            json.dump(sample_data, jsonfile, indent=2)


def print_processing_summary(results: List, logger):
    """
    Print a summary of processing results.
    
    Args:
        results: List of ProcessingResult objects
        logger: Logger instance
    """
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total devices processed: {len(results)}")
    print(f"Successful operations: {len(successful)}")
    print(f"Failed operations: {len(failed)}")
    
    if successful:
        avg_time = sum(r.processing_time for r in successful if r.processing_time) / len(successful)
        print(f"Average processing time: {avg_time:.2f} seconds")
    
    print(f"Success rate: {(len(successful) / len(results)) * 100:.1f}%")
    
    if successful:
        print(f"\n{'='*60}")
        print("SUCCESSFUL OPERATIONS")
        print(f"{'='*60}")
        for result in successful:
            print(f"✓ {result.device_id}: Certificate generated at {result.certificate_path}")
            if result.transaction_hash:
                print(f"  Blockchain TX: {result.transaction_hash}")
    
    if failed:
        print(f"\n{'='*60}")
        print("FAILED OPERATIONS")
        print(f"{'='*60}")
        for result in failed:
            print(f"✗ {result.device_id}: {result.error_message}")
    
    print(f"\n{'='*60}")
    logger.info(f"Batch processing completed: {len(successful)} successful, {len(failed)} failed")


def cmd_batch_process(args):
    """Handle batch processing command."""
    logger = setup_cli_logging(args.log_level)
    logger.info(f"Starting batch processing from {args.input_file}")
    
    try:
        # Parse input file
        if args.input_file.endswith('.csv'):
            devices = parse_device_csv(args.input_file)
        elif args.input_file.endswith('.json'):
            devices = parse_device_json(args.input_file)
        else:
            raise ValueError("Input file must be CSV or JSON format")
        
        logger.info(f"Loaded {len(devices)} devices from {args.input_file}")
        
        # Initialize system controller
        controller = SystemController(config_path=args.config)
        
        # Initialize system
        if not controller.initialize_system():
            logger.error("Failed to initialize system")
            return 1
        
        logger.info("System initialized successfully")
        
        # Process devices
        results = controller.process_batch(devices, continue_on_error=args.continue_on_error)
        
        # Print summary
        print_processing_summary(results, logger)
        
        # Generate summary report if requested
        if args.output_report:
            generate_summary_report(results, args.output_report)
            logger.info(f"Summary report generated: {args.output_report}")
        
        # Shutdown system
        controller.shutdown_system()
        
        # Return appropriate exit code
        failed_count = sum(1 for r in results if not r.success)
        return 1 if failed_count > 0 and not args.continue_on_error else 0
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return 1


def cmd_create_sample(args):
    """Handle create sample file command."""
    logger = setup_cli_logging(args.log_level)
    
    try:
        create_sample_device_file(args.output_file, args.format)
        logger.info(f"Sample {args.format.upper()} file created: {args.output_file}")
        print(f"Sample {args.format.upper()} file created: {args.output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to create sample file: {e}")
        return 1


def cmd_single_device(args):
    """Handle single device processing command."""
    logger = setup_cli_logging(args.log_level)
    logger.info(f"Processing single device: {args.device_id}")
    
    try:
        # Create device info
        device_info = DeviceInfo(
            device_id=args.device_id,
            device_type=DeviceType(args.device_type.lower()),
            manufacturer=args.manufacturer,
            model=args.model,
            serial_number=args.serial_number,
            capacity=args.capacity
        )
        
        # Create wipe config
        wipe_config = WipeConfig(
            method=WipeMethod(args.wipe_method.lower()),
            passes=args.passes,
            verify_wipe=args.verify_wipe
        )
        
        # Initialize system controller
        controller = SystemController(config_path=args.config)
        
        # Initialize system
        if not controller.initialize_system():
            logger.error("Failed to initialize system")
            return 1
        
        logger.info("System initialized successfully")
        
        # Process device
        result = controller.process_device(device_info, wipe_config)
        
        # Print result
        if result.success:
            print(f"✓ Device {args.device_id} processed successfully")
            print(f"  Certificate: {result.certificate_path}")
            if result.transaction_hash:
                print(f"  Blockchain TX: {result.transaction_hash}")
            print(f"  Processing time: {result.processing_time:.2f} seconds")
        else:
            print(f"✗ Device {args.device_id} processing failed: {result.error_message}")
        
        # Shutdown system
        controller.shutdown_system()
        
        return 0 if result.success else 1
        
    except Exception as e:
        logger.error(f"Single device processing failed: {e}")
        return 1


def generate_summary_report(results: List, output_path: str):
    """
    Generate a detailed summary report in JSON format.
    
    Args:
        results: List of ProcessingResult objects
        output_path: Path where to save the report
    """
    report_data = {
        "summary": {
            "total_devices": len(results),
            "successful_operations": sum(1 for r in results if r.success),
            "failed_operations": sum(1 for r in results if not r.success),
            "success_rate": (sum(1 for r in results if r.success) / len(results)) * 100 if results else 0,
            "average_processing_time": sum(r.processing_time for r in results if r.processing_time and r.success) / max(1, sum(1 for r in results if r.success))
        },
        "operations": [
            {
                "operation_id": r.operation_id,
                "device_id": r.device_id,
                "success": r.success,
                "error_message": r.error_message,
                "wipe_hash": r.wipe_hash,
                "transaction_hash": r.transaction_hash,
                "certificate_path": r.certificate_path,
                "processing_time": r.processing_time
            }
            for r in results
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Secure Data Wiping System - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process devices from CSV file
  python -m secure_data_wiping.cli batch-process devices.csv
  
  # Process devices with custom config
  python -m secure_data_wiping.cli batch-process devices.json --config custom_config.yaml
  
  # Process single device
  python -m secure_data_wiping.cli single-device DEV_001 --device-type hdd --wipe-method clear
  
  # Create sample device file
  python -m secure_data_wiping.cli create-sample sample_devices.csv --format csv
        """
    )
    
    parser.add_argument('--config', '-c', 
                       help='Path to configuration file')
    parser.add_argument('--log-level', '-l', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO',
                       help='Logging level (default: INFO)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Batch processing command
    batch_parser = subparsers.add_parser('batch-process', 
                                        help='Process multiple devices from file')
    batch_parser.add_argument('input_file', 
                             help='Input file (CSV or JSON) containing device information')
    batch_parser.add_argument('--continue-on-error', '-k', 
                             action='store_true',
                             help='Continue processing even if some devices fail')
    batch_parser.add_argument('--output-report', '-o',
                             help='Generate detailed summary report (JSON format)')
    batch_parser.set_defaults(func=cmd_batch_process)
    
    # Single device command
    single_parser = subparsers.add_parser('single-device',
                                         help='Process a single device')
    single_parser.add_argument('device_id', 
                              help='Device identifier')
    single_parser.add_argument('--device-type', '-t',
                              choices=['hdd', 'ssd', 'usb', 'nvme', 'sd_card', 'other'],
                              default='other',
                              help='Device type (default: other)')
    single_parser.add_argument('--manufacturer', '-m',
                              help='Device manufacturer')
    single_parser.add_argument('--model',
                              help='Device model')
    single_parser.add_argument('--serial-number', '-s',
                              help='Device serial number')
    single_parser.add_argument('--capacity',
                              type=int,
                              help='Device capacity in bytes')
    single_parser.add_argument('--wipe-method', '-w',
                              choices=['clear', 'purge', 'destroy'],
                              default='clear',
                              help='Wiping method (default: clear)')
    single_parser.add_argument('--passes', '-p',
                              type=int,
                              default=1,
                              help='Number of wiping passes (default: 1)')
    single_parser.add_argument('--verify-wipe', '-v',
                              action='store_true',
                              help='Verify wiping operation')
    single_parser.set_defaults(func=cmd_single_device)
    
    # Create sample file command
    sample_parser = subparsers.add_parser('create-sample',
                                         help='Create sample device file')
    sample_parser.add_argument('output_file',
                              help='Output file path')
    sample_parser.add_argument('--format', '-f',
                              choices=['csv', 'json'],
                              default='csv',
                              help='File format (default: csv)')
    sample_parser.set_defaults(func=cmd_create_sample)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())