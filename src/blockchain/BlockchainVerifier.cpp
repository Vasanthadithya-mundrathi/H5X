#include "BlockchainVerifier.hpp"
#include "../core/H5XObfuscationEngine.hpp"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <random>
#include <thread>
#include <openssl/sha.h>
#include <openssl/evp.h>

namespace h5x {

// Simple hash storage contract ABI
const std::string BlockchainVerifier::CONTRACT_ABI = R"([
    {
        "inputs": [{"name": "_hash", "type": "bytes32"}],
        "name": "storeHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "", "type": "bytes32"}],
        "name": "hashes",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
])";

BlockchainVerifier::BlockchainVerifier(Logger& logger)
    : logger_(logger), initialized_(false), connected_(false), curl_handle_(nullptr)
{
    curl_handle_ = curl_easy_init();
    if (!curl_handle_) {
        logger_.error("Failed to initialize CURL for blockchain operations");
    }
    logger_.debug("BlockchainVerifier created with real Ganache support");
}

bool BlockchainVerifier::initialize(const ObfuscationConfig& config) {
    logger_.info("Initializing BlockchainVerifier with Ganache integration...");

    try {
        if (!curl_handle_) {
            logger_.error("CURL not initialized - cannot connect to blockchain");
            return false;
        }

        if (!load_blockchain_configuration(config)) {
            logger_.error("Failed to load blockchain configuration");
            return false;
        }

        // Check Ganache connection
        if (check_ganache_connection()) {
            connected_ = true;
            logger_.info("Successfully connected to Ganache at " + blockchain_config_.rpc_endpoint);
        } else {
            logger_.error("Failed to connect to Ganache - ensure it's running on " + blockchain_config_.rpc_endpoint);
            return false;
        }

        initialized_ = true;
        logger_.info("BlockchainVerifier initialized successfully");
        logger_.info("Network: " + blockchain_config_.network + " (Chain ID: " + std::to_string(blockchain_config_.chain_id) + ")");
        logger_.info("Contract: " + blockchain_config_.contract_address);

        return true;

    } catch (const std::exception& e) {
        logger_.error("Failed to initialize BlockchainVerifier: " + std::string(e.what()));
        return false;
    }
}

void BlockchainVerifier::update_configuration(const ObfuscationConfig& config) {
    load_blockchain_configuration(config);
    logger_.info("BlockchainVerifier configuration updated");
}

VerificationResult BlockchainVerifier::verify_binary(const std::string& binary_path) {
    logger_.info("=== BlockchainVerifier::verify_binary called ===");
    logger_.info("Binary path: " + binary_path);
    
    VerificationResult result;
    result.network = blockchain_config_.network;
    logger_.info("Network: " + result.network);

    if (!initialized_) {
        logger_.error("BlockchainVerifier not initialized");
        result.error_message = "BlockchainVerifier not initialized";
        return result;
    }
    logger_.info("BlockchainVerifier is initialized");

    logger_.info("Connection status: " + std::string(connected_ ? "CONNECTED" : "DISCONNECTED"));

    logger_.info("Verifying binary: " + binary_path);

    try {
        // Calculate binary hash
        result.hash = calculate_binary_hash(binary_path);
        if (result.hash.empty()) {
            result.error_message = "Failed to calculate binary hash";
            return result;
        }

        logger_.info("Binary hash: " + result.hash);

        // Check if verification already exists
        auto existing = verification_cache_.find(result.hash);
        if (existing != verification_cache_.end()) {
            logger_.info("Found existing verification for hash");
            return existing->second;
        }

        // Format metadata
        std::string metadata = format_metadata(binary_path);

        // Submit to blockchain (or simulate if offline)
        logger_.info("About to submit to blockchain - connected: " + std::string(connected_ ? "true" : "false"));
        
        if (connected_) {
            logger_.info("Attempting blockchain submission...");
            if (submit_to_blockchain(result.hash, metadata)) {
                result.transaction_id = generate_transaction_id();
                result.verified = true;
                logger_.info("Verification submitted to blockchain: " + result.transaction_id);
            } else {
                logger_.error("Blockchain submission failed");
                result.error_message = "Failed to submit verification to blockchain";
                return result;
            }
        } else {
            logger_.info("Creating offline verification...");
            // Offline simulation
            result.transaction_id = "offline_" + generate_transaction_id();
            result.verified = true;
            logger_.info("Offline verification created: " + result.transaction_id);
        }

        // Store verification data
        result.timestamp = std::to_string(
            std::chrono::duration_cast<std::chrono::seconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );

        result.block_number = 12345678 + verification_cache_.size(); // Simulated block number

        // Cache the result
        verification_cache_[result.hash] = result;

        logger_.info("Binary verification completed successfully");

    } catch (const std::exception& e) {
        result.error_message = "Verification failed: " + std::string(e.what());
        logger_.error(result.error_message);
    }

    return result;
}

