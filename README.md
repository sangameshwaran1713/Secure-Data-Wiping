# Secure Data Wiping for Trustworthy IT Asset Recycling

A comprehensive blockchain-based secure data wiping system that provides cryptographically verifiable proof of data destruction for IT asset recycling. This system implements NIST 800-88 compliant data wiping procedures with immutable audit trails stored on a local Ethereum blockchain.

## 🎯 Project Overview

This final year project demonstrates the integration of cybersecurity best practices with blockchain technology to solve real-world IT asset recycling challenges. The system ensures that sensitive data is securely destroyed and provides legally defensible proof of destruction through blockchain-verified certificates.

### Key Features

- **NIST 800-88 Compliant Wiping**: Implements industry-standard data destruction procedures
- **Blockchain Audit Trail**: Immutable record storage on local Ethereum blockchain
- **Cryptographic Verification**: SHA-256 hash generation for tamper detection
- **Professional Certificates**: PDF certificates with QR codes for blockchain verification
- **Local Infrastructure**: Operates entirely on local systems for maximum security
- **Privacy Protection**: Ensures no sensitive data is exposed during the process
- **Batch Processing**: Command-line interface for processing multiple devices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Wipe Engine   │    │ Hash Generator  │    │Certificate Gen. │
│                 │    │                 │    │                 │
│ NIST 800-88     │───▶│ SHA-256 Hashes  │───▶│ PDF + QR Codes  │
│ Compliance      │    │ Tamper Detection│    │ Blockchain Links│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    System Controller                            │
│              Sequential Workflow Orchestration                  │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Blockchain Logger│    │ Local Database  │    │Privacy & Security│
│                 │    │                 │    │                 │
│ Ganache/Web3.py │    │ SQLite Storage  │    │ Network Isolation│
│ Smart Contract  │    │ Operation Logs  │    │ Data Filtering   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js (for Ganache)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd secure-data-wiping-blockchain
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install and start Ganache**
   ```bash
   npm install -g ganache-cli
   ganache-cli --host 127.0.0.1 --port 8545 --accounts 10 --deterministic
   ```

4. **Deploy smart contract**
   ```bash
   python scripts/deploy_contract.py
   ```

5. **Initialize the system**
   ```bash
   python main.py
   ```

### Basic Usage

#### Single Device Processing
```bash
python -m secure_data_wiping.cli single-device DEV_001 \
  --device-type hdd \
  --manufacturer "Seagate" \
  --model "ST1000DM003" \
  --wipe-method clear
```

#### Batch Processing
```bash
# Create sample device file
python -m secure_data_wiping.cli create-sample devices.csv

# Process all devices
python -m secure_data_wiping.cli batch-process devices.csv
```

## 📋 System Requirements

### Hardware Requirements
- **Minimum**: 4GB RAM, 10GB free disk space
- **Recommended**: 8GB RAM, 50GB free disk space
- **Storage**: Additional space for device images and certificates

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8 or higher with pip
- **Node.js**: 14.0 or higher (for Ganache)
- **Network**: Local network access only (no internet required)

### Dependencies
- **Web3.py**: Ethereum blockchain interaction
- **ReportLab**: PDF certificate generation
- **Hypothesis**: Property-based testing
- **SQLite**: Local database storage
- **QRCode**: QR code generation for verification

## 🔧 Configuration

The system uses a YAML configuration file (`config.yaml`) for customization:

```yaml
# Database Configuration
database:
  path: "data/secure_wiping.db"

# Blockchain Configuration
blockchain:
  ganache_url: "http://127.0.0.1:8545"
  contract_address: "0x..."
  max_retry_attempts: 3

# Certificate Configuration
certificates:
  output_dir: "certificates"
  template: "default"
  include_qr_codes: true

# Logging Configuration
logging:
  level: "INFO"
  audit_enabled: true
  file_path: "logs/secure_wiping.log"
```

## 🧪 Testing

The system includes comprehensive testing with both unit tests and property-based tests:

### Run All Tests
```bash
# Core system checkpoint
python test_core_system_checkpoint.py

# Complete workflow test
python test_complete_workflow.py

# Property-based tests
python test_hash_properties_simple.py
python test_wipe_engine_properties.py
python test_local_infrastructure_properties.py

# Documentation completeness
python test_documentation_completeness.py
```

### Property-Based Testing
The system validates 18 correctness properties including:
- **Property 1**: NIST Compliance for Wiping Operations
- **Property 2**: Hash Generation Completeness and Determinism
- **Property 3**: Tamper Detection Through Hash Verification
- **Property 14**: Local Infrastructure Operation
- **Property 16**: Data Privacy Protection

