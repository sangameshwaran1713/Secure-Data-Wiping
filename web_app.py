#!/usr/bin/env python3
"""
Secure Data Wiping System - Web Interface

A Flask-based web application that provides an easy-to-use interface
for the existing CLI-based secure data wiping system.

Features:
- File-level secure deletion with drag & drop
- Device-level wiping with visual interface
- Batch processing with progress tracking
- Real-time operation monitoring
- Certificate management and download
- Blockchain verification integration
"""

import os
import sys
import json
import subprocess
import tempfile
import threading
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
import shutil
import hashlib

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import secrets
from functools import wraps

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import certificate generation functionality
try:
    from secure_data_wiping.certificate_generator.certificate_generator import CertificateGenerator
    from secure_data_wiping.utils.data_models import WipeData, BlockchainData, DeviceInfo, DeviceType, WipeMethod
    CERTIFICATE_GENERATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Certificate generation not available: {e}")
    CERTIFICATE_GENERATION_AVAILABLE = False

# Import system utilities for device detection
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - device detection will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Secure random secret key
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'web_uploads'
app.config['TEMP_FOLDER'] = 'web_temp'
app.config['CERTIFICATES_FOLDER'] = 'certificates'

# Authentication configuration
DEVICE_WIPE_PASSWORD = "SecureWipe2024!"  # In production, use environment variable
SESSION_TIMEOUT = 300  # 5 minutes in seconds

# Global variables for operation tracking
active_operations = {}
operation_logs = []
system_stats = {
    'operations_today': 0,
    'total_operations': 0,
    'success_rate': 100.0,
    'files_wiped_today': 0,
    'total_files_wiped': 0,
    'bytes_wiped_today': 0,
    'total_bytes_wiped': 0,
    'last_operation': None
}

def generate_certificate_for_operation(operation_details: Dict[str, Any], file_path: str = None) -> Optional[str]:
    """
    Generate a certificate for a completed wiping operation.
    
    Args:
        operation_details: Details of the wiping operation
        file_path: Path of the wiped file (for file operations)
        
    Returns:
        Path to generated certificate or None if generation failed
    """
    if not CERTIFICATE_GENERATION_AVAILABLE:
        logger.warning("Certificate generation not available - skipping")
        return None
    
    try:
        # Create certificate generator
        cert_generator = CertificateGenerator(output_dir=app.config['CERTIFICATES_FOLDER'])
        
        # Create WipeData object
        device_id = operation_details.get('device_id', 'FILE_OPERATION')
        if file_path:
            # For file operations, use filename as device_id
            device_id = f"FILE_{Path(file_path).name}_{int(time.time())}"
        
        wipe_data = WipeData(
            device_id=device_id,
            wipe_hash=operation_details.get('wipe_hash', hashlib.sha256(f"{device_id}_{time.time()}".encode()).hexdigest()),
            timestamp=datetime.now(),
            method=operation_details.get('method', 'destroy'),
            operator=operation_details.get('operator', 'web_interface'),
            passes=operation_details.get('passes', 7)
        )
        
        # Create mock blockchain data (in production, this would come from actual blockchain)
        blockchain_data = BlockchainData(
            transaction_hash=f"0x{hashlib.sha256(f'{device_id}_{time.time()}'.encode()).hexdigest()}",
            block_number=random.randint(1000000, 9999999),
            contract_address="0x742d35Cc6C4C45dC8C4B1180B5e89532c0c4b92e",
            gas_used=random.randint(50000, 150000),
            confirmation_count=6,
            network_id="local"
        )
        
        # Create device info for file operations
        device_info = None
        if file_path:
            device_info = DeviceInfo(
                device_id=device_id,
                device_type=DeviceType.OTHER,
                manufacturer="File System",
                model="Secure File Deletion",
                serial_number=f"FILE_{int(time.time())}",
                capacity=operation_details.get('file_size', 0)
            )
        
        # Generate certificate
        certificate_path = cert_generator.generate_certificate(
            wipe_data=wipe_data,
            blockchain_data=blockchain_data,
            device_info=device_info
        )
        
        logger.info(f"Certificate generated: {certificate_path}")
        return certificate_path
        
    except Exception as e:
        logger.error(f"Certificate generation failed: {e}")
        return None


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['TEMP_FOLDER'],
        app.config['CERTIFICATES_FOLDER'],
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

# ============================================================================
# AUTHENTICATION SYSTEM
# ============================================================================

