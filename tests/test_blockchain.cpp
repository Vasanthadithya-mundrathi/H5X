#include <gtest/gtest.h>
#include "blockchain/BlockchainVerifier.hpp"
#include <fstream>

namespace h5x {
namespace test {

class BlockchainTest : public ::testing::Test {
protected:
    void SetUp() override {
        verifier = std::make_unique<BlockchainVerifier>();
        
        // Create a test binary file
        testBinary = "test_binary.exe";
        std::ofstream file(testBinary, std::ios::binary);
        file << "fake binary content for testing";
        file.close();
    }
    
    void TearDown() override {
        if (std::filesystem::exists(testBinary)) {
            std::filesystem::remove(testBinary);
        }
    }
    
    std::unique_ptr<BlockchainVerifier> verifier;
    std::string testBinary;
};

TEST_F(BlockchainTest, BlockchainVerifierInitialization) {
    ASSERT_TRUE(verifier != nullptr);
    
    // Test configuration
    verifier->setNetwork("test-network");
    verifier->setRPCEndpoint("http://test.example.com:8545");
    
    // These should not crash
    EXPECT_NO_THROW(verifier->setNetwork("ganache-local"));
    EXPECT_NO_THROW(verifier->setRPCEndpoint("http://127.0.0.1:8545"));
}

TEST_F(BlockchainTest, BlockchainVerifierNetworkCheck) {
    // Set up test network (this will likely fail, which is expected in unit tests)
    verifier->setNetwork("test-network");
    verifier->setRPCEndpoint("http://invalid.test.endpoint:8545");
    
    // Network should not be available for invalid endpoint
    bool isAvailable = verifier->isNetworkAvailable();
    EXPECT_FALSE(isAvailable); // Should be false for invalid endpoint
}

TEST_F(BlockchainTest, BlockchainVerifierVerification) {
    // Configure for local testing
    verifier->setNetwork("ganache-local");
    verifier->setRPCEndpoint("http://127.0.0.1:8545");
    
    auto result = verifier->verifyBinary(testBinary);
    
    // The verification might fail if Ganache is not running, but we should get a proper result structure
    EXPECT_FALSE(result.binaryHash.empty()); // Hash should always be generated
    
    if (!result.success) {
        EXPECT_FALSE(result.errorMessage.empty()); // Should have error message if failed
    } else {
        EXPECT_FALSE(result.transactionHash.empty());
        EXPECT_FALSE(result.blockHash.empty());
    }
}

TEST_F(BlockchainTest, BlockchainVerifierInvalidBinary) {
    auto result = verifier->verifyBinary("nonexistent_binary.exe");
    
    EXPECT_FALSE(result.success);
    EXPECT_FALSE(result.errorMessage.empty());
    EXPECT_TRUE(result.transactionHash.empty());
    EXPECT_TRUE(result.blockHash.empty());
}

} // namespace test
} // namespace h5x