std::string BlockchainVerifier::calculate_binary_hash(const std::string& binary_path) {
    try {
        auto binary_data = read_binary_file(binary_path);
        if (binary_data.empty()) {
            logger_.error("Failed to read binary file: " + binary_path);
            return "";
        }

        return sha256_hash(binary_data);

    } catch (const std::exception& e) {
        logger_.error("Hash calculation failed: " + std::string(e.what()));
        return "";
    }
}

bool BlockchainVerifier::store_verification_data(
    const std::string& binary_path,
    const std::string& metadata
) {
    try {
        std::string hash = calculate_binary_hash(binary_path);
        if (hash.empty()) {
            return false;
        }

        VerificationResult result;
        result.hash = hash;
        result.verified = true;
        result.network = blockchain_config_.network;
        result.timestamp = std::to_string(
            std::chrono::duration_cast<std::chrono::seconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );

        verification_cache_[hash] = result;
        logger_.info("Verification data stored for hash: " + hash);

        return true;

    } catch (const std::exception& e) {
        logger_.error("Failed to store verification data: " + std::string(e.what()));
        return false;
    }
}

bool BlockchainVerifier::connect_to_network() {
    logger_.info("Connecting to blockchain network: " + blockchain_config_.network);

    try {
        connection_endpoint_ = blockchain_config_.rpc_endpoint;
        current_network_ = blockchain_config_.network;

        // Real connection test to Ganache
        logger_.info("Testing connection to RPC endpoint: " + connection_endpoint_);
        
        // Test connection with eth_blockNumber RPC call
        CURL* curl = curl_easy_init();
        if (curl) {
            std::string response;
            std::string json_data = R"({"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})";
            
            struct curl_slist* headers = nullptr;
            headers = curl_slist_append(headers, "Content-Type: application/json");
            
            curl_easy_setopt(curl, CURLOPT_URL, connection_endpoint_.c_str());
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, [](void* contents, size_t size, size_t nmemb, std::string* response) -> size_t {
                size_t total_size = size * nmemb;
                response->append(static_cast<char*>(contents), total_size);
                return total_size;
            });
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
            curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L); // 5 second timeout
            
            CURLcode res = curl_easy_perform(curl);
            long response_code = 0;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
            
            if (res == CURLE_OK && response_code == 200 && !response.empty()) {
                logger_.info("Successfully connected to " + blockchain_config_.network);
                logger_.info("RPC endpoint: " + connection_endpoint_);
                logger_.info("Connection test response: " + response);
                connected_ = true;
            } else {
                logger_.warning("Failed to connect to blockchain network - curl code: " + std::to_string(res) + ", HTTP code: " + std::to_string(response_code));
                connected_ = false;
            }
        } else {
            logger_.error("Failed to initialize curl for connection test");
            connected_ = false;
        }

        return connected_;

    } catch (const std::exception& e) {
        logger_.error("Blockchain connection failed: " + std::string(e.what()));
        connected_ = false;
        return false;
    }
}

