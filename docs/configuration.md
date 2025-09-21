# H5X ENGINE Configuration Guide

## Overview

This guide covers all configuration options for the H5X Obfuscation Engine, including file-based configuration, command-line options, and programmatic configuration.

## Configuration File Format

H5X uses JSON configuration files with the following structure:

### config/config.json

```json
{
  "obfuscation": {
    "level": 2,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": true,
    "enable_control_flow_flattening": false,
    "enable_bogus_control_flow": true,
    "enable_anti_analysis": true,
    "substitution_rate": 0.3,
    "bogus_flow_rate": 0.2
  },
  "ai": {
    "enabled": true,
    "population_size": 50,
    "generations": 100,
    "mutation_rate": 0.1,
    "crossover_rate": 0.8,
    "tournament_size": 5
  },
  "blockchain": {
    "enabled": true,
    "network": "ganache-local",
    "rpc_endpoint": "http://127.0.0.1:8545",
    "chain_id": 1337,
    "gas_limit": 200000,
    "confirmation_blocks": 1
  },
  "output": {
    "generate_report": true,
    "report_format": "json",
    "verbose": false,
    "preserve_debug_info": false
  },
  "security": {
    "string_encryption_method": "AES-256-GCM",
    "key_derivation": "PBKDF2",
    "iterations": 10000,
    "obfuscate_function_names": true,
    "remove_debug_info": true
  }
}
```

## Configuration Sections

### Obfuscation Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | integer | 1 | Obfuscation level (1-5) |
| `enable_string_obfuscation` | boolean | true | Enable string encryption |
| `enable_instruction_substitution` | boolean | false | Enable arithmetic obfuscation |
| `enable_control_flow_flattening` | boolean | false | Enable control flow transformation |
| `enable_bogus_control_flow` | boolean | false | Enable fake control flow injection |
| `enable_anti_analysis` | boolean | true | Enable anti-reverse engineering |
| `substitution_rate` | float | 0.3 | Rate of instruction substitution (0.0-1.0) |
| `bogus_flow_rate` | float | 0.2 | Rate of bogus block injection (0.0-1.0) |

### AI Optimization Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | false | Enable AI optimization |
| `population_size` | integer | 50 | Genetic algorithm population size |
| `generations` | integer | 100 | Number of generations to run |
| `mutation_rate` | float | 0.1 | Mutation rate (0.0-1.0) |
| `crossover_rate` | float | 0.8 | Crossover rate (0.0-1.0) |
| `tournament_size` | integer | 5 | Tournament selection size |

### Blockchain Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | false | Enable blockchain verification |
| `network` | string | "ganache-local" | Blockchain network name |
| `rpc_endpoint` | string | "http://127.0.0.1:8545" | RPC endpoint URL |
| `chain_id` | integer | 1337 | Chain ID for network |
| `gas_limit` | integer | 200000 | Gas limit for transactions |
| `confirmation_blocks` | integer | 1 | Required confirmation blocks |

### Output Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `generate_report` | boolean | true | Generate obfuscation report |
| `report_format` | string | "json" | Report format (json, xml, html) |
| `verbose` | boolean | false | Enable verbose output |
| `preserve_debug_info` | boolean | false | Keep debug information |

### Security Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `string_encryption_method` | string | "AES-256-GCM" | Encryption method for strings |
| `key_derivation` | string | "PBKDF2" | Key derivation function |
| `iterations` | integer | 10000 | Key derivation iterations |
| `obfuscate_function_names` | boolean | true | Randomize function names |
| `remove_debug_info` | boolean | true | Remove debug information |

## Command Line Configuration

### Basic Usage

```bash
./h5x-cli obfuscate input.cpp -o output_dir [OPTIONS]
```

### Command Line Options

| Option | Long Form | Description |
|--------|-----------|-------------|
| `-l` | `--level` | Obfuscation level (1-5) |
| `-c` | `--config` | Configuration file path |
| `-o` | `--output` | Output directory |
| `-r` | `--report` | Generate report |
| `-v` | `--verbose` | Verbose output |
| `-a` | `--ai-optimize` | Enable AI optimization |
| `-b` | `--blockchain-verify` | Enable blockchain verification |
| `-s` | `--string-obfuscation` | Enable string obfuscation |
| `-i` | `--instruction-substitution` | Enable instruction substitution |
| `-f` | `--control-flow-flattening` | Enable control flow flattening |
| `-g` | `--bogus-control-flow` | Enable bogus control flow |

### Examples

