#include "TestRunner.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <random>
#include <cstdlib>
#include <cstring>
#include <sys/stat.h>
#include <unistd.h>
#include <dirent.h>
#include <errno.h>
#include <chrono>

using namespace h5x_test;

TestRunner::TestRunner()
    : outputDirectory_("./test_output")
    , buildDirectory_("./build_test")
    , compiler_("g++")
    , verbose_(false)
    , obfuscationEngine_(std::make_unique<h5x::H5XObfuscationEngine>())
{
    // Create output directory if it doesn't exist
    mkdir(outputDirectory_.c_str(), 0755);
    mkdir(buildDirectory_.c_str(), 0755);
}

TestRunner::~TestRunner() {
    cleanup();
}

bool TestRunner::initialize(const std::string& configPath) {
    try {
        if (!obfuscationEngine_->initialize(configPath)) {
            lastError_ = "Failed to initialize H5X obfuscation engine";
            return false;
        }
        log("TestRunner initialized successfully");
        return true;
    } catch (const std::exception& e) {
        lastError_ = "Initialization error: " + std::string(e.what());
        return false;
    }
}

void TestRunner::setOutputDirectory(const std::string& outputDir) {
    outputDirectory_ = outputDir;
    mkdir(outputDirectory_.c_str(), 0755);
}

void TestRunner::setBuildDirectory(const std::string& buildDir) {
    buildDirectory_ = buildDir;
    mkdir(buildDirectory_.c_str(), 0755);
}

void TestRunner::setCompiler(const std::string& compiler) {
    compiler_ = compiler;
}

void TestRunner::setCompilerFlags(const std::vector<std::string>& flags) {
    compilerFlags_ = flags;
}


TestResult TestRunner::runTest(const TestCase& testCase) {
    TestResult result;
    result.testName = testCase.name;
    result.passed = false;
    result.timestamp = std::chrono::system_clock::now();

    log("Running test: " + testCase.name);

    try {
        // Generate temporary file paths
        std::string originalBinary = generateTempFile("original", "");
        std::string obfuscatedBinary = generateTempFile("obfuscated", "");

        // Step 1: Compile original program
        if (!compileOriginal(testCase.sourceFile, originalBinary)) {
            result.errorMessage = "Failed to compile original: " + lastError_;
            return result;
        }

        result.originalBinarySize = getBinarySize(originalBinary);

        // Step 2: Obfuscate the binary
        if (!obfuscateBinary(testCase.sourceFile, obfuscatedBinary, testCase.obfuscationLevel)) {
            result.errorMessage = "Failed to obfuscate: " + lastError_;
            return result;
        }

        result.obfuscatedBinarySize = getBinarySize(obfuscatedBinary);

        // Step 3: Execute both binaries and compare outputs
        std::string originalOutput, obfuscatedOutput;

        // Measure original execution time
        auto startTime = std::chrono::high_resolution_clock::now();
        if (!executeBinary(originalBinary, testCase.inputs, originalOutput)) {
            result.errorMessage = "Failed to execute original binary: " + lastError_;
            return result;
        }
        auto endTime = std::chrono::high_resolution_clock::now();
        result.originalExecutionTime = std::chrono::duration_cast<std::chrono::microseconds>(endTime - startTime).count() / 1000.0;

        // Measure obfuscated execution time
        startTime = std::chrono::high_resolution_clock::now();
        if (!executeBinary(obfuscatedBinary, testCase.inputs, obfuscatedOutput)) {
            result.errorMessage = "Failed to execute obfuscated binary: " + lastError_;
            return result;
        }
        endTime = std::chrono::high_resolution_clock::now();
        result.obfuscatedExecutionTime = std::chrono::duration_cast<std::chrono::microseconds>(endTime - startTime).count() / 1000.0;

        // Store outputs
        result.originalOutput = extractOutputFromExecution(originalOutput);
        result.obfuscatedOutput = extractOutputFromExecution(obfuscatedOutput);

        // Step 4: Compare outputs
        result.passed = compareOutputs(result.originalOutput, result.obfuscatedOutput);

        if (!result.passed) {
            result.errorMessage = "Outputs differ between original and obfuscated versions";
        }

        // Clean up temporary files
        remove(originalBinary.c_str());
        remove(obfuscatedBinary.c_str());

        log("Test completed: " + testCase.name + " - " + (result.passed ? "PASSED" : "FAILED"));

    } catch (const std::exception& e) {
        result.errorMessage = "Test execution error: " + std::string(e.what());
        log("Test failed with exception: " + result.errorMessage);
    }

    return result;
}

std::vector<TestResult> TestRunner::runAllTests(const std::vector<TestCase>& testCases) {
    std::vector<TestResult> results;

    log("Starting test suite with " + std::to_string(testCases.size()) + " tests");

    for (const auto& testCase : testCases) {
        TestResult result = runTest(testCase);
        results.push_back(result);

        if (!result.passed && verbose_) {
            log("FAILED: " + result.testName + " - " + result.errorMessage);
        }
    }

    size_t passed = 0;
    for (const auto& result : results) {
        if (result.passed) passed++;
    }

    log("Test suite completed: " + std::to_string(passed) + "/" + std::to_string(results.size()) + " tests passed");

    return results;
}

bool TestRunner::compileOriginal(const std::string& sourceFile, const std::string& outputBinary) {
    std::ostringstream command;
    command << compiler_;

    // Add compiler flags
    for (const auto& flag : compilerFlags_) {
        command << " " << flag;
    }

    command << " -o " << outputBinary << " " << sourceFile;

    std::string output;
    int exitCode;
    if (!runCommand(command.str(), output, exitCode)) {
        lastError_ = "Command execution failed";
        return false;
    }

    if (exitCode != 0) {
        lastError_ = "Compilation failed: " + output;
        return false;
    }

    return true;
}