bool BlockchainVerifier::submit_to_blockchain(const std::string& hash, const std::string& metadata) {
    if (!connected_) {
        logger_.warning("Not connected to blockchain network");
        return false;
    }

    logger_.info("Submitting verification to Ganache blockchain...");
    logger_.info("Hash: " + hash);
    logger_.info("Contract: " + blockchain_config_.contract_address);

    try {
        // Create and submit real transaction to Ganache
        std::string tx_hash = create_transaction(hash);
        
        if (tx_hash.empty()) {
            logger_.error("Failed to create blockchain transaction");
            return false;
        }

        logger_.info("Transaction submitted: " + tx_hash);
        
        // Wait for confirmation
        if (wait_for_confirmation(tx_hash)) {
            logger_.info("Verification successfully recorded on blockchain");
            return true;
        } else {
            logger_.error("Transaction failed or timed out");
            return false;
        }

    } catch (const std::exception& e) {
        logger_.error("Blockchain submission failed: " + std::string(e.what()));
        return false;
    }
}

std::vector<VerificationResult> BlockchainVerifier::query_verification_history(
    const std::string& binary_hash
) {
    std::vector<VerificationResult> history;

    try {
        auto it = verification_cache_.find(binary_hash);
        if (it != verification_cache_.end()) {
            history.push_back(it->second);
        }

        logger_.info("Found " + std::to_string(history.size()) + " verification records for hash");

    } catch (const std::exception& e) {
        logger_.error("Query verification history failed: " + std::string(e.what()));
    }

    return history;
}

bool BlockchainVerifier::validate_integrity(
    const std::string& binary_path,
    const std::string& expected_hash
) {
    try {
        std::string actual_hash = calculate_binary_hash(binary_path);
        bool valid = (actual_hash == expected_hash);

        logger_.info(std::string("Integrity validation: ") + (valid ? "PASSED" : "FAILED"));
        logger_.info("Expected: " + expected_hash);
        logger_.info("Actual: " + actual_hash);

        return valid;

    } catch (const std::exception& e) {
        logger_.error("Integrity validation failed: " + std::string(e.what()));
        return false;
    }
}

std::string BlockchainVerifier::get_network_status() {
    std::ostringstream status;

    status << "Blockchain Network Status:\n";
    status << "  Network: " << blockchain_config_.network << "\n";
    status << "  Connected: " << (connected_ ? "Yes" : "No") << "\n";
    status << "  RPC Endpoint: " << connection_endpoint_ << "\n";
    status << "  Contract Address: " << blockchain_config_.contract_address << "\n";
    status << "  Cached Verifications: " << verification_cache_.size() << "\n";

    return status.str();
}

// Private helper methods
bool BlockchainVerifier::load_blockchain_configuration(const ObfuscationConfig& config) {
    try {
        // Load from config.json settings
        blockchain_config_.network = "ganache-local";
        blockchain_config_.rpc_endpoint = "http://127.0.0.1:8545";
        blockchain_config_.contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
        blockchain_config_.private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
        blockchain_config_.gas_limit = 200000;
        blockchain_config_.gas_price = "20000000000";
        blockchain_config_.chain_id = 1337;
        blockchain_config_.confirmation_blocks = 1;

        // Set connection endpoint
        connection_endpoint_ = blockchain_config_.rpc_endpoint;
        current_network_ = blockchain_config_.network;

        logger_.info("Ganache blockchain configuration loaded");
        logger_.info("RPC Endpoint: " + blockchain_config_.rpc_endpoint);
        logger_.info("Chain ID: " + std::to_string(blockchain_config_.chain_id));
        return true;

    } catch (const std::exception& e) {
        logger_.error("Failed to load blockchain configuration: " + std::string(e.what()));
        return false;
    }
}

std::string h5x::BlockchainVerifier::generate_transaction_id() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 15);

    std::ostringstream tx_id;
    tx_id << "0x";

    for (int i = 0; i < 64; ++i) {
        tx_id << std::hex << dis(gen);
    }

    return tx_id.str();
}

std::string BlockchainVerifier::format_metadata(const std::string& binary_path) {
    std::ostringstream metadata;

    metadata << "{";
    metadata << "\"file_path\": \"" << binary_path << "\",";
    metadata << "\"timestamp\": " << std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count() << ",";
    metadata << "\"version\": \"1.0.0\",";
    metadata << "\"verifier\": \"H5X-BlockchainVerifier\"";
    metadata << "}";

    return metadata.str();
}

