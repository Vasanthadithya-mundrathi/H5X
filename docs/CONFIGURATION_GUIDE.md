# H5X Engine - Configuration Guide

## Table of Contents
- [Quick Configuration](#quick-configuration)
- [Configuration Files](#configuration-files)
- [Obfuscation Levels](#obfuscation-levels)
- [AI Optimization Settings](#ai-optimization-settings)
- [Blockchain Configuration](#blockchain-configuration)
- [Validation Settings](#validation-settings)
- [Advanced Tuning](#advanced-tuning)

---

## Quick Configuration

### Basic Setup

**Default Configuration** (`config/config.json`):
```json
{
  "obfuscation_level": 3,
  "target_platform": "native",
  "verbose": false,
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "enable_report_generation": true
}
```

**Quick Start Commands:**
```bash
# Use default configuration
./h5x-cli obfuscate app.cpp -o protected_app --level 3

# Use custom configuration
./h5x-cli obfuscate app.cpp -o protected_app --config custom.json

# Override specific settings
./h5x-cli obfuscate app.cpp -o protected_app --level 5 --ai-optimize --blockchain-verify
```

---

## Configuration Files

### File Locations

| Configuration Type | Default Location | Purpose |
|-------------------|------------------|---------|
| **Main Config** | `config/config.json` | Primary obfuscation settings |
| **Security Profiles** | `config/security_profiles/` | Predefined security levels |
| **Platform Configs** | `config/platforms/` | Platform-specific settings |
| **Custom Configs** | `config/custom/` | User-defined configurations |

### Configuration File Structure

```json
{
  "basic_settings": {
    "obfuscation_level": 3,
    "target_platform": "linux",
    "verbose": true
  },

  "feature_toggles": {
    "enable_ai_optimization": true,
    "enable_blockchain_verification": true,
    "enable_report_generation": true,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": true,
    "enable_bogus_control_flow": true,
    "enable_control_flow_flattening": true,
    "enable_anti_analysis": true,
    "enable_junk_code_insertion": true
  },

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
    "confirmation_blocks": 1,
    "auto_start": false
  },

  "validation": {
    "strict_mode": true,
    "thresholds": {
      "min_security_score": 80.0,
      "max_size_increase": 1000.0,
      "max_processing_time": 300.0,
      "min_functions_processed": 1,
      "min_strings_obfuscated": 1
    }
  },

  "optimization_settings": {
    "performance_weight": 0.3,
    "security_weight": 0.7,
    "size_weight": 0.2,
    "time_weight": 0.1
  }
}
```

---

## Obfuscation Levels

### Level Configuration

Each obfuscation level applies different combinations of techniques:

#### **Level 1: Basic Protection**
```json
{
  "obfuscation_level": 1,
  "enable_string_obfuscation": true,
  "enable_instruction_substitution": false,
  "enable_bogus_control_flow": false,
  "enable_control_flow_flattening": false,
  "enable_anti_analysis": false,
  "enable_junk_code_insertion": false
}
```

**Expected Results:**
- Security Score: 70-80/100
- Size Increase: 800-1500%
- Processing Time: 1-2 seconds
- Use Case: Basic IP protection

#### **Level 2: Enhanced Security**
```json
{
  "obfuscation_level": 2,
  "enable_string_obfuscation": true,
  "enable_instruction_substitution": true,
  "enable_bogus_control_flow": false,
  "enable_control_flow_flattening": false,
  "enable_anti_analysis": false,
  "enable_junk_code_insertion": true
}
```

**Expected Results:**
- Security Score: 80-90/100
- Size Increase: 400-800%
- Processing Time: 2-4 seconds
- Use Case: Commercial software

#### **Level 3: Professional Protection**
```json
{
  "obfuscation_level": 3,
  "enable_string_obfuscation": true,
  "enable_instruction_substitution": true,
  "enable_bogus_control_flow": true,
  "enable_control_flow_flattening": false,
  "enable_anti_analysis": false,
  "enable_junk_code_insertion": true
}
```

**Expected Results:**
- Security Score: 85-95/100
- Size Increase: 800-1500%
- Processing Time: 3-6 seconds
- Use Case: Enterprise applications

#### **Level 4: Enterprise Security**
```json
{
  "obfuscation_level": 4,
  "enable_string_obfuscation": true,
  "enable_instruction_substitution": true,
  "enable_bogus_control_flow": true,
  "enable_control_flow_flattening": true,
  "enable_anti_analysis": false,
  "enable_junk_code_insertion": true
}
```

**Expected Results:**
- Security Score: 90-98/100
- Size Increase: 1500-3000%
- Processing Time: 5-10 seconds
- Use Case: Financial systems, DRM

#### **Level 5: Military-Grade Protection**
```json
{
  "obfuscation_level": 5,
  "enable_string_obfuscation": true,
  "enable_instruction_substitution": true,
  "enable_bogus_control_flow": true,
  "enable_control_flow_flattening": true,
  "enable_anti_analysis": true,
  "enable_junk_code_insertion": true
}
```

**Expected Results:**
- Security Score: 95-100/100
- Size Increase: 3000-8000%
- Processing Time: 8-20 seconds
- Use Case: Military, cryptocurrency

---

## AI Optimization Settings

### Basic AI Configuration

```json
{
  "ai_optimization": {
    "enabled": true,
    "generations": 100,
    "population_size": 50,
    "mutation_rate": 0.1,
    "crossover_rate": 0.8
  }
}
```

### Performance vs Security Tuning

**Speed-Optimized:**
```json
{
  "ai_optimization": {
    "generations": 30,
    "population_size": 20,
    "mutation_rate": 0.05
  },
  "optimization_settings": {
    "performance_weight": 0.6,
    "security_weight": 0.4
  }
}
```

**Security-Optimized:**
```json
{
  "ai_optimization": {
    "generations": 200,
    "population_size": 100,
    "mutation_rate": 0.15
  },
  "optimization_settings": {
    "performance_weight": 0.2,
    "security_weight": 0.8
  }
}
```

### Custom Fitness Function Weights

```json
{
  "optimization_settings": {
    "security_weight": 0.5,      // Security score importance
    "performance_weight": 0.3,   // Runtime performance importance
    "size_weight": 0.15,         // Binary size importance
    "time_weight": 0.05          // Processing time importance
  }
}
```

---

## Blockchain Configuration

### Ganache Local Network

```json
{
  "blockchain": {
    "network": "ganache-local",
    "rpc_endpoint": "http://127.0.0.1:8545",
    "chain_id": 1337,
    "contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    "gas_limit": 200000,
    "gas_price": "20000000000",
    "confirmation_blocks": 1,
    "auto_start": false
  }
}
```

### Ethereum Mainnet (Future)

```json
{
  "blockchain": {
    "network": "ethereum-mainnet",
    "rpc_endpoint": "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
    "chain_id": 1,
    "gas_limit": 100000,
    "gas_price": "50000000000",
    "confirmation_blocks": 12,
    "auto_start": false
  }
}
```

### Polygon Network (Future)

```json
{
  "blockchain": {
    "network": "polygon-mainnet",
    "rpc_endpoint": "https://polygon-rpc.com",
    "chain_id": 137,
    "gas_limit": 150000,
    "gas_price": "40000000000",
    "confirmation_blocks": 32,
    "auto_start": false
  }
}
```

### Blockchain Startup Script

```bash
#!/bin/bash
# start_ganache.sh

echo "Starting Ganache blockchain..."
ganache --host 127.0.0.1 \
        --port 8545 \
        --chain.chainId 1337 \
        --deterministic \
        --accounts 10 \
        --defaultBalanceEther 1000 &

echo "Ganache started with PID: $!"
echo "RPC Endpoint: http://127.0.0.1:8545"
echo "Chain ID: 1337"
```

---

## Validation Settings

### Basic Validation

```json
{
  "validation": {
    "strict_mode": false,
    "thresholds": {
      "min_security_score": 50.0,
      "max_size_increase": 2000.0,
      "max_processing_time": 600.0
    }
  }
}
```

### Strict Validation

```json
{
  "validation": {
    "strict_mode": true,
    "thresholds": {
      "min_security_score": 80.0,
      "max_size_increase": 1000.0,
      "max_processing_time": 300.0,
      "min_functions_processed": 1,
      "min_strings_obfuscated": 1,
      "min_instructions_modified": 1
    }
  }
}
```

### Custom Thresholds

```json
{
  "validation": {
    "thresholds": {
      "security_score": {
        "min": 90.0,
        "max": 100.0,
        "weight": 0.4
      },
      "size_increase": {
        "min": 0.0,
        "max": 500.0,
        "weight": 0.2
      },
      "processing_time": {
        "min": 0.0,
        "max": 60.0,
        "weight": 0.2
      },
      "functions_processed": {
        "min": 1,
        "max": 10000,
        "weight": 0.1
      },
      "strings_obfuscated": {
        "min": 1,
        "max": 1000,
        "weight": 0.1
      }
    }
  }
}
```

---

## Advanced Tuning

### Platform-Specific Configuration

#### Linux Configuration
```json
{
  "target_platform": "linux",
  "compiler_settings": {
    "optimization_level": "-O2",
    "march": "native",
    "additional_flags": "-march=native -mtune=native"
  }
}
```

#### macOS Configuration
```json
{
  "target_platform": "macos",
  "compiler_settings": {
    "optimization_level": "-O2",
    "march": "native",
    "llvm_path": "/opt/homebrew/opt/llvm/bin"
  }
}
```

#### Windows Configuration (Future)
```json
{
  "target_platform": "windows",
  "compiler_settings": {
    "optimization_level": "/O2",
    "platform": "x64",
    "subsystem": "console"
  }
}
```

### Memory and Performance Tuning

#### Low Memory Systems
```json
{
  "ai_optimization": {
    "population_size": 20,
    "generations": 50
  },
  "obfuscation_level": 3,
  "optimization_settings": {
    "performance_weight": 0.5,
    "security_weight": 0.5
  }
}
```

#### High Performance Systems
```json
{
  "ai_optimization": {
    "population_size": 100,
    "generations": 200
  },
  "obfuscation_level": 5,
  "optimization_settings": {
    "performance_weight": 0.2,
    "security_weight": 0.8
  }
}
```

### Codebase-Specific Tuning

#### Small Applications (< 1000 lines)
```json
{
  "obfuscation_level": 3,
  "ai_optimization": {
    "generations": 50,
    "population_size": 25
  }
}
```

#### Medium Applications (1000-10000 lines)
```json
{
  "obfuscation_level": 4,
  "ai_optimization": {
    "generations": 100,
    "population_size": 50
  }
}
```

#### Large Applications (> 10000 lines)
```json
{
  "obfuscation_level": 5,
  "ai_optimization": {
    "generations": 150,
    "population_size": 75
  },
  "validation": {
    "max_processing_time": 600
  }
}
```

---

## Security Profiles

### Predefined Security Profiles

#### Development Profile
```json
{
  "profile_name": "development",
  "description": "Fast obfuscation for development and testing",
  "obfuscation_level": 2,
  "enable_ai_optimization": false,
  "enable_blockchain_verification": false,
  "enable_report_generation": true,
  "optimization_settings": {
    "performance_weight": 0.7,
    "security_weight": 0.3
  }
}
```

#### Production Profile
```json
{
  "profile_name": "production",
  "description": "Balanced security and performance for production",
  "obfuscation_level": 4,
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "enable_report_generation": true,
  "optimization_settings": {
    "performance_weight": 0.4,
    "security_weight": 0.6
  }
}
```

#### Enterprise Profile
```json
{
  "profile_name": "enterprise",
  "description": "Maximum security for enterprise applications",
  "obfuscation_level": 5,
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "enable_report_generation": true,
  "validation": {
    "strict_mode": true,
    "min_security_score": 95.0
  }
}
```

#### Military Profile
```json
{
  "profile_name": "military",
  "description": "Ultimate security for military/cryptocurrency applications",
  "obfuscation_level": 5,
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "enable_report_generation": true,
  "ai_optimization": {
    "generations": 200,
    "population_size": 100
  },
  "validation": {
    "strict_mode": true,
    "min_security_score": 98.0,
    "max_processing_time": 900
  }
}
```

### Using Security Profiles

```bash
# Use predefined profile
./h5x-cli obfuscate app.cpp -o protected_app --config config/security_profiles/production.json

# List available profiles
ls config/security_profiles/

# Create custom profile
cp config/security_profiles/production.json config/security_profiles/custom.json
# Edit custom.json as needed
```

---

## Environment Variables

### Build Configuration

```bash
# Set LLVM path
export LLVM_DIR="/opt/homebrew/Cellar/llvm/21.1.1/lib/cmake/llvm"

# Set build type
export CMAKE_BUILD_TYPE=Release

# Set number of parallel jobs
export MAKEFLAGS="-j$(nproc)"

# Enable verbose output
export VERBOSE=1
```

### Runtime Configuration

```bash
# Set configuration file
export H5X_CONFIG="config/custom.json"

# Enable debug mode
export H5X_DEBUG=1

# Set blockchain endpoint
export H5X_BLOCKCHAIN_RPC="http://127.0.0.1:8545"

# Set log level
export H5X_LOG_LEVEL=DEBUG
```

### Platform Detection

```bash
# Automatic platform configuration
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export TARGET_PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    export TARGET_PLATFORM="macos"
    export LLVM_DIR="/opt/homebrew/opt/llvm/bin"
fi
```

---

## Configuration Validation

### Validate Configuration File

```bash
# Check configuration syntax
./h5x-cli validate-config config/custom.json

# Test configuration with dry run
./h5x-cli obfuscate test.cpp -o /dev/null --config custom.json --dry-run

# Check configuration against schema
./tools/validate_config_schema.py config/custom.json
```

### Configuration Debugging

```bash
# Enable configuration debugging
./h5x-cli obfuscate test.cpp -o output --verbose --debug-config

# Output current configuration
./h5x-cli show-config

# Compare configurations
./h5x-cli diff-config config/default.json config/custom.json
```

### Common Configuration Issues

**Problem:** Configuration file not found
```bash
# Solution: Check file path
ls -la config/
./h5x-cli obfuscate test.cpp -o output --config /path/to/config.json
```

**Problem:** Invalid JSON syntax
```bash
# Solution: Validate JSON
python3 -m json.tool config/custom.json
```

**Problem:** Missing required fields
```bash
# Solution: Use configuration validator
./tools/validate_config.py config/custom.json
```

---

## Integration Examples

### CI/CD Pipeline Configuration

#### GitHub Actions
```yaml
# .github/workflows/obfuscate.yml
name: Obfuscate Binary
on: [push, pull_request]

jobs:
  obfuscate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Environment
      run: |
        sudo apt install llvm-dev cmake libssl-dev libjsoncpp-dev
        npm install -g ganache

    - name: Build H5X
      run: |
        mkdir build && cd build
        cmake .. -DCMAKE_BUILD_TYPE=Release
        make -j$(nproc)

    - name: Obfuscate Binary
      run: |
        ./h5x-cli obfuscate app.cpp -o app_protected \
          --level 5 \
          --ai-optimize \
          --blockchain-verify \
          --report

    - name: Validate Results
      run: |
        ./tools/validate_obfuscation_reports.sh --strict
        ./app_protected
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any

    stages {
        stage('Build H5X') {
            steps {
                sh '''
                    ./build.sh
                '''
            }
        }

        stage('Obfuscate') {
            steps {
                sh '''
                    ./h5x-cli obfuscate app.cpp -o app_protected \
                      --level 5 \
                      --ai-optimize \
                      --blockchain-verify \
                      --report \
                      --verbose
                '''
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    ./tools/validate_obfuscation_reports.sh --strict
                '''
            }
        }
    }
}
```

### Docker Configuration

#### Dockerfile
```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt update && apt install -y \
    llvm-dev \
    cmake \
    libssl-dev \
    libjsoncpp-dev \
    libcurl4-openssl-dev \
    nodejs \
    npm \
    g++ \
    git

# Install Ganache
RUN npm install -g ganache

# Clone and build H5X
WORKDIR /app
COPY . .
RUN ./build.sh

# Default command
CMD ["./h5x-cli", "--help"]
```

#### Docker Usage
```bash
# Build Docker image
docker build -t h5x-engine .

# Run obfuscation
docker run -v $(pwd):/work h5x-engine \
  ./h5x-cli obfuscate /work/app.cpp -o /work/protected_app \
    --level 5 \
    --ai-optimize \
    --blockchain-verify

# Start with blockchain
docker run -d --name ganache -p 8545:8545 h5x-engine ganache
```

---

## Best Practices

### 1. Start with Conservative Settings

```json
{
  "obfuscation_level": 2,
  "enable_ai_optimization": false,
  "enable_blockchain_verification": false
}
```

### 2. Gradually Increase Security

```bash
# Step 1: Basic obfuscation
./h5x-cli obfuscate app.cpp -o protected_app --level 2

# Step 2: Test functionality
./protected_app

# Step 3: Add AI optimization
./h5x-cli obfuscate app.cpp -o ai_protected --level 3 --ai-optimize

# Step 4: Add blockchain verification
./h5x-cli obfuscate app.cpp -o verified_app --level 4 --ai-optimize --blockchain-verify

# Step 5: Maximum security
./h5x-cli obfuscate app.cpp -o ultra_secure --level 5 --ai-optimize --blockchain-verify
```

### 3. Use Profiles for Different Environments

```bash
# Development
./h5x-cli obfuscate app.cpp -o dev_protected --config config/security_profiles/development.json

# Staging
./h5x-cli obfuscate app.cpp -o staging_protected --config config/security_profiles/production.json

# Production
./h5x-cli obfuscate app.cpp -o prod_protected --config config/security_profiles/enterprise.json
```

### 4. Validate Every Configuration Change

```bash
# Test new configuration
./h5x-cli obfuscate test.cpp -o test_output --config new_config.json --verbose

# Validate results
./tools/validate_obfuscation_reports.sh --strict

# Check performance impact
time ./test_output
```

### 5. Document Your Configuration Choices

```json
{
  "metadata": {
    "description": "Custom configuration for financial application",
    "author": "Security Team",
    "version": "1.0",
    "last_updated": "2025-01-28",
    "rationale": "Maximum security required for financial calculations"
  },
  "obfuscation_level": 5,
  "security_justification": "Handles sensitive financial data and algorithms"
}
```

---

## Troubleshooting Configuration

### Common Configuration Issues

#### Issue: Configuration File Not Found
```bash
# Check file exists
ls -la config/config.json

# Use absolute path
./h5x-cli obfuscate app.cpp -o output --config /full/path/to/config.json

# Check file permissions
chmod 644 config/config.json
```

#### Issue: Invalid JSON Syntax
```bash
# Validate JSON
python3 -c "import json; json.load(open('config/config.json'))"

# Use online JSON validator
# or
cat config/config.json | jq .
```

#### Issue: Missing Required Fields
```bash
# Check required fields
./h5x-cli validate-config config/config.json

# Compare with working config
./h5x-cli diff-config config/default.json config/custom.json
```

#### Issue: Blockchain Connection Fails
```bash
# Check Ganache is running
curl -X POST --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
  http://127.0.0.1:8545

# Start Ganache if needed
ganache --host 127.0.0.1 --port 8545 --chain.chainId 1337 &

# Update RPC endpoint in config
{
  "blockchain": {
    "rpc_endpoint": "http://127.0.0.1:8545"
  }
}
```

#### Issue: AI Optimization Too Slow
```bash
# Reduce AI complexity
{
  "ai_optimization": {
    "generations": 50,
    "population_size": 25
  }
}

# Disable AI for quick testing
{
  "enable_ai_optimization": false
}
```

### Debug Configuration

```bash
# Show current configuration
./h5x-cli show-config

# Show configuration with defaults
./h5x-cli show-config --all

# Test configuration with dry run
./h5x-cli obfuscate test.cpp -o /dev/null --dry-run --verbose

# Debug configuration loading
H5X_DEBUG=1 ./h5x-cli obfuscate test.cpp -o output 2>&1 | tee debug.log
```

### Performance Profiling

```bash
# Profile obfuscation performance
time ./h5x-cli obfuscate app.cpp -o output --level 5 --verbose

# Memory usage profiling
valgrind --tool=massif ./h5x-cli obfuscate app.cpp -o output --level 3

# CPU profiling
perf record ./h5x-cli obfuscate app.cpp -o output --level 3
perf report
```

---

## Configuration Templates

### Template 1: Basic Protection
```json
{
  "obfuscation_level": 2,
  "target_platform": "native",
  "enable_ai_optimization": false,
  "enable_blockchain_verification": false,
  "enable_report_generation": true,
  "verbose": false
}
```

### Template 2: Enterprise Security
```json
{
  "obfuscation_level": 5,
  "target_platform": "native",
  "enable_ai_optimization": true,
  "enable_blockchain_verification": true,
  "enable_report_generation": true,
  "verbose": true,
  "ai_optimization": {
    "generations": 150,
    "population_size": 75
  },
  "validation": {
    "strict_mode": true,
    "min_security_score": 95.0
  }
}
```

### Template 3: Development/Fast
```json
{
  "obfuscation_level": 1,
  "target_platform": "native",
  "enable_ai_optimization": false,
  "enable_blockchain_verification": false,
  "enable_report_generation": true,
  "verbose": true,
  "optimization_settings": {
    "performance_weight": 0.8,
    "security_weight": 0.2
  }
}
```

---

## Migration Guide

### Migrating from v0.9 to v1.0

**Old Configuration:**
```json
{
  "level": 3,
  "platform": "linux",
  "ai_enabled": true
}
```

**New Configuration:**
```json
{
  "obfuscation_level": 3,
  "target_platform": "linux",
  "enable_ai_optimization": true,
  "ai_optimization": {
    "enabled": true
  }
}
```

### Migration Script

```bash
#!/bin/bash
# migrate_config.sh

echo "Migrating configuration files..."

# Backup old configs
cp -r config/ config_backup_$(date +%Y%m%d_%H%M%S)/

# Migrate main config
if [[ -f "config/config.json" ]]; then
    # Update field names
    sed -i 's/"level":/"obfuscation_level":/g' config/config.json
    sed -i 's/"platform":/"target_platform":/g' config/config.json
    sed -i 's/"ai_enabled":/"enable_ai_optimization":/g' config/config.json
    sed -i 's/"blockchain_enabled":/"enable_blockchain_verification":/g' config/config.json

    echo "Main configuration migrated"
fi

echo "Migration complete!"
```

---

## Support and Maintenance

### Configuration Backup

```bash
# Create configuration backup
cp -r config/ config_backup_$(date +%Y%m%d_%H%M%S)/

# List available backups
ls -la config_backup_*/

# Restore from backup
cp -r config_backup_20250128_120000/* config/
```

### Configuration Version Control

```bash
# Track configuration changes
git add config/
git commit -m "Update security configuration for production"

# Create configuration branch
git checkout -b config/production-security
# Make configuration changes
git add config/
git commit -m "Production security configuration"
git checkout main
git merge config/production-security
```

### Configuration Documentation

```bash
# Generate configuration documentation
./tools/generate_config_docs.py > docs/CONFIGURATION_REFERENCE.md

# Validate all configurations
./tools/validate_all_configs.sh

# Check configuration coverage
./tools/check_config_coverage.sh
```

---

## Summary

### Configuration Checklist

- [ ] Choose appropriate obfuscation level (1-5)
- [ ] Configure AI optimization settings
- [ ] Set up blockchain verification (if needed)
- [ ] Define validation thresholds
- [ ] Test configuration with small example
- [ ] Validate configuration syntax
- [ ] Document configuration choices
- [ ] Backup working configurations

### Quick Reference

| Setting | Default | Options | Impact |
|---------|---------|---------|---------|
| `obfuscation_level` | 3 | 1-5 | Higher = more security, larger size |
| `ai_optimization` | true | true/false | Better optimization, more time |
| `blockchain_verification` | true | true/false | Immutable verification, network dependency |
| `security_weight` | 0.7 | 0.0-1.0 | Higher = more security focus |
| `performance_weight` | 0.3 | 0.0-1.0 | Higher = faster execution |

### Getting Help

1. **Check Examples**: Look in `config/security_profiles/`
2. **Validate Configuration**: Use `./h5x-cli validate-config`
3. **Test Small**: Try configuration on small test file first
4. **Read Logs**: Enable verbose output for debugging
5. **Compare**: Use working configurations as reference

**Example Help Command:**
```bash
./h5x-cli obfuscate --help
./tools/validate_config.py --help