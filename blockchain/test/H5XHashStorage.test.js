const H5XHashStorage = artifacts.require("H5XHashStorage");

/**
 * @title H5XHashStorage Contract Tests
 * @dev Comprehensive test suite for the hash storage contract
 */
contract("H5XHashStorage", (accounts) => {
  let hashStorage;
  const owner = accounts[0];
  const user1 = accounts[1];
  const user2 = accounts[2];
  
  // Test hashes (SHA256 format)
  const testHash1 = "0x1234567890123456789012345678901234567890123456789012345678901234";
  const testHash2 = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef";
  const testHash3 = "0x9876543210987654321098765432109876543210987654321098765432109876";
  const emptyHash = "0x0000000000000000000000000000000000000000000000000000000000000000";

  beforeEach(async () => {
    hashStorage = await H5XHashStorage.new({ from: owner });
  });

  describe("Contract Deployment", () => {
    it("should deploy successfully", async () => {
      assert(hashStorage.address !== "");
      console.log("📄 Contract deployed at:", hashStorage.address);
    });

    it("should set correct owner", async () => {
      const contractOwner = await hashStorage.owner();
      assert.equal(contractOwner, owner, "Owner should be set correctly");
    });

    it("should initialize with zero hashes", async () => {
      const stats = await hashStorage.getStats();
      assert.equal(stats.total.toNumber(), 0, "Initial hash count should be 0");
    });
  });

  describe("Hash Storage", () => {
    it("should store a hash successfully", async () => {
      const tx = await hashStorage.storeHash(testHash1, { from: user1 });
      
      // Check if hash exists
      const exists = await hashStorage.hashes(testHash1);
      assert.equal(exists, true, "Hash should exist after storage");
      
      // Check event emission
      assert.equal(tx.logs[0].event, "HashStored", "HashStored event should be emitted");
      assert.equal(tx.logs[0].args.hash, testHash1, "Event should have correct hash");
      assert.equal(tx.logs[0].args.sender, user1, "Event should have correct sender");
    });

    it("should not store empty hash", async () => {
      try {
        await hashStorage.storeHash(emptyHash, { from: user1 });
        assert.fail("Should have thrown an error for empty hash");
      } catch (error) {
        assert(error.message.includes("Hash cannot be empty"), "Should reject empty hash");
      }
    });

    it("should not store duplicate hash", async () => {
      // Store hash first time
      await hashStorage.storeHash(testHash1, { from: user1 });
      
      // Try to store same hash again
      try {
        await hashStorage.storeHash(testHash1, { from: user2 });
        assert.fail("Should have thrown an error for duplicate hash");
      } catch (error) {
        assert(error.message.includes("Hash already exists"), "Should reject duplicate hash");
      }
    });

    it("should track hash ownership correctly", async () => {
      await hashStorage.storeHash(testHash1, { from: user1 });
      
      const hashInfo = await hashStorage.getHashInfo(testHash1);
      assert.equal(hashInfo.exists, true, "Hash should exist");
      assert.equal(hashInfo.storer, user1, "Hash owner should be correct");
      assert(hashInfo.timestamp.toNumber() > 0, "Timestamp should be set");
    });

    it("should increment total hash count", async () => {
      await hashStorage.storeHash(testHash1, { from: user1 });
      await hashStorage.storeHash(testHash2, { from: user2 });
      
      const stats = await hashStorage.getStats();
      assert.equal(stats.total.toNumber(), 2, "Total hash count should be 2");
    });
  });

  describe("Hash Verification", () => {
    beforeEach(async () => {
      await hashStorage.storeHash(testHash1, { from: user1 });
    });

    it("should verify existing hash", async () => {
      const tx = await hashStorage.verifyHash(testHash1, { from: user2 });
      
      // Check return value (would need to call as a view function)
      const exists = await hashStorage.hashes(testHash1);
      assert.equal(exists, true, "Hash should be verified as existing");
      
      // Check event emission
      assert.equal(tx.logs[0].event, "HashVerified", "HashVerified event should be emitted");
      assert.equal(tx.logs[0].args.hash, testHash1, "Event should have correct hash");
      assert.equal(tx.logs[0].args.verifier, user2, "Event should have correct verifier");
    });

    it("should not verify non-existing hash", async () => {
      const exists = await hashStorage.hashes(testHash2);
      assert.equal(exists, false, "Non-existing hash should not be verified");
    });
  });

  describe("Batch Operations", () => {
    it("should store multiple hashes in batch", async () => {
      const hashes = [testHash1, testHash2, testHash3];
      const tx = await hashStorage.batchStoreHashes(hashes, { from: user1 });
      
      // Verify all hashes were stored
      for (let hash of hashes) {
        const exists = await hashStorage.hashes(hash);
        assert.equal(exists, true, `Hash ${hash} should exist`);
      }
      
      // Check total count
      const stats = await hashStorage.getStats();
      assert.equal(stats.total.toNumber(), 3, "Total hash count should be 3");
      
      // Check events
      assert.equal(tx.logs.length, 3, "Should emit 3 HashStored events");
    });

    it("should verify multiple hashes in batch", async () => {
      // Store some hashes first
      await hashStorage.storeHash(testHash1, { from: user1 });
      await hashStorage.storeHash(testHash2, { from: user1 });
      
      const hashes = [testHash1, testHash2, testHash3];
      const results = await hashStorage.batchVerifyHashes(hashes);
      
      assert.equal(results[0], true, "First hash should exist");
      assert.equal(results[1], true, "Second hash should exist");
      assert.equal(results[2], false, "Third hash should not exist");
    });

    it("should reject empty batch", async () => {
      try {
        await hashStorage.batchStoreHashes([], { from: user1 });
        assert.fail("Should have thrown an error for empty batch");
      } catch (error) {
        assert(error.message.includes("No hashes provided"), "Should reject empty batch");
      }
    });

    it("should reject batch that's too large", async () => {
      // Create array with 51 hashes (limit is 50)
      const largeHashArray = Array(51).fill().map((_, i) => 
        `0x${i.toString(16).padStart(64, '0')}`
      );
      
      try {
        await hashStorage.batchStoreHashes(largeHashArray, { from: user1 });
        assert.fail("Should have thrown an error for batch too large");
      } catch (error) {
        assert(error.message.includes("Too many hashes in batch"), "Should reject large batch");
      }
    });
  });

  describe("Ownership Management", () => {
    it("should transfer ownership", async () => {
      await hashStorage.transferOwnership(user1, { from: owner });
      
      const newOwner = await hashStorage.owner();
      assert.equal(newOwner, user1, "Ownership should be transferred");
    });

    it("should not allow non-owner to transfer ownership", async () => {
      try {
        await hashStorage.transferOwnership(user2, { from: user1 });
        assert.fail("Should have thrown an error for non-owner");
      } catch (error) {
        assert(error.message.includes("Only owner can call this function"), 
               "Should reject non-owner transfer");
      }
    });

    it("should not allow transfer to zero address", async () => {
      try {
        await hashStorage.transferOwnership("0x0000000000000000000000000000000000000000", { from: owner });
        assert.fail("Should have thrown an error for zero address");
      } catch (error) {
        assert(error.message.includes("New owner cannot be zero address"), 
               "Should reject zero address");
      }
    });
  });

  describe("Integration Scenarios", () => {
    it("should handle typical H5X workflow", async () => {
      console.log("🔄 Testing H5X integration workflow...");
      
      // Simulate H5X storing obfuscation hashes
      const obfuscatedCodeHash = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef";
      const metadataHash = "0xcafebabecafebabecafebabecafebabecafebabecafebabecafebabecafebabe";
      
      // Store hashes
      await hashStorage.storeHash(obfuscatedCodeHash, { from: user1 });
      await hashStorage.storeHash(metadataHash, { from: user1 });
      
      // Verify hashes (as H5X would do during verification)
      const codeExists = await hashStorage.hashes(obfuscatedCodeHash);
      const metaExists = await hashStorage.hashes(metadataHash);
      
      assert.equal(codeExists, true, "Obfuscated code hash should be verified");
      assert.equal(metaExists, true, "Metadata hash should be verified");
      
      // Check complete hash info
      const codeInfo = await hashStorage.getHashInfo(obfuscatedCodeHash);
      assert.equal(codeInfo.storer, user1, "Hash should be attributed to correct user");
      
      console.log("✅ H5X integration workflow completed successfully");
    });
  });
});