"""
Offline Verification Module

Implements offline certificate verification functionality that works
without network access, providing local verification of certificates.
"""

import json
import hashlib
import qrcode
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict

from ..utils.data_models import WipeData, BlockchainData, DeviceInfo


class OfflineVerificationError(Exception):
    """Raised when offline verification fails."""
    pass


@dataclass
class VerificationData:
    """Data structure for offline verification."""
    certificate_hash: str
    wipe_hash: str
    device_id: str
    timestamp: str
    method: str
    operator: str
    blockchain_tx: str
    block_number: int
    verification_code: str
    generated_at: str


@dataclass
class VerificationResult:
    """Result of offline verification."""
    valid: bool
    certificate_hash: str
    wipe_hash: str
    device_id: str
    verification_details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


class OfflineVerifier:
    """
    Provides offline certificate verification functionality.
    
    Enables verification of certificates without requiring network access
    or connection to external services.
    """
    
    def __init__(self, verification_data_dir: str = "verification_data"):
        """
        Initialize the offline verifier.
        
        Args:
            verification_data_dir: Directory to store verification data
        """
        self.logger = logging.getLogger(__name__)
        self.verification_data_dir = Path(verification_data_dir)
        self.verification_data_dir.mkdir(exist_ok=True)
    
    def create_verification_data(self, wipe_data: WipeData, blockchain_data: BlockchainData,
                               device_info: DeviceInfo, certificate_path: str) -> VerificationData:
        """
        Create offline verification data for a certificate.
        
        Args:
            wipe_data: Wiping operation data
            blockchain_data: Blockchain transaction data
            device_info: Device information
            certificate_path: Path to the generated certificate
            
        Returns:
            VerificationData: Offline verification data
        """
        self.logger.info(f"Creating offline verification data for device {wipe_data.device_id}")
        
        try:
            # Calculate certificate hash
            certificate_hash = self._calculate_certificate_hash(certificate_path)
            
            # Generate verification code
            verification_code = self._generate_verification_code(
                wipe_data, blockchain_data, certificate_hash
            )
            
            # Create verification data
            verification_data = VerificationData(
                certificate_hash=certificate_hash,
                wipe_hash=wipe_data.wipe_hash,
                device_id=wipe_data.device_id,
                timestamp=wipe_data.timestamp.isoformat(),
                method=wipe_data.method,
                operator=wipe_data.operator,
                blockchain_tx=blockchain_data.transaction_hash,
                block_number=blockchain_data.block_number,
                verification_code=verification_code,
                generated_at=datetime.now().isoformat()
            )
            
            # Store verification data
            self._store_verification_data(verification_data)
            
            # Generate QR code for offline verification
            self._generate_verification_qr_code(verification_data)
            
            self.logger.info(f"Offline verification data created for device {wipe_data.device_id}")
            return verification_data
            
        except Exception as e:
            error_msg = f"Failed to create offline verification data: {e}"
            self.logger.error(error_msg)
            raise OfflineVerificationError(error_msg) from e
    
    def verify_certificate_offline(self, certificate_path: str, 
                                 verification_code: Optional[str] = None) -> VerificationResult:
        """
        Verify a certificate using offline verification data.
        
        Args:
            certificate_path: Path to the certificate to verify
            verification_code: Optional verification code for additional validation
            
        Returns:
            VerificationResult: Result of the verification
        """
        self.logger.info(f"Starting offline verification for certificate: {certificate_path}")
        
        errors = []
        warnings = []
        verification_details = {}
        
        try:
            # Calculate current certificate hash
            current_hash = self._calculate_certificate_hash(certificate_path)
            verification_details['current_certificate_hash'] = current_hash
            
            # Extract device ID from certificate (simplified - would parse PDF in real implementation)
            device_id = self._extract_device_id_from_certificate(certificate_path)
            verification_details['device_id'] = device_id
            
            if not device_id:
                errors.append("Could not extract device ID from certificate")
                return VerificationResult(
                    valid=False,
                    certificate_hash=current_hash,
                    wipe_hash="",
                    device_id="",
                    verification_details=verification_details,
                    errors=errors,
                    warnings=warnings
                )
            
            # Load stored verification data
            stored_data = self._load_verification_data(device_id)
            
            if not stored_data:
                errors.append(f"No verification data found for device {device_id}")
                return VerificationResult(
                    valid=False,
                    certificate_hash=current_hash,
                    wipe_hash="",
                    device_id=device_id,
                    verification_details=verification_details,
                    errors=errors,
                    warnings=warnings
                )
            
            verification_details['stored_data'] = asdict(stored_data)
            
            # Verify certificate hash
            if current_hash != stored_data.certificate_hash:
                errors.append("Certificate hash mismatch - certificate may have been modified")
            else:
                verification_details['certificate_integrity'] = 'VALID'
            
            # Verify verification code if provided
            if verification_code:
                if verification_code != stored_data.verification_code:
                    errors.append("Verification code mismatch")
                else:
                    verification_details['verification_code'] = 'VALID'
            
            # Additional integrity checks
            self._perform_integrity_checks(stored_data, verification_details, warnings)
            
            # Determine overall validity
            is_valid = len(errors) == 0
            
            result = VerificationResult(
                valid=is_valid,
                certificate_hash=current_hash,
                wipe_hash=stored_data.wipe_hash,
                device_id=device_id,
                verification_details=verification_details,
                errors=errors,
                warnings=warnings
            )
            
            self.logger.info(f"Offline verification completed for {device_id}: {'VALID' if is_valid else 'INVALID'}")
            return result
            
        except Exception as e:
            error_msg = f"Error during offline verification: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            
            return VerificationResult(
                valid=False,
                certificate_hash="",
                wipe_hash="",
                device_id="",
                verification_details=verification_details,
                errors=errors,
                warnings=warnings
            )
    
    def get_verification_summary(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get verification summary for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Optional[Dict]: Verification summary or None if not found
        """
        try:
            stored_data = self._load_verification_data(device_id)
            
            if not stored_data:
                return None
            
            return {
                'device_id': stored_data.device_id,
                'wipe_hash': stored_data.wipe_hash,
                'timestamp': stored_data.timestamp,
                'method': stored_data.method,
                'operator': stored_data.operator,
                'blockchain_tx': stored_data.blockchain_tx,
                'block_number': stored_data.block_number,
                'generated_at': stored_data.generated_at,
                'verification_available': True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting verification summary for {device_id}: {e}")
            return None
    
    def list_verifiable_certificates(self) -> List[Dict[str, Any]]:
        """
        List all certificates that have offline verification data.
        
        Returns:
            List[Dict]: List of verifiable certificates
        """
        certificates = []
        
        try:
            for verification_file in self.verification_data_dir.glob("*.json"):
                device_id = verification_file.stem
                summary = self.get_verification_summary(device_id)
                
                if summary:
                    certificates.append(summary)
            
        except Exception as e:
            self.logger.error(f"Error listing verifiable certificates: {e}")
        
        return certificates
    
    def _calculate_certificate_hash(self, certificate_path: str) -> str:
        """Calculate SHA-256 hash of certificate file."""
        try:
            with open(certificate_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating certificate hash: {e}")
            raise OfflineVerificationError(f"Cannot calculate certificate hash: {e}")
    
    def _generate_verification_code(self, wipe_data: WipeData, blockchain_data: BlockchainData,
                                  certificate_hash: str) -> str:
        """Generate verification code for offline verification."""
        # Combine key data elements for verification code
        verification_input = (
            f"{wipe_data.device_id}|"
            f"{wipe_data.wipe_hash}|"
            f"{wipe_data.timestamp.isoformat()}|"
            f"{blockchain_data.transaction_hash}|"
            f"{certificate_hash}"
        )
        
        # Generate SHA-256 hash and take first 16 characters for verification code
        verification_hash = hashlib.sha256(verification_input.encode()).hexdigest()
        return verification_hash[:16].upper()
    
    def _store_verification_data(self, verification_data: VerificationData):
        """Store verification data to local file."""
        file_path = self.verification_data_dir / f"{verification_data.device_id}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(asdict(verification_data), f, indent=2)
            
            self.logger.info(f"Verification data stored: {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to store verification data: {e}"
            self.logger.error(error_msg)
            raise OfflineVerificationError(error_msg)
    
    def _load_verification_data(self, device_id: str) -> Optional[VerificationData]:
        """Load verification data from local file."""
        file_path = self.verification_data_dir / f"{device_id}.json"
        
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                return VerificationData(**data)
                
        except Exception as e:
            self.logger.error(f"Error loading verification data for {device_id}: {e}")
            return None
    
    def _generate_verification_qr_code(self, verification_data: VerificationData):
        """Generate QR code for offline verification."""
        try:
            # Create verification URL (local only)
            verification_url = (
                f"verify://offline/{verification_data.device_id}?"
                f"code={verification_data.verification_code}&"
                f"hash={verification_data.wipe_hash[:16]}"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Save QR code image
            qr_path = self.verification_data_dir / f"{verification_data.device_id}_qr.png"
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save(qr_path)
            
            self.logger.info(f"Verification QR code generated: {qr_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate QR code: {e}")
    
    def _extract_device_id_from_certificate(self, certificate_path: str) -> Optional[str]:
        """Extract device ID from certificate (simplified implementation)."""
        try:
            # In a real implementation, this would parse the PDF
            # For now, extract from filename if it follows convention
            filename = Path(certificate_path).stem
            
            # Look for device ID pattern in filename
            if "certificate_" in filename:
                parts = filename.split("_")
                if len(parts) >= 2:
                    return parts[1]  # Assume device ID is after "certificate_"
            
            # Alternative: look for device ID in first part of filename
            if "_" in filename:
                return filename.split("_")[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting device ID from certificate: {e}")
            return None
    
    def _perform_integrity_checks(self, stored_data: VerificationData, 
                                verification_details: Dict[str, Any], warnings: List[str]):
        """Perform additional integrity checks."""
        try:
            # Check timestamp validity
            stored_timestamp = datetime.fromisoformat(stored_data.timestamp)
            generated_timestamp = datetime.fromisoformat(stored_data.generated_at)
            
            if generated_timestamp < stored_timestamp:
                warnings.append("Verification data generated before wipe operation")
            
            # Check for reasonable time differences
            time_diff = (generated_timestamp - stored_timestamp).total_seconds()
            if time_diff > 3600:  # More than 1 hour
                warnings.append(f"Large time gap between wipe and verification data generation: {time_diff/3600:.1f} hours")
            
            verification_details['time_checks'] = {
                'wipe_timestamp': stored_data.timestamp,
                'verification_generated': stored_data.generated_at,
                'time_difference_seconds': time_diff
            }
            
            # Check hash format
            if len(stored_data.wipe_hash) != 64:  # SHA-256 should be 64 hex characters
                warnings.append("Wipe hash format appears invalid")
            
            verification_details['hash_format_check'] = 'VALID' if len(stored_data.wipe_hash) == 64 else 'INVALID'
            
        except Exception as e:
            warnings.append(f"Error during integrity checks: {e}")


def verify_certificate_offline(certificate_path: str, verification_code: Optional[str] = None) -> VerificationResult:
    """
    Convenience function for offline certificate verification.
    
    Args:
        certificate_path: Path to certificate to verify
        verification_code: Optional verification code
        
    Returns:
        VerificationResult: Verification result
    """
    verifier = OfflineVerifier()
    return verifier.verify_certificate_offline(certificate_path, verification_code)


def create_offline_verification_data(wipe_data: WipeData, blockchain_data: BlockchainData,
                                   device_info: DeviceInfo, certificate_path: str) -> VerificationData:
    """
    Convenience function to create offline verification data.
    
    Args:
        wipe_data: Wiping operation data
        blockchain_data: Blockchain transaction data
        device_info: Device information
        certificate_path: Path to certificate
        
    Returns:
        VerificationData: Created verification data
    """
    verifier = OfflineVerifier()
    return verifier.create_verification_data(wipe_data, blockchain_data, device_info, certificate_path)