```bash
# Basic Level 2 obfuscation
./h5x-cli obfuscate demo.cpp -l 2 -o obfuscated/

# AI-optimized Level 3 with blockchain verification
./h5x-cli obfuscate demo.cpp -l 3 -a -b -o obfuscated/ -r

# Custom configuration file
./h5x-cli obfuscate demo.cpp -c custom_config.json -o obfuscated/

# Maximum obfuscation with all features
./h5x-cli obfuscate demo.cpp -l 5 -a -b -s -i -f -g -v -o obfuscated/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `H5X_CONFIG_PATH` | Default configuration file path | `./config/config.json` |
| `H5X_LOG_LEVEL` | Logging level (DEBUG, INFO, WARN, ERROR) | `INFO` |
| `H5X_LOG_FILE` | Log file path | `./logs/h5x.log` |
| `H5X_TEMP_DIR` | Temporary directory for processing | `/tmp/h5x/` |
| `H5X_BLOCKCHAIN_TIMEOUT` | Blockchain operation timeout (seconds) | `30` |

## Level-Specific Configurations

### Level 1 (Basic Protection)

```json
{
  "obfuscation": {
    "level": 1,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": false,
    "enable_control_flow_flattening": false,
    "enable_bogus_control_flow": false,
    "enable_anti_analysis": true
  }
}
```

### Level 2 (Enhanced Security)

```json
{
  "obfuscation": {
    "level": 2,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": true,
    "enable_control_flow_flattening": false,
    "enable_bogus_control_flow": true,
    "enable_anti_analysis": true,
    "substitution_rate": 0.3,
    "bogus_flow_rate": 0.15
  }
}
```

### Level 3 (Professional Protection)

```json
{
  "obfuscation": {
    "level": 3,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": true,
    "enable_control_flow_flattening": true,
    "enable_bogus_control_flow": true,
    "enable_anti_analysis": true,
    "substitution_rate": 0.5,
    "bogus_flow_rate": 0.25
  }
}
```

### Level 4 (Enterprise Security)

```json
{
  "obfuscation": {
    "level": 4,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": true,
    "enable_control_flow_flattening": true,
    "enable_bogus_control_flow": true,
    "enable_anti_analysis": true,
    "substitution_rate": 0.7,
    "bogus_flow_rate": 0.35
  }
}
```

### Level 5 (Military-Grade Protection)

```json
{
  "obfuscation": {
    "level": 5,
    "enable_string_obfuscation": true,
    "enable_instruction_substitution": true,
    "enable_control_flow_flattening": true,
    "enable_bogus_control_flow": true,
    "enable_anti_analysis": true,
    "substitution_rate": 0.9,
    "bogus_flow_rate": 0.5
  }
}
```

## AI Optimization Profiles

### Fast Profile (Quick Results)

```json
{
  "ai": {
    "enabled": true,
    "population_size": 20,
    "generations": 50,
    "mutation_rate": 0.15,
    "crossover_rate": 0.7
  }
}
```

### Balanced Profile (Recommended)

```json
{
  "ai": {
    "enabled": true,
    "population_size": 50,
    "generations": 100,
    "mutation_rate": 0.1,
    "crossover_rate": 0.8
  }
}
```

### Thorough Profile (Best Results)

```json
{
  "ai": {
    "enabled": true,
    "population_size": 100,
    "generations": 200,
    "mutation_rate": 0.05,
    "crossover_rate": 0.9
  }
}
```

## Blockchain Network Configurations

### Ganache (Local Development)

```json
{
  "blockchain": {
    "enabled": true,
    "network": "ganache-local",
    "rpc_endpoint": "http://127.0.0.1:8545",
    "chain_id": 1337,
    "gas_limit": 200000,
    "confirmation_blocks": 1
  }
}
```

### Ethereum Testnet (Sepolia)

```json
{
  "blockchain": {
    "enabled": true,
    "network": "sepolia",
    "rpc_endpoint": "https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
    "chain_id": 11155111,
    "gas_limit": 150000,
    "confirmation_blocks": 3
  }
}
```

### Polygon Mumbai (Testnet)

```json
{
  "blockchain": {
    "enabled": true,
    "network": "polygon-mumbai",
    "rpc_endpoint": "https://rpc-mumbai.maticvigil.com",
    "chain_id": 80001,
    "gas_limit": 100000,
    "confirmation_blocks": 2
  }
}
```

## Performance Tuning

### High-Performance Configuration

```json
{
  "obfuscation": {
    "substitution_rate": 0.2,
    "bogus_flow_rate": 0.1
  },
  "ai": {
    "population_size": 30,
    "generations": 50
  },
  "output": {
    "verbose": false,
    "preserve_debug_info": false
  }
}
```

### High-Security Configuration

```json
{
  "obfuscation": {
    "substitution_rate": 0.8,
    "bogus_flow_rate": 0.4
  },
  "security": {
    "iterations": 50000,
    "obfuscate_function_names": true,
    "remove_debug_info": true
  }
}
```

## Configuration Validation

The engine validates configurations at startup and provides detailed error messages for invalid settings:

- **Range Validation**: Numeric values are checked against valid ranges
- **Type Validation**: Data types must match expected types
- **Dependency Validation**: Dependent features are checked for consistency
- **Network Validation**: Blockchain endpoints are tested for connectivity

## Configuration Management CLI

```bash
# View current configuration
./h5x-cli config show

# Set configuration values
./h5x-cli config set obfuscation.level 3
./h5x-cli config set ai.enabled true

# Get specific configuration value
./h5x-cli config get blockchain.rpc_endpoint

# Validate configuration file
./h5x-cli config validate config/config.json

# Generate default configuration
./h5x-cli config init config/default.json
```

## Troubleshooting

### Common Configuration Issues

1. **Invalid JSON Format**: Use a JSON validator to check syntax
2. **Missing Dependencies**: Ensure LLVM, OpenSSL, and curl are installed
3. **Network Connectivity**: Test blockchain endpoints manually
4. **File Permissions**: Check read/write permissions for config and output directories
5. **Memory Limits**: Adjust system memory limits for large obfuscation jobs

### Debug Configuration

```json
{
  "output": {
    "verbose": true,
    "preserve_debug_info": true
  }
}
```

Set environment variable:

```bash
export H5X_LOG_LEVEL=DEBUG
```

---

For additional configuration examples, see the [config/examples/](../config/examples/) directory.
