# System Architecture Documentation

## Overview

The Secure Data Wiping system follows a modular, layered architecture that ensures security, auditability, and compliance with industry standards. The system is designed to operate entirely on local infrastructure while providing blockchain-based immutable audit trails.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Command Line Interface (CLI)           │  Main Application Entry Point     │
│  - Batch processing commands            │  - Single device processing       │
│  - Configuration management             │  - System initialization          │
│  - Progress reporting                   │  - Status monitoring               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUSINESS LOGIC LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                          System Controller                                  │
│  - Workflow orchestration              │  - Error handling & recovery      │
│  - Component initialization            │  - Processing statistics           │
│  - Sequential execution control        │  - System status monitoring       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CORE COMPONENTS LAYER                               │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│   Wipe Engine   │ Hash Generator  │Blockchain Logger│ Certificate Generator   │
│                 │                 │                 │                         │
│ • NIST 800-88   │ • SHA-256       │ • Web3.py       │ • PDF Generation        │
│   Compliance    │   Hashing       │   Integration   │ • QR Code Creation      │
│ • Multi-pass    │ • Deterministic │ • Smart Contract│ • Security Features     │
│   Overwriting   │   Generation    │   Interaction   │ • Professional Format   │
│ • Verification  │ • Tamper        │ • Transaction   │ • Blockchain Links      │
│   Procedures    │   Detection     │   Management    │ • Offline Verification  │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                   │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│Local Blockchain │  Local Database │ Privacy & Security│    File System        │
│                 │                 │                 │                         │
│ • Ganache       │ • SQLite        │ • Network       │ • Certificate Storage   │
│   Instance      │   Database      │   Isolation     │ • Log File Management   │
│ • Smart Contract│ • Operation     │ • Data Privacy  │ • Configuration Files   │
│   Deployment    │   History       │   Filtering     │ • Temporary Files       │
│ • Transaction   │ • Audit Logs    │ • Local-Only    │ • Backup & Recovery     │
│   Processing    │ • Metadata      │   Validation    │ • Access Control        │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
```

## Component Interaction Flow

### 1. System Initialization
```
User Request → System Controller → Component Initialization
                     │
                     ├─ Initialize Wipe Engine
                     ├─ Initialize Hash Generator  
                     ├─ Initialize Blockchain Logger
                     ├─ Initialize Certificate Generator
                     ├─ Initialize Database Manager
                     └─ Validate Local Infrastructure
                     │
                     ▼
              Verify Blockchain Connectivity
                     │
                     ▼
              System Ready for Processing
```

### 2. Device Processing Workflow
```
Device Input → System Controller → Sequential Processing
                     │
                     ▼
              Step 1: Secure Wiping
                     │ (Wipe Engine)
                     ├─ NIST 800-88 Compliance Check
                     ├─ Device Type Detection
                     ├─ Multi-pass Overwriting
                     └─ Verification Procedures
                     │
                     ▼
              Step 2: Hash Generation
                     │ (Hash Generator)
                     ├─ Metadata Collection
                     ├─ SHA-256 Hash Creation
                     └─ Deterministic Processing
                     │
                     ▼
              Step 3: Blockchain Logging
                     │ (Blockchain Logger)
                     ├─ Privacy Filtering
                     ├─ Smart Contract Interaction
                     ├─ Transaction Submission
                     └─ Confirmation Waiting
                     │
                     ▼
              Step 4: Certificate Generation
                     │ (Certificate Generator)
                     ├─ PDF Creation
                     ├─ QR Code Generation
                     ├─ Security Features
                     └─ Blockchain Verification Links
                     │
                     ▼
              Step 5: Database Storage
                     │ (Database Manager)
                     ├─ Operation Recording
                     ├─ Audit Trail Creation
                     └─ Metadata Storage
                     │
                     ▼
              Processing Complete
```

## Data Flow Architecture

### 1. Input Data Flow
```
Device Information → Validation → Processing Queue
        │                │              │
        ├─ Device ID      ├─ Format      ├─ Priority
        ├─ Device Type    ├─ Required    ├─ Batch
        ├─ Capacity       ├─ Fields      ├─ Status
        ├─ Manufacturer   ├─ Data Types  └─ Tracking
        └─ Serial Number  └─ Constraints
```

### 2. Processing Data Flow
```
Raw Device Data → Wiping Operation → Hash Generation → Blockchain Storage
        │                │                  │               │
        ├─ File Content   ├─ Wipe Patterns  ├─ Metadata     ├─ Hash Only
        ├─ Device Info    ├─ Pass Count     ├─ Timestamp    ├─ Device ID
        └─ Configuration  ├─ Verification   ├─ Method       ├─ Operator
                         └─ Results        └─ Operator     └─ Timestamp
```

### 3. Output Data Flow
```
Blockchain Record → Certificate Generation → File Storage → User Delivery
        │                    │                   │              │
        ├─ Transaction Hash   ├─ PDF Document    ├─ Local FS    ├─ Certificate
        ├─ Block Number       ├─ QR Codes        ├─ Database    ├─ Verification
        ├─ Gas Used          ├─ Security         ├─ Logs        ├─ Reports
        └─ Confirmations     └─ Features         └─ Backups     └─ Status
```

## Security Architecture

### 1. Network Isolation
```
External Network ─┤ BLOCKED ├─ System Components
                  │         │
