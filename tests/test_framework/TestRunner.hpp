#ifndef TEST_RUNNER_HPP
#define TEST_RUNNER_HPP

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include "../../src/core/H5XObfuscationEngine.hpp"

namespace h5x_test {

struct TestResult {
    std::string testName;
    bool passed;
    std::string originalOutput;
    std::string obfuscatedOutput;
    double originalExecutionTime;
    double obfuscatedExecutionTime;
    size_t originalBinarySize;
    size_t obfuscatedBinarySize;
    std::string errorMessage;
    std::chrono::system_clock::time_point timestamp;
};

struct TestCase {
    std::string name;
    std::string sourceFile;
    std::vector<std::string> inputs;
    std::string expectedOutput;
    int obfuscationLevel;
    bool checkPerformance;
    bool checkBinarySize;
};

class TestRunner {
public:
    TestRunner();
    ~TestRunner();

    // Configuration
    bool initialize(const std::string& configPath = "");
    void setOutputDirectory(const std::string& outputDir);
    void setBuildDirectory(const std::string& buildDir);
    void setCompiler(const std::string& compiler);
    void setCompilerFlags(const std::vector<std::string>& flags);
    double measureExecutionTime(const std::string& binaryPath, const std::vector<std::string>& inputs);

    // Test execution
    TestResult runTest(const TestCase& testCase);
    std::vector<TestResult> runAllTests(const std::vector<TestCase>& testCases);
    std::vector<TestResult> runTestsFromDirectory(const std::string& testDir);

    // Binary management
    bool compileOriginal(const std::string& sourceFile, const std::string& outputBinary);
    bool obfuscateBinary(const std::string& inputFile, const std::string& outputBinary, int level);
    bool executeBinary(const std::string& binaryPath, const std::vector<std::string>& inputs, std::string& output);

    // Comparison utilities
    bool compareOutputs(const std::string& originalOutput, const std::string& obfuscatedOutput);
    double measureExecutionTime(const std::string& binaryPath, const std::vector<std::string>& inputs);
    size_t getBinarySize(const std::string& binaryPath);

    // Report generation
    void generateTestReport(const std::vector<TestResult>& results, const std::string& reportPath);
    void generatePerformanceReport(const std::vector<TestResult>& results, const std::string& reportPath);

    // Utility functions
    std::string getLastError() const;
    void setVerbose(bool verbose);
    void cleanup();

private:
    // Internal helper methods
    std::string generateTempFile(const std::string& prefix, const std::string& extension);
    bool runCommand(const std::string& command, std::string& output, int& exitCode);
    std::string extractOutputFromExecution(const std::string& rawOutput);
    void log(const std::string& message);

    // Member variables
    std::string outputDirectory_;
    std::string buildDirectory_;
    std::string compiler_;
    std::vector<std::string> compilerFlags_;
    bool verbose_;
    std::string lastError_;

    // H5X engine for obfuscation
    std::unique_ptr<h5x::H5XObfuscationEngine> obfuscationEngine_;
};

} // namespace h5x_test

#endif // TEST_RUNNER_HPP