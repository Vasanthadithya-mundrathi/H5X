# H5X Blockchain Component

This directory contains the smart contracts and blockchain infrastructure for the H5X obfuscation engine.

## Overview

The H5X blockchain component provides cryptographic proof-of-obfuscation by storing hashes of obfuscated code on the Ethereum blockchain. This creates an immutable record that can be used to verify the authenticity and integrity of obfuscated binaries.

## Architecture

### Smart Contracts

- **H5XHashStorage.sol**: Main contract for storing and verifying obfuscation hashes
- **Migrations.sol**: Standard Truffle migrations contract

### Key Features

- **Hash Storage**: Store SHA256 hashes of obfuscated code on-chain
- **Batch Operations**: Efficiently store/verify multiple hashes in single transactions
- **Ownership Tracking**: Track who stored each hash and when
- **Gas Optimization**: Minimized gas costs for storage and verification
- **Event Logging**: Comprehensive event logging for transparency

## Quick Start

### Prerequisites

- Node.js 14+
- npm
- Ganache (CLI or GUI)

### Setup and Deployment

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start Ganache (if not already running):**
   ```bash
   # Option 1: Ganache CLI
   npm run ganache
   
   # Option 2: Start Ganache GUI manually
   # Use port 7545 and network ID 5777
   ```

3. **Deploy contracts:**
   ```bash
   ./deploy.sh
   ```

The deployment script will:
- Install all dependencies
- Start Ganache if needed
- Compile smart contracts
- Deploy to local network
- Run comprehensive tests
- Save contract address for H5X integration

### Manual Operations

**Compile contracts:**
```bash
npm run compile
```

**Deploy to specific network:**
```bash
npm run deploy:development  # Ganache CLI (port 8545)
npm run deploy:ganache      # Ganache GUI (port 7545)
```

**Run tests:**
```bash
npm test
```

**Interactive console:**
```bash
npx truffle console --network development
```

## Smart Contract API

### H5XHashStorage Contract

#### Core Functions

**storeHash(bytes32 _hash)**
- Stores a hash on the blockchain
- Emits `HashStored` event
- Gas cost: ~50,000

**verifyHash(bytes32 _hash) → bool**
- Verifies if a hash exists
- Emits `HashVerified` event
- Gas cost: ~25,000

**getHashInfo(bytes32 _hash) → (bool, address, uint256)**
- Returns hash existence, storer address, and timestamp
- View function (no gas cost)

#### Batch Operations

**batchStoreHashes(bytes32[] _hashes)**
- Store up to 50 hashes in one transaction
- More gas efficient than individual calls
- Gas cost: ~45,000 per hash

**batchVerifyHashes(bytes32[] _hashes) → bool[]**
- Verify multiple hashes at once
- View function (no gas cost)

#### Administrative Functions

**getStats() → (uint256, address)**
- Returns total hash count and contract owner
- View function

**transferOwnership(address newOwner)**
- Transfer contract ownership (owner only)

## Integration with H5X

The H5X obfuscation engine integrates with this blockchain component through:

1. **Configuration**: Contract address in `config.json`
2. **Hash Storage**: Automatic storage of obfuscation hashes
3. **Verification**: Real-time verification of stored hashes
4. **Reporting**: Blockchain transaction IDs in reports

### Configuration

Update your H5X configuration:

```json
{
  "blockchain": {
    "enabled": true,
    "rpc_url": "http://127.0.0.1:8545",
    "verification_contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3"
  }
}
```

## Network Configuration

### Development Networks

| Network | Port | Network ID | Usage |
|---------|------|------------|-------|
| development | 8545 | * | Ganache CLI |
| ganache | 7545 | 5777 | Ganache GUI |
| test | 8545 | * | CI/CD testing |

### Gas Configuration

- **Gas Limit**: 6,721,975
- **Gas Price**: 20 gwei
- **Optimization**: Enabled (200 runs)

## Testing

The test suite covers:

- Contract deployment and initialization
- Hash storage and retrieval
- Batch operations
- Ownership management
- Integration scenarios
- Error handling
- Gas optimization

Run tests with detailed output:
```bash
npm test
```

### Test Coverage

- ✅ Basic hash storage and verification
- ✅ Duplicate prevention
- ✅ Batch operations (up to 50 hashes)
- ✅ Ownership management
- ✅ Event emission
- ✅ Error handling
- ✅ Gas optimization
- ✅ H5X integration workflow

## Security Considerations

### Smart Contract Security

- **Access Control**: Owner-only administrative functions
- **Input Validation**: Comprehensive parameter validation
- **Gas Limits**: Protection against gas limit attacks
- **Event Logging**: Full audit trail

### Operational Security

- **Private Keys**: Never commit private keys to repository
- **Network Security**: Use appropriate network configurations
- **Contract Verification**: Verify contracts on block explorers
- **Upgrade Path**: Consider proxy patterns for upgradability

## Troubleshooting

### Common Issues

**Ganache not starting:**
- Check if port 8545/7545 is already in use
- Try restarting with `npm run ganache`

**Contract deployment fails:**
- Ensure sufficient ETH in deployment account
- Check gas limits and gas prices
- Verify Ganache is running and accessible

**Tests failing:**
- Restart Ganache with clean state
- Check Node.js version (14+ required)
- Verify all dependencies are installed

**H5X integration issues:**
- Verify contract address in H5X config
- Ensure Ganache is running
- Check RPC URL configuration

### Debugging

Enable verbose logging:
```bash
DEBUG=* npm test
```

Check contract state in console:
```bash
npx truffle console --network development
truffle(development)> const contract = await H5XHashStorage.deployed()
truffle(development)> await contract.getStats()
```

## Development

### Adding New Features

1. Update `H5XHashStorage.sol`
2. Add corresponding tests in `test/`
3. Update migration scripts if needed
4. Run full test suite
5. Update documentation

### Best Practices

- Write comprehensive tests for all functions
- Use events for important state changes
- Optimize for gas efficiency
- Follow Solidity security guidelines
- Document all functions and parameters

## Gas Optimization

Current gas usage:

| Operation | Gas Cost | Notes |
|-----------|----------|-------|
| Contract deployment | ~400,000 | One-time cost |
| storeHash | ~50,000 | Per hash |
| verifyHash | ~25,000 | Per verification |
| batchStoreHashes | ~45,000/hash | More efficient |
| batchVerifyHashes | ~15,000/hash | Read-only |

### Optimization Strategies

- Use batch operations for multiple hashes
- Pack multiple operations in single transaction
- Use view functions for read-only operations
- Consider storage vs. memory usage

## Monitoring and Analytics

### Events for Monitoring

- `HashStored(bytes32 indexed hash, address indexed sender, uint256 timestamp)`
- `HashVerified(bytes32 indexed hash, address indexed verifier, uint256 timestamp)`

### Analytics Queries

Track H5X usage:
```javascript
// Get all hashes stored by specific address
const events = await contract.getPastEvents('HashStored', {
  filter: { sender: userAddress },
  fromBlock: 0,
  toBlock: 'latest'
});
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](../LICENSE) file for details.