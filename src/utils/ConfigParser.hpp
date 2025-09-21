#ifndef H5X_CONFIG_PARSER_HPP
#define H5X_CONFIG_PARSER_HPP

#include <string>
#include <memory>
#include <vector>
#include <chrono>

namespace h5x {

struct ObfuscationConfig {
    // Core obfuscation settings
    int obfuscation_level{2};
    bool enable_control_flow_flattening{true};
    bool enable_instruction_substitution{true};
    bool enable_string_obfuscation{true};
    bool enable_bogus_control_flow{false};
    bool enable_anti_analysis{false};

    // AI optimization settings
    bool enable_ai_optimization{false};
    int genetic_algorithm_generations{20};
    double mutation_rate{0.1};
    double crossover_rate{0.8};

    // Blockchain verification
    bool enable_blockchain_verification{false};
    std::string blockchain_network{"ganache-local"};
    std::string verification_contract_address{"0x5FbDB2315678afecb367f032d93F642f64180aa3"};

    // Performance tuning
    int max_complexity_threshold{1000};
    double performance_weight{0.3};
    double security_weight{0.7};
    int max_threads{4};
    int memory_limit_mb{6144};

    // Cross-platform settings
    std::vector<std::string> target_architectures{"arm64"};
    std::vector<std::string> target_platforms{"darwin"};

    // Output configuration
    bool generate_detailed_report{true};
    bool enable_debug_symbols{false};
    std::string output_directory{"./output"};
};

struct ObfuscationResult {
    // Success indicators
    bool success{false};
    std::string error_message;

    // File information
    std::string input_file_path;
    std::string output_file_path;
    size_t original_file_size{0};
    size_t obfuscated_file_size{0};

    // Obfuscation metrics
    double complexity_increase_factor{1.0};
    int functions_obfuscated{0};
    int strings_obfuscated{0};
    int bogus_blocks_added{0};
    int control_flow_modifications{0};

    // Performance metrics
    std::chrono::milliseconds compilation_time{0};
    std::chrono::milliseconds obfuscation_time{0};
    double estimated_runtime_overhead{0.0};

    // Security analysis
    double security_score{0.0};
    int anti_analysis_features_added{0};
    std::vector<std::string> applied_techniques;

    // AI optimization results
    bool ai_optimization_used{false};
    std::vector<int> optimal_pass_sequence;
    double fitness_score{0.0};

    // Blockchain verification
    bool blockchain_verified{false};
    std::string integrity_hash;
    std::string blockchain_transaction_id;
};

class ConfigParser {
public:
    ConfigParser() = default;
    ~ConfigParser() = default;

    bool load_from_file(const std::string& config_path);
    ObfuscationConfig get_config() const { return config_; }
    bool validate_config() const;
    
    // Static utility methods for CLI
    static ObfuscationConfig loadFromFile(const std::string& config_path);
    static bool saveToFile(const ObfuscationConfig& config, const std::string& config_path);
    static ObfuscationConfig getDefaultConfig();

private:
    ObfuscationConfig config_;
};

} // namespace h5x

#endif // H5X_CONFIG_PARSER_HPP