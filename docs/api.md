# H5X ENGINE API Reference

## Overview

The H5X Engine provides a comprehensive C++ API for code obfuscation with AI optimization and blockchain verification. This document covers all public interfaces and usage patterns.

## Core Classes

### H5XObfuscationEngine

The main engine class that orchestrates all obfuscation operations.

```cpp
#include "core/H5XObfuscationEngine.hpp"

namespace h5x {
    class H5XObfuscationEngine {
    public:
        // Constructor
        H5XObfuscationEngine();
        
        // Destructor
        ~H5XObfuscationEngine();
        
        // Main obfuscation interface
        bool obfuscateFile(const std::string& inputPath, 
                          const std::string& outputPath, 
                          int level = 1);
        
        // Configuration
        void setConfig(const ObfuscationConfig& config);
        ObfuscationConfig getConfig() const;
        
        // AI Optimization
        void enableAIOptimization(bool enable = true);
        bool isAIOptimizationEnabled() const;
        
        // Blockchain Verification
        void enableBlockchainVerification(bool enable = true);
        bool isBlockchainVerificationEnabled() const;
        
        // Report Generation
        void enableReportGeneration(bool enable = true);
        ObfuscationReport getLastReport() const;
        
        // Error Handling
        std::string getLastError() const;
    };
}
```

### ObfuscationConfig

Configuration structure for obfuscation parameters.

```cpp
struct ObfuscationConfig {
    // Obfuscation Levels (1-5)
    int level = 1;
    
    // String Obfuscation
    bool enableStringObfuscation = true;
    std::string stringEncryptionMethod = "AES-256-GCM";
    
    // Instruction Substitution
    bool enableInstructionSubstitution = false;
    double substitutionRate = 0.3;
    
    // Control Flow Obfuscation
    bool enableControlFlowFlattening = false;
    bool enableBogusControlFlow = false;
    double bogusFlowRate = 0.2;
    
    // Anti-Analysis
    bool enableAntiAnalysis = true;
    bool obfuscateFunctionNames = true;
    bool removeDebugInfo = true;
    
    // AI Optimization
    bool enableAI = false;
    int populationSize = 50;
    int generations = 100;
    double mutationRate = 0.1;
    
    // Blockchain
    bool enableBlockchain = false;
    std::string blockchainNetwork = "ganache-local";
    std::string rpcEndpoint = "http://127.0.0.1:8545";
    
    // Output Options
    bool generateReport = true;
    bool verbose = false;
};
```

### ObfuscationReport

Report structure containing metrics and results.

```cpp
struct ObfuscationReport {
    // Basic Info
    std::string inputFile;
    std::string outputFile;
    int obfuscationLevel;
    
    // Timing
    double processingTime;
    std::chrono::system_clock::time_point timestamp;
    
    // Size Metrics
    size_t originalSize;
    size_t obfuscatedSize;
    double sizeIncrease;
    
    // Security Metrics
    double securityScore;
    int functionsProcessed;
    int stringsObfuscated;
    int instructionsModified;
    
    // AI Metrics (if enabled)
    bool aiOptimizationUsed;
    int generations;
    double fitnessScore;
    
    // Blockchain Metrics (if enabled)
    bool blockchainVerificationUsed;
    std::string transactionHash;
    std::string blockHash;
    
    // Error Info
    bool success;
    std::string errorMessage;
};
```

## Utility Classes

### Logger

Logging system for debugging and monitoring.

```cpp
#include "utils/Logger.hpp"

namespace h5x {
    class Logger {
    public:
        enum Level { DEBUG, INFO, WARN, ERROR };
        
        static void log(Level level, const std::string& message);
        static void debug(const std::string& message);
        static void info(const std::string& message);
        static void warn(const std::string& message);
        static void error(const std::string& message);
        
        static void setLevel(Level level);
        static void setOutputFile(const std::string& filename);
    };
}
```

### ConfigParser

Configuration file parsing and management.

```cpp
#include "utils/ConfigParser.hpp"

namespace h5x {
    class ConfigParser {
    public:
        static ObfuscationConfig loadFromFile(const std::string& filename);
        static bool saveToFile(const ObfuscationConfig& config, 
                              const std::string& filename);
        static ObfuscationConfig getDefaultConfig();
    };
}
```

## AI Optimization

### GeneticOptimizer

AI-driven optimization for obfuscation parameters.

```cpp
#include "ai/GeneticOptimizer.hpp"

namespace h5x {
    class GeneticOptimizer {
    public:
        struct OptimizationResult {
            ObfuscationConfig optimizedConfig;
            double fitnessScore;
            int generations;
        };
        
        OptimizationResult optimize(const std::string& inputFile,
                                   const ObfuscationConfig& baseConfig);
        
        void setPopulationSize(int size);
        void setGenerations(int generations);
        void setMutationRate(double rate);
    };
}
```

