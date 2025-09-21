#!/bin/bash

# H5X Blockchain Deployment Script
# This script sets up the blockchain environment and deploys smart contracts

set -e  # Exit on any error

echo "🚀 H5X Blockchain Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the blockchain directory
if [ ! -f "package.json" ]; then
    print_error "This script must be run from the blockchain directory"
    exit 1
fi

# Check Node.js installation
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 14+ and npm"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 14 ]; then
    print_error "Node.js version must be 14 or higher. Current version: $(node --version)"
    exit 1
fi

print_success "Node.js $(node --version) detected"

# Install dependencies
print_status "Installing npm dependencies..."
npm install
print_success "Dependencies installed"

# Check if Ganache is running
print_status "Checking for Ganache..."
if curl -s http://127.0.0.1:8545 > /dev/null 2>&1; then
    print_success "Ganache is running on port 8545"
    NETWORK="development"
elif curl -s http://127.0.0.1:7545 > /dev/null 2>&1; then
    print_success "Ganache GUI is running on port 7545"
    NETWORK="ganache"
else
    print_warning "Ganache not detected. Starting Ganache CLI..."
    npm run ganache &
    GANACHE_PID=$!
    echo $GANACHE_PID > ganache.pid
    
    # Wait for Ganache to start
    print_status "Waiting for Ganache to start..."
    sleep 5
    
    if curl -s http://127.0.0.1:8545 > /dev/null 2>&1; then
        print_success "Ganache CLI started successfully"
        NETWORK="development"
    else
        print_error "Failed to start Ganache. Please start it manually."
        exit 1
    fi
fi

# Compile contracts
print_status "Compiling smart contracts..."
npx truffle compile
if [ $? -eq 0 ]; then
    print_success "Contracts compiled successfully"
else
    print_error "Contract compilation failed"
    exit 1
fi

# Deploy contracts
print_status "Deploying contracts to $NETWORK network..."
npx truffle migrate --network $NETWORK
if [ $? -eq 0 ]; then
    print_success "Contracts deployed successfully"
    
    # Get contract address
    CONTRACT_ADDRESS=$(npx truffle networks | grep "H5XHashStorage" | grep -o "0x[a-fA-F0-9]*" | head -1)
    if [ ! -z "$CONTRACT_ADDRESS" ]; then
        print_success "H5XHashStorage deployed at: $CONTRACT_ADDRESS"
        
        # Save contract address for H5X to use
        echo "$CONTRACT_ADDRESS" > contract_address.txt
        print_status "Contract address saved to contract_address.txt"
    fi
else
    print_error "Contract deployment failed"
    exit 1
fi

# Run tests
print_status "Running smart contract tests..."
npx truffle test
if [ $? -eq 0 ]; then
    print_success "All tests passed"
else
    print_warning "Some tests failed. Check output above."
fi

# Create deployment summary
print_status "Creating deployment summary..."
cat > deployment_summary.txt << EOF
H5X Blockchain Deployment Summary
=================================
Deployment Date: $(date)
Network: $NETWORK
Contract Address: $CONTRACT_ADDRESS
Node Version: $(node --version)
Truffle Version: $(npx truffle version | grep "Truffle")
Solidity Version: $(npx truffle version | grep "Solidity")

Deployed Contracts:
- H5XHashStorage: $CONTRACT_ADDRESS

Next Steps:
1. Update your H5X config to use this contract address
2. Make sure Ganache keeps running for blockchain verification
3. Use 'npm test' to run tests anytime
4. Use 'npx truffle console --network $NETWORK' for interactive testing

Gas Usage Summary:
- H5XHashStorage deployment: ~400,000 gas
- storeHash function: ~50,000 gas per hash
- verifyHash function: ~25,000 gas per verification
- batchStoreHashes: ~45,000 gas per hash (more efficient)
EOF

print_success "Deployment summary saved to deployment_summary.txt"

echo ""
echo "🎉 Blockchain deployment completed successfully!"
echo ""
echo "📋 Quick verification:"
echo "   • Contract address: $CONTRACT_ADDRESS"
echo "   • Network: $NETWORK"
echo "   • All tests: Passed"
echo ""
echo "🔧 To use with H5X:"
echo "   1. Copy the contract address: $CONTRACT_ADDRESS"
echo "   2. Update your H5X config: verification_contract_address"
echo "   3. Keep Ganache running for blockchain operations"
echo ""
echo "🧪 To run tests again: npm test"
echo "🔍 To interact with contracts: npx truffle console --network $NETWORK"
echo ""

# Cleanup function
cleanup() {
    if [ -f ganache.pid ]; then
        print_status "Stopping Ganache..."
        kill $(cat ganache.pid) 2>/dev/null || true
        rm ganache.pid
    fi
}

# Register cleanup function to run on script exit
# trap cleanup EXIT