## 📊 Performance Metrics

Based on testing with the current implementation:

- **Processing Speed**: ~0.06 seconds per device (simulation)
- **Certificate Generation**: ~15KB PDF with security features
- **Hash Generation**: SHA-256 in <0.01 seconds
- **Blockchain Transaction**: ~2-5 seconds on local Ganache
- **Memory Usage**: <100MB for typical operations
- **Storage**: ~20KB per operation (database + certificate)

## 🔒 Security Features

### Data Protection
- **Local-Only Operation**: No external network connections
- **Privacy Filtering**: Sensitive data never stored on blockchain
- **Cryptographic Integrity**: SHA-256 hashes for tamper detection
- **Access Control**: Smart contract authorization mechanisms

### Compliance
- **NIST 800-88**: Industry-standard data wiping procedures
- **Audit Trail**: Immutable blockchain records
- **Certificate Generation**: Professional documentation
- **Offline Verification**: Independent certificate validation

## 📁 Project Structure

```
secure-data-wiping-blockchain/
├── secure_data_wiping/           # Main package
│   ├── wipe_engine/             # NIST 800-88 wiping implementation
│   ├── hash_generator/          # SHA-256 hash generation
│   ├── blockchain_logger/       # Ethereum blockchain integration
│   ├── certificate_generator/   # PDF certificate creation
│   ├── system_controller/       # Workflow orchestration
│   ├── local_infrastructure/    # Privacy and security controls
│   ├── database/               # SQLite database management
│   └── utils/                  # Shared utilities and data models
├── contracts/                   # Solidity smart contracts
├── scripts/                    # Deployment and setup scripts
├── tests/                      # Test files
├── data/                       # Database and logs
├── certificates/               # Generated certificates
├── config.yaml                # System configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🎓 Academic Context

This project was developed as a final year computer science project focusing on:

### Learning Objectives
- **Blockchain Technology**: Practical implementation of Ethereum smart contracts
- **Cybersecurity**: NIST-compliant data destruction procedures
- **Software Engineering**: Modular architecture and comprehensive testing
- **System Integration**: Combining multiple technologies into a cohesive solution

### Technical Contributions
- **Novel Integration**: Blockchain-based audit trails for data wiping
- **Compliance Implementation**: NIST 800-88 standard in Python
- **Privacy-First Design**: Local-only operation with data protection
- **Comprehensive Testing**: Property-based testing for correctness validation

### Evaluation Criteria
- **Functionality**: Complete workflow from wiping to certification
- **Security**: Privacy protection and cryptographic integrity
- **Quality**: Code documentation and testing coverage
- **Innovation**: Blockchain integration for audit trails

## 🔍 Sample Outputs

### Certificate Example
Generated certificates include:
- Device identification and specifications
- Wiping method and parameters
- Cryptographic hash of operation
- Blockchain transaction reference
- QR code for verification
- Professional formatting with security features

### Blockchain Record
```json
{
  "deviceId": "DEV_001",
  "wipeHash": "a1b2c3d4e5f6...",
  "timestamp": 1704723600,
  "operator": "0x742d35Cc...",
  "transactionHash": "0x8f2a1b3c...",
  "blockNumber": 12345
}
```

## 🚨 Important Notes

### Security Considerations
- **Local Operation Only**: System designed for air-gapped environments
- **No Internet Required**: All operations performed locally
- **Data Privacy**: Sensitive information never leaves local system
- **Blockchain Security**: Uses local Ganache for development/testing

### Limitations
- **Simulation Mode**: Actual device wiping simulated for safety
- **Local Blockchain**: Uses Ganache for development (not production Ethereum)
- **Academic Purpose**: Designed for educational demonstration
- **Testing Environment**: Optimized for controlled testing scenarios

## 🤝 Contributing

This is an academic project, but contributions for educational purposes are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes with comprehensive tests
4. Ensure all property tests pass
5. Submit a pull request with detailed description

## 📄 License

This project is developed for academic purposes. Please respect intellectual property rights and use responsibly.

## 📞 Support

For questions about this academic project:
- Review the comprehensive documentation in each module
- Check the test files for usage examples
- Examine the property-based tests for correctness validation
- Refer to the academic deliverables for theoretical background

## 🏆 Acknowledgments

- **NIST**: For the 800-88 data sanitization guidelines
- **Ethereum Foundation**: For blockchain technology and tools
- **Python Community**: For excellent libraries and frameworks
- **Academic Supervisors**: For guidance and support throughout the project

---

**Final Year Project - Computer Science**  
**Secure Data Wiping for Trustworthy IT Asset Recycling using Blockchain-Based Audit Trail**  
**Version 1.0.0**