/**
 * @title H5X Blockchain Configuration
 * @dev Truffle configuration for H5X smart contract deployment
 */

const HDWalletProvider = require('@truffle/hdwallet-provider');

// Default mnemonic for local development (Ganache)
const mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about';

module.exports = {
  // Configure networks
  networks: {
    // Local Ganache development network
    development: {
      host: "127.0.0.1",       // Localhost (default: none)
      port: 8545,              // Standard Ethereum port (default: none)
      network_id: "*",         // Any network (default: none)
      gas: 6721975,           // Gas limit
      gasPrice: 20000000000,  // 20 gwei (in wei)
      confirmations: 0,       // # of confirmations to wait between deployments
      timeoutBlocks: 200,     // # of blocks before deployment times out
      skipDryRun: true        // Skip dry run before migrations
    },

    // Ganache GUI
    ganache: {
      host: "127.0.0.1",
      port: 7545,              // Ganache GUI default port
      network_id: "5777",      // Ganache GUI default network id
      gas: 6721975,
      gasPrice: 20000000000,
      confirmations: 0,
      timeoutBlocks: 200,
      skipDryRun: true
    },

    // Local test network (for CI/CD)
    test: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*",
      gas: 6721975,
      gasPrice: 1,
      confirmations: 0,
      timeoutBlocks: 200,
      skipDryRun: true
    }
  },

  // Set default mocha options here, use special reporters etc.
  mocha: {
    timeout: 100000,
    reporter: 'spec'
  },

  // Configure your compilers
  compilers: {
    solc: {
      version: "0.8.19",      // Fetch exact version from solc-bin
      settings: {
        optimizer: {
          enabled: true,      // Enable optimization
          runs: 200          // Optimize for how many times you intend to run the code
        },
        evmVersion: "byzantium" // Target EVM version
      }
    }
  },

  // Truffle DB is currently disabled by default
  db: {
    enabled: false
  },

  // Plugin configuration
  plugins: [
    'truffle-plugin-verify'   // For contract verification on block explorers
  ],

  // API keys for contract verification (if needed)
  api_keys: {
    // etherscan: "YOUR_ETHERSCAN_API_KEY"
  }
};