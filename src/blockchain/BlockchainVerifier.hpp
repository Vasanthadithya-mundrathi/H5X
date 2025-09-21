#ifndef H5X_BLOCKCHAIN_VERIFIER_HPP
#define H5X_BLOCKCHAIN_VERIFIER_HPP

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <curl/curl.h>
#include <json/json.h>
#include "../utils/Logger.hpp"

namespace h5x {

struct ObfuscationConfig;

struct VerificationResult {
    bool verified{false};
    std::string hash;
    std::string transaction_id;
    std::string network;
    std::string error_message;
    uint64_t block_number{0};
    std::string timestamp;
    double gas_used{0.0};
};

struct BlockchainConfig {
    std::string network{"ganache-local"};
    std::string rpc_endpoint{"http://127.0.0.1:8545"};
    std::string contract_address;
    std::string private_key;
    uint64_t gas_limit{200000};
    std::string gas_price{"20000000000"};  // 20 gwei in wei
    int chain_id{1337};
    int confirmation_blocks{1};
};

class BlockchainVerifier {
public:
    explicit BlockchainVerifier(Logger& logger);
    ~BlockchainVerifier() = default;

    bool initialize(const ObfuscationConfig& config);
    void update_configuration(const ObfuscationConfig& config);

    VerificationResult verify_binary(const std::string& binary_path);
    bool store_verification_data(const std::string& binary_path, const std::string& metadata);

    std::string calculate_binary_hash(const std::string& binary_path);
    bool submit_to_blockchain(const std::string& hash, const std::string& metadata);

    std::vector<VerificationResult> query_verification_history(const std::string& binary_hash);
    bool validate_integrity(const std::string& binary_path, const std::string& expected_hash);

    // Blockchain network operations
    bool connect_to_network();
    std::string get_network_status();
    bool check_ganache_connection();

private:
    Logger& logger_;
    bool initialized_;
    BlockchainConfig blockchain_config_;

    // Web3/RPC connection
    std::string current_network_;
    std::string connection_endpoint_;
    bool connected_{false};
    CURL* curl_handle_;

    // Smart contract interaction
    std::string contract_address_;
    static const std::string CONTRACT_ABI;

    // Helper methods
    bool load_blockchain_configuration(const ObfuscationConfig& config);
    bool wait_for_confirmation(const std::string& transaction_id);
    std::string format_metadata(const std::string& binary_path);

    // RPC communication
    struct CurlResponse {
        std::string data;
        long response_code;
    };
    CurlResponse make_rpc_call(const Json::Value& payload);
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, CurlResponse* response);

    // Ethereum transaction creation
    std::string create_transaction(const std::string& hash);
    std::string sign_transaction(const std::string& raw_tx);
    std::string encode_function_call(const std::string& function_sig, const std::string& hash);

    // Cryptographic functions
    std::string sha256_hash(const std::vector<uint8_t>& data);
    std::string keccak256_hash(const std::string& input);
    std::vector<uint8_t> read_binary_file(const std::string& filepath);
    std::string generate_transaction_id();

    // Local verification cache
    std::unordered_map<std::string, VerificationResult> verification_cache_;
};

} // namespace h5x

#endif // H5X_BLOCKCHAIN_VERIFIER_HPP
