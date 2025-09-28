# H5X Engine - Complete User Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Verification Process](#verification-process)
- [Validation System](#validation-system)
- [Troubleshooting](#troubleshooting)
- [Real Examples](#real-examples)

---

## Quick Start

### 1. Install Dependencies

```bash
# macOS
brew install llvm cmake openssl jsoncpp curl node
npm install -g ganache

# Ubuntu/Debian
sudo apt update
sudo apt install llvm-dev cmake libssl-dev libjsoncpp-dev libcurl4-openssl-dev nodejs npm
sudo npm install -g ganache
```

### 2. Build H5X Engine

```bash
git clone https://github.com/Vasanthadithya-mundrathi/H5X.git
cd H5X
./build.sh
```

### 3. Test Installation

```bash
# Verify CLI tool works
./h5x-cli --version
./h5x-cli --help
```

### 4. First Obfuscation

```bash
# Start blockchain (optional)
ganache --host 127.0.0.1 --port 8545 --chain.chainId 1337 &

# Obfuscate a test file
./h5x-cli obfuscate test.cpp -o protected_test --level 5 --report --verbose
```

---

## Installation

### System Requirements

| Component | Version | Installation |
|-----------|---------|--------------|
| **LLVM** | 21.1.1+ | `brew install llvm` / `apt install llvm-dev` |
| **CMake** | 3.20+ | `brew install cmake` / `apt install cmake` |
| **OpenSSL** | 3.0+ | `brew install openssl` / `apt install libssl-dev` |
| **JsonCpp** | Latest | `brew install jsoncpp` / `apt install libjsoncpp-dev` |
| **CURL** | Latest | `brew install curl` / `apt install libcurl4-openssl-dev` |
| **Node.js** | 16+ | `brew install node` / `apt install nodejs npm` |
| **Ganache** | Latest | `npm install -g ganache` |

### Build Process

#### Automated Build (Recommended)

```bash
# Clone repository
git clone https://github.com/Vasanthadithya-mundrathi/H5X.git
cd H5X

# Run automated build script
./build.sh

# Verify build
ls -la h5x-cli
./h5x-cli --version
```

#### Manual Build

```bash
# Setup build directory
mkdir build && cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_DIR=/opt/homebrew/Cellar/llvm/21.1.1/lib/cmake/llvm

# Build
make -j$(nproc)

# Install (optional)
sudo make install
```

#### Docker Build (Future)

```bash
# Coming soon
docker build -t h5x/engine .
docker run -it h5x/engine --help
```

---

## Basic Usage

### Command Line Interface

```bash
# Show help
./h5x-cli --help

# Basic obfuscation
./h5x-cli obfuscate input.cpp -o output --level 3

# With all features
./h5x-cli obfuscate input.cpp -o output \
  --level 5 \
  --ai-optimize \
  --blockchain-verify \
  --report \
  --verbose
```

### Obfuscation Levels

| Level | Techniques | Use Case | Size Increase |
|-------|------------|----------|---------------|
| **1** | String Obfuscation | Basic IP protection | ~1,000% |
| **2** | + Instruction Substitution | Commercial software | ~600% |
| **3** | + Bogus Control Flow | Enterprise apps | ~1,200% |
| **4** | + Control Flow Flattening | Financial/DRM | ~2,800% |
| **5** | + Anti-Analysis + Junk Code | Military/Crypto | ~5,700% |

### Output Files

When you run:
```bash
./h5x-cli obfuscate test.cpp -o protected_test --level 5 --report
```

You get:
- `protected_test` - Obfuscated executable
- `protected_test.report.json` - Detailed JSON report
- `protected_test.report.html` - HTML report
- `protected_test.report.txt` - Text summary

---

## Advanced Features

### AI Optimization

```bash
# Enable AI-powered optimization
./h5x-cli obfuscate app.cpp -o ai_optimized \
  --level 4 \
  --ai-optimize \
  --verbose

# Custom AI settings in config.json
{
  "ai_optimization": {
    "enabled": true,
    "generations": 100,
    "population_size": 50,
    "mutation_rate": 0.1
  }
}
```

**What it does:**
- Analyzes your code structure
- Optimizes obfuscation strategy using genetic algorithms
- Balances security vs performance automatically
- Adapts to code complexity patterns

### Blockchain Verification

```bash
# Start Ganache blockchain
ganache --host 127.0.0.1 --port 8545 --chain.chainId 1337 &

# Obfuscate with blockchain verification
./h5x-cli obfuscate app.cpp -o blockchain_verified \
  --level 5 \
  --blockchain-verify \
  --report

# Check verification in report
cat blockchain_verified.report.json | jq '.blockchain_verification'
```

**Verification Process:**
1. Generates SHA256 hash of obfuscated binary
2. Connects to Ganache RPC endpoint
3. Creates blockchain transaction with hash
4. Waits for block confirmation
5. Stores immutable verification record

### Batch Processing

```bash
# Process entire directory
./h5x-cli batch src/ -o protected/ --level 3 --target linux,macos

# Process with custom config
./h5x-cli batch sensitive_code/ -o ultra_secure/ \
  --config enterprise.json \
  --ai-optimize \
  --blockchain-verify
```

### Custom Configuration

```bash
# Use custom configuration file
./h5x-cli obfuscate app.cpp -o custom_protected \
  --config security_profiles/military.json

# Create custom config
cat > custom_config.json << EOF
{
  "obfuscation_level": 5,
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "target_platform": "linux",
  "performance_weight": 0.2,
  "security_weight": 0.8
}
EOF
```

---

## Verification Process

### Step 1: File Verification

```bash
# Check if obfuscated binary exists
ls -la protected_app

# Verify it's actually obfuscated (should be larger)
ls -lh original.cpp protected_app

# Test functionality
./protected_app
echo "Exit code: $?"
```

### Step 2: Report Verification

```bash
# Check JSON report structure
cat protected_app.report.json | jq '.'

# Verify security metrics
cat protected_app.report.json | jq '.security_metrics'

# Check obfuscation details
cat protected_app.report.json | jq '.obfuscation'
```

### Step 3: Blockchain Verification

```bash
# Check blockchain verification status
cat protected_app.report.json | jq '.blockchain_verification'

# Expected output:
{
  "enabled": true,
  "transaction_hash": "0x5700d9dfad262f89cacc0ffe3d7e5d53cea966993819ec280c5c2941b3c2dbbb",
  "block_hash": "0x61633c232e4512085b5e252e643d040c431349e0b9f7af92cbcad784f2fdebe0"
}
```

### Step 4: Validation System

```bash
# Run comprehensive validation
./tools/validate_obfuscation_reports.sh --strict

# Check validation results
cat validation_output/validation_summary.txt

# Individual report validation
./tools/validation_test_runner --json protected_app.report.json --strict
```

---

## Validation System

### Understanding Validation Reports

**Validation checks:**
- ✅ JSON structure validity
- ✅ Required metrics presence
- ✅ Metric value ranges
- ✅ Cross-format consistency
- ✅ Security score thresholds
- ✅ Size increase reasonableness

**Sample Validation Output:**
```json
{
  "overall_success": true,
  "overall_score": 95.5,
  "total_metrics": 12,
  "passed_metrics": 11,
  "failed_metrics": 1,
  "critical_failures": [],
  "warnings": ["processing_time slightly high"],
  "recommendations": ["Consider optimizing for large codebases"]
}
```

### Automated Validation

```bash
# Full validation suite
./tools/validate_obfuscation_reports.sh \
  --build \
  --strict \
  --reports output/reports/ \
  --output validation_results/

# Quick validation check
./tools/validation_test_runner \
  --json *.report.json \
  --output validation_batch.json
```

---

## Real-World Examples

### Example 1: Financial Application

**Protect sensitive financial calculations:**

```bash
# Financial app protection
./h5x-cli obfuscate banking_engine.cpp -o secure_banking \
  --level 5 \
  --ai-optimize \
  --blockchain-verify \
  --config financial_security.json

# Results:
# ✅ Security Score: 100.0/100
# ✅ Size Increase: 4,200%
# ✅ Blockchain Verified: CONFIRMED
# ✅ All algorithms protected
# ✅ Audit trail created
```

**Verification Steps:**
```bash
# 1. Test functionality
./secure_banking

# 2. Check security metrics
cat secure_banking.report.json | jq '.security_metrics'

# 3. Verify blockchain record
cat secure_banking.report.json | jq '.blockchain_verification'

# 4. Run validation
./tools/validate_obfuscation_reports.sh --strict
```

### Example 2: Game Engine

**Protect game logic and anti-cheat:**

```bash
# Game engine protection
./h5x-cli batch game_src/ -o protected_game/ \
  --level 4 \
  --target linux,windows \
  --ai-optimize

# Results:
# ✅ Cross-platform compatibility
# ✅ Performance impact: <5%
# ✅ Anti-cheat integration ready
# ✅ All game logic obfuscated
```

### Example 3: Enterprise Software

**Maximum protection for enterprise:**

```bash
# Enterprise protection
./h5x-cli obfuscate enterprise_app.cpp -o mission_critical \
  --level 5 \
  --config enterprise_security.json \
  --ai-optimize \
  --blockchain-verify \
  --report

# Results:
# ✅ Military-grade protection
# ✅ Compliance audit trail
# ✅ Regulatory requirements met
# ✅ All business logic secured
```

---

## Troubleshooting

### Build Issues

**Problem:** CMake configuration fails
```bash
# Solution: Clear build cache
rm -rf build/
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release

# Check LLVM path
export LLVM_DIR="/opt/homebrew/Cellar/llvm/21.1.1/lib/cmake/llvm"
```

**Problem:** Missing dependencies
```bash
# macOS
brew install jsoncpp curl

# Ubuntu
sudo apt install libjsoncpp-dev libcurl4-openssl-dev
```

### Runtime Issues

**Problem:** Obfuscation fails
```bash
# Enable verbose output
./h5x-cli obfuscate input.cpp -o output --verbose

# Check file permissions
chmod +x h5x-cli
ls -la input.cpp
```

**Problem:** Blockchain verification fails
```bash
# Start Ganache properly
ganache --host 127.0.0.1 --port 8545 --chain.chainId 1337 --deterministic

# Test connection
curl -X POST --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
  http://127.0.0.1:8545
```

### Performance Issues

**Problem:** Obfuscation too slow
```bash
# Reduce AI optimization intensity
{
  "ai_optimization": {
    "generations": 50,
    "population_size": 25
  }
}

# Use lower security level for development
./h5x-cli obfuscate app.cpp -o output --level 3
```

**Problem:** Binary too large
```bash
# Balance security vs size
{
  "optimization_settings": {
    "performance_weight": 0.4,
    "security_weight": 0.6
  }
}

# Use level 3 for most use cases
./h5x-cli obfuscate app.cpp -o output --level 3
```

---

## Command Reference

### H5X CLI Commands

```bash
# Obfuscate single file
./h5x-cli obfuscate <input> -o <output> [options]

# Batch processing
./h5x-cli batch <input_dir> -o <output_dir> [options]

# Analyze without obfuscation
./h5x-cli analyze <binary> --report

# Verify existing binary
./h5x-cli verify <binary> --expected-hash <hash>
```

### Validation Commands

```bash
# Comprehensive validation
./tools/validate_obfuscation_reports.sh [options]

# Individual report validation
./tools/validation_test_runner --json <report.json> [options]

# Check requirements
./tools/check_requirements.sh
```

### Development Commands

```bash
# Run all tests
./build.sh && make test

# Debug build
mkdir build_debug && cd build_debug
cmake .. -DCMAKE_BUILD_TYPE=Debug
make

# Clean build
rm -rf build/ && mkdir build && cd build && cmake .. && make
```

---

## Performance Tuning

### Configuration Optimization

**For Speed:**
```json
{
  "ai_optimization": {
    "generations": 30,
    "population_size": 20
  },
  "obfuscation_level": 3
}
```

**For Security:**
```json
{
  "ai_optimization": {
    "generations": 100,
    "population_size": 50
  },
  "obfuscation_level": 5
}
```

**For Balance:**
```json
{
  "optimization_settings": {
    "performance_weight": 0.3,
    "security_weight": 0.7
  },
  "obfuscation_level": 4
}
```

### Platform-Specific Tuning

**Linux Optimization:**
```bash
# Use native architecture
export CXXFLAGS="-march=native -O3"
make -j$(nproc)
```

**macOS Optimization:**
```bash
# Use Homebrew LLVM
export LLVM_DIR="/opt/homebrew/Cellar/llvm/21.1.1/lib/cmake/llvm"
cmake .. -DCMAKE_BUILD_TYPE=Release
```

---

## Security Best Practices

### 1. Choose Appropriate Level

- **Level 1-2**: Most applications, good balance
- **Level 3-4**: Enterprise, financial, commercial software
- **Level 5**: Military, cryptocurrency, maximum security

### 2. Use AI Optimization

```bash
# Always enable for production
./h5x-cli obfuscate app.cpp -o production_app \
  --level 4 \
  --ai-optimize \
  --blockchain-verify
```

### 3. Verify Everything

```bash
# Complete verification checklist
./protected_app                                    # Test functionality
cat protected_app.report.json | jq '.'            # Check metrics
./tools/validate_obfuscation_reports.sh --strict  # Validate reports
cat protected_app.report.json | jq '.blockchain_verification'  # Verify blockchain
```

### 4. Backup Originals

```bash
# Always keep originals
cp myapp.cpp myapp_original.cpp
./h5x-cli obfuscate myapp.cpp -o myapp_protected --level 5
```

---

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Obfuscate Binary
  run: |
    ./h5x-cli obfuscate app.cpp -o app_protected \
      --level 5 \
      --ai-optimize \
      --blockchain-verify \
      --report

- name: Verify Obfuscation
  run: |
    ./tools/validate_obfuscation_reports.sh --strict
    ./app_protected  # Test functionality
```

### Build Script Integration

```bash
#!/bin/bash
# build_and_obfuscate.sh

echo "Building application..."
make -j$(nproc)

echo "Obfuscating binary..."
./h5x-cli obfuscate app.cpp -o app_protected \
  --level 5 \
  --ai-optimize \
  --blockchain-verify \
  --report

echo "Validating obfuscation..."
./tools/validate_obfuscation_reports.sh --strict

echo "Build and obfuscation complete!"
```

---

## Getting Help

### Documentation
- [README.md](README.md) - Main project documentation
- [API Reference](docs/api.md) - Complete API documentation
- [Configuration Guide](docs/configuration.md) - Configuration options

### Community
- [GitHub Issues](https://github.com/Vasanthadithya-mundrathi/H5X/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/Vasanthadithya-mundrathi/H5X/discussions) - Q&A and discussions

### Debug Information

```bash
# Get detailed debug info
./h5x-cli obfuscate input.cpp -o output --verbose 2>&1 | tee debug.log

# System information
echo "LLVM version: $(llvm-config --version)"
echo "CMake version: $(cmake --version | head -1)"
echo "Compiler: $(which g++)"
```

---

## Success Checklist

After obfuscation, verify:

- [ ] Obfuscated binary exists and runs
- [ ] Size increase is reasonable for chosen level
- [ ] Security score meets requirements
- [ ] All planned techniques were applied
- [ ] Report files are generated and valid
- [ ] Blockchain verification completed (if enabled)
- [ ] Validation system passes all checks
- [ ] Functionality is preserved
- [ ] Performance impact is acceptable

**Example Success Output:**
```bash
✅ Obfuscation completed successfully
✅ Security Score: 100.0/100
✅ Size Increase: 5,756%
✅ All 6 techniques applied
✅ Blockchain verification: CONFIRMED
✅ Validation: PASSED
✅ Runtime test: SUCCESS