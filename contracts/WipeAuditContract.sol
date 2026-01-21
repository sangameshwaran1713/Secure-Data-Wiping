// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title WipeAuditContract
 * @dev Smart contract for immutable audit trail of secure data wiping operations
 * 
 * This contract provides cryptographically verifiable proof of data destruction
 * for IT asset recycling. It stores immutable records of wiping operations
 * on the blockchain for compliance and audit purposes.
 * 
 * Features:
 * - Immutable wipe record storage
 * - Event emission for external monitoring
 * - Access control for authorized operators
 * - Hash verification functions
 * 
 * Requirements Compliance:
 * - Requirement 4.1: WipeRecord struct with deviceId, wipeHash, timestamp, operator
 * - Requirement 4.2: recordWipe function accepting deviceId and wipeHash
 * - Requirement 4.3: getWipeRecord function returning WipeRecord by deviceId
 * - Requirement 4.4: WipeRecorded events with all required fields
 * - Requirement 4.5: Mapping from deviceId to WipeRecord for efficient lookups
 * - Requirement 4.7: Access control to prevent unauthorized modifications
 * 
 * @author Final Year Project Student
 * @notice This contract is designed for academic demonstration and local blockchain use
 */
contract WipeAuditContract {
    
    // ============================================================================
    // STATE VARIABLES
    // ============================================================================
    
    /**
     * @dev Structure to store wipe operation records
     * Contains all essential information for audit trail verification
     */
    struct WipeRecord {
        string deviceId;        // Unique device identifier
        bytes32 wipeHash;      // SHA-256 hash of wiping operation metadata
        uint256 timestamp;     // Block timestamp when record was created
        address operator;      // Address of the operator who performed the wipe
        bool exists;          // Flag to check if record exists (for validation)
    }
    
    /**
     * @dev Mapping from device ID to wipe record for efficient lookups
     * Requirement 4.5: Maintain mapping from deviceId to WipeRecord
     */
    mapping(string => WipeRecord) private wipeRecords;
    
    /**
     * @dev Mapping to track which devices have been processed
     * Used for existence checks and preventing duplicate records
     */
    mapping(string => bool) private deviceExists;
    
    /**
     * @dev Mapping to track authorized operators
     * Requirement 4.7: Access control to prevent unauthorized modifications
     */
    mapping(address => bool) private authorizedOperators;
    
    /**
     * @dev Contract owner for administrative functions
     */
    address private owner;
    
    /**
     * @dev Total number of wipe records stored
     */
    uint256 private totalRecords;
    
    // ============================================================================
    // EVENTS
    // ============================================================================
    
    /**
     * @dev Emitted when a wipe record is successfully stored
     * Requirement 4.4: Emit WipeRecorded events with deviceId, wipeHash, timestamp, operator
     * 
     * @param deviceId Unique identifier of the wiped device
     * @param wipeHash SHA-256 hash of the wiping operation metadata
     * @param timestamp Block timestamp when the record was created
     * @param operator Address of the operator who performed the wipe
     */
    event WipeRecorded(
        string indexed deviceId,
        bytes32 indexed wipeHash,
        uint256 timestamp,
        address indexed operator
    );
    
    /**
     * @dev Emitted when an operator is authorized
     * 
     * @param operator Address of the newly authorized operator
     * @param authorizer Address of the admin who granted authorization
     */
    event OperatorAuthorized(
        address indexed operator,
        address indexed authorizer
    );
    
    /**
     * @dev Emitted when an operator authorization is revoked
     * 
     * @param operator Address of the operator whose authorization was revoked
     * @param revoker Address of the admin who revoked authorization
     */
    event OperatorRevoked(
        address indexed operator,
        address indexed revoker
    );
    
    // ============================================================================
    // MODIFIERS
    // ============================================================================
    
    /**
     * @dev Modifier to restrict access to contract owner only
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "WipeAudit: Only owner can perform this action");
        _;
    }
    
    /**
     * @dev Modifier to restrict access to authorized operators only
     * Requirement 4.7: Access control to prevent unauthorized modifications
     */
    modifier onlyAuthorizedOperator() {
        require(
            authorizedOperators[msg.sender] || msg.sender == owner,
            "WipeAudit: Only authorized operators can record wipes"
        );
        _;
    }
    
    /**
     * @dev Modifier to validate device ID input
     */
    modifier validDeviceId(string memory deviceId) {
        require(bytes(deviceId).length > 0, "WipeAudit: Device ID cannot be empty");
        require(bytes(deviceId).length <= 100, "WipeAudit: Device ID too long");
        _;
    }
    
    /**
     * @dev Modifier to validate wipe hash input
     */
    modifier validWipeHash(bytes32 wipeHash) {
        require(wipeHash != bytes32(0), "WipeAudit: Wipe hash cannot be zero");
        _;
    }
    
    // ============================================================================
    // CONSTRUCTOR
    // ============================================================================
    
    /**
     * @dev Contract constructor
     * Sets the deployer as the owner and first authorized operator
     */
    constructor() {
        owner = msg.sender;
        authorizedOperators[msg.sender] = true;
        totalRecords = 0;
        
        emit OperatorAuthorized(msg.sender, msg.sender);
    }
    
    // ============================================================================
    // MAIN FUNCTIONS
    // ============================================================================
    
    /**
     * @dev Records a wipe operation on the blockchain
     * Requirement 4.2: Provide recordWipe function accepting deviceId and wipeHash
     * 
     * @param deviceId Unique identifier of the device that was wiped
     * @param wipeHash SHA-256 hash of the wiping operation metadata
     * 
     * Requirements:
     * - Only authorized operators can call this function
     * - Device ID must be valid (non-empty, reasonable length)
     * - Wipe hash must be non-zero
     * - Device cannot have been previously recorded (prevents duplicates)
     */
    function recordWipe(
        string memory deviceId,
        bytes32 wipeHash
    )
        public
        onlyAuthorizedOperator
        validDeviceId(deviceId)
        validWipeHash(wipeHash)
    {
        // Check if device has already been processed
        require(
            !deviceExists[deviceId],
            "WipeAudit: Device has already been processed"
        );
        
        // Create the wipe record
        // Requirement 4.1: WipeRecord struct with deviceId, wipeHash, timestamp, operator
        WipeRecord memory newRecord = WipeRecord({
            deviceId: deviceId,
            wipeHash: wipeHash,
            timestamp: block.timestamp,
            operator: msg.sender,
            exists: true
        });
        
        // Store the record
        wipeRecords[deviceId] = newRecord;
        deviceExists[deviceId] = true;
        totalRecords++;
        
        // Emit event for external monitoring
        // Requirement 4.4: Emit WipeRecorded events
        emit WipeRecorded(deviceId, wipeHash, block.timestamp, msg.sender);
    }
    
    /**
     * @dev Retrieves a wipe record by device ID
     * Requirement 4.3: Provide getWipeRecord function returning WipeRecord by deviceId
     * 
     * @param deviceId Unique identifier of the device
     * @return WipeRecord The complete wipe record for the device
     * 
     * Requirements:
     * - Device ID must be valid
     * - Record must exist for the device
     */
    function getWipeRecord(
        string memory deviceId
    )
        public
        view
        validDeviceId(deviceId)
        returns (WipeRecord memory)
    {
        require(
            deviceExists[deviceId],
            "WipeAudit: No record found for this device"
        );
        
        return wipeRecords[deviceId];
    }
    
    /**
     * @dev Verifies if a wipe hash matches the stored record for a device
     * 
     * @param deviceId Unique identifier of the device
     * @param expectedHash The hash to verify against stored record
     * @return bool True if the hash matches, false otherwise
     */
    function verifyWipe(
        string memory deviceId,
        bytes32 expectedHash
    )
        public
        view
        validDeviceId(deviceId)
        validWipeHash(expectedHash)
        returns (bool)
    {
        if (!deviceExists[deviceId]) {
            return false;
        }
        
        return wipeRecords[deviceId].wipeHash == expectedHash;
    }
    
    /**
     * @dev Checks if a device has been processed
     * 
     * @param deviceId Unique identifier of the device
     * @return bool True if device has been processed, false otherwise
     */
    function deviceProcessed(
        string memory deviceId
    )
        public
        view
        validDeviceId(deviceId)
        returns (bool)
    {
        return deviceExists[deviceId];
    }
    
    // ============================================================================
    // ADMINISTRATIVE FUNCTIONS
    // ============================================================================
    
    /**
     * @dev Authorizes an operator to record wipe operations
     * Requirement 4.7: Access control implementation
     * 
     * @param operator Address to authorize as an operator
     */
    function authorizeOperator(address operator) public onlyOwner {
        require(operator != address(0), "WipeAudit: Cannot authorize zero address");
        require(!authorizedOperators[operator], "WipeAudit: Operator already authorized");
        
        authorizedOperators[operator] = true;
        emit OperatorAuthorized(operator, msg.sender);
    }
    
    /**
     * @dev Revokes operator authorization
     * 
     * @param operator Address to revoke authorization from
     */
    function revokeOperator(address operator) public onlyOwner {
        require(operator != owner, "WipeAudit: Cannot revoke owner authorization");
        require(authorizedOperators[operator], "WipeAudit: Operator not authorized");
        
        authorizedOperators[operator] = false;
        emit OperatorRevoked(operator, msg.sender);
    }
    
    /**
     * @dev Checks if an address is an authorized operator
     * 
     * @param operator Address to check
     * @return bool True if authorized, false otherwise
     */
    function isAuthorizedOperator(address operator) public view returns (bool) {
        return authorizedOperators[operator];
    }
    
    /**
     * @dev Gets the contract owner address
     * 
     * @return address The owner's address
     */
    function getOwner() public view returns (address) {
        return owner;
    }
    
    /**
     * @dev Gets the total number of wipe records stored
     * 
     * @return uint256 Total number of records
     */
    function getTotalRecords() public view returns (uint256) {
        return totalRecords;
    }
    
    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================
    
    /**
     * @dev Gets contract information for verification
     * 
     * @return contractOwner Address of the contract owner
     * @return recordCount Total number of wipe records
     * @return contractVersion Version identifier for the contract
     */
    function getContractInfo()
        public
        view
        returns (
            address contractOwner,
            uint256 recordCount,
            string memory contractVersion
        )
    {
        return (owner, totalRecords, "1.0.0");
    }
    
    /**
     * @dev Emergency function to pause contract (if needed for security)
     * Note: This is a simple implementation for academic purposes
     * In production, consider using OpenZeppelin's Pausable contract
     */
    bool private paused = false;
    
    modifier whenNotPaused() {
        require(!paused, "WipeAudit: Contract is paused");
        _;
    }
    
    function pause() public onlyOwner {
        paused = true;
    }
    
    function unpause() public onlyOwner {
        paused = false;
    }
    
    function isPaused() public view returns (bool) {
        return paused;
    }
}