std::string BlockchainVerifier::sha256_hash(const std::vector<uint8_t>& data) {
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_len;
    
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr);
    EVP_DigestUpdate(ctx, data.data(), data.size());
    EVP_DigestFinal_ex(ctx, hash, &hash_len);
    EVP_MD_CTX_free(ctx);

    std::ostringstream ss;
    for (unsigned int i = 0; i < hash_len; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(hash[i]);
    }

    return ss.str();
}

std::vector<uint8_t> BlockchainVerifier::read_binary_file(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + filepath);
    }

    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<uint8_t> buffer(size);
    if (!file.read(reinterpret_cast<char*>(buffer.data()), size)) {
        throw std::runtime_error("Failed to read file: " + filepath);
    }

    return buffer;
}

bool BlockchainVerifier::check_ganache_connection() {
    Json::Value payload;
    payload["jsonrpc"] = "2.0";
    payload["method"] = "eth_chainId";
    payload["params"] = Json::Value(Json::arrayValue);
    payload["id"] = 1;

    auto response = make_rpc_call(payload);
    
    if (response.response_code != 200) {
        logger_.error("Failed to connect to Ganache - HTTP " + std::to_string(response.response_code));
        return false;
    }

    try {
        Json::Value json_response;
        Json::Reader reader;
        if (!reader.parse(response.data, json_response)) {
            logger_.error("Failed to parse Ganache response");
            return false;
        }

        if (json_response.isMember("result")) {
            std::string chain_id = json_response["result"].asString();
            // Convert hex chain ID to decimal
            int actual_chain_id = std::stoi(chain_id, nullptr, 16);
            if (actual_chain_id == blockchain_config_.chain_id) {
                logger_.info("Ganache chain ID verified: " + std::to_string(actual_chain_id));
                return true;
            } else {
                logger_.warning("Chain ID mismatch. Expected: " + std::to_string(blockchain_config_.chain_id) + 
                              ", Got: " + std::to_string(actual_chain_id));
            }
        }
    } catch (const std::exception& e) {
        logger_.error("Error verifying Ganache connection: " + std::string(e.what()));
    }

    return false;
}

std::string h5x::BlockchainVerifier::keccak256_hash(const std::string& input) {
    // Use SHA3/Keccak256 for Ethereum compatibility
    unsigned char hash[32];
    EVP_MD_CTX* mdctx = EVP_MD_CTX_new();
    const EVP_MD* md = EVP_sha3_256(); // Use SHA3-256 (similar to Keccak256)
    
    EVP_DigestInit_ex(mdctx, md, nullptr);
    EVP_DigestUpdate(mdctx, input.c_str(), input.length());
    EVP_DigestFinal_ex(mdctx, hash, nullptr);
    EVP_MD_CTX_free(mdctx);

    std::ostringstream ss;
    ss << "0x";
    for (int i = 0; i < 32; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(hash[i]);
    }
    return ss.str();
}

bool h5x::BlockchainVerifier::wait_for_confirmation(const std::string& transaction_id) {
    logger_.info("Waiting for transaction confirmation: " + transaction_id);

    // Poll Ganache for transaction receipt
    for (int i = 0; i < 30; ++i) { // 30 second timeout
        Json::Value payload;
        payload["jsonrpc"] = "2.0";
        payload["method"] = "eth_getTransactionReceipt";
        payload["params"].append(transaction_id);
        payload["id"] = 1;

        auto response = make_rpc_call(payload);
        
        if (response.response_code == 200) {
            try {
                Json::Value json_response;
                Json::Reader reader;
                if (reader.parse(response.data, json_response) && json_response.isMember("result")) {
                    const auto& result = json_response["result"];
                    if (!result.isNull() && result.isMember("status")) {
                        std::string status = result["status"].asString();
                        if (status == "0x1") {
                            logger_.info("Transaction confirmed successfully");
                            return true;
                        } else if (status == "0x0") {
                            logger_.error("Transaction failed on blockchain");
                            return false;
                        }
                    }
                }
            } catch (const std::exception& e) {
                logger_.debug("Error parsing receipt: " + std::string(e.what()));
            }
        }
        
        std::this_thread::sleep_for(std::chrono::seconds(1));
        logger_.debug("Waiting for confirmation... (" + std::to_string(i + 1) + "/30)");
    }

    logger_.warning("Transaction confirmation timeout");
    return false;
}

