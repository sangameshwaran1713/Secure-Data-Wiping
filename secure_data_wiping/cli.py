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
from .utils.data_models import DeviceInfo, WipeConfig, DeviceType, WipeMethod, WipeTarget, WipeTargetType, FileWipeConfig
from .utils.logging_config import setup_logging
from .file_operations import FileSelector, FileWipeEngine


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


def cmd_wipe_file(args):
    """Handle file wiping command."""
    logger = setup_cli_logging(args.log_level)
    logger.info(f"Starting file wipe operation: {args.file_path}")
    
    try:
        # Create file wipe target
        target = WipeTarget(
            target_id=f"FILE_{int(time.time())}",
            target_type=WipeTargetType.FILE,
            target_path=args.file_path,
            device_context=args.device_context
        )
        
        # Create file wipe configuration
        method_map = {
            'clear': WipeMethod.NIST_CLEAR,
            'purge': WipeMethod.NIST_PURGE,
            'destroy': WipeMethod.NIST_DESTROY
        }
        config = FileWipeConfig(
            method=method_map[args.method],
            passes=args.passes,
            verify_wipe=args.verify,
            wipe_file_metadata=args.wipe_metadata,
            overwrite_free_space=args.wipe_free_space
        )
        
        # Initialize file wipe engine
        file_engine = FileWipeEngine()
        
        # Perform wiping
        result = file_engine.wipe_target(target, config)
        
        # Display results
        if result.success:
            print(f"✓ File wiped successfully: {args.file_path}")
            print(f"  Operation ID: {result.operation_id}")
            print(f"  Method: {result.method.value}")
            print(f"  Passes: {result.passes_completed}")
            print(f"  Size: {result.total_size_bytes} bytes")
            print(f"  Duration: {result.duration:.2f} seconds")
            if result.verification_hash:
                print(f"  Verification Hash: {result.verification_hash[:16]}...")
        else:
            print(f"✗ File wiping failed: {result.error_message}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"File wiping failed: {e}")
        print(f"Error: {e}")
        return 1


def cmd_wipe_directory(args):
    """Handle directory wiping command."""
    logger = setup_cli_logging(args.log_level)
    logger.info(f"Starting directory wipe operation: {args.directory_path}")
    
    try:
        # Create directory wipe target
        target = WipeTarget(
            target_id=f"DIR_{int(time.time())}",
            target_type=WipeTargetType.DIRECTORY,
            target_path=args.directory_path,
            device_context=args.device_context,
            recursive=args.recursive
        )
        
        # Create file wipe configuration
        method_map = {
            'clear': WipeMethod.NIST_CLEAR,
            'purge': WipeMethod.NIST_PURGE,
            'destroy': WipeMethod.NIST_DESTROY
        }
        config = FileWipeConfig(
            method=method_map[args.method],
            passes=args.passes,
            verify_wipe=args.verify,
            wipe_file_metadata=args.wipe_metadata,
            overwrite_free_space=args.wipe_free_space,
            preserve_directory_structure=args.preserve_structure
        )
        
        # Initialize file wipe engine
        file_engine = FileWipeEngine()
        
        # Perform wiping
        result = file_engine.wipe_target(target, config)
        
        # Display results
        if result.success:
            print(f"✓ Directory wiped successfully: {args.directory_path}")
            print(f"  Operation ID: {result.operation_id}")
            print(f"  Method: {result.method.value}")
            print(f"  Files processed: {result.files_processed}")
            print(f"  Files successful: {result.files_successful}")
            print(f"  Total size: {result.total_size_bytes} bytes")
            print(f"  Success rate: {result.success_rate:.1f}%")
            print(f"  Duration: {result.duration:.2f} seconds")
        else:
            print(f"✗ Directory wiping failed: {result.error_message}")
            if result.files_failed > 0:
                print(f"  Files failed: {result.files_failed}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Directory wiping failed: {e}")
        print(f"Error: {e}")
        return 1


def cmd_wipe_pattern(args):
    """Handle pattern-based wiping command."""
    logger = setup_cli_logging(args.log_level)
    logger.info(f"Starting pattern wipe operation: {args.pattern} in {args.base_path}")
    
    try:
        # Create pattern wipe target
        target = WipeTarget(
            target_id=f"PATTERN_{int(time.time())}",
            target_type=WipeTargetType.PATTERN,
            target_path=args.base_path,
            device_context=args.device_context,
            pattern=args.pattern,
            recursive=args.recursive
        )
        
        # Create file wipe configuration
        method_map = {
            'clear': WipeMethod.NIST_CLEAR,
            'purge': WipeMethod.NIST_PURGE,
            'destroy': WipeMethod.NIST_DESTROY
        }
        config = FileWipeConfig(
            method=method_map[args.method],
            passes=args.passes,
            verify_wipe=args.verify,
            wipe_file_metadata=args.wipe_metadata,
            confirm_each_file=args.confirm
        )
        
        # Initialize file wipe engine
        file_engine = FileWipeEngine()
        
        # Perform wiping
        result = file_engine.wipe_target(target, config)
        
        # Display results
        if result.success:
            print(f"✓ Pattern wiping completed: {args.pattern}")
            print(f"  Operation ID: {result.operation_id}")
            print(f"  Base path: {args.base_path}")
            print(f"  Files found: {result.files_processed}")
            print(f"  Files wiped: {result.files_successful}")
            print(f"  Total size: {result.total_size_bytes} bytes")
            print(f"  Success rate: {result.success_rate:.1f}%")
            print(f"  Duration: {result.duration:.2f} seconds")
        else:
            print(f"✗ Pattern wiping failed: {result.error_message}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Pattern wiping failed: {e}")
        print(f"Error: {e}")
        return 1


def cmd_wipe_extensions(args):
    """Handle extension-based wiping command."""
    logger = setup_cli_logging(args.log_level)
    extensions = [ext.strip() for ext in args.extensions.split(',')]
    logger.info(f"Starting extension wipe operation: {extensions} in {args.base_path}")
    
    try:
        # Create extension wipe target
        target = WipeTarget(
            target_id=f"EXT_{int(time.time())}",
            target_type=WipeTargetType.EXTENSIONS,
            target_path=args.base_path,
            device_context=args.device_context,
            extensions=extensions,
            recursive=args.recursive
        )
        
        # Create file wipe configuration
        method_map = {
            'clear': WipeMethod.NIST_CLEAR,
            'purge': WipeMethod.NIST_PURGE,
            'destroy': WipeMethod.NIST_DESTROY
        }
        config = FileWipeConfig(
            method=method_map[args.method],
            passes=args.passes,
            verify_wipe=args.verify,
            wipe_file_metadata=args.wipe_metadata
        )
        
        # Initialize file wipe engine
        file_engine = FileWipeEngine()
        
        # Perform wiping
        result = file_engine.wipe_target(target, config)
        
        # Display results
        if result.success:
            print(f"✓ Extension wiping completed: {extensions}")
            print(f"  Operation ID: {result.operation_id}")
            print(f"  Base path: {args.base_path}")
            print(f"  Files found: {result.files_processed}")
            print(f"  Files wiped: {result.files_successful}")
            print(f"  Total size: {result.total_size_bytes} bytes")
            print(f"  Success rate: {result.success_rate:.1f}%")
            print(f"  Duration: {result.duration:.2f} seconds")
        else:
            print(f"✗ Extension wiping failed: {result.error_message}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Extension wiping failed: {e}")
        print(f"Error: {e}")
        return 1


def cmd_scan_files(args):
    """Handle file scanning command."""
    logger = setup_cli_logging(args.log_level)
    logger.info(f"Starting file scan: {args.base_path}")
    
    try:
        # Initialize file selector
        selector = FileSelector()
        
        # Scan for files
        if args.pattern:
            files = selector.select_by_pattern(args.pattern, args.base_path, args.recursive)
        elif args.extensions:
            extensions = [ext.strip() for ext in args.extensions.split(',')]
            files = selector.select_by_extensions(extensions, args.base_path, args.recursive)
        else:
            files = selector.select_directory_contents(args.base_path, args.recursive)
        
        # Display results
        print(f"File scan results for: {args.base_path}")
        print(f"Files found: {len(files)}")
        
        if args.detailed:
            total_size = 0
            for file_info in files:
                print(f"  {file_info.path} ({file_info.size} bytes)")
                total_size += file_info.size
            print(f"Total size: {total_size} bytes ({total_size / (1024*1024):.1f} MB)")
        else:
            total_size = sum(f.size for f in files)
            print(f"Total size: {total_size} bytes ({total_size / (1024*1024):.1f} MB)")
        
        # Save report if requested
        if args.output:
            report_data = {
                'scan_path': args.base_path,
                'pattern': args.pattern,
                'extensions': args.extensions.split(',') if args.extensions else None,
                'recursive': args.recursive,
                'files_found': len(files),
                'total_size_bytes': total_size,
                'files': [
                    {
                        'path': f.path,
                        'size': f.size,
                        'extension': f.extension,
                        'modified_time': f.modified_time,
                        'is_accessible': f.is_accessible
                    }
                    for f in files
                ]
            }
            
            with open(args.output, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"Report saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"File scanning failed: {e}")
        print(f"Error: {e}")
        return 1


import time


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Secure Data Wiping System - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # DEVICE-LEVEL OPERATIONS (Existing)
  python -m secure_data_wiping.cli batch-process devices.csv
  python -m secure_data_wiping.cli single-device DEV_001 --device-type hdd --wipe-method clear
  python -m secure_data_wiping.cli create-sample sample_devices.csv --format csv
  
  # FILE-LEVEL OPERATIONS (New)
  python -m secure_data_wiping.cli wipe-file /path/to/sensitive.pdf --method purge --passes 3
  python -m secure_data_wiping.cli wipe-directory /confidential --method clear --wipe-free-space
  python -m secure_data_wiping.cli wipe-pattern "*.tmp" /temp --method clear
  python -m secure_data_wiping.cli wipe-extensions pdf,docx,xlsx /documents --method purge
  python -m secure_data_wiping.cli scan-files /documents --pattern "*.pdf" --detailed
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
    
    # ========================================
    # FILE-LEVEL OPERATIONS (NEW)
    # ========================================
    
    # Wipe single file command
    file_parser = subparsers.add_parser('wipe-file',
                                       help='Securely wipe a single file')
    file_parser.add_argument('file_path',
                            help='Path to file to wipe')
    file_parser.add_argument('--method', '-m',
                            choices=['clear', 'purge', 'destroy'],
                            default='clear',
                            help='Wiping method (default: clear)')
    file_parser.add_argument('--passes', '-p',
                            type=int,
                            default=3,
                            help='Number of overwrite passes (default: 3)')
    file_parser.add_argument('--verify', '-v',
                            action='store_true',
                            help='Verify file wiping')
    file_parser.add_argument('--wipe-metadata',
                            action='store_true',
                            default=True,
                            help='Also wipe file metadata (default: True)')
    file_parser.add_argument('--wipe-free-space',
                            action='store_true',
                            help='Also wipe free space after deletion')
    file_parser.add_argument('--device-context',
                            help='Device context for audit trail')
    file_parser.set_defaults(func=cmd_wipe_file)
    
    # Wipe directory command
    dir_parser = subparsers.add_parser('wipe-directory',
                                      help='Securely wipe entire directory')
    dir_parser.add_argument('directory_path',
                           help='Path to directory to wipe')
    dir_parser.add_argument('--method', '-m',
                           choices=['clear', 'purge', 'destroy'],
                           default='clear',
                           help='Wiping method (default: clear)')
    dir_parser.add_argument('--passes', '-p',
                           type=int,
                           default=3,
                           help='Number of overwrite passes (default: 3)')
    dir_parser.add_argument('--verify', '-v',
                           action='store_true',
                           help='Verify wiping operations')
    dir_parser.add_argument('--recursive', '-r',
                           action='store_true',
                           default=True,
                           help='Include subdirectories (default: True)')
    dir_parser.add_argument('--preserve-structure',
                           action='store_true',
                           help='Keep empty directories')
    dir_parser.add_argument('--wipe-metadata',
                           action='store_true',
                           default=True,
                           help='Also wipe file metadata (default: True)')
    dir_parser.add_argument('--wipe-free-space',
                           action='store_true',
                           help='Also wipe free space after deletion')
    dir_parser.add_argument('--device-context',
                           help='Device context for audit trail')
    dir_parser.set_defaults(func=cmd_wipe_directory)
    
    # Wipe by pattern command
    pattern_parser = subparsers.add_parser('wipe-pattern',
                                          help='Wipe files matching pattern')
    pattern_parser.add_argument('pattern',
                               help='File pattern (e.g., "*.pdf", "temp_*")')
    pattern_parser.add_argument('base_path',
                               nargs='?',
                               default='.',
                               help='Base directory to search (default: current)')
    pattern_parser.add_argument('--method', '-m',
                               choices=['clear', 'purge', 'destroy'],
                               default='clear',
                               help='Wiping method (default: clear)')
    pattern_parser.add_argument('--passes', '-p',
                               type=int,
                               default=3,
                               help='Number of overwrite passes (default: 3)')
    pattern_parser.add_argument('--verify', '-v',
                               action='store_true',
                               help='Verify wiping operations')
    pattern_parser.add_argument('--recursive', '-r',
                               action='store_true',
                               default=True,
                               help='Search subdirectories (default: True)')
    pattern_parser.add_argument('--confirm',
                               action='store_true',
                               help='Confirm each file before wiping')
    pattern_parser.add_argument('--wipe-metadata',
                               action='store_true',
                               default=True,
                               help='Also wipe file metadata (default: True)')
    pattern_parser.add_argument('--device-context',
                               help='Device context for audit trail')
    pattern_parser.set_defaults(func=cmd_wipe_pattern)
    
    # Wipe by extensions command
    ext_parser = subparsers.add_parser('wipe-extensions',
                                      help='Wipe files by extensions')
    ext_parser.add_argument('extensions',
                           help='Comma-separated extensions (e.g., "pdf,docx,xlsx")')
    ext_parser.add_argument('base_path',
                           nargs='?',
                           default='.',
                           help='Base directory to search (default: current)')
    ext_parser.add_argument('--method', '-m',
                           choices=['clear', 'purge', 'destroy'],
                           default='clear',
                           help='Wiping method (default: clear)')
    ext_parser.add_argument('--passes', '-p',
                           type=int,
                           default=3,
                           help='Number of overwrite passes (default: 3)')
    ext_parser.add_argument('--verify', '-v',
                           action='store_true',
                           help='Verify wiping operations')
    ext_parser.add_argument('--recursive', '-r',
                           action='store_true',
                           default=True,
                           help='Search subdirectories (default: True)')
    ext_parser.add_argument('--wipe-metadata',
                           action='store_true',
                           default=True,
                           help='Also wipe file metadata (default: True)')
    ext_parser.add_argument('--device-context',
                           help='Device context for audit trail')
    ext_parser.set_defaults(func=cmd_wipe_extensions)
    
    # Scan files command
    scan_parser = subparsers.add_parser('scan-files',
                                       help='Scan and analyze files')
    scan_parser.add_argument('base_path',
                            nargs='?',
                            default='.',
                            help='Base directory to scan (default: current)')
    scan_parser.add_argument('--pattern',
                            help='File pattern to match')
    scan_parser.add_argument('--extensions',
                            help='Comma-separated extensions to match')
    scan_parser.add_argument('--recursive', '-r',
                            action='store_true',
                            default=True,
                            help='Scan subdirectories (default: True)')
    scan_parser.add_argument('--detailed', '-d',
                            action='store_true',
                            help='Show detailed file information')
    scan_parser.add_argument('--output', '-o',
                            help='Save scan report to file (JSON format)')
    scan_parser.set_defaults(func=cmd_scan_files)
    
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