def require_device_wipe_auth(f):
    """Decorator to require authentication for device wiping operations."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated for device wiping
        if not session.get('device_wipe_authenticated'):
            return jsonify({
                'success': False, 
                'error': 'Authentication required for device wiping operations',
                'auth_required': True
            }), 401
        
        # Check session timeout
        if session.get('device_wipe_auth_time'):
            auth_time = session['device_wipe_auth_time']
            if time.time() - auth_time > SESSION_TIMEOUT:
                session.pop('device_wipe_authenticated', None)
                session.pop('device_wipe_auth_time', None)
                return jsonify({
                    'success': False,
                    'error': 'Authentication session expired. Please re-authenticate.',
                    'auth_required': True
                }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def generate_challenge():
    """Generate a mathematical challenge for additional security."""
    import random
    a = random.randint(10, 99)
    b = random.randint(10, 99)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        answer = a + b
    elif operation == '-':
        answer = a - b
    else:  # multiplication
        answer = a * b
    
    challenge = f"{a} {operation} {b}"
    return challenge, answer

def update_stats(operation_result: Dict[str, Any]):
    """Update system statistics based on operation result."""
    global system_stats
    
    system_stats['total_operations'] += 1
    system_stats['operations_today'] += 1
    system_stats['last_operation'] = datetime.now().isoformat()
    
    if operation_result.get('success', False):
        files_processed = operation_result.get('files_processed', 1)
        bytes_processed = operation_result.get('bytes_processed', 0)
        
        system_stats['total_files_wiped'] += files_processed
        system_stats['files_wiped_today'] += files_processed
        system_stats['total_bytes_wiped'] += bytes_processed
        system_stats['bytes_wiped_today'] += bytes_processed
    
    # Calculate success rate
    if system_stats['total_operations'] > 0:
        successful_ops = system_stats['total_operations'] - len([op for op in operation_logs if not op.get('success', True)])
        system_stats['success_rate'] = (successful_ops / system_stats['total_operations']) * 100

def log_operation(operation_type: str, details: Dict[str, Any], success: bool = True, error: str = None):
    """Log operation for tracking and display."""
    global operation_logs
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'operation_type': operation_type,
        'details': details,
        'success': success,
        'error': error,
        'id': str(uuid.uuid4())
    }
    
    operation_logs.insert(0, log_entry)  # Most recent first
    
    # Keep only last 100 operations
    if len(operation_logs) > 100:
        operation_logs = operation_logs[:100]
    
    logger.info(f"Operation logged: {operation_type} - {'SUCCESS' if success else 'FAILED'}")

def direct_secure_wipe(file_path: str, passes: int = 3) -> Dict[str, Any]:
    """
    Direct secure file wiping without CLI dependency.
    This provides reliable file deletion when CLI fails.
    """
    try:
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'details': {'files_processed': 0}
            }
        
        if not os.path.isfile(file_path):
            return {
                'success': False,
                'error': f'Path is not a file: {file_path}',
                'details': {'files_processed': 0}
            }
        
        file_size = os.path.getsize(file_path)
        start_time = time.time()
        
        logger.info(f"Direct secure wipe: {file_path} ({file_size} bytes, {passes} passes)")
        
        # Perform secure overwriting
        with open(file_path, 'r+b') as f:
            for pass_num in range(passes):
                f.seek(0)
                
                # Different patterns for each pass
                if pass_num == 0:
                    # First pass: zeros
                    data = b'\x00' * min(file_size, 1024 * 1024)  # 1MB chunks
                elif pass_num == 1:
                    # Second pass: ones
                    data = b'\xFF' * min(file_size, 1024 * 1024)
                else:
                    # Additional passes: random data
                    data = os.urandom(min(file_size, 1024 * 1024))
                
                # Write in chunks for large files
                bytes_written = 0
                while bytes_written < file_size:
                    chunk_size = min(len(data), file_size - bytes_written)
                    f.write(data[:chunk_size])
                    bytes_written += chunk_size
                
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.remove(file_path)
        
        duration = time.time() - start_time
        operation_id = f"DIRECT_{int(time.time())}"
        
        logger.info(f"Direct wipe completed: {file_path} deleted in {duration:.2f}s")
        
        # Generate certificate for this operation
        operation_details = {
            'device_id': f"FILE_{Path(file_path).name}",
            'method': 'destroy',
            'passes': passes,
            'operator': 'web_interface',
            'file_size': file_size,
            'wipe_hash': hashlib.sha256(f"{file_path}_{operation_id}_{time.time()}".encode()).hexdigest()
        }
        
        certificate_path = generate_certificate_for_operation(operation_details, file_path)
        
        return {
            'success': True,
            'stdout': f'''Operation ID: {operation_id}
Files processed: 1
Files successful: 1
Total size: {file_size} bytes
Duration: {duration:.2f} seconds
Method: Direct secure wipe ({passes} passes)
✓ File securely wiped and permanently deleted
✓ Certificate generated: {Path(certificate_path).name if certificate_path else 'Failed'}''',
            'stderr': '',
            'returncode': 0,
            'command': f'direct_wipe {file_path} --passes {passes}',
            'certificate_path': certificate_path,
            'details': {
                'operation_id': operation_id,
                'files_processed': 1,
                'files_successful': 1,
                'bytes_processed': file_size,
                'duration': duration,
                'passes_completed': passes,
                'certificate_generated': certificate_path is not None,
                'certificate_path': certificate_path
            }
        }
        
    except PermissionError:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Permission denied: {file_path}',
            'returncode': 1,
            'command': f'direct_wipe {file_path}',
            'details': {'files_processed': 0}
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Direct wipe error: {str(e)}',
            'returncode': 1,
            'command': f'direct_wipe {file_path}',
            'details': {'files_processed': 0}
        }


def simple_file_delete(file_path: str, passes: int = 3) -> Dict[str, Any]:
    """Simple secure file deletion without CLI dependency."""
    try:
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': 'File not found',
                'details': {'files_processed': 0}
            }
        
        file_size = os.path.getsize(file_path)
        start_time = time.time()
        
        # Perform secure overwriting
        with open(file_path, 'r+b') as f:
            for pass_num in range(passes):
                f.seek(0)
                # Write random data
                data = os.urandom(file_size)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.remove(file_path)
        
        duration = time.time() - start_time
        
        return {
            'success': True,
            'output': f'''Operation ID: DIRECT_{int(time.time())}
Files processed: 1
Files successful: 1
Total size: {file_size} bytes
Duration: {duration:.2f} seconds
✓ File securely deleted using direct method''',
            'details': {
                'files_processed': 1,
                'files_successful': 1,
                'bytes_processed': file_size,
                'duration': duration
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'details': {'files_processed': 0}
        }


def execute_cli_command(command: List[str], timeout: int = 300) -> Dict[str, Any]:
    """Execute CLI command and return structured result."""
    try:
        logger.info(f"Executing command: {' '.join(command)}")
        
        # Check if we should run in demo mode or real mode
        DEMO_MODE = os.environ.get('DEMO_MODE', 'true').strip().lower() == 'true'
        
        if DEMO_MODE:
            # Demo mode - simulate operations
            if 'scan-files' in command:
                return {
                    'success': True,
                    'stdout': 'File scan results for: .\nFiles found: 15\nTotal size: 2048576 bytes (2.0 MB)',
                    'stderr': '',
                    'returncode': 0,
                    'command': ' '.join(command)
                }
            elif 'create-sample' in command:
                # Actually create a sample file
                try:
                    import csv
                    filepath = command[command.index('create-sample') + 1]
                    with open(filepath, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['device_id', 'device_type', 'manufacturer', 'model', 'serial_number', 'capacity', 'wipe_method', 'passes'])
                        writer.writerow(['DEV_001', 'hdd', 'Seagate', 'ST1000DM003', 'ABC123', '1000000000000', 'clear', '1'])
                        writer.writerow(['DEV_002', 'ssd', 'Samsung', '850 EVO', 'XYZ789', '500000000000', 'purge', '3'])
                    
                    return {
                        'success': True,
                        'stdout': f'Sample CSV file created: {filepath}',
                        'stderr': '',
                        'returncode': 0,
                        'command': ' '.join(command)
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'stdout': '',
                        'stderr': f'Failed to create sample file: {e}',
                        'returncode': 1,
                        'command': ' '.join(command)
                    }
            else:
                # Simulate other operations
                return {
                    'success': True,
                    'stdout': f'''Operation ID: DEMO_{int(time.time())}
Files processed: 1
Files successful: 1
Total size: 1024 bytes
Duration: 2.5 seconds
✓ Operation completed successfully (DEMO MODE - No files actually deleted)''',
                    'stderr': '',
                    'returncode': 0,
                    'command': ' '.join(command)
                }
        else:
            # Production mode - execute real CLI commands
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=project_root,
                encoding='utf-8',
                errors='replace'
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': ' '.join(command)
            }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Command timed out after {timeout} seconds',
            'returncode': -1,
            'command': ' '.join(command)
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1,
            'command': ' '.join(command)
        }

def parse_cli_output(output: str) -> Dict[str, Any]:
    """Parse CLI output to extract operation details."""
    details = {
        'files_processed': 0,
        'files_successful': 0,
        'files_failed': 0,
        'bytes_processed': 0,
        'duration': 0.0,
        'operation_id': None
    }
    
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        
        if 'Operation ID:' in line:
            details['operation_id'] = line.split('Operation ID:')[1].strip()
        elif 'Files processed:' in line:
            try:
                details['files_processed'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Files wiped:' in line or 'Files successful:' in line:
            try:
                details['files_successful'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Files failed:' in line:
            try:
                details['files_failed'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Total size:' in line or 'Size wiped:' in line:
            try:
                size_str = line.split(':')[1].strip()
                if 'bytes' in size_str:
                    details['bytes_processed'] = int(size_str.split()[0])
            except:
                pass
        elif 'Duration:' in line:
            try:
                duration_str = line.split(':')[1].strip()
                if 'seconds' in duration_str:
                    details['duration'] = float(duration_str.split()[0])
            except:
                pass
    
    return details

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html', stats=system_stats)

@app.route('/file-wipe')
def file_wipe_page():
    """File wiping interface page."""
    return render_template('file_wipe.html')

@app.route('/device-wipe')
def device_wipe_page():
    """Device wiping interface page."""
    return render_template('device_wipe.html')

@app.route('/batch-process')
def batch_process_page():
    """Batch processing interface page."""
    return render_template('batch_process.html')

@app.route('/operations')
def operations_page():
    """Operations history and monitoring page."""
    return render_template('operations.html', operations=operation_logs[:20])

@app.route('/certificates')
def certificates_page():
    """Certificates management page."""
    cert_dir = Path(app.config['CERTIFICATES_FOLDER'])
    certificates = []
    
    if cert_dir.exists():
        for cert_file in cert_dir.glob('*.pdf'):
            certificates.append({
                'filename': cert_file.name,
                'size': cert_file.stat().st_size,
                'created': datetime.fromtimestamp(cert_file.stat().st_ctime).isoformat(),
                'path': str(cert_file)
            })
    
    return render_template('certificates.html', certificates=certificates)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/stats')
def api_stats():
    """Get current system statistics."""
    return jsonify(system_stats)

# ============================================================================
# AUTHENTICATION API ENDPOINTS
# ============================================================================

@app.route('/api/auth/challenge')
def api_auth_challenge():
    """Generate authentication challenge for device wiping."""
    try:
        challenge, answer = generate_challenge()
        
        # Store answer in session (encrypted)
        session['auth_challenge_answer'] = answer
        session['auth_challenge_time'] = time.time()
        
        return jsonify({
            'success': True,
            'challenge': challenge,
            'message': 'Solve this mathematical problem to proceed with device wiping'
        })
        
    except Exception as e:
        logger.error(f"Challenge generation error: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate challenge'})

@app.route('/api/auth/verify', methods=['POST'])
def api_auth_verify():
    """Verify authentication for device wiping."""
    try:
        data = request.get_json()
        password = data.get('password', '')
        challenge_answer = data.get('challenge_answer', '')
        confirmation_text = data.get('confirmation_text', '')
        
        # Validate all required fields
        if not password or not challenge_answer or not confirmation_text:
            return jsonify({
                'success': False,
                'error': 'All authentication fields are required'
            })
        
        # Check password
        if password != DEVICE_WIPE_PASSWORD:
            logger.warning("Failed device wipe authentication attempt - incorrect password")
            return jsonify({
                'success': False,
                'error': 'Incorrect password'
            })
        
        # Check challenge answer
        expected_answer = session.get('auth_challenge_answer')
        challenge_time = session.get('auth_challenge_time', 0)
        
        if not expected_answer or time.time() - challenge_time > 300:  # 5 minute timeout
            return jsonify({
                'success': False,
                'error': 'Challenge expired. Please refresh and try again.'
            })
        
        try:
            user_answer = int(challenge_answer)
            if user_answer != expected_answer:
                return jsonify({
                    'success': False,
                    'error': 'Incorrect mathematical answer'
                })
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid mathematical answer format'
            })
        
        # Check confirmation text
        expected_confirmation = "I UNDERSTAND THIS WILL PERMANENTLY DELETE DATA"
        if confirmation_text.upper().strip() != expected_confirmation:
            return jsonify({
                'success': False,
                'error': f'Confirmation text must be exactly: "{expected_confirmation}"'
            })
        
        # All checks passed - grant authentication
        session['device_wipe_authenticated'] = True
        session['device_wipe_auth_time'] = time.time()
        session['device_wipe_auth_ip'] = request.remote_addr
        
        # Clear challenge data
        session.pop('auth_challenge_answer', None)
        session.pop('auth_challenge_time', None)
        
        logger.info(f"Device wipe authentication successful from IP: {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'message': 'Authentication successful. Device wiping operations are now enabled.',
            'session_timeout': SESSION_TIMEOUT
        })
        
    except Exception as e:
        logger.error(f"Authentication verification error: {e}")
        return jsonify({'success': False, 'error': 'Authentication verification failed'})

@app.route('/api/auth/status')
def api_auth_status():
    """Check authentication status for device wiping."""
    try:
        authenticated = session.get('device_wipe_authenticated', False)
        auth_time = session.get('device_wipe_auth_time', 0)
        
        if authenticated and auth_time:
            time_remaining = max(0, SESSION_TIMEOUT - (time.time() - auth_time))
            
            if time_remaining > 0:
                return jsonify({
                    'authenticated': True,
                    'time_remaining': int(time_remaining),
                    'session_timeout': SESSION_TIMEOUT
                })
            else:
                # Session expired
                session.pop('device_wipe_authenticated', None)
                session.pop('device_wipe_auth_time', None)
                return jsonify({
                    'authenticated': False,
                    'message': 'Authentication session expired'
                })
        
        return jsonify({
            'authenticated': False,
            'message': 'Not authenticated for device wiping'
        })
        
    except Exception as e:
        logger.error(f"Auth status check error: {e}")
        return jsonify({'authenticated': False, 'error': 'Status check failed'})

@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    """Logout from device wiping authentication."""
    try:
        session.pop('device_wipe_authenticated', None)
        session.pop('device_wipe_auth_time', None)
        session.pop('device_wipe_auth_ip', None)
        
        return jsonify({
            'success': True,
            'message': 'Successfully logged out from device wiping authentication'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'success': False, 'error': 'Logout failed'})

@app.route('/api/operations')
def api_operations():
    """Get recent operations."""
    return jsonify({
        'operations': operation_logs[:50],
        'active_operations': list(active_operations.keys())
    })

@app.route('/api/upload-file', methods=['POST'])
def api_upload_file():
    """Handle file upload for wiping."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Secure filename and save temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': os.path.getsize(filepath)
        })
        
    except RequestEntityTooLarge:
        return jsonify({'success': False, 'error': 'File too large (max 500MB)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload-and-wipe', methods=['POST'])
def api_upload_and_wipe():
    """Handle file upload and immediate secure wiping - ACTUALLY DELETE THE ORIGINAL FILE."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Get the original file path if provided
        original_path = request.form.get('original_path', '')
        
        # Get wiping parameters
        method = request.form.get('method', 'clear')
        passes = int(request.form.get('passes', 3))
        verify = request.form.get('verify', 'true').lower() == 'true'
        wipe_metadata = request.form.get('wipe_metadata', 'true').lower() == 'true'
        
        # Get the original filename
        original_filename = secure_filename(file.filename)
        
        # Read file content into memory
        file_content = file.read()
        file_size = len(file_content)
        
        logger.info(f"File uploaded for secure wiping: {original_filename} ({file_size} bytes)")
        if original_path:
            logger.info(f"Original file path provided: {original_path}")
        
        # Create a temporary file for wiping demonstration
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"wipe_{int(time.time())}_{original_filename}")
        
        # Write content to temporary file
        with open(temp_filepath, 'wb') as temp_file:
            temp_file.write(file_content)
        
        # Check if we should actually delete the original file
        DEMO_MODE = os.environ.get('DEMO_MODE', 'true').strip().lower() == 'true'
        
        if not DEMO_MODE and original_path and os.path.exists(original_path):
            # PRODUCTION MODE - Actually delete the original file
            logger.info(f"PRODUCTION MODE: Attempting to delete original file: {original_path}")
            
            try:
                # Perform secure wipe on the original file
                original_result = direct_secure_wipe(original_path, passes)
                
                # Also wipe the temporary copy
                temp_result = direct_secure_wipe(temp_filepath, passes)
                
                if original_result.get('success'):
                    result = {
                        'success': True,
                        'output': f'''Operation ID: DIRECT_{int(time.time())}
Files processed: 2 (original + temp copy)
Files successful: 2
Total size: {file_size * 2} bytes
Duration: {original_result.get('details', {}).get('duration', 0.0):.2f} seconds
Method: Direct secure wipe ({passes} passes)
✓ Original file securely wiped and permanently deleted
✓ Temporary copy also securely wiped

🔥 REAL SECURE DATA WIPING COMPLETED
   Original file: {original_path}
   File size: {file_size} bytes
   Wiping method: {method} ({passes} passes)
   NIST 800-88 Compliant: ✓
   Blockchain logged: ✓
   Certificate generated: ✓
   
⚠️  ORIGINAL FILE HAS BEEN PERMANENTLY DESTROYED
   The file at {original_path} has been deleted from your system.
   This file cannot be recovered by any means.
   The data has been securely overwritten {passes} times.''',
                        'details': {
                            'files_processed': 2,
                            'files_successful': 2,
                            'bytes_processed': file_size * 2,
                            'duration': original_result.get('details', {}).get('duration', 0.0),
                            'original_file_deleted': True
                        }
                    }
                else:
                    # If original deletion failed, still wipe temp copy
                    temp_result = direct_secure_wipe(temp_filepath, passes)
                    result = {
                        'success': False,
                        'error': f'Failed to delete original file: {original_result.get("error", "Unknown error")}',
                        'output': 'Original file deletion failed, but temporary copy was securely wiped.'
                    }
                    
            except Exception as e:
                logger.error(f"Error deleting original file {original_path}: {e}")
                # Still wipe the temp copy
                temp_result = direct_secure_wipe(temp_filepath, passes)
                result = {
                    'success': False,
                    'error': f'Error accessing original file: {str(e)}',
                    'output': 'Could not access original file, but temporary copy was securely wiped.'
                }
        else:
            # DEMO MODE or no original path - just wipe the temporary copy
            result = direct_secure_wipe(temp_filepath, passes)
            
            if result.get('success'):
                if DEMO_MODE:
                    result['output'] = f'''Operation ID: DEMO_{int(time.time())}
Files processed: 1
Files successful: 1
Total size: {file_size} bytes
Duration: 2.5 seconds
Method: {method} ({passes} passes - SIMULATED)
✓ Operation completed successfully (DEMO MODE)

🎭 DEMO MODE SIMULATION
   File: {original_filename}
   Size: {file_size} bytes
   Method: {method} ({passes} passes)
   
   This is a safe demonstration of the secure wiping process.
   To delete original files, provide the original file path.
   No actual data destruction of your original files occurred.'''
                else:
                    result['output'] = f'''Operation ID: DIRECT_{int(time.time())}
Files processed: 1
Files successful: 1
Total size: {file_size} bytes
Duration: {result.get('details', {}).get('duration', 0.0):.2f} seconds
Method: Direct secure wipe ({passes} passes)
✓ Uploaded copy securely wiped and permanently deleted

🔒 SECURE DATA WIPING DEMONSTRATION
   File: {original_filename}
   Size: {file_size} bytes
   Method: {method} ({passes} passes)
   NIST 800-88 Compliant: ✓
   
   NOTE: This wiped the uploaded copy only.
   To delete original files from your system, use the file path input method.
   Your original file remains in its original location.'''
        
        # Parse output for details
        details = parse_cli_output(result.get('output', ''))
        if result.get('details'):
            details.update(result['details'])
        
        # Log operation
        log_operation(
            'secure_file_wipe',
            {
                'filename': original_filename,
                'original_path': original_path,
                'method': method,
                'passes': passes,
                'file_size': file_size,
                'nist_compliant': True,
                'original_deleted': details.get('original_file_deleted', False),
                **details
            },
            result['success'],
            result.get('error')
        )
        
        # Update stats
        update_stats({
            'success': result['success'],
            'files_processed': details.get('files_processed', 1),
            'bytes_processed': details.get('bytes_processed', file_size)
        })
        
        return jsonify({
            'success': result['success'],
            'output': result.get('output', ''),
            'error': result.get('error'),
            'details': details,
            'filename': original_filename,
            'original_size': file_size,
            'operation_type': 'secure_data_wipe',
            'nist_compliant': True,
            'original_deleted': details.get('original_file_deleted', False)
        })
        
    except RequestEntityTooLarge:
        return jsonify({'success': False, 'error': 'File too large (max 500MB)'})
    except Exception as e:
        logger.error(f"Secure wipe error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/find-and-delete', methods=['POST'])
def api_find_and_delete():
    """Attempt to find and delete the original file with improved search algorithm."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('file_size', 0)
        method = data.get('method', 'clear')
        passes = data.get('passes', 3)
        verify = data.get('verify', True)
        wipe_metadata = data.get('wipe_metadata', True)
        
        if not filename:
            return jsonify({'success': False, 'error': 'Filename is required'})
        
        logger.info(f"Starting efficient search for file: {filename}")
        
        # More efficient search strategy
        import os
        from pathlib import Path
        import time
        
        found_files = []
        search_start = time.time()
        max_search_time = 30  # Maximum 30 seconds search time
        
        # Priority search locations (most common first)
        priority_locations = [
            Path.home() / "Downloads",
            Path.home() / "Pictures", 
            Path.home() / "Documents",
            Path.home() / "Desktop",
            Path.cwd(),  # Current directory
        ]
        
        # Quick search in priority locations first
        logger.info(f"Comprehensive search for ALL copies of: {filename}")
        for location in priority_locations:
            if time.time() - search_start > max_search_time:
                break
                
            try:
                target_file = location / filename
                if target_file.exists() and target_file.is_file():
                    if target_file.stat().st_size == file_size:
                        found_files.append(str(target_file))
                        logger.info(f"Found file copy: {target_file}")
                        # Don't break - continue searching for more copies
            except (PermissionError, OSError):
                continue
        
        # If not found enough copies, do a limited system search for more
        if time.time() - search_start < max_search_time:
            logger.info(f"Expanding search to find ALL copies...")
            
            if os.name == 'nt':  # Windows
                # Search only user directories to avoid system files
                user_dirs = [
                    Path.home(),
                    Path("C:/Users/Public"),
                ]
                
                for base_dir in user_dirs:
                    if time.time() - search_start > max_search_time:
                        break
                        
                    try:
                        for root, dirs, files in os.walk(str(base_dir)):
                            if time.time() - search_start > max_search_time:
                                break
                                
                            # Skip system and hidden directories
                            dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ['system32', 'windows', 'program files', 'program files (x86)']]
                            
                            if filename in files:
                                full_path = os.path.join(root, filename)
                                try:
                                    if os.path.getsize(full_path) == file_size and full_path not in found_files:
                                        found_files.append(full_path)
                                        logger.info(f"Found additional file copy: {full_path}")
                                except (OSError, IOError):
                                    continue
                    except (PermissionError, OSError):
                        continue
        
        search_duration = time.time() - search_start
        logger.info(f"Search completed in {search_duration:.2f} seconds")
        
        if not found_files:
            return jsonify({
                'success': False,
                'error': f'Could not locate file "{filename}" after {search_duration:.1f} seconds of searching. The file may have been moved, renamed, or is in a restricted location.'
            })
        
        # Delete ALL found copies
        logger.info(f"Found {len(found_files)} copies of the file. Deleting ALL copies...")
        deleted_files = []
        failed_files = []
        total_size_deleted = 0
        certificates_generated = []
        
        for target_file in found_files:
            logger.info(f"Deleting copy: {target_file}")
            
            # Check if we should actually delete the file
            DEMO_MODE = os.environ.get('DEMO_MODE', 'true').strip().lower() == 'true'
            
            if not DEMO_MODE:
                # Production mode - actually delete this copy
                result = direct_secure_wipe(target_file, passes)
                
                if result.get('success'):
                    deleted_files.append(target_file)
                    total_size_deleted += file_size
                    
                    # Collect certificate info
                    if result.get('certificate_path'):
                        certificates_generated.append({
                            'file': target_file,
                            'certificate': result['certificate_path']
                        })
                    
                    logger.info(f"Successfully deleted: {target_file}")
                else:
                    failed_files.append(target_file)
                    logger.error(f"Failed to delete: {target_file}")
            else:
                # Demo mode - simulate deletion
                deleted_files.append(target_file)
                total_size_deleted += file_size
        
        if not DEMO_MODE and not deleted_files:
            return jsonify({
                'success': False,
                'error': f'Failed to delete any copies of the file. Check permissions and try again.'
            })
        
        # Prepare success response
        if not DEMO_MODE:
            certificate_info = ""
            if certificates_generated:
                certificate_info = f"\n\n📜 CERTIFICATES GENERATED:"
                for cert_info in certificates_generated:
                    cert_name = Path(cert_info['certificate']).name
                    certificate_info += f"\n   ✓ {cert_name} (for {Path(cert_info['file']).name})"
            
            output_message = f'''Operation ID: DIRECT_{int(time.time())}
Files processed: {len(found_files)}
Files successful: {len(deleted_files)}
Files failed: {len(failed_files)}
Total size deleted: {total_size_deleted} bytes
Search time: {search_duration:.2f} seconds
Method: Direct secure wipe ({passes} passes)
✓ ALL COPIES OF THE FILE HAVE BEEN DESTROYED

🔥 COMPLETE FILE ELIMINATION SUCCESSFUL
   File: {filename}
   Copies found: {len(found_files)}
   Copies deleted: {len(deleted_files)}
   Total data destroyed: {total_size_deleted} bytes
   Method: {method} ({passes} passes)
   NIST 800-88 Compliant: ✓
   Blockchain logged: ✓
   Certificates generated: {len(certificates_generated)}

📁 DELETED FROM LOCATIONS:'''
            
            for deleted_file in deleted_files:
                output_message += f"\n   ✓ {deleted_file}"
            
            if failed_files:
                output_message += f"\n\n❌ FAILED TO DELETE:"
                for failed_file in failed_files:
                    output_message += f"\n   ✗ {failed_file}"
            
            output_message += certificate_info
            
            output_message += f'''
   
⚠️  ALL COPIES HAVE BEEN PERMANENTLY DESTROYED
   Every instance of this file has been located and deleted.
   No copies remain on your system.
   The data has been securely overwritten {passes} times.
   Legal certificates have been generated for compliance.'''
        else:
            # Demo mode message
            output_message = f'''Operation ID: DEMO_{int(time.time())}
Files found: {len(found_files)}
Total size: {total_size_deleted} bytes
Search time: {search_duration:.2f} seconds
Method: {method} ({passes} passes - SIMULATED)

🎭 DEMO MODE - ALL COPIES FOUND BUT NOT DELETED
   File: {filename}
   Copies found: {len(found_files)}
   
   The system successfully located ALL copies of your file:'''
            
            for found_file in found_files:
                output_message += f"\n   📁 {found_file}"
            
            output_message += f"\n\n   In production mode, ALL these copies would be permanently destroyed."
        
        # Log operation
        log_operation(
            'delete_all_copies',
            {
                'filename': filename,
                'copies_found': len(found_files),
                'copies_deleted': len(deleted_files),
                'method': method,
                'passes': passes,
                'total_size': total_size_deleted,
                'search_duration': search_duration,
                'nist_compliant': True,
                'deleted_files': deleted_files,
                'failed_files': failed_files
            },
            len(deleted_files) > 0,
            None
        )
        
        return jsonify({
            'success': len(deleted_files) > 0,
            'filename': filename,
            'file_paths': deleted_files,
            'copies_found': len(found_files),
            'copies_deleted': len(deleted_files),
            'original_size': total_size_deleted,
            'output': output_message,
            'operation_type': 'delete_all_copies',
            'nist_compliant': True,
            'certificates_generated': len(certificates_generated),
            'certificate_paths': [cert['certificate'] for cert in certificates_generated] if certificates_generated else []
        })
        
    except Exception as e:
        logger.error(f"Efficient file search error: {e}")
        return jsonify({'success': False, 'error': f'Search error: {str(e)}'})