bool TestRunner::obfuscateBinary(const std::string& inputFile, const std::string& outputBinary, int level) {
    // Use H5X CLI to obfuscate the file
    std::ostringstream command;
    command << "./h5x-cli obfuscate " << inputFile << " -o " << outputBinary << " --level " << level;

    if (!verbose_) {
        command << " --quiet";
    }

    std::string output;
    int exitCode;
    if (!runCommand(command.str(), output, exitCode)) {
        lastError_ = "H5X CLI execution failed";
        return false;
    }

    if (exitCode != 0) {
        lastError_ = "Obfuscation failed: " + output;
        return false;
    }

    return true;
}

bool TestRunner::executeBinary(const std::string& binaryPath, const std::vector<std::string>& inputs, std::string& output) {
    std::ostringstream command;
    command << binaryPath;

    for (const auto& input : inputs) {
        command << " " << input;
    }

    int exitCode;
    return runCommand(command.str(), output, exitCode);
}

bool TestRunner::compareOutputs(const std::string& originalOutput, const std::string& obfuscatedOutput) {
    // Simple string comparison - can be enhanced for more sophisticated comparison
    return originalOutput == obfuscatedOutput;
}

double TestRunner::measureExecutionTime(const std::string& binaryPath, const std::vector<std::string>& inputs) {
    auto startTime = std::chrono::high_resolution_clock::now();

    std::string output;
    executeBinary(binaryPath, inputs, output);

    auto endTime = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<std::chrono::microseconds>(endTime - startTime).count() / 1000.0;
}

size_t TestRunner::getBinarySize(const std::string& binaryPath) {
    struct stat st;
    if (stat(binaryPath.c_str(), &st) != 0) {
        return 0;
    }
    return st.st_size;
}

void TestRunner::generateTestReport(const std::vector<TestResult>& results, const std::string& reportPath) {
    std::ofstream reportFile(reportPath);

    if (!reportFile.is_open()) {
        log("Failed to create test report: " + reportPath);
        return;
    }

    reportFile << "H5X OBFUSCATION TEST REPORT\n";
    reportFile << "=====================================\n\n";
    reportFile << "Generated: " << std::chrono::system_clock::to_time_t(std::chrono::system_clock::now()) << "\n\n";

    size_t passed = 0;
    size_t failed = 0;

    for (const auto& result : results) {
        reportFile << "Test: " << result.testName << "\n";
        reportFile << "Status: " << (result.passed ? "PASSED" : "FAILED") << "\n";

        if (!result.passed) {
            reportFile << "Error: " << result.errorMessage << "\n";
            reportFile << "Expected Output: " << result.originalOutput << "\n";
            reportFile << "Actual Output: " << result.obfuscatedOutput << "\n";
        }

        reportFile << "Original Size: " << result.originalBinarySize << " bytes\n";
        reportFile << "Obfuscated Size: " << result.obfuscatedBinarySize << " bytes\n";
        reportFile << "Original Time: " << result.originalExecutionTime << " ms\n";
        reportFile << "Obfuscated Time: " << result.obfuscatedExecutionTime << " ms\n";
        reportFile << "Performance Impact: "
                   << (result.obfuscatedExecutionTime - result.originalExecutionTime) / result.originalExecutionTime * 100
                   << "%\n\n";

        if (result.passed) passed++;
        else failed++;
    }

    reportFile << "SUMMARY\n";
    reportFile << "=======\n";
    reportFile << "Total Tests: " << results.size() << "\n";
    reportFile << "Passed: " << passed << "\n";
    reportFile << "Failed: " << failed << "\n";
    reportFile << "Success Rate: " << (passed * 100 / results.size()) << "%\n";

    reportFile.close();
    log("Test report generated: " + reportPath);
}

std::string TestRunner::generateTempFile(const std::string& prefix, const std::string& extension) {
    std::string filename = prefix + "_" + std::to_string(rand()) + extension;
    return buildDirectory_ + "/" + filename;
}

bool TestRunner::runCommand(const std::string& command, std::string& output, int& exitCode) {
    try {
        std::string fullCommand = command + " 2>&1";
        FILE* pipe = popen(fullCommand.c_str(), "r");

        if (!pipe) {
            lastError_ = "Failed to execute command: " + command;
            return false;
        }

        char buffer[128];
        while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
            output += buffer;
        }

        exitCode = pclose(pipe);
        return true;
    } catch (const std::exception& e) {
        lastError_ = "Command execution error: " + std::string(e.what());
        return false;
    }
}

std::string TestRunner::extractOutputFromExecution(const std::string& rawOutput) {
    // Simple implementation - return the raw output
    // Can be enhanced to filter out prompts, timestamps, etc.
    return rawOutput;
}

void TestRunner::log(const std::string& message) {
    if (verbose_) {
        std::cout << "[TestRunner] " << message << std::endl;
    }
}

std::string TestRunner::getLastError() const {
    return lastError_;
}

void TestRunner::setVerbose(bool verbose) {
    verbose_ = verbose;
}

void TestRunner::cleanup() {
    try {
        // Clean up temporary files
        DIR* dir = opendir(buildDirectory_.c_str());
        if (dir) {
            struct dirent* entry;
            while ((entry = readdir(dir)) != nullptr) {
                std::string filename = buildDirectory_ + "/" + entry->d_name;
                if (filename.find("temp_") != std::string::npos) {
                    remove(filename.c_str());
                }
            }
            closedir(dir);
        }
    } catch (const std::exception& e) {
        // Ignore cleanup errors
    }
}