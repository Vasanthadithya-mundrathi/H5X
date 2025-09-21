# H5X Test Archive

This directory contains all test files and outputs generated during development and validation.

## Directory Structure

- `tests/binaries/` - Obfuscated executable binaries from various test runs
- `tests/reports/` - HTML, JSON, and summary reports for each test
- `tests/temp_files/` - Temporary LLVM IR files and other intermediate outputs

## Test Files Naming Convention

- `test_*_blockchain*` - Tests with blockchain verification
- `test_*_complete*` - Full feature tests (AI + Blockchain + Reports)
- `test_*_level2*` - Level 2 obfuscation tests
- `test_*_validation*` - Final validation tests

All binaries are functional and can be executed to verify obfuscation worked correctly.