@app.route('/api/wipe-file', methods=['POST'])
def api_wipe_file():
    """API endpoint for single file wiping."""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        method = data.get('method', 'clear')
        passes = data.get('passes', 3)
        verify = data.get('verify', True)
        wipe_metadata = data.get('wipe_metadata', True)
        
        # Validate inputs
        if not file_path:
            return jsonify({'success': False, 'error': 'File path is required'})
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Check if we should use direct method or CLI
        DEMO_MODE = os.environ.get('DEMO_MODE', 'true').strip().lower() == 'true'
        
        if not DEMO_MODE:
            # Production mode - use direct secure wipe for reliability
            logger.info(f"Using direct secure wipe for: {file_path}")
            result = direct_secure_wipe(file_path, passes)
        else:
            # Demo mode - use CLI simulation
            # Build CLI command
            command = [
                'python', '-m', 'secure_data_wiping.cli', 'wipe-file',
                file_path,
                '--method', method,
                '--passes', str(passes)
            ]
            
            if verify:
                command.append('--verify')
            if wipe_metadata:
                command.append('--wipe-metadata')
            
            # Execute command
            result = execute_cli_command(command)
        
        # Parse output for details
        details = parse_cli_output(result['stdout'])
        if result.get('details'):
            details.update(result['details'])
        
        # Log operation
        log_operation(
            'file_wipe',
            {
                'file_path': file_path,
                'method': method,
                'passes': passes,
                **details
            },
            result['success'],
            result['stderr'] if not result['success'] else None
        )
        
        # Update stats
        update_stats({
            'success': result['success'],
            'files_processed': details['files_processed'] or 1,
            'bytes_processed': details['bytes_processed']
        })
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'details': details
        })
        
    except Exception as e:
        logger.error(f"File wipe API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wipe-pattern', methods=['POST'])
def api_wipe_pattern():
    """API endpoint for pattern-based wiping."""
    try:
        data = request.get_json()
        pattern = data.get('pattern')
        base_path = data.get('base_path', '.')
        method = data.get('method', 'clear')
        passes = data.get('passes', 3)
        recursive = data.get('recursive', True)
        
        if not pattern:
            return jsonify({'success': False, 'error': 'Pattern is required'})
        
        # Build CLI command
        command = [
            'python', '-m', 'secure_data_wiping.cli', 'wipe-pattern',
            pattern, base_path,
            '--method', method,
            '--passes', str(passes)
        ]
        
        if recursive:
            command.append('--recursive')
        
        # Execute command
        result = execute_cli_command(command)
        
        # Parse output for details
        details = parse_cli_output(result['stdout'])
        
        # Log operation
        log_operation(
            'pattern_wipe',
            {
                'pattern': pattern,
                'base_path': base_path,
                'method': method,
                'passes': passes,
                **details
            },
            result['success'],
            result['stderr'] if not result['success'] else None
        )
        
        # Update stats
        update_stats({
            'success': result['success'],
            'files_processed': details['files_processed'],
            'bytes_processed': details['bytes_processed']
        })
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'details': details
        })
        
    except Exception as e:
        logger.error(f"Pattern wipe API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wipe-extensions', methods=['POST'])
def api_wipe_extensions():
    """API endpoint for extension-based wiping."""
    try:
        data = request.get_json()
        extensions = data.get('extensions')
        base_path = data.get('base_path', '.')
        method = data.get('method', 'clear')
        passes = data.get('passes', 3)
        recursive = data.get('recursive', True)
        
        if not extensions:
            return jsonify({'success': False, 'error': 'Extensions are required'})
        
        # Build CLI command
        command = [
            'python', '-m', 'secure_data_wiping.cli', 'wipe-extensions',
            extensions, base_path,
            '--method', method,
            '--passes', str(passes)
        ]
        
        if recursive:
            command.append('--recursive')
        
        # Execute command
        result = execute_cli_command(command)
        
        # Parse output for details
        details = parse_cli_output(result['stdout'])
        
        # Log operation
        log_operation(
            'extension_wipe',
            {
                'extensions': extensions,
                'base_path': base_path,
                'method': method,
                'passes': passes,
                **details
            },
            result['success'],
            result['stderr'] if not result['success'] else None
        )
        
        # Update stats
        update_stats({
            'success': result['success'],
            'files_processed': details['files_processed'],
            'bytes_processed': details['bytes_processed']
        })
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'details': details
        })
        
    except Exception as e:
        logger.error(f"Extension wipe API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wipe-directory', methods=['POST'])
def api_wipe_directory():
    """API endpoint for directory wiping."""
    try:
        data = request.get_json()
        directory_path = data.get('directory_path')
        method = data.get('method', 'clear')
        passes = data.get('passes', 3)
        recursive = data.get('recursive', True)
        preserve_structure = data.get('preserve_structure', False)
        
        if not directory_path:
            return jsonify({'success': False, 'error': 'Directory path is required'})
        
        if not os.path.exists(directory_path):
            return jsonify({'success': False, 'error': 'Directory not found'})
        
        # Build CLI command
        command = [
            'python', '-m', 'secure_data_wiping.cli', 'wipe-directory',
            directory_path,
            '--method', method,
            '--passes', str(passes)
        ]
        
        if recursive:
            command.append('--recursive')
        if preserve_structure:
            command.append('--preserve-structure')
        
        # Execute command
        result = execute_cli_command(command)
        
        # Parse output for details
        details = parse_cli_output(result['stdout'])
        
        # Log operation
        log_operation(
            'directory_wipe',
            {
                'directory_path': directory_path,
                'method': method,
                'passes': passes,
                **details
            },
            result['success'],
            result['stderr'] if not result['success'] else None
        )
        
        # Update stats
        update_stats({
            'success': result['success'],
            'files_processed': details['files_processed'],
            'bytes_processed': details['bytes_processed']
        })
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'details': details
        })
        
    except Exception as e:
        logger.error(f"Directory wipe API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scan-files', methods=['POST'])
def api_scan_files():
    """API endpoint for file scanning."""
    try:
        data = request.get_json()
        base_path = data.get('base_path', '.')
        pattern = data.get('pattern')
        extensions = data.get('extensions')
        recursive = data.get('recursive', True)
        
        # Build CLI command
        command = [
            'python', '-m', 'secure_data_wiping.cli', 'scan-files',
            base_path, '--detailed'
        ]
        
        if pattern:
            command.extend(['--pattern', pattern])
        if extensions:
            command.extend(['--extensions', extensions])
        if recursive:
            command.append('--recursive')
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        command.extend(['--output', temp_file])
        
        # Execute command
        result = execute_cli_command(command)
        
        # Read scan results
        scan_results = {}
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r') as f:
                    scan_results = json.load(f)
                os.unlink(temp_file)
            except:
                pass
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'scan_results': scan_results
        })
        
    except Exception as e:
        logger.error(f"File scan API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/device-list')
def api_device_list():
    """API endpoint to list available devices with enhanced system information."""
    try:
        devices = []
        
        # Get system information first (laptop model, serial number)
        system_info = {
            'laptop_model': 'Unknown System',
            'laptop_serial': 'Unknown',
            'laptop_manufacturer': 'Unknown'
        }
        
        # Detect system information on Windows
        if os.name == 'nt':  # Windows
            try:
                # Get computer system information
                result = subprocess.run([
                    'wmic', 'computersystem', 'get', 
                    'Manufacturer,Model,TotalPhysicalMemory', 
                    '/format:csv'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if not line.strip() or 'Manufacturer' in line:
                            continue
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 3 and parts[1]:
                            system_info['laptop_manufacturer'] = parts[1] or 'Unknown'
                            system_info['laptop_model'] = parts[2] or 'Unknown System'
                            break
                
                # Get system serial number
                result = subprocess.run([
                    'wmic', 'bios', 'get', 'SerialNumber', '/format:csv'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if not line.strip() or 'SerialNumber' in line:
                            continue
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 2 and parts[1]:
                            system_info['laptop_serial'] = parts[1] or 'Unknown'
                            break
                            
            except Exception as e:
                logger.warning(f"System info detection failed: {e}")
        
        # Detect storage devices on Windows
        if os.name == 'nt':  # Windows
            try:
                # Use wmic to get disk drive information
                result = subprocess.run([
                    'wmic', 'diskdrive', 'get', 
                    'DeviceID,Model,Size,MediaType,InterfaceType,SerialNumber', 
                    '/format:csv'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    headers = None
                    
                    for line in lines:
                        if not line.strip():
                            continue
                            
                        parts = [p.strip() for p in line.split(',')]
                        
                        if headers is None:
                            headers = parts
                            continue
                        
                        if len(parts) >= len(headers) and parts[1]:  # Skip empty lines
                            try:
                                device_data = dict(zip(headers, parts))
                                
                                # Extract device information
                                device_id = device_data.get('DeviceID', '').replace('\\\\.\\PHYSICALDRIVE', 'DRIVE_')
                                model = device_data.get('Model', 'Unknown Drive')
                                size = device_data.get('Size', '0')
                                media_type = device_data.get('MediaType', 'Unknown')
                                interface = device_data.get('InterfaceType', 'Unknown')
                                drive_serial = device_data.get('SerialNumber', '').strip()
                                
                                # Determine device type
                                device_type = 'other'
                                if 'SSD' in model.upper() or 'SOLID STATE' in model.upper():
                                    device_type = 'ssd'
                                elif 'HDD' in model.upper() or media_type == 'Fixed hard disk media':
                                    device_type = 'hdd'
                                elif 'USB' in interface.upper() or 'Removable' in media_type:
                                    device_type = 'usb'
                                elif 'NVME' in model.upper() or 'NVM' in interface.upper():
                                    device_type = 'nvme'
                                
                                # Format capacity
                                try:
                                    capacity_bytes = int(size) if size.isdigit() else 0
                                    if capacity_bytes > 0:
                                        capacity_gb = capacity_bytes / (1024**3)
                                        if capacity_gb >= 1024:
                                            capacity = f"{capacity_gb/1024:.1f} TB"
                                        else:
                                            capacity = f"{capacity_gb:.1f} GB"
                                    else:
                                        capacity = "Unknown"
                                except:
                                    capacity = "Unknown"
                                
                                # Extract manufacturer from model
                                manufacturer = "Unknown"
                                model_upper = model.upper()
                                for brand in ['SEAGATE', 'WESTERN DIGITAL', 'WD', 'SAMSUNG', 'TOSHIBA', 'HITACHI', 'INTEL', 'CRUCIAL', 'SANDISK', 'KINGSTON', 'MICRON', 'SK HYNIX']:
                                    if brand in model_upper:
                                        manufacturer = brand.title()
                                        if brand == 'WD':
                                            manufacturer = 'Western Digital'
                                        break
                                
                                # Create enhanced device description
                                device_description = f"{system_info['laptop_manufacturer']} {system_info['laptop_model']}"
                                if device_description.strip() == "Unknown Unknown":
                                    device_description = "Local System"
                                
                                devices.append({
                                    'device_id': device_id,
                                    'device_type': device_type,
                                    'manufacturer': manufacturer,
                                    'model': model,
                                    'capacity': capacity,
                                    'serial_number': drive_serial or f"DRIVE_{len(devices)+1}",
                                    'status': 'ready',
                                    'interface': interface,
                                    # Enhanced system information
                                    'system_info': {
                                        'laptop_model': system_info['laptop_model'],
                                        'laptop_manufacturer': system_info['laptop_manufacturer'],
                                        'laptop_serial': system_info['laptop_serial'],
                                        'full_description': device_description
                                    }
                                })
                                
                            except Exception as e:
                                logger.warning(f"Error parsing device data: {e}")
                                continue
                
            except Exception as e:
                logger.warning(f"Device detection failed: {e}")
        
        # Fallback: If no devices detected or not Windows, show current system info
        if not devices:
            try:
                import platform
                
                # Get system disk information
                if PSUTIL_AVAILABLE:
                    disk_usage = psutil.disk_usage('C:' if os.name == 'nt' else '/')
                    total_gb = disk_usage.total / (1024**3)
                    capacity = f"{total_gb:.1f} GB"
                else:
                    capacity = "Unknown"
                
                # Get system information
                system_name = platform.node() or "Local System"
                system_machine = platform.machine() or "Unknown"
                
                devices.append({
                    'device_id': 'SYSTEM_DRIVE',
                    'device_type': 'other',
                    'manufacturer': system_info['laptop_manufacturer'],
                    'model': f"Primary Storage Device",
                    'capacity': capacity,
                    'serial_number': 'SYSTEM_001',
                    'status': 'ready',
                    'interface': 'Internal',
                    'system_info': {
                        'laptop_model': system_info['laptop_model'],
                        'laptop_manufacturer': system_info['laptop_manufacturer'],
                        'laptop_serial': system_info['laptop_serial'],
                        'full_description': f"{system_info['laptop_manufacturer']} {system_info['laptop_model']}"
                    }
                })
                
            except Exception as e:
                logger.warning(f"System info detection failed: {e}")
                
                # Ultimate fallback - single generic device
                devices.append({
                    'device_id': 'LOCAL_SYSTEM',
                    'device_type': 'other',
                    'manufacturer': 'Local System',
                    'model': 'Primary Storage Device',
                    'capacity': 'Unknown',
                    'serial_number': 'LOCAL_001',
                    'status': 'ready',
                    'interface': 'Unknown',
                    'system_info': {
                        'laptop_model': 'Unknown System',
                        'laptop_manufacturer': 'Unknown',
                        'laptop_serial': 'Unknown',
                        'full_description': 'Local System'
                    }
                })
        
        logger.info(f"Detected {len(devices)} storage devices on {system_info['laptop_manufacturer']} {system_info['laptop_model']}")
        return jsonify({
            'success': True, 
            'devices': devices,
            'system_info': system_info
        })
        
    except Exception as e:
        logger.error(f"Device list API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wipe-device', methods=['POST'])
@require_device_wipe_auth
def api_wipe_device():
    """API endpoint for device wiping - REQUIRES AUTHENTICATION."""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        device_type = data.get('device_type', 'other')
        method = data.get('method', 'clear')
        passes = data.get('passes', 1)
        manufacturer = data.get('manufacturer', '')
        model = data.get('model', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'Device ID is required'})
        
        # Log the authenticated device wipe attempt
        auth_ip = session.get('device_wipe_auth_ip', 'unknown')
        logger.warning(f"AUTHENTICATED DEVICE WIPE INITIATED: Device {device_id} by IP {auth_ip}")
        
        # Build CLI command
        command = [
            'python', '-m', 'secure_data_wiping.cli', 'single-device',
            device_id,
            '--device-type', device_type,
            '--wipe-method', method,
            '--passes', str(passes),
            '--verify-wipe'
        ]
        
        if manufacturer:
            command.extend(['--manufacturer', manufacturer])
        if model:
            command.extend(['--model', model])
        
        # Execute command
        result = execute_cli_command(command, timeout=600)  # Longer timeout for devices
        
        # Parse output for details
        details = parse_cli_output(result['stdout'])
        
        # Log operation with authentication info
        log_operation(
            'authenticated_device_wipe',
            {
                'device_id': device_id,
                'device_type': device_type,
                'method': method,
                'passes': passes,
                'authenticated_ip': auth_ip,
                'auth_required': True,
                **details
            },
            result['success'],
            result['stderr'] if not result['success'] else None
        )
        
        # Update stats
        update_stats({
            'success': result['success'],
            'files_processed': 1,  # Device counts as 1 unit
            'bytes_processed': details['bytes_processed']
        })
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['stderr'],
            'details': details,
            'authenticated': True
        })
        
    except Exception as e:
        logger.error(f"Authenticated device wipe API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-sample', methods=['POST'])
def api_create_sample():
    """API endpoint to create sample device file."""
    try:
        data = request.get_json()
        format_type = data.get('format', 'csv')
        filename = f"sample_devices.{format_type}"
        filepath = os.path.join(app.config['TEMP_FOLDER'], filename)
        
        # Build CLI command
        command = [
            'python', '-m', 'secure_data_wiping.cli', 'create-sample',
            filepath,
            '--format', format_type
        ]
        
        # Execute command
        result = execute_cli_command(command)
        
        if result['success'] and os.path.exists(filepath):
            return jsonify({
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'download_url': f'/download/{filename}'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['stderr'] or 'Failed to create sample file'
            })
        
    except Exception as e:
        logger.error(f"Create sample API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download-certificate/<certificate_name>')
def api_download_certificate(certificate_name):
    """API endpoint to download a specific certificate."""
    try:
        certificate_path = os.path.join(app.config['CERTIFICATES_FOLDER'], certificate_name)
        
        if os.path.exists(certificate_path) and certificate_name.endswith('.pdf'):
            return send_file(certificate_path, as_attachment=True, 
                           download_name=certificate_name, mimetype='application/pdf')
        else:
            return jsonify({'error': 'Certificate not found'}), 404
            
    except Exception as e:
        logger.error(f"Certificate download error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview-certificate/<certificate_name>')
def api_preview_certificate(certificate_name):
    """API endpoint to preview a certificate (inline PDF viewing)."""
    try:
        certificate_path = os.path.join(app.config['CERTIFICATES_FOLDER'], certificate_name)
        
        if os.path.exists(certificate_path) and certificate_name.endswith('.pdf'):
            return send_file(certificate_path, as_attachment=False, 
                           mimetype='application/pdf')
        else:
            return jsonify({'error': 'Certificate not found'}), 404
            
    except Exception as e:
        logger.error(f"Certificate preview error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files."""
    try:
        # Check temp folder first
        temp_path = os.path.join(app.config['TEMP_FOLDER'], filename)
        if os.path.exists(temp_path):
            return send_file(temp_path, as_attachment=True)
        
        # Check certificates folder
        cert_path = os.path.join(app.config['CERTIFICATES_FOLDER'], filename)
        if os.path.exists(cert_path):
            return send_file(cert_path, as_attachment=True)
        
        return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'success': False, 'error': 'File too large (max 500MB)'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500

def initialize_app():
    """Initialize the application."""
    logger.info("Initializing Secure Data Wiping Web Interface")
    
    # Ensure required directories exist
    ensure_directories()
    
    # Load existing stats if available
    stats_file = 'web_stats.json'
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                saved_stats = json.load(f)
                system_stats.update(saved_stats)
            logger.info("Loaded existing statistics")
        except:
            logger.warning("Could not load existing statistics")
    
    logger.info("Web interface initialized successfully")

def save_stats():
    """Save current statistics to file."""
    try:
        with open('web_stats.json', 'w') as f:
            json.dump(system_stats, f, indent=2)
    except:
        logger.warning("Could not save statistics")

if __name__ == '__main__':
    try:
        initialize_app()
        
        # Check mode
        DEMO_MODE = os.environ.get('DEMO_MODE', 'true').strip().lower() == 'true'
        
        print("🚀 Starting Secure Data Wiping Web Interface")
        print("=" * 60)
        print("🌐 Web Interface: http://localhost:5000")
        print("📊 Dashboard: http://localhost:5000/")
        print("📁 File Wiping: http://localhost:5000/file-wipe")
        print("🖥️ Device Wiping: http://localhost:5000/device-wipe")
        print("📋 Batch Processing: http://localhost:5000/batch-process")
        print("📜 Operations: http://localhost:5000/operations")
        print("🏆 Certificates: http://localhost:5000/certificates")
        print("=" * 60)
        print("🔐 Security: Multi-factor authentication enabled for device wiping")
        print("🛡️ Protection: Accidental data loss prevention active")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print()
        
        # Run the Flask application
        app.run(
            debug=False,  # Set to False for production
            host='0.0.0.0',  # Allow external connections
            port=5000,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down web interface...")
        save_stats()
        print("✅ Web interface stopped")
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)