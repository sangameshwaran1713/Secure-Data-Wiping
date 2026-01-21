"""
Certificate Generator Implementation

Creates professional PDF certificates with blockchain verification for secure data destruction proof.
Provides legally defensible documentation of NIST 800-88 compliant wiping operations.
"""

import os
import io
import logging
import qrcode
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import Color, black, blue, red, green
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from reportlab.lib import colors

from ..utils.data_models import WipeData, BlockchainData, DeviceInfo


class CertificateGeneratorError(Exception):
    """Base exception for certificate generator operations."""
    pass


class TemplateError(CertificateGeneratorError):
    """Raised when certificate template processing fails."""
    pass


class PDFGenerationError(CertificateGeneratorError):
    """Raised when PDF generation fails."""
    pass


class QRCodeError(CertificateGeneratorError):
    """Raised when QR code generation fails."""
    pass


class CertificateGenerator:
    """
    Generates professional PDF certificates with blockchain verification.
    
    Creates legally defensible certificates of data destruction that include:
    - Device information and wiping details
    - Blockchain transaction verification
    - QR codes for independent verification
    - Professional formatting with security features
    """
    
    # Certificate template configuration
    DEFAULT_TEMPLATE_CONFIG = {
        'page_size': A4,
        'margins': {
            'top': 72,      # 1 inch
            'bottom': 72,   # 1 inch
            'left': 72,     # 1 inch
            'right': 72     # 1 inch
        },
        'colors': {
            'primary': Color(0.2, 0.3, 0.6, 1),      # Dark blue
            'secondary': Color(0.4, 0.4, 0.4, 1),    # Gray
            'accent': Color(0.8, 0.2, 0.2, 1),       # Red
            'success': Color(0.2, 0.6, 0.2, 1),      # Green
            'text': black
        },
        'fonts': {
            'title': ('Helvetica-Bold', 24),
            'heading': ('Helvetica-Bold', 16),
            'subheading': ('Helvetica-Bold', 12),
            'body': ('Helvetica', 10),
            'small': ('Helvetica', 8)
        },
        'security_features': {
            'watermark': True,
            'border': True,
            'timestamp': True,
            'verification_url': True
        }
    }
    
    def __init__(self, template_config: Optional[Dict[str, Any]] = None, 
                 output_dir: str = "certificates"):
        """
        Initialize the certificate generator.
        
        Args:
            template_config: Optional template configuration (uses default if not provided)
            output_dir: Directory to save generated certificates
        """
        self.logger = logging.getLogger(__name__)
        
        # Merge template config with defaults
        self.template_config = self.DEFAULT_TEMPLATE_CONFIG.copy()
        if template_config:
            # Deep merge the configurations
            for key, value in template_config.items():
                if key in self.template_config and isinstance(self.template_config[key], dict) and isinstance(value, dict):
                    self.template_config[key].update(value)
                else:
                    self.template_config[key] = value
        
        self.output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.certificates_generated = 0
        self.last_generation_time = None
        
        self.logger.info(f"CertificateGenerator initialized with output directory: {self.output_dir}")
    
    def generate_certificate(self, wipe_data: WipeData, blockchain_data: BlockchainData,
                           device_info: Optional[DeviceInfo] = None,
                           custom_filename: Optional[str] = None) -> str:
        """
        Generate a professional PDF certificate of data destruction.
        
        Args:
            wipe_data: Wiping operation data
            blockchain_data: Blockchain transaction data
            device_info: Optional device information for additional details
            custom_filename: Optional custom filename (auto-generated if not provided)
            
        Returns:
            str: Path to the generated certificate file
            
        Raises:
            PDFGenerationError: If certificate generation fails
        """
        self.logger.info(f"Generating certificate for device {wipe_data.device_id}")
        
        try:
            # Generate filename if not provided
            if custom_filename:
                filename = custom_filename
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
            else:
                timestamp = wipe_data.timestamp.strftime("%Y%m%d_%H%M%S")
                filename = f"certificate_{wipe_data.device_id}_{timestamp}.pdf"
            
            certificate_path = self.output_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(certificate_path),
                pagesize=self.template_config['page_size'],
                topMargin=self.template_config['margins']['top'],
                bottomMargin=self.template_config['margins']['bottom'],
                leftMargin=self.template_config['margins']['left'],
                rightMargin=self.template_config['margins']['right']
            )
            
            # Build certificate content
            story = []
            
            # Add header
            story.extend(self._create_header())
            
            # Add title
            story.extend(self._create_title())
            
            # Add certificate body
            story.extend(self._create_certificate_body(wipe_data, blockchain_data, device_info))
            
            # Add verification section
            story.extend(self._create_verification_section(blockchain_data))
            
            # Add footer
            story.extend(self._create_footer())
            
            # Build PDF with custom page template for security features
            doc.build(story, onFirstPage=self._add_security_features, 
                     onLaterPages=self._add_security_features)
            
            # Update statistics
            self.certificates_generated += 1
            self.last_generation_time = datetime.now()
            
            self.logger.info(f"Certificate generated successfully: {certificate_path}")
            return str(certificate_path)
            
        except Exception as e:
            self.logger.error(f"Certificate generation failed: {e}")
            raise PDFGenerationError(f"Failed to generate certificate: {e}") from e
    
    def _create_header(self) -> list:
        """Create certificate header with logo and organization info."""
        styles = getSampleStyleSheet()
        
        # Organization header
        org_style = ParagraphStyle(
            'OrgHeader',
            parent=styles['Normal'],
            fontSize=14,
            textColor=self.template_config['colors']['primary'],
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        header_content = [
            Paragraph("<b>SECURE DATA DESTRUCTION CERTIFICATE</b>", org_style),
            Paragraph("Blockchain-Verified NIST 800-88 Compliant Data Wiping", styles['Normal']),
            Spacer(1, 20),
            HRFlowable(width="100%", thickness=2, 
                      color=self.template_config['colors']['primary'])
        ]
        
        return header_content
    
    def _create_title(self) -> list:
        """Create certificate title section."""
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Title'],
            fontSize=self.template_config['fonts']['title'][1],
            textColor=self.template_config['colors']['primary'],
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        return [
            Spacer(1, 20),
            Paragraph("CERTIFICATE OF DATA DESTRUCTION", title_style),
            Spacer(1, 10)
        ]
    
    def _create_certificate_body(self, wipe_data: WipeData, blockchain_data: BlockchainData,
                               device_info: Optional[DeviceInfo]) -> list:
        """Create the main certificate body with operation details."""
        styles = getSampleStyleSheet()
        content = []
        
        # Certificate statement
        statement_style = ParagraphStyle(
            'Statement',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_JUSTIFY,
            spaceAfter=20
        )
        
        statement_text = f"""
        This certificate confirms that secure data destruction has been performed on the device 
        identified below in accordance with NIST 800-88 guidelines. The wiping operation has been 
        cryptographically verified and recorded on an immutable blockchain for audit purposes.
        """
        
        content.append(Paragraph(statement_text, statement_style))
        content.append(Spacer(1, 20))
        
        # Device and operation details table
        table_data = [
            ['Device Information', ''],
            ['Device ID:', wipe_data.device_id],
            ['Wiping Method:', wipe_data.method.upper()],
            ['Number of Passes:', str(wipe_data.passes)],
            ['Operation Date:', wipe_data.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")],
            ['Operator:', wipe_data.operator],
            ['', ''],
            ['Cryptographic Verification', ''],
            ['Wipe Hash (SHA-256):', wipe_data.wipe_hash[:32] + '...'],
            ['Full Hash:', wipe_data.wipe_hash],
        ]
        
        # Add device info if available
        if device_info:
            device_details = [
                ['', ''],
                ['Device Details', ''],
                ['Type:', device_info.device_type.value.upper()],
                ['Manufacturer:', device_info.manufacturer or 'N/A'],
                ['Model:', device_info.model or 'N/A'],
            ]
            if device_info.capacity:
                capacity_gb = device_info.capacity / (1024**3)
                device_details.append(['Capacity:', f"{capacity_gb:.2f} GB"])
            
            # Insert device details after operation info
            table_data[6:6] = device_details
        
        # Add blockchain information
        blockchain_info = [
            ['', ''],
            ['Blockchain Verification', ''],
            ['Transaction Hash:', blockchain_data.transaction_hash[:32] + '...'],
            ['Block Number:', str(blockchain_data.block_number)],
            ['Contract Address:', blockchain_data.contract_address[:20] + '...'],
            ['Gas Used:', str(blockchain_data.gas_used)],
            ['Confirmations:', str(blockchain_data.confirmation_count)]
        ]
        table_data.extend(blockchain_info)
        
        # Create table
        table = Table(table_data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            # Header rows
            ('BACKGROUND', (0, 0), (1, 0), self.template_config['colors']['primary']),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            
            # Section headers
            ('BACKGROUND', (0, 7), (1, 7), self.template_config['colors']['secondary']),
            ('TEXTCOLOR', (0, 7), (1, 7), colors.white),
            ('FONTNAME', (0, 7), (1, 7), 'Helvetica-Bold'),
            
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            
            # Grid and alignment
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Color(0.95, 0.95, 0.95, 1)])
        ]))
        
        content.append(table)
        content.append(Spacer(1, 30))
        
        return content
    
    def _create_verification_section(self, blockchain_data: BlockchainData) -> list:
        """Create blockchain verification section with QR code."""
        styles = getSampleStyleSheet()
        content = []
        
        # Verification heading
        verify_style = ParagraphStyle(
            'VerifyHeading',
            parent=styles['Heading2'],
            fontSize=self.template_config['fonts']['heading'][1],
            textColor=self.template_config['colors']['primary'],
            spaceAfter=15
        )
        
        content.append(Paragraph("Blockchain Verification", verify_style))
        
        # Generate QR code for verification
        try:
            qr_image_path = self._generate_qr_code(blockchain_data)
            
            # Create verification table with QR code
            verification_text = f"""
            <b>Independent Verification:</b><br/>
            This certificate can be independently verified using the blockchain transaction hash. 
            Scan the QR code or visit the verification URL to confirm the authenticity of this 
            data destruction certificate.<br/><br/>
            <b>Transaction Hash:</b> {blockchain_data.transaction_hash}<br/>
            <b>Block Number:</b> {blockchain_data.block_number}<br/>
            <b>Contract:</b> {blockchain_data.contract_address}
            """
            
            verify_table_data = [
                [Paragraph(verification_text, styles['Normal']), 
                 Image(qr_image_path, width=1.5*inch, height=1.5*inch)]
            ]
            
            verify_table = Table(verify_table_data, colWidths=[4*inch, 2*inch])
            verify_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(verify_table)
            
        except Exception as e:
            self.logger.warning(f"Failed to generate QR code: {e}")
            # Add verification text without QR code
            verify_text = f"""
            <b>Blockchain Verification:</b><br/>
            Transaction Hash: {blockchain_data.transaction_hash}<br/>
            Block Number: {blockchain_data.block_number}<br/>
            Contract Address: {blockchain_data.contract_address}
            """
            content.append(Paragraph(verify_text, styles['Normal']))
        
        content.append(Spacer(1, 30))
        return content
    
    def _create_footer(self) -> list:
        """Create certificate footer with compliance and signature info."""
        styles = getSampleStyleSheet()
        content = []
        
        # Compliance statement
        compliance_style = ParagraphStyle(
            'Compliance',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.template_config['colors']['secondary'],
            alignment=TA_JUSTIFY,
            spaceAfter=20
        )
        
        compliance_text = """
        <b>Compliance Statement:</b> This data destruction operation was performed in accordance 
        with NIST Special Publication 800-88 Revision 1 "Guidelines for Media Sanitization". 
        The cryptographic hash and blockchain record provide immutable proof of the wiping operation. 
        This certificate serves as legal documentation of secure data destruction for compliance 
        and audit purposes.
        """
        
        content.append(HRFlowable(width="100%", thickness=1, color=colors.gray))
        content.append(Spacer(1, 10))
        content.append(Paragraph(compliance_text, compliance_style))
        
        # Generation timestamp
        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.template_config['colors']['secondary'],
            alignment=TA_RIGHT
        )
        
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        content.append(Paragraph(f"Certificate generated: {generation_time}", timestamp_style))
        
        return content
    
    def _generate_qr_code(self, blockchain_data: BlockchainData) -> str:
        """
        Generate QR code for blockchain verification.
        
        Args:
            blockchain_data: Blockchain transaction data
            
        Returns:
            str: Path to generated QR code image
            
        Raises:
            QRCodeError: If QR code generation fails
        """
        try:
            # Create verification URL (in production, this would be a real verification service)
            verification_url = f"https://verify.securewiping.local/tx/{blockchain_data.transaction_hash}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code image
            qr_filename = f"qr_{blockchain_data.transaction_hash[:16]}.png"
            qr_path = self.output_dir / qr_filename
            qr_image.save(qr_path)
            
            return str(qr_path)
            
        except Exception as e:
            raise QRCodeError(f"Failed to generate QR code: {e}") from e
    
    def _add_security_features(self, canvas_obj, doc):
        """
        Add security features to the PDF page.
        
        Args:
            canvas_obj: ReportLab canvas object
            doc: Document template object
        """
        if not self.template_config['security_features'].get('watermark', True):
            return
        
        try:
            # Add watermark
            canvas_obj.saveState()
            canvas_obj.setFillColor(Color(0.9, 0.9, 0.9, 0.3))  # Light gray, semi-transparent
            canvas_obj.setFont("Helvetica-Bold", 60)
            
            # Rotate and position watermark
            canvas_obj.rotate(45)
            canvas_obj.drawString(350, -100, "SECURE DATA DESTRUCTION")
            
            # Add border if enabled
            if self.template_config['security_features'].get('border', True):
                canvas_obj.setStrokeColor(self.template_config['colors']['primary'])
                canvas_obj.setLineWidth(2)
                canvas_obj.rect(36, 36, doc.width + 72, doc.height + 72)
            
            canvas_obj.restoreState()
            
        except Exception as e:
            self.logger.warning(f"Failed to add security features: {e}")
    
    def add_qr_verification(self, certificate_path: str, verification_url: str) -> bool:
        """
        Add QR code verification to an existing certificate.
        
        Args:
            certificate_path: Path to existing certificate
            verification_url: URL for verification
            
        Returns:
            bool: True if QR code added successfully, False otherwise
        """
        try:
            # This would modify an existing PDF to add QR code
            # For now, we generate QR codes during initial creation
            self.logger.info(f"QR verification URL: {verification_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add QR verification: {e}")
            return False
    
    def add_security_features(self, certificate_path: str) -> bool:
        """
        Add additional security features to an existing certificate.
        
        Args:
            certificate_path: Path to certificate file
            
        Returns:
            bool: True if security features added successfully, False otherwise
        """
        try:
            # Security features are added during generation
            # This method is for post-processing if needed
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add security features: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get certificate generation statistics.
        
        Returns:
            Dict containing generation statistics
        """
        return {
            'certificates_generated': self.certificates_generated,
            'last_generation_time': self.last_generation_time.isoformat() if self.last_generation_time else None,
            'output_directory': str(self.output_dir),
            'template_config': self.template_config
        }
    
    def validate_certificate_data(self, wipe_data: WipeData, blockchain_data: BlockchainData) -> list:
        """
        Validate certificate data before generation.
        
        Args:
            wipe_data: Wiping operation data
            blockchain_data: Blockchain transaction data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate wipe data
        if not wipe_data.device_id:
            errors.append("Device ID is required")
        
        if not wipe_data.wipe_hash:
            errors.append("Wipe hash is required")
        
        if not wipe_data.timestamp:
            errors.append("Timestamp is required")
        
        if not wipe_data.method:
            errors.append("Wiping method is required")
        
        # Validate blockchain data
        if not blockchain_data.transaction_hash:
            errors.append("Transaction hash is required")
        
        if blockchain_data.block_number is None or blockchain_data.block_number < 0:
            errors.append("Valid block number is required")
        
        if not blockchain_data.contract_address:
            errors.append("Contract address is required")
        
        return errors


def create_certificate_generator_from_config(config_dict: Dict[str, Any]) -> CertificateGenerator:
    """
    Create CertificateGenerator from configuration dictionary.
    
    Args:
        config_dict: Configuration parameters
        
    Returns:
        CertificateGenerator: Configured certificate generator instance
    """
    template_config = config_dict.get('template_config')
    output_dir = config_dict.get('output_dir', 'certificates')
    
    return CertificateGenerator(
        template_config=template_config,
        output_dir=output_dir
    )