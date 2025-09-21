// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title H5XHashStorage
 * @dev Simple contract for storing and verifying obfuscation hashes
 * @notice This contract is used by the H5X obfuscation engine to record
 *         cryptographic proofs of obfuscation operations on the blockchain
 */
contract H5XHashStorage {
    
    // Event emitted when a hash is stored
    event HashStored(bytes32 indexed hash, address indexed sender, uint256 timestamp);
    
    // Event emitted when a hash is verified
    event HashVerified(bytes32 indexed hash, address indexed verifier, uint256 timestamp);
    
    // Mapping to store whether a hash exists
    mapping(bytes32 => bool) public hashes;
    
    // Mapping to store who stored each hash
    mapping(bytes32 => address) public hashOwners;
    
    // Mapping to store when each hash was stored
    mapping(bytes32 => uint256) public hashTimestamps;
    
    // Counter for total hashes stored
    uint256 public totalHashes;
    
    // Owner of the contract (for administrative functions)
    address public owner;
    
    // Modifier to restrict access to owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    /**
     * @dev Constructor sets the contract owner
     */
    constructor() {
        owner = msg.sender;
        totalHashes = 0;
    }
    
    /**
     * @dev Store a hash on the blockchain
     * @param _hash The hash to store (typically SHA256 of obfuscated code)
     */
    function storeHash(bytes32 _hash) external {
        require(_hash != bytes32(0), "Hash cannot be empty");
        require(!hashes[_hash], "Hash already exists");
        
        // Store the hash
        hashes[_hash] = true;
        hashOwners[_hash] = msg.sender;
        hashTimestamps[_hash] = block.timestamp;
        totalHashes++;
        
        // Emit event
        emit HashStored(_hash, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Verify if a hash exists on the blockchain
     * @param _hash The hash to verify
     * @return bool True if hash exists, false otherwise
     */
    function verifyHash(bytes32 _hash) external returns (bool) {
        bool exists = hashes[_hash];
        
        if (exists) {
            emit HashVerified(_hash, msg.sender, block.timestamp);
        }
        
        return exists;
    }
    
    /**
     * @dev Get information about a specific hash
     * @param _hash The hash to query
     * @return exists Whether the hash exists
     * @return storer Address that stored the hash
     * @return timestamp When the hash was stored
     */
    function getHashInfo(bytes32 _hash) external view returns (bool exists, address storer, uint256 timestamp) {
        return (hashes[_hash], hashOwners[_hash], hashTimestamps[_hash]);
    }
    
    /**
     * @dev Get contract statistics
     * @return total Total number of hashes stored
     * @return contractOwner Address of the contract owner
     */
    function getStats() external view returns (uint256 total, address contractOwner) {
        return (totalHashes, owner);
    }
    
    /**
     * @dev Emergency function to transfer ownership (admin only)
     * @param newOwner New owner address
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "New owner cannot be zero address");
        owner = newOwner;
    }
    
    /**
     * @dev Batch store multiple hashes (gas optimization)
     * @param _hashes Array of hashes to store
     */
    function batchStoreHashes(bytes32[] calldata _hashes) external {
        require(_hashes.length > 0, "No hashes provided");
        require(_hashes.length <= 50, "Too many hashes in batch");
        
        for (uint256 i = 0; i < _hashes.length; i++) {
            bytes32 hash = _hashes[i];
            require(hash != bytes32(0), "Hash cannot be empty");
            
            if (!hashes[hash]) {
                hashes[hash] = true;
                hashOwners[hash] = msg.sender;
                hashTimestamps[hash] = block.timestamp;
                totalHashes++;
                
                emit HashStored(hash, msg.sender, block.timestamp);
            }
        }
    }
    
    /**
     * @dev Check if multiple hashes exist (batch verification)
     * @param _hashes Array of hashes to verify
     * @return results Array of boolean results
     */
    function batchVerifyHashes(bytes32[] calldata _hashes) external view returns (bool[] memory results) {
        results = new bool[](_hashes.length);
        
        for (uint256 i = 0; i < _hashes.length; i++) {
            results[i] = hashes[_hashes[i]];
        }
        
        return results;
    }
}