# Smart Contract Documentation

## WipeAuditContract.sol

The `WipeAuditContract` is a Solidity smart contract designed to provide immutable audit trails for secure data wiping operations. This contract serves as the blockchain component of the secure data wiping system for trustworthy IT asset recycling.

### Overview

The contract stores cryptographic proof of data wiping operations on a local Ethereum blockchain (Ganache), ensuring that audit records are immutable, verifiable, and tamper-proof. It follows academic best practices and is designed for final year project evaluation.

### Features

- **Immutable Record Storage**: Once a wipe record is stored, it cannot be modified or deleted
- **Access Control**: Only authorized operators can record wipe operations
- **Event Emission**: All operations emit events for external monitoring and audit trails
- **Hash Verification**: Built-in functions to verify wipe operation integrity
- **Owner Management**: Contract owner can authorize/revoke operators
- **Emergency Controls**: Pause/unpause functionality for security

### Contract Structure

#### Data Structures

```solidity
struct WipeRecord {
    string deviceId;        // Unique device identifier
    bytes32 wipeHash;      // SHA-256 hash of wiping operation metadata
    uint256 timestamp;     // Block timestamp when record was created
    address operator;      // Address of the operator who performed the wipe
    bool exists;          // Flag to check if record exists
}
```

#### Key Functions

##### Core Functions

- `recordWipe(string deviceId, bytes32 wipeHash)`: Records a new wipe operation
- `getWipeRecord(string deviceId)`: Retrieves a wipe record by device ID
- `verifyWipe(string deviceId, bytes32 expectedHash)`: Verifies a wipe hash against stored record
- `deviceProcessed(string deviceId)`: Checks if a device has been processed

##### Administrative Functions

- `authorizeOperator(address operator)`: Authorize an operator (owner only)
- `revokeOperator(address operator)`: Revoke operator authorization (owner only)
- `isAuthorizedOperator(address operator)`: Check if address is authorized
- `getOwner()`: Get contract owner address
- `getTotalRecords()`: Get total number of wipe records

##### Utility Functions

- `getContractInfo()`: Get contract metadata (owner, record count, version)
- `pause()/unpause()`: Emergency pause controls (owner only)
- `isPaused()`: Check if contract is paused

#### Events

- `WipeRecorded(string indexed deviceId, bytes32 indexed wipeHash, uint256 timestamp, address indexed operator)`
- `OperatorAuthorized(address indexed operator, address indexed authorizer)`
- `OperatorRevoked(address indexed operator, address indexed revoker)`

### Security Features

1. **Access Control Modifiers**:
   - `onlyOwner`: Restricts access to contract owner
   - `onlyAuthorizedOperator`: Restricts access to authorized operators
   - `validDeviceId`: Validates device ID input
   - `validWipeHash`: Validates wipe hash input

2. **Input Validation**:
   - Device IDs must be non-empty and reasonable length (≤100 characters)
   - Wipe hashes must be non-zero bytes32 values
   - Prevents duplicate device processing

3. **Immutability**:
   - Once recorded, wipe records cannot be modified
   - Device uniqueness enforced (one record per device)

4. **Emergency Controls**:
   - Pause functionality for security incidents
   - Owner-only administrative functions

### Deployment Information

#### Requirements

- **Solidity Version**: ^0.8.0
- **Network**: Local Ganache blockchain
- **Gas Limit**: ~3,000,000 (estimated)
- **Dependencies**: None (standalone contract)

#### Deployment Process

1. **Start Ganache**: `python scripts/start_ganache.py`
2. **Deploy Contract**: `python scripts/deploy_contract.py`
3. **Verify Deployment**: Automatic verification included in deployment script

#### Configuration Files Generated

After deployment, the following configuration files are created in the `config/` directory:

- `contract_config.json`: Contract address, ABI, and deployment info
- `blockchain_config.json`: Ganache connection and network information
- `contract_config.py`: Python module with contract constants
- `ganache_config.json`: Ganache connection parameters

### Usage Examples

#### Recording a Wipe Operation

```solidity
// Only authorized operators can call this
recordWipe("DEVICE_SN_123456", 0x1234567890abcdef...);
```

#### Retrieving a Wipe Record

```solidity
WipeRecord memory record = getWipeRecord("DEVICE_SN_123456");
```

#### Verifying a Wipe Operation

```solidity
bool isValid = verifyWipe("DEVICE_SN_123456", expectedHash);
```

### Testing

The contract has been thoroughly tested with property-based tests that verify:

- **Property 8**: Smart Contract Access Control
  - Unauthorized users cannot record wipe operations
  - Only contract owner can authorize/revoke operators
  - Multiple unauthorized attempts are consistently blocked
  - Batch operations respect access control

- **Data Integrity Properties**:
  - Wipe records are immutable once stored
  - Each device can only have one wipe record
  - Events are properly emitted for all operations

#### Running Tests

```bash
# Run smart contract property tests
python test_smart_contract_simple.py

# Run deployment tests
python test_deployment_simple.py
```

### Integration with Python Backend

The contract integrates with the Python backend through Web3.py:

```python
from web3 import Web3
import json

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# Load contract
with open('config/contract_config.json', 'r') as f:
    config = json.load(f)

contract = w3.eth.contract(
    address=config['contract_address'],
    abi=config['contract_abi']
)

# Record a wipe operation
tx_hash = contract.functions.recordWipe(
    device_id, wipe_hash
).transact({'from': operator_address})
```

### Academic Considerations

This smart contract is designed for academic evaluation and includes:

1. **Comprehensive Documentation**: Detailed comments and documentation
2. **Security Best Practices**: Access control, input validation, emergency controls
3. **Testing Coverage**: Property-based and unit tests
4. **Real-world Applicability**: Follows industry standards for audit trails
5. **Viva Preparation**: Clear explanations of design decisions and security features

### Compliance and Standards

- **NIST 800-88 Alignment**: Supports secure data wiping audit requirements
- **Blockchain Best Practices**: Immutable records, event emission, access control
- **Academic Standards**: Suitable for final year project evaluation
- **Industry Relevance**: Applicable to real-world IT asset recycling scenarios

### Future Enhancements

Potential improvements for production deployment:

1. **Multi-signature Support**: Require multiple operators for critical operations
2. **Role-based Access Control**: Different permission levels for different operations
3. **Batch Operations**: Support for recording multiple wipes in single transaction
4. **Upgrade Patterns**: Proxy contracts for future upgrades
5. **Gas Optimization**: Further optimization for lower transaction costs

### Troubleshooting

#### Common Issues

1. **"Only authorized operators can record wipes"**
   - Solution: Ensure the calling address is authorized via `authorizeOperator()`

2. **"Device has already been processed"**
   - Solution: Each device can only be processed once (immutability feature)

3. **"Contract is paused"**
   - Solution: Contract owner needs to call `unpause()`

4. **Gas estimation failed**
   - Solution: Increase gas limit or check input parameters

#### Support

For issues or questions:
1. Check the deployment logs in `logs/` directory
2. Verify Ganache is running on localhost:8545
3. Ensure contract is properly deployed with valid address
4. Review test outputs for debugging information

---

**Note**: This contract is designed for local development and academic purposes. For production deployment, additional security audits and optimizations would be recommended.