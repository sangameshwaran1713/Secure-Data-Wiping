"""
Data Privacy Module

Implements data privacy filters to ensure no sensitive data is stored
in blockchain records, certificates, or log files.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class DataPrivacyError(Exception):
    """Raised when data privacy violations are detected."""
    pass


class SensitivityLevel(Enum):
    """Data sensitivity levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class PrivacyViolation:
    """Represents a data privacy violation."""
    field_name: str
    violation_type: str
    description: str
    severity: SensitivityLevel
    suggested_action: str


@dataclass
class PrivacyFilterResult:
    """Result of privacy filtering operation."""
    filtered_data: Dict[str, Any]
    violations: List[PrivacyViolation]
    warnings: List[str]
    filtered_fields: List[str]


class DataPrivacyFilter:
    """
    Filters sensitive data to ensure privacy compliance.
    
    Ensures that blockchain records, certificates, and logs contain only
    cryptographic hashes and non-sensitive metadata.
    """
    
    def __init__(self):
        """Initialize the data privacy filter."""
        self.logger = logging.getLogger(__name__)
        
        # Define sensitive data patterns
        self.sensitive_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'mac_address': re.compile(r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b'),
            'file_path': re.compile(r'[A-Za-z]:\\[^<>:"|?*\n\r]*|/[^<>:"|?*\n\r]*'),
            'username': re.compile(r'\b[A-Za-z0-9._-]+\\[A-Za-z0-9._-]+\b')  # Domain\username
        }
        
        # Define allowed fields for different contexts
        self.blockchain_allowed_fields = {
            'device_id',
            'wipe_hash',
            'timestamp',
            'method',
            'operator_id',
            'transaction_hash',
            'block_number',
            'gas_used',
            'confirmation_count'
        }
        
        self.certificate_allowed_fields = {
            'device_id',
            'wipe_hash',
            'timestamp',
            'method',
            'operator',
            'passes',
            'transaction_hash',
            'block_number',
            'contract_address',
            'verification_code'
        }
        
        self.log_allowed_fields = {
            'operation_id',
            'device_id',
            'method',
            'timestamp',
            'success',
            'error_type',
            'processing_time',
            'passes_completed'
        }
        
        # Define sensitive field names
        self.sensitive_field_names = {
            'password', 'secret', 'key', 'token', 'credential',
            'personal_data', 'pii', 'sensitive_info', 'private_key',
            'recovery_data', 'file_content', 'raw_data', 'backup_data',
            'user_data', 'customer_data', 'confidential', 'classified'
        }
    
    def filter_blockchain_data(self, data: Dict[str, Any]) -> PrivacyFilterResult:
        """
        Filter data for blockchain storage.
        
        Args:
            data: Data to filter for blockchain storage
            
        Returns:
            PrivacyFilterResult: Filtered data and privacy analysis
        """
        self.logger.info("Filtering data for blockchain storage")
        
        return self._filter_data(
            data=data,
            allowed_fields=self.blockchain_allowed_fields,
            context="blockchain"
        )
    
    def filter_certificate_data(self, data: Dict[str, Any]) -> PrivacyFilterResult:
        """
        Filter data for certificate generation.
        
        Args:
            data: Data to filter for certificate
            
        Returns:
            PrivacyFilterResult: Filtered data and privacy analysis
        """
        self.logger.info("Filtering data for certificate generation")
        
        return self._filter_data(
            data=data,
            allowed_fields=self.certificate_allowed_fields,
            context="certificate"
        )
    
    def filter_log_data(self, data: Dict[str, Any]) -> PrivacyFilterResult:
        """
        Filter data for logging.
        
        Args:
            data: Data to filter for logging
            
        Returns:
            PrivacyFilterResult: Filtered data and privacy analysis
        """
        self.logger.info("Filtering data for logging")
        
        return self._filter_data(
            data=data,
            allowed_fields=self.log_allowed_fields,
            context="logging"
        )
    
    def validate_privacy_compliance(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """
        Validate data for privacy compliance.
        
        Args:
            data: Data to validate
            context: Context of data usage (blockchain, certificate, log)
            
        Returns:
            List[PrivacyViolation]: List of privacy violations found
        """
        violations = []
        
        try:
            # Check for sensitive field names
            for field_name, value in data.items():
                if self._is_sensitive_field_name(field_name):
                    violations.append(PrivacyViolation(
                        field_name=field_name,
                        violation_type="sensitive_field_name",
                        description=f"Field name '{field_name}' indicates sensitive data",
                        severity=SensitivityLevel.CONFIDENTIAL,
                        suggested_action="Remove or rename field to non-sensitive name"
                    ))
                
                # Check for sensitive patterns in values
                if isinstance(value, str):
                    pattern_violations = self._check_sensitive_patterns(field_name, value)
                    violations.extend(pattern_violations)
            
            # Check context-specific compliance
            context_violations = self._check_context_compliance(data, context)
            violations.extend(context_violations)
            
        except Exception as e:
            self.logger.error(f"Error during privacy compliance validation: {e}")
            violations.append(PrivacyViolation(
                field_name="validation_error",
                violation_type="validation_failure",
                description=f"Privacy validation failed: {e}",
                severity=SensitivityLevel.RESTRICTED,
                suggested_action="Review data structure and validation logic"
            ))
        
        return violations
    
    def sanitize_error_message(self, error_message: str) -> str:
        """
        Sanitize error messages to remove sensitive information.
        
        Args:
            error_message: Original error message
            
        Returns:
            str: Sanitized error message
        """
        sanitized = error_message
        
        try:
            # Remove file paths
            sanitized = re.sub(r'[A-Za-z]:\\[^<>:"|?*\s]*', '[FILE_PATH]', sanitized)
            sanitized = re.sub(r'/[^<>:"|?*\s]*', '[FILE_PATH]', sanitized)
            
            # Remove IP addresses
            sanitized = re.sub(self.sensitive_patterns['ip_address'], '[IP_ADDRESS]', sanitized)
            
            # Remove MAC addresses
            sanitized = re.sub(self.sensitive_patterns['mac_address'], '[MAC_ADDRESS]', sanitized)
            
            # Remove email addresses
            sanitized = re.sub(self.sensitive_patterns['email'], '[EMAIL]', sanitized)
            
            # Remove usernames (domain\username format)
            sanitized = re.sub(self.sensitive_patterns['username'], '[USERNAME]', sanitized)
            
            # Remove potential passwords or keys (sequences of random characters)
            sanitized = re.sub(r'\b[A-Za-z0-9+/]{20,}\b', '[REDACTED]', sanitized)
            
        except Exception as e:
            self.logger.warning(f"Error sanitizing error message: {e}")
            # Return generic message if sanitization fails
            return "Error occurred during operation [details redacted for privacy]"
        
        return sanitized
    
    def create_privacy_report(self, violations: List[PrivacyViolation]) -> Dict[str, Any]:
        """
        Create a privacy compliance report.
        
        Args:
            violations: List of privacy violations
            
        Returns:
            Dict: Privacy compliance report
        """
        report = {
            'compliance_status': 'COMPLIANT' if not violations else 'VIOLATIONS_FOUND',
            'total_violations': len(violations),
            'violations_by_severity': {},
            'violations_by_type': {},
            'recommendations': [],
            'violations': []
        }
        
        # Categorize violations
        for violation in violations:
            # By severity
            severity = violation.severity.value
            if severity not in report['violations_by_severity']:
                report['violations_by_severity'][severity] = 0
            report['violations_by_severity'][severity] += 1
            
            # By type
            vtype = violation.violation_type
            if vtype not in report['violations_by_type']:
                report['violations_by_type'][vtype] = 0
            report['violations_by_type'][vtype] += 1
            
            # Add to violations list
            report['violations'].append({
                'field': violation.field_name,
                'type': violation.violation_type,
                'description': violation.description,
                'severity': violation.severity.value,
                'action': violation.suggested_action
            })
        
        # Generate recommendations
        if violations:
            report['recommendations'] = [
                "Review data collection practices to minimize sensitive data",
                "Implement data anonymization techniques where possible",
                "Use cryptographic hashes instead of raw data",
                "Regularly audit data privacy compliance",
                "Train operators on data privacy best practices"
            ]
        
        return report
    
    def _filter_data(self, data: Dict[str, Any], allowed_fields: Set[str], 
                    context: str) -> PrivacyFilterResult:
        """Internal method to filter data based on allowed fields."""
        filtered_data = {}
        violations = []
        warnings = []
        filtered_fields = []
        
        try:
            for field_name, value in data.items():
                if field_name in allowed_fields:
                    # Field is allowed, but check for sensitive content
                    if isinstance(value, str):
                        pattern_violations = self._check_sensitive_patterns(field_name, value)
                        if pattern_violations:
                            violations.extend(pattern_violations)
                            # Sanitize the value
                            sanitized_value = self._sanitize_value(value)
                            filtered_data[field_name] = sanitized_value
                            warnings.append(f"Sanitized sensitive content in field '{field_name}'")
                        else:
                            filtered_data[field_name] = value
                    else:
                        filtered_data[field_name] = value
                else:
                    # Field not allowed in this context
                    filtered_fields.append(field_name)
                    
                    if self._is_sensitive_field_name(field_name):
                        violations.append(PrivacyViolation(
                            field_name=field_name,
                            violation_type="disallowed_sensitive_field",
                            description=f"Sensitive field '{field_name}' not allowed in {context}",
                            severity=SensitivityLevel.CONFIDENTIAL,
                            suggested_action=f"Remove field or use allowed alternative for {context}"
                        ))
                    else:
                        warnings.append(f"Field '{field_name}' filtered out for {context} context")
            
        except Exception as e:
            self.logger.error(f"Error during data filtering: {e}")
            violations.append(PrivacyViolation(
                field_name="filtering_error",
                violation_type="filtering_failure",
                description=f"Data filtering failed: {e}",
                severity=SensitivityLevel.RESTRICTED,
                suggested_action="Review data structure and filtering logic"
            ))
        
        return PrivacyFilterResult(
            filtered_data=filtered_data,
            violations=violations,
            warnings=warnings,
            filtered_fields=filtered_fields
        )
    
    def _is_sensitive_field_name(self, field_name: str) -> bool:
        """Check if a field name indicates sensitive data."""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.sensitive_field_names)
    
    def _check_sensitive_patterns(self, field_name: str, value: str) -> List[PrivacyViolation]:
        """Check for sensitive patterns in field values."""
        violations = []
        
        for pattern_name, pattern in self.sensitive_patterns.items():
            if pattern.search(value):
                violations.append(PrivacyViolation(
                    field_name=field_name,
                    violation_type=f"sensitive_pattern_{pattern_name}",
                    description=f"Field '{field_name}' contains {pattern_name} pattern",
                    severity=SensitivityLevel.CONFIDENTIAL,
                    suggested_action=f"Remove or hash {pattern_name} data"
                ))
        
        return violations
    
    def _check_context_compliance(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Check context-specific compliance rules."""
        violations = []
        
        if context == "blockchain":
            # Blockchain should only contain hashes and metadata
            for field_name, value in data.items():
                if isinstance(value, str) and len(value) > 256:
                    violations.append(PrivacyViolation(
                        field_name=field_name,
                        violation_type="blockchain_data_too_large",
                        description=f"Field '{field_name}' too large for blockchain storage",
                        severity=SensitivityLevel.INTERNAL,
                        suggested_action="Use hash or reference instead of full data"
                    ))
        
        elif context == "certificate":
            # Certificates should not contain raw file data
            for field_name, value in data.items():
                if "content" in field_name.lower() or "data" in field_name.lower():
                    violations.append(PrivacyViolation(
                        field_name=field_name,
                        violation_type="certificate_raw_data",
                        description=f"Field '{field_name}' may contain raw data in certificate",
                        severity=SensitivityLevel.CONFIDENTIAL,
                        suggested_action="Use hash or summary instead of raw data"
                    ))
        
        return violations
    
    def _sanitize_value(self, value: str) -> str:
        """Sanitize a string value by removing sensitive patterns."""
        sanitized = value
        
        # Replace sensitive patterns with placeholders
        for pattern_name, pattern in self.sensitive_patterns.items():
            sanitized = pattern.sub(f'[{pattern_name.upper()}]', sanitized)
        
        return sanitized


def filter_sensitive_data(data: Dict[str, Any], context: str) -> PrivacyFilterResult:
    """
    Convenience function to filter sensitive data.
    
    Args:
        data: Data to filter
        context: Context (blockchain, certificate, log)
        
    Returns:
        PrivacyFilterResult: Filtered data and analysis
    """
    filter_instance = DataPrivacyFilter()
    
    if context == "blockchain":
        return filter_instance.filter_blockchain_data(data)
    elif context == "certificate":
        return filter_instance.filter_certificate_data(data)
    elif context == "log":
        return filter_instance.filter_log_data(data)
    else:
        raise DataPrivacyError(f"Unknown context: {context}")


def validate_privacy_compliance(data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
    """
    Convenience function to validate privacy compliance.
    
    Args:
        data: Data to validate
        context: Context of data usage
        
    Returns:
        List[PrivacyViolation]: Privacy violations found
    """
    filter_instance = DataPrivacyFilter()
    return filter_instance.validate_privacy_compliance(data, context)