Internet Access ──┤ DENIED  ├─ Local Operations Only
                  │         │
Remote Servers ───┤ BLOCKED ├─ Ganache Local Blockchain
                  │         │
Cloud Services ───┤ DENIED  ├─ Local File System
```

### 2. Data Privacy Protection
```
Sensitive Data → Privacy Filter → Safe Data → Blockchain/Certificates
      │              │               │              │
      ├─ PII         ├─ Detection    ├─ Hashes      ├─ Public Records
      ├─ Passwords   ├─ Filtering    ├─ Metadata    ├─ Audit Trails
      ├─ Keys        ├─ Validation   ├─ Timestamps  ├─ Verification
      └─ Content     └─ Reporting    └─ IDs         └─ Documentation
```

### 3. Access Control
```
User Request → Authentication → Authorization → Component Access
      │              │               │                │
      ├─ CLI         ├─ Local User   ├─ Role Check    ├─ Wipe Engine
      ├─ API         ├─ System       ├─ Permission    ├─ Blockchain
      └─ Direct      └─ Account      └─ Validation    └─ Database
```

## Scalability Architecture

### 1. Horizontal Scaling
```
Multiple Devices → Batch Processing → Parallel Operations
        │                │                    │
        ├─ Queue         ├─ Worker Pool       ├─ Independent
        ├─ Priority      ├─ Load Balance      ├─ Processes
        └─ Scheduling    └─ Resource Mgmt     └─ Results
```

### 2. Vertical Scaling
```
System Resources → Optimization → Performance
        │               │            │
        ├─ Memory       ├─ Caching   ├─ Throughput
        ├─ CPU          ├─ Buffering ├─ Latency
        ├─ Storage      ├─ Indexing  ├─ Reliability
        └─ Network      └─ Pooling   └─ Efficiency
```

## Error Handling Architecture

### 1. Error Detection
```
Component Operations → Error Detection → Classification → Response
        │                    │               │            │
        ├─ Wipe Failures     ├─ Exception    ├─ Critical  ├─ Halt
        ├─ Hash Errors       ├─ Monitoring   ├─ Warning   ├─ Retry
        ├─ Blockchain        ├─ Validation   ├─ Info      ├─ Log
        └─ Certificate       └─ Checking     └─ Debug     └─ Continue
```

### 2. Recovery Procedures
```
Error Occurrence → Assessment → Recovery Strategy → Execution
        │              │            │                │
        ├─ Type        ├─ Impact    ├─ Rollback      ├─ Cleanup
        ├─ Severity    ├─ Scope     ├─ Retry         ├─ Restart
        ├─ Context     ├─ Resources ├─ Alternative   ├─ Report
        └─ Timing      └─ State     └─ Manual        └─ Monitor
```

## Monitoring and Logging Architecture

### 1. System Monitoring
```
Component Status → Metrics Collection → Analysis → Alerting
        │               │                │          │
        ├─ Health       ├─ Performance   ├─ Trends  ├─ Warnings
        ├─ Resources    ├─ Errors        ├─ Patterns├─ Errors
        ├─ Operations   ├─ Throughput    ├─ Issues  ├─ Status
        └─ Connections  └─ Latency       └─ Reports └─ Updates
```

### 2. Audit Logging
```
System Events → Log Processing → Storage → Reporting
        │            │             │         │
        ├─ Operations├─ Formatting  ├─ Files  ├─ Compliance
        ├─ Errors    ├─ Filtering   ├─ Database├─ Analysis
        ├─ Security  ├─ Enrichment  ├─ Archive├─ Forensics
        └─ Access    └─ Validation  └─ Backup └─ Audit
```

## Technology Stack

### Core Technologies
- **Python 3.8+**: Main application language
- **Web3.py**: Ethereum blockchain interaction
- **SQLite**: Local database storage
- **ReportLab**: PDF certificate generation
- **Ganache**: Local Ethereum blockchain

### Supporting Libraries
- **Hypothesis**: Property-based testing
- **QRCode**: QR code generation
- **PyYAML**: Configuration management
- **Logging**: Audit trail and debugging
- **Pathlib**: File system operations

### Development Tools
- **pytest**: Unit and integration testing
- **Black**: Code formatting
- **mypy**: Type checking
- **Git**: Version control
- **Virtual Environment**: Dependency isolation

## Deployment Architecture

### 1. Local Development
```
Developer Machine → Virtual Environment → Local Testing
        │                  │                  │
        ├─ Python 3.8+     ├─ Dependencies    ├─ Unit Tests
        ├─ Git Repo        ├─ Configuration   ├─ Integration
        ├─ IDE/Editor      ├─ Database        ├─ Property Tests
        └─ Ganache         └─ Certificates    └─ Validation
```

### 2. Production Deployment
```
Target System → Environment Setup → System Configuration → Operation
        │              │                    │                │
        ├─ Hardware    ├─ Python Install    ├─ Config Files  ├─ Processing
        ├─ OS          ├─ Dependencies      ├─ Database      ├─ Monitoring
        ├─ Network     ├─ Ganache Setup     ├─ Certificates  ├─ Maintenance
        └─ Security    └─ Permissions       └─ Logging       └─ Backup
```

This architecture ensures a robust, secure, and scalable system for secure data wiping with blockchain-based audit trails, suitable for academic demonstration and real-world application principles.