## Blockchain Integration

### BlockchainVerifier

Blockchain verification for code integrity.

```cpp
#include "blockchain/BlockchainVerifier.hpp"

namespace h5x {
    class BlockchainVerifier {
    public:
        struct VerificationResult {
            bool success;
            std::string transactionHash;
            std::string blockHash;
            std::string binaryHash;
            std::string errorMessage;
        };
        
        VerificationResult verifyBinary(const std::string& binaryPath);
        
        void setNetwork(const std::string& network);
        void setRPCEndpoint(const std::string& endpoint);
        
        bool isNetworkAvailable() const;
    };
}
```

## Pass System

### Custom LLVM Passes

The H5X Engine includes custom LLVM passes for advanced transformations:

- **InstructionSubstitutionPass**: Mathematical operation obfuscation
- **ControlFlowFlatteningPass**: Control flow transformation
- **BogusControlFlowPass**: Fake control flow injection
- **StringObfuscationPass**: String encryption and decryption
- **AntiAnalysisPass**: Anti-reverse engineering techniques

## Usage Examples

### Basic Obfuscation

```cpp
#include "core/H5XObfuscationEngine.hpp"

int main() {
    h5x::H5XObfuscationEngine engine;
    
    // Configure obfuscation
    h5x::ObfuscationConfig config;
    config.level = 2;
    config.enableStringObfuscation = true;
    config.enableInstructionSubstitution = true;
    
    engine.setConfig(config);
    
    // Obfuscate file
    bool success = engine.obfuscateFile("input.cpp", "output_obfuscated", 2);
    
    if (success) {
        auto report = engine.getLastReport();
        std::cout << "Obfuscation completed in " << report.processingTime << "s" << std::endl;
        std::cout << "Security score: " << report.securityScore << std::endl;
    } else {
        std::cerr << "Error: " << engine.getLastError() << std::endl;
    }
    
    return 0;
}
```

### AI-Optimized Obfuscation

```cpp
#include "core/H5XObfuscationEngine.hpp"
#include "ai/GeneticOptimizer.hpp"

int main() {
    h5x::H5XObfuscationEngine engine;
    h5x::GeneticOptimizer optimizer;
    
    // Base configuration
    h5x::ObfuscationConfig baseConfig;
    baseConfig.level = 3;
    
    // Optimize configuration
    auto result = optimizer.optimize("input.cpp", baseConfig);
    
    // Use optimized configuration
    engine.setConfig(result.optimizedConfig);
    engine.enableAIOptimization(true);
    
    bool success = engine.obfuscateFile("input.cpp", "output_optimized", 3);
    
    return success ? 0 : 1;
}
```

### Blockchain-Verified Obfuscation

```cpp
#include "core/H5XObfuscationEngine.hpp"

int main() {
    h5x::H5XObfuscationEngine engine;
    
    // Enable blockchain verification
    engine.enableBlockchainVerification(true);
    
    h5x::ObfuscationConfig config;
    config.enableBlockchain = true;
    config.blockchainNetwork = "ganache-local";
    config.rpcEndpoint = "http://127.0.0.1:8545";
    
    engine.setConfig(config);
    
    bool success = engine.obfuscateFile("input.cpp", "output_verified", 2);
    
    if (success) {
        auto report = engine.getLastReport();
        std::cout << "Transaction Hash: " << report.transactionHash << std::endl;
        std::cout << "Block Hash: " << report.blockHash << std::endl;
    }
    
    return 0;
}
```

## Error Handling

All API functions provide comprehensive error handling:

- **Return Values**: Boolean success indicators for operations
- **Error Messages**: Detailed error descriptions via `getLastError()`
- **Exceptions**: Critical errors throw `std::runtime_error`
- **Logging**: All operations are logged for debugging

## Thread Safety

- **Engine**: Not thread-safe, use separate instances per thread
- **Logger**: Thread-safe for concurrent logging
- **ConfigParser**: Thread-safe for reading configurations

## Performance Considerations

- **Memory Usage**: Scales with input file size (2-5x typical)
- **Processing Time**: Level 1-2: <5s, Level 3-5: 5-30s
- **AI Optimization**: Additional 30-120s depending on parameters
- **Blockchain**: Additional 1-3s per verification

## Supported Platforms

- **macOS**: Intel x64, Apple Silicon (ARM64)
- **Linux**: x86_64, ARM64
- **Windows**: x64 (experimental)

## Dependencies

- **LLVM**: 17+ (21.1.1 recommended)
- **OpenSSL**: 1.1.1+ or 3.0+
- **libcurl**: 7.68.0+
- **jsoncpp**: 1.9.4+

---

For more examples and advanced usage, see the [examples](../examples/) directory.
