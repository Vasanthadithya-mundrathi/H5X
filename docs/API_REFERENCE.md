# H5X Engine - API Reference

## Table of Contents
- [Core Classes](#core-classes)
- [CLI Interface](#cli-interface)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Core Classes

### H5XObfuscationEngine

Main obfuscation engine class that orchestrates the entire obfuscation process.

#### Constructor
```cpp
H5XObfuscationEngine::H5XObfuscationEngine()
```

#### Initialization
```cpp
bool initialize(const std::string& configPath = "config/config.json")
```
**Parameters:**
- `configPath` (optional): Path to configuration file

**Returns:** `true` if initialization successful, `false` otherwise

#### Main Obfuscation Method
```cpp
bool obfuscateFile(const std::string& inputPath,
                   const std::string& outputPath,
                   int level)
```
**Parameters:**
- `inputPath`: Path to source file to obfuscate
- `outputPath`: Path for obfuscated output binary
- `level`: Obfuscation level (1-5)

**Returns:** `true` if obfuscation successful, `false` otherwise

#### Feature Toggles
```cpp
void enableAIOptimization(bool enable)
void enableBlockchainVerification(bool enable)
void enableReportGeneration(bool enable)

bool isAIOptimizationEnabled() const
bool isBlockchainVerificationEnabled() const
bool isReportGenerationEnabled() const
```

#### Configuration
```cpp
void setConfig(const ObfuscationConfig& config)
ObfuscationConfig getConfig() const
bool loadConfig(const std::string& configPath)
```

#### Information
```cpp
ObfuscationReport getLastReport() const
std::string getLastError() const
void setVerbose(bool verbose)
bool isVerbose() const
```

### ObfuscationReport

Structure containing detailed information about an obfuscation operation.

```cpp
struct ObfuscationReport {
    // File information
    std::string inputFile;
    std::string outputFile;
    size_t originalSize{0};
    size_t obfuscatedSize{0};
    double sizeIncrease{0.0};

    // Obfuscation details
    int obfuscationLevel{0};
    double processingTime{0.0};
    bool success{false};
    std::string errorMessage;
    std::vector<std::string> passesApplied;
    std::map<std::string, double> passTimings;

    // Metrics
    double securityScore{0.0};
    int functionsProcessed{0};
    int stringsObfuscated{0};
    int instructionsModified{0};

    // Advanced features
    bool aiOptimizationUsed{false};
    int generations{0};
    double fitnessScore{0.0};
    bool blockchainVerificationUsed{false};
    std::string transactionHash;
    std::string blockHash;

    // Timestamp
    std::chrono::system_clock::time_point timestamp;
};
```

### ObfuscationConfig

Configuration structure for customizing obfuscation behavior.

```cpp
struct ObfuscationConfig {
    // Basic settings
    int obfuscation_level{3};
    std::string target_platform{"native"};
    bool verbose{false};

    // Feature flags
    bool enable_string_obfuscation{true};
    bool enable_instruction_substitution{true};
    bool enable_bogus_control_flow{true};
    bool enable_control_flow_flattening{true};
    bool enable_anti_analysis{true};
    bool enable_junk_code_insertion{true};

    // AI optimization
    bool enable_ai_optimization{true};
    int genetic_algorithm_generations{100};
    int population_size{50};
    double mutation_rate{0.1};
    double crossover_rate{0.8};

    // Blockchain verification
    bool enable_blockchain_verification{true};
    std::string blockchain_network{"ganache-local"};
    std::string rpc_endpoint{"http://127.0.0.1:8545"};
    std::string contract_address;

    // Performance tuning
    double performance_weight{0.3};
    double security_weight{0.7};
};
```

---

## CLI Interface

### Command Line Usage

```bash
h5x-cli <command> [options] <input> -o <output>
```

### Commands

#### obfuscate
Obfuscate a single source file.

```bash
./h5x-cli obfuscate input.cpp -o output [options]

Options:
  -l, --level INT          Obfuscation level (1-5) [default: 3]
  --ai-optimize           Enable AI optimization
  --blockchain-verify     Enable blockchain verification
  --report               Generate detailed reports
  --verbose              Enable verbose output
  --config FILE          Use custom configuration file
  --target PLATFORM      Target platform (linux,macos,windows)
```

#### batch
Process multiple files in a directory.

```bash
./h5x-cli batch input_dir -o output_dir [options]

Options:
  --pattern PATTERN      File pattern to process (default: *.cpp)
  --recursive           Process subdirectories recursively
  --jobs INT            Number of parallel jobs [default: 4]
```

#### analyze
Analyze binary without obfuscation.

```bash
./h5x-cli analyze binary --report --verbose
```

#### verify
Verify existing obfuscated binary.

```bash
./h5x-cli verify binary --expected-hash HASH --report
```

### Exit Codes

| Code | Description |
|------|-------------|
| 0    | Success |
| 1    | General error |
| 2    | Invalid arguments |
| 3    | File not found |
| 4    | Obfuscation failed |
| 5    | Validation failed |

---

## Configuration

### Configuration File Format

#### Basic Configuration
```json
{
  "obfuscation_level": 3,
  "target_platform": "linux",
  "verbose": true,
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "enable_report_generation": true
}
```

#### Advanced Configuration
```json
{
  "obfuscation_level": 5,
  "target_platform": "native",
  "verbose": true,

  "ai_optimization": {
    "enabled": true,
    "generations": 100,
    "population_size": 50,
    "mutation_rate": 0.1,
    "crossover_rate": 0.8,
    "tournament_size": 3,
    "elitism_ratio": 0.1
  },

  "blockchain": {
    "network": "ganache-local",
    "rpc_endpoint": "http://127.0.0.1:8545",
    "chain_id": 1337,
    "contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    "gas_limit": 200000,
    "gas_price": "20000000000",
    "confirmation_blocks": 1
  },

  "validation": {
    "strict_mode": true,
    "thresholds": {
      "min_security_score": 80.0,
      "max_size_increase": 1000.0,
      "max_processing_time": 300.0
    }
  },

  "optimization_settings": {
    "performance_weight": 0.3,
    "security_weight": 0.7
  }
}
```

### Configuration Parameters

#### Obfuscation Levels
| Level | Techniques Applied | Typical Use Case |
|-------|-------------------|------------------|
| 1 | String Obfuscation | Basic IP protection |
| 2 | + Instruction Substitution | Commercial software |
| 3 | + Bogus Control Flow | Enterprise applications |
| 4 | + Control Flow Flattening | Financial systems |
| 5 | + Anti-Analysis + Junk Code | Military/cryptocurrency |

#### AI Optimization Settings
- `generations`: Number of genetic algorithm iterations (50-200)
- `population_size`: Size of solution population (20-100)
- `mutation_rate`: Probability of random mutations (0.01-0.2)
- `crossover_rate`: Probability of solution breeding (0.6-0.9)

#### Blockchain Settings
- `network`: Blockchain network ("ganache-local", "ethereum-mainnet")
- `rpc_endpoint`: RPC server URL
- `chain_id`: Network chain ID (1337 for Ganache)
- `gas_limit`: Maximum gas per transaction
- `confirmation_blocks`: Blocks to wait for confirmation

---

## Error Handling

### Exception Types

#### H5XException
Base exception class for all H5X errors.

```cpp
class H5XException : public std::runtime_error {
public:
    H5XException(const std::string& message);
    const char* what() const noexcept override;
};
```

#### InitializationException
Thrown when engine initialization fails.

```cpp
class InitializationException : public H5XException {
public:
    InitializationException(const std::string& component);
};
```

#### ObfuscationException
Thrown when obfuscation process fails.

```cpp
class ObfuscationException : public H5XException {
public:
    ObfuscationException(const std::string& pass, const std::string& reason);
};
```

### Error Reporting

#### Via Return Values
```cpp
bool success = engine.obfuscateFile("input.cpp", "output", 3);
if (!success) {
    std::string error = engine.getLastError();
    std::cerr << "Obfuscation failed: " << error << std::endl;
}
```

#### Via Exception Handling
```cpp
try {
    engine.obfuscateFile("input.cpp", "output", 3);
} catch (const H5XException& e) {
    std::cerr << "H5X Error: " << e.what() << std::endl;
} catch (const std::exception& e) {
    std::cerr << "System Error: " << e.what() << std::endl;
}
```

#### Via Report Structure
```cpp
ObfuscationReport report = engine.getLastReport();
if (!report.success) {
    std::cerr << "Obfuscation failed: " << report.errorMessage << std::endl;
}
```

---

## Examples

### Basic C++ Program Obfuscation

```cpp
#include "H5XObfuscationEngine.hpp"

int main() {
    h5x::H5XObfuscationEngine engine;

    // Initialize with default config
    if (!engine.initialize()) {
        std::cerr << "Failed to initialize: " << engine.getLastError() << std::endl;
        return 1;
    }

    // Obfuscate file
    bool success = engine.obfuscateFile("myapp.cpp", "protected_app", 5);

    if (success) {
        // Get results
        auto report = engine.getLastReport();
        std::cout << "Security Score: " << report.securityScore << std::endl;
        std::cout << "Size Increase: " << (report.sizeIncrease * 100) << "%" << std::endl;

        if (report.blockchainVerificationUsed) {
            std::cout << "Blockchain Hash: " << report.transactionHash << std::endl;
        }
    }

    return success ? 0 : 1;
}
```

### Custom Configuration

```cpp
#include "H5XObfuscationEngine.hpp"
#include "ConfigParser.hpp"

int main() {
    h5x::H5XObfuscationEngine engine;

    // Load custom configuration
    h5x::ConfigParser parser;
    if (!parser.load_from_file("custom_config.json")) {
        std::cerr << "Failed to load config" << std::endl;
        return 1;
    }

    auto config = parser.get_config();
    engine.setConfig(config);

    // Enable features
    engine.enableAIOptimization(true);
    engine.enableBlockchainVerification(true);
    engine.enableReportGeneration(true);
    engine.setVerbose(true);

    // Obfuscate
    return engine.obfuscateFile("app.cpp", "protected_app", config.obfuscation_level) ? 0 : 1;
}
```

### Batch Processing

```cpp
#include "H5XObfuscationEngine.hpp"
#include <filesystem>

int main() {
    h5x::H5XObfuscationEngine engine;
    engine.initialize();

    // Process all .cpp files in directory
    for (const auto& entry : std::filesystem::directory_iterator("src/")) {
        if (entry.path().extension() == ".cpp") {
            std::string input = entry.path().string();
            std::string output = "protected/" + entry.path().filename().string() + ".obf";

            std::cout << "Processing: " << input << std::endl;
            engine.obfuscateFile(input, output, 4);
        }
    }

    return 0;
}
```

### Report Analysis

```cpp
#include "H5XObfuscationEngine.hpp"
#include <iostream>

void analyzeReport(const h5x::ObfuscationReport& report) {
    std::cout << "=== Obfuscation Report ===" << std::endl;
    std::cout << "Input: " << report.inputFile << std::endl;
    std::cout << "Output: " << report.outputFile << std::endl;
    std::cout << "Level: " << report.obfuscationLevel << std::endl;
    std::cout << "Success: " << (report.success ? "Yes" : "No") << std::endl;

    if (report.success) {
        std::cout << "Security Score: " << report.securityScore << "/100" << std::endl;
        std::cout << "Size Increase: " << (report.sizeIncrease * 100) << "%" << std::endl;
        std::cout << "Processing Time: " << report.processingTime << "s" << std::endl;
        std::cout << "Functions Processed: " << report.functionsProcessed << std::endl;
        std::cout << "Strings Obfuscated: " << report.stringsObfuscated << std::endl;

        std::cout << "Passes Applied:" << std::endl;
        for (const auto& pass : report.passesApplied) {
            std::cout << "  - " << pass << std::endl;
        }

        if (report.aiOptimizationUsed) {
            std::cout << "AI Optimization: Yes (Fitness: " << report.fitnessScore << ")" << std::endl;
        }

        if (report.blockchainVerificationUsed) {
            std::cout << "Blockchain: Verified" << std::endl;
            std::cout << "  Transaction: " << report.transactionHash << std::endl;
            std::cout << "  Block: " << report.blockHash << std::endl;
        }
    } else {
        std::cout << "Error: " << report.errorMessage << std::endl;
    }
}

int main() {
    h5x::H5XObfuscationEngine engine;
    engine.initialize();

    engine.obfuscateFile("test.cpp", "protected_test", 5);
    analyzeReport(engine.getLastReport());

    return 0;
}
```

### Validation Integration

```cpp
#include "H5XObfuscationEngine.hpp"
#include "ReportValidator.hpp"

int main() {
    h5x::H5XObfuscationEngine engine;
    h5x::ReportValidator validator;

    // Obfuscate
    engine.initialize();
    bool obfuscationSuccess = engine.obfuscateFile("app.cpp", "protected_app", 5);

    if (obfuscationSuccess) {
        // Validate report
        auto report = engine.getLastReport();
        auto validation = validator.validateJsonReport("protected_app.report.json");

        std::cout << "Validation Score: " << validation.overallScore << "/100" << std::endl;
        std::cout << "Passed Metrics: " << validation.passedMetrics << std::endl;
        std::cout << "Failed Metrics: " << validation.failedMetrics << std::endl;

        if (!validation.criticalFailures.empty()) {
            std::cout << "Critical Failures:" << std::endl;
            for (const auto& failure : validation.criticalFailures) {
                std::cout << "  - " << failure << std::endl;
            }
        }

        if (!validation.recommendations.empty()) {
            std::cout << "Recommendations:" << std::endl;
            for (const auto& rec : validation.recommendations) {
                std::cout << "  - " << rec << std::endl;
            }
        }
    }

    return obfuscationSuccess ? 0 : 1;
}
```

---

## Integration Examples

### CMake Integration

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(MyApp)

# Find H5X
find_package(H5X REQUIRED)

# Source files
add_executable(myapp main.cpp)

# Obfuscate target
h5x_obfuscate_target(myapp
    LEVEL 5
    AI_OPTIMIZE ON
    BLOCKCHAIN_VERIFY ON
    REPORT ON
)
```

### Makefile Integration

```makefile
# Makefile
APP = myapp
SOURCE = main.cpp

.PHONY: build obfuscate clean

build: $(SOURCE)
	g++ -o $(APP) $(SOURCE)

obfuscate: build
	h5x-cli obfuscate $(SOURCE) -o $(APP)_protected \
		--level 5 \
		--ai-optimize \
		--blockchain-verify \
		--report

clean:
	rm -f $(APP) $(APP)_protected *.report.*
```

### Shell Script Integration

```bash
#!/bin/bash
# obfuscate_project.sh

set -e

PROJECT_NAME="myapp"
SOURCE_DIR="src"
OUTPUT_DIR="protected"

echo "Building H5X Engine..."
./build.sh

echo "Obfuscating $(PROJECT_NAME)..."
./h5x-cli batch $(SOURCE_DIR) -o $(OUTPUT_DIR) \
    --level 5 \
    --ai-optimize \
    --blockchain-verify \
    --report \
    --verbose

echo "Validating obfuscation..."
./tools/validate_obfuscation_reports.sh --strict

echo "Obfuscation complete!"
ls -la $(OUTPUT_DIR)/
```

---

## Best Practices

### 1. Choose Appropriate Obfuscation Level

```cpp
// For most applications
engine.obfuscateFile("app.cpp", "protected_app", 3);  // Good balance

// For high security
engine.obfuscateFile("sensitive.cpp", "ultra_secure", 5);  // Maximum protection

// For development/testing
engine.obfuscateFile("test.cpp", "debug_protected", 2);  // Faster builds
```

### 2. Always Validate Results

```cpp
// Complete validation workflow
bool success = engine.obfuscateFile("input.cpp", "output", level);
if (success) {
    // 1. Test functionality
    system("./output");

    // 2. Check report
    auto report = engine.getLastReport();
    if (report.securityScore < 80.0) {
        std::cerr << "Security score too low!" << std::endl;
    }

    // 3. Validate report format
    ReportValidator validator;
    auto validation = validator.validateJsonReport("output.report.json");
    if (!validation.overallSuccess) {
        std::cerr << "Report validation failed!" << std::endl;
    }
}
```

### 3. Use AI Optimization for Complex Code

```cpp
// Enable AI optimization for better results
engine.enableAIOptimization(true);
engine.obfuscateFile("complex_app.cpp", "optimized_protected", 4);
```

### 4. Verify Blockchain Integration

```cpp
// Check blockchain verification
auto report = engine.getLastReport();
if (report.blockchainVerificationUsed) {
    std::cout << "Blockchain verification: "
              << report.transactionHash << std::endl;
}
```

### 5. Handle Errors Gracefully

```cpp
try {
    engine.obfuscateFile("input.cpp", "output", 5);
} catch (const H5XException& e) {
    std::cerr << "H5X Error: " << e.what() << std::endl;
    // Log error, notify user, fallback to lower level
    engine.obfuscateFile("input.cpp", "output", 3);
} catch (const std::exception& e) {
    std::cerr << "System Error: " << e.what() << std::endl;
}
```

---

## Performance Considerations

### Memory Usage

- **Level 1-2**: ~100-200MB additional memory
- **Level 3-4**: ~200-500MB additional memory
- **Level 5**: ~500MB-1GB additional memory

### Processing Time

- **Level 1-2**: 1-3 seconds for typical applications
- **Level 3-4**: 3-8 seconds for typical applications
- **Level 5**: 8-20 seconds for typical applications

### Binary Size Impact

- **Level 1**: 800-1500% size increase
- **Level 2**: 400-800% size increase
- **Level 3**: 800-1500% size increase
- **Level 4**: 1500-3000% size increase
- **Level 5**: 3000-8000% size increase

### Runtime Performance Impact

- **Optimized builds**: <5% runtime overhead
- **Debug builds**: 5-15% runtime overhead
- **Unoptimized builds**: 15-30% runtime overhead

---

## Security Considerations

### Threat Model

H5X Engine is designed to protect against:

- **Static Analysis**: Disassembly and reverse engineering
- **Dynamic Analysis**: Debugging and runtime inspection
- **Automated Analysis**: Script-based deobfuscation attempts
- **Manual Analysis**: Human reverse engineering efforts

### Protection Limitations

H5X Engine does **not** protect against:

- **Side-channel attacks**: Timing, power, or cache analysis
- **Hardware attacks**: Physical access to memory or storage
- **Social engineering**: Tricking users into revealing information
- **Supply chain attacks**: Compromised build environments

### Compliance

For regulatory compliance:

```cpp
// Enable all verification features
engine.enableAIOptimization(true);
engine.enableBlockchainVerification(true);
engine.enableReportGeneration(true);

// Use maximum protection level
engine.obfuscateFile("sensitive_app.cpp", "compliant_app", 5);

// Verify compliance
auto report = engine.getLastReport();
assert(report.securityScore >= 95.0);
assert(report.blockchainVerificationUsed);
assert(report.aiOptimizationUsed);
```

---

## Troubleshooting

### Common Issues

#### Build Issues
```cpp
// Check LLVM installation
if (!engine.initialize()) {
    std::string error = engine.getLastError();
    if (error.find("LLVM") != std::string::npos) {
        // LLVM not found or incompatible version
        std::cerr << "Please install LLVM 21.1.1+" << std::endl;
    }
}
```

#### Runtime Issues
```cpp
// Check file permissions
struct stat buffer;
if (stat("input.cpp", &buffer) != 0) {
    std::cerr << "Input file not found or not readable" << std::endl;
}

// Check output directory
std::filesystem::create_directories("output/dir");
```

#### Performance Issues
```cpp
// Reduce complexity for large codebases
ObfuscationConfig config;
config.obfuscation_level = 3;
config.enable_ai_optimization = false;
engine.setConfig(config);
```

### Debug Information

```cpp
// Enable verbose logging
engine.setVerbose(true);

// Get detailed error information
std::string lastError = engine.getLastError();
auto report = engine.getLastReport();

// Log debug information
std::ofstream debug("debug.log");
debug << "Last Error: " << lastError << std::endl;
debug << "Report Success: " << report.success << std::endl;
if (!report.success) {
    debug << "Error Message: " << report.errorMessage << std::endl;
}
```

---

## Version History

### v1.0.0 (Current)
- ✅ All 6 obfuscation techniques implemented
- ✅ AI genetic optimization
- ✅ Blockchain verification with Ganache
- ✅ Comprehensive validation system
- ✅ Cross-platform support
- ✅ Production-ready stability

### Future Enhancements
- 🔄 Docker containerization
- 🔄 Web-based dashboard
- 🔄 Additional blockchain networks
- 🔄 Enhanced AI algorithms
- 🔄 Cloud deployment options

---

## Support

For technical support:

1. **Check Documentation**: [User Guide](H5X_USER_GUIDE.md)
2. **Review Examples**: See `demos/` directory
3. **Search Issues**: [GitHub Issues](https://github.com/Vasanthadithya-mundrathi/H5X/issues)
4. **Create Issue**: Report bugs or request features

**Example Issue Report:**
```markdown
## Problem
Obfuscation fails with "LLVM not found" error

## Environment
- OS: macOS 14.0
- LLVM: 21.1.1 (Homebrew)
- CMake: 3.28

## Steps to Reproduce
1. Run `./build.sh`
2. Run `./h5x-cli obfuscate test.cpp -o output`
3. Get error: "LLVM not found"

## Expected Behavior
Successful obfuscation with LLVM integration