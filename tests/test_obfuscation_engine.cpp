#include <gtest/gtest.h>
#include "core/H5XObfuscationEngine.hpp"
#include "utils/ConfigParser.hpp"
#include <filesystem>
#include <fstream>

namespace h5x {
namespace test {

class H5XObfuscationEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        engine = std::make_unique<H5XObfuscationEngine>();
        
        // Create test input file
        testInputFile = "test_input.cpp";
        std::ofstream file(testInputFile);
        file << R"(
#include <iostream>
#include <string>

int main() {
    std::string message = "Hello, World!";
    std::cout << message << std::endl;
    
    int result = 5 + 3;
    std::cout << "Result: " << result << std::endl;
    
    return 0;
}
)";
        file.close();
        
        testOutputDir = "test_output/";
        std::filesystem::create_directories(testOutputDir);
    }
    
    void TearDown() override {
        // Clean up test files
        if (std::filesystem::exists(testInputFile)) {
            std::filesystem::remove(testInputFile);
        }
        if (std::filesystem::exists(testOutputDir)) {
            std::filesystem::remove_all(testOutputDir);
        }
    }
    
    std::unique_ptr<H5XObfuscationEngine> engine;
    std::string testInputFile;
    std::string testOutputDir;
};

TEST_F(H5XObfuscationEngineTest, BasicObfuscationLevel1) {
    ASSERT_TRUE(engine != nullptr);
    
    bool success = engine->obfuscateFile(testInputFile, testOutputDir + "level1", 1);
    EXPECT_TRUE(success) << "Level 1 obfuscation should succeed";
    
    if (success) {
        auto report = engine->getLastReport();
        EXPECT_EQ(report.obfuscationLevel, 1);
        EXPECT_TRUE(report.success);
        EXPECT_GT(report.securityScore, 0.0);
        EXPECT_GT(report.processingTime, 0.0);
    }
}

TEST_F(H5XObfuscationEngineTest, BasicObfuscationLevel2) {
    ASSERT_TRUE(engine != nullptr);
    
    bool success = engine->obfuscateFile(testInputFile, testOutputDir + "level2", 2);
    EXPECT_TRUE(success) << "Level 2 obfuscation should succeed";
    
    if (success) {
        auto report = engine->getLastReport();
        EXPECT_EQ(report.obfuscationLevel, 2);
        EXPECT_TRUE(report.success);
        EXPECT_GT(report.securityScore, 60.0); // Level 2 should have reasonable security score
    }
}

TEST_F(H5XObfuscationEngineTest, ConfigurationSettings) {
    ObfuscationConfig config;
    config.level = 2;
    config.enableStringObfuscation = true;
    config.enableInstructionSubstitution = true;
    config.enableAI = false; // Disable AI for faster testing
    config.enableBlockchain = false; // Disable blockchain for testing
    
    engine->setConfig(config);
    
    auto retrievedConfig = engine->getConfig();
    EXPECT_EQ(retrievedConfig.level, 2);
    EXPECT_TRUE(retrievedConfig.enableStringObfuscation);
    EXPECT_TRUE(retrievedConfig.enableInstructionSubstitution);
    EXPECT_FALSE(retrievedConfig.enableAI);
    EXPECT_FALSE(retrievedConfig.enableBlockchain);
}

TEST_F(H5XObfuscationEngineTest, InvalidInputFile) {
    bool success = engine->obfuscateFile("nonexistent_file.cpp", testOutputDir + "invalid", 1);
    EXPECT_FALSE(success) << "Obfuscation should fail for nonexistent input file";
    
    std::string error = engine->getLastError();
    EXPECT_FALSE(error.empty()) << "Error message should be provided for invalid input";
}

TEST_F(H5XObfuscationEngineTest, InvalidObfuscationLevel) {
    bool success = engine->obfuscateFile(testInputFile, testOutputDir + "invalid_level", 10);
    EXPECT_FALSE(success) << "Obfuscation should fail for invalid level";
    
    std::string error = engine->getLastError();
    EXPECT_FALSE(error.empty()) << "Error message should be provided for invalid level";
}

TEST_F(H5XObfuscationEngineTest, ReportGeneration) {
    engine->enableReportGeneration(true);
    
    bool success = engine->obfuscateFile(testInputFile, testOutputDir + "report_test", 1);
    EXPECT_TRUE(success);
    
    auto report = engine->getLastReport();
    EXPECT_FALSE(report.inputFile.empty());
    EXPECT_FALSE(report.outputFile.empty());
    EXPECT_GT(report.originalSize, 0);
    EXPECT_GT(report.obfuscatedSize, 0);
    EXPECT_GT(report.sizeIncrease, 0.0);
}

} // namespace test
} // namespace h5x