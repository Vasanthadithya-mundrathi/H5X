#include <gtest/gtest.h>
#include "utils/ConfigParser.hpp"
#include "utils/Logger.hpp"
#include "utils/FileUtils.hpp"
#include <fstream>
#include <filesystem>

namespace h5x {
namespace test {

class UtilsTest : public ::testing::Test {
protected:
    void SetUp() override {
        testConfigFile = "test_config.json";
        testLogFile = "test.log";
    }
    
    void TearDown() override {
        if (std::filesystem::exists(testConfigFile)) {
            std::filesystem::remove(testConfigFile);
        }
        if (std::filesystem::exists(testLogFile)) {
            std::filesystem::remove(testLogFile);
        }
    }
    
    std::string testConfigFile;
    std::string testLogFile;
};

TEST_F(UtilsTest, ConfigParserDefaultConfig) {
    auto config = ConfigParser::getDefaultConfig();
    
    EXPECT_EQ(config.level, 1);
    EXPECT_TRUE(config.enableStringObfuscation);
    EXPECT_FALSE(config.enableInstructionSubstitution);
    EXPECT_FALSE(config.enableControlFlowFlattening);
    EXPECT_FALSE(config.enableBogusControlFlow);
    EXPECT_TRUE(config.enableAntiAnalysis);
    EXPECT_FALSE(config.enableAI);
    EXPECT_FALSE(config.enableBlockchain);
    EXPECT_TRUE(config.generateReport);
    EXPECT_FALSE(config.verbose);
}

TEST_F(UtilsTest, ConfigParserSaveAndLoad) {
    ObfuscationConfig originalConfig;
    originalConfig.level = 3;
    originalConfig.enableStringObfuscation = false;
    originalConfig.enableInstructionSubstitution = true;
    originalConfig.enableAI = true;
    originalConfig.aiPopulationSize = 75;
    originalConfig.aiGenerations = 150;
    originalConfig.blockchainNetwork = "test-network";
    originalConfig.rpcEndpoint = "http://test.example.com:8545";
    
    bool saveSuccess = ConfigParser::saveToFile(originalConfig, testConfigFile);
    EXPECT_TRUE(saveSuccess);
    EXPECT_TRUE(std::filesystem::exists(testConfigFile));
    
    auto loadedConfig = ConfigParser::loadFromFile(testConfigFile);
    
    EXPECT_EQ(loadedConfig.level, originalConfig.level);
    EXPECT_EQ(loadedConfig.enableStringObfuscation, originalConfig.enableStringObfuscation);
    EXPECT_EQ(loadedConfig.enableInstructionSubstitution, originalConfig.enableInstructionSubstitution);
    EXPECT_EQ(loadedConfig.enableAI, originalConfig.enableAI);
    EXPECT_EQ(loadedConfig.aiPopulationSize, originalConfig.aiPopulationSize);
    EXPECT_EQ(loadedConfig.aiGenerations, originalConfig.aiGenerations);
    EXPECT_EQ(loadedConfig.blockchainNetwork, originalConfig.blockchainNetwork);
    EXPECT_EQ(loadedConfig.rpcEndpoint, originalConfig.rpcEndpoint);
}

TEST_F(UtilsTest, ConfigParserInvalidFile) {
    auto config = ConfigParser::loadFromFile("nonexistent_config.json");
    
    // Should return default config when file doesn't exist
    auto defaultConfig = ConfigParser::getDefaultConfig();
    EXPECT_EQ(config.level, defaultConfig.level);
    EXPECT_EQ(config.enableStringObfuscation, defaultConfig.enableStringObfuscation);
}

TEST_F(UtilsTest, LoggerBasicFunctionality) {
    Logger::setOutputFile(testLogFile);
    Logger::setLevel(Logger::DEBUG);
    
    Logger::debug("Debug message");
    Logger::info("Info message");
    Logger::warn("Warning message");
    Logger::error("Error message");
    
    EXPECT_TRUE(std::filesystem::exists(testLogFile));
    
    std::ifstream logFile(testLogFile);
    std::string logContent((std::istreambuf_iterator<char>(logFile)),
                          std::istreambuf_iterator<char>());
    
    EXPECT_TRUE(logContent.find("Debug message") != std::string::npos);
    EXPECT_TRUE(logContent.find("Info message") != std::string::npos);
    EXPECT_TRUE(logContent.find("Warning message") != std::string::npos);
    EXPECT_TRUE(logContent.find("Error message") != std::string::npos);
}

TEST_F(UtilsTest, LoggerLevelFiltering) {
    Logger::setOutputFile(testLogFile);
    Logger::setLevel(Logger::WARN); // Only WARN and ERROR should be logged
    
    Logger::debug("Debug message");  // Should not appear
    Logger::info("Info message");    // Should not appear
    Logger::warn("Warning message"); // Should appear
    Logger::error("Error message");  // Should appear
    
    std::ifstream logFile(testLogFile);
    std::string logContent((std::istreambuf_iterator<char>(logFile)),
                          std::istreambuf_iterator<char>());
    
    EXPECT_TRUE(logContent.find("Debug message") == std::string::npos);
    EXPECT_TRUE(logContent.find("Info message") == std::string::npos);
    EXPECT_TRUE(logContent.find("Warning message") != std::string::npos);
    EXPECT_TRUE(logContent.find("Error message") != std::string::npos);
}

TEST_F(UtilsTest, FileUtilsReadWriteFile) {
    std::string testFile = "test_file_utils.txt";
    std::string testContent = "This is test content for file operations.";
    
    bool writeSuccess = FileUtils::writeFile(testFile, testContent);
    EXPECT_TRUE(writeSuccess);
    EXPECT_TRUE(std::filesystem::exists(testFile));
    
    std::string readContent = FileUtils::readFile(testFile);
    EXPECT_EQ(readContent, testContent);
    
    // Clean up
    if (std::filesystem::exists(testFile)) {
        std::filesystem::remove(testFile);
    }
}

TEST_F(UtilsTest, FileUtilsFileExists) {
    std::string existingFile = "existing_test_file.txt";
    std::string nonExistingFile = "non_existing_file.txt";
    
    // Create a test file
    std::ofstream file(existingFile);
    file << "test content";
    file.close();
    
    EXPECT_TRUE(FileUtils::fileExists(existingFile));
    EXPECT_FALSE(FileUtils::fileExists(nonExistingFile));
    
    // Clean up
    if (std::filesystem::exists(existingFile)) {
        std::filesystem::remove(existingFile);
    }
}

TEST_F(UtilsTest, FileUtilsGetFileSize) {
    std::string testFile = "test_size_file.txt";
    std::string content = "This content has a specific length.";
    
    std::ofstream file(testFile);
    file << content;
    file.close();
    
    size_t fileSize = FileUtils::getFileSize(testFile);
    EXPECT_EQ(fileSize, content.length());
    
    // Clean up
    if (std::filesystem::exists(testFile)) {
        std::filesystem::remove(testFile);
    }
}

} // namespace test
} // namespace h5x