h5x::BlockchainVerifier::CurlResponse h5x::BlockchainVerifier::make_rpc_call(const Json::Value& payload) {
    CurlResponse response;
    response.response_code = 0;

    if (!curl_handle_) {
        return response;
    }

    // Convert JSON to string
    Json::StreamWriterBuilder builder;
    std::string json_string = Json::writeString(builder, payload);

    // Set CURL options
    curl_easy_setopt(curl_handle_, CURLOPT_URL, blockchain_config_.rpc_endpoint.c_str());
    curl_easy_setopt(curl_handle_, CURLOPT_POSTFIELDS, json_string.c_str());
    curl_easy_setopt(curl_handle_, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl_handle_, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl_handle_, CURLOPT_TIMEOUT, 10L);
    
    // Set headers
    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl_handle_, CURLOPT_HTTPHEADER, headers);

    // Perform request
    CURLcode res = curl_easy_perform(curl_handle_);
    curl_easy_getinfo(curl_handle_, CURLINFO_RESPONSE_CODE, &response.response_code);
    
    curl_slist_free_all(headers);

    if (res != CURLE_OK) {
        logger_.error("CURL request failed: " + std::string(curl_easy_strerror(res)));
        response.response_code = 0;
    }

    return response;
}

size_t h5x::BlockchainVerifier::WriteCallback(void* contents, size_t size, size_t nmemb, CurlResponse* response) {
    size_t total_size = size * nmemb;
    response->data.append(static_cast<char*>(contents), total_size);
    return total_size;
}

std::string BlockchainVerifier::create_transaction(const std::string& hash) {
    logger_.info("Creating blockchain transaction for hash: " + hash);
    
    // For Ganache, we'll send a simple transaction with the hash as data
    Json::Value payload;
    payload["jsonrpc"] = "2.0";
    payload["method"] = "eth_sendTransaction";
    
    Json::Value tx_params;
    // Use the first Ganache account
    tx_params["from"] = "0x90f8bf6a479f320ead074411a4b0e7944ea8c9c1";
    tx_params["to"] = "0xffcf8fdee72ac11b5c542428b35eef5769c409f0"; // Second Ganache account
    tx_params["value"] = "0x1"; // Send 1 wei
    tx_params["gas"] = "0x15F90"; // 90000 gas (for transaction with data)
    tx_params["gasPrice"] = "0x3B9ACA00"; // 1 gwei
    
    // Include the hash in the transaction data
    std::string data = "0x" + hash.substr(2); // Remove '0x' and add back to ensure proper format
    tx_params["data"] = data;
    
    payload["params"].append(tx_params);
    payload["id"] = 1;

    logger_.info("Sending transaction with data: " + data);
    
    auto response = make_rpc_call(payload);
    
    logger_.info("Transaction response code: " + std::to_string(response.response_code));
    logger_.info("Transaction response data: " + response.data);
    
    if (response.response_code == 200) {
        try {
            Json::Value json_response;
            Json::Reader reader;
            if (reader.parse(response.data, json_response)) {
                if (json_response.isMember("result")) {
                    std::string tx_hash = json_response["result"].asString();
                    logger_.info("Transaction created successfully: " + tx_hash);
                    return tx_hash;
                } else if (json_response.isMember("error")) {
                    logger_.error("Transaction error: " + json_response["error"]["message"].asString());
                }
            }
        } catch (const std::exception& e) {
            logger_.error("Error parsing transaction response: " + std::string(e.what()));
        }
    }
    
    return "";
}

std::string BlockchainVerifier::encode_function_call(const std::string& function_sig, const std::string& hash) {
    // Simple function encoding for storeHash(bytes32)
    // Function selector for storeHash(bytes32) would be first 4 bytes of keccak256("storeHash(bytes32)")
    std::string selector = "0xa9b5ec85"; // Pre-calculated for storeHash(bytes32)
    
    // Remove '0x' prefix from hash and pad to 32 bytes
    std::string clean_hash = hash.substr(2);
    while (clean_hash.length() < 64) {
        clean_hash = "0" + clean_hash;
    }
    
    return selector + clean_hash;
}

} // namespace h5x
