#include "ConfigParser.hpp"
#include <fstream>
#include <iostream>

namespace h5x {

bool ConfigParser::load_from_file(const std::string& config_path) {
    // For now, use hardcoded Level 2 configuration
    config_.obfuscation_level = 2;
    config_.enable_control_flow_flattening = true;
    config_.enable_instruction_substitution = true;
    config_.enable_string_obfuscation = true;
    config_.enable_bogus_control_flow = false;
    config_.enable_anti_analysis = false;
    config_.enable_ai_optimization = false;
    config_.enable_blockchain_verification = true;
    
    config_.genetic_algorithm_generations = 20;
    config_.mutation_rate = 0.1;
    config_.crossover_rate = 0.8;
    
    config_.max_threads = 4;
    config_.memory_limit_mb = 6144;
    
    config_.blockchain_network = "ganache-local";
    config_.verification_contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
    
    return true;
}

bool ConfigParser::validate_config() const {
    return config_.obfuscation_level >= 1 && config_.obfuscation_level <= 5;
}

// Static utility methods for CLI
ObfuscationConfig ConfigParser::loadFromFile(const std::string& config_path) {
    ConfigParser parser;
    if (parser.load_from_file(config_path)) {
        return parser.get_config();
    }
    // Return default config if loading fails
    return getDefaultConfig();
}

bool ConfigParser::saveToFile(const ObfuscationConfig& config, const std::string& config_path) {
    try {
        // Create JSON representation of config
        std::ofstream file(config_path);
        if (!file.is_open()) {
            return false;
        }
        
        file << "{\n";
        file << "  \"obfuscation_level\": " << config.obfuscation_level << ",\n";
        file << "  \"enable_control_flow_flattening\": " << (config.enable_control_flow_flattening ? "true" : "false") << ",\n";
        file << "  \"enable_instruction_substitution\": " << (config.enable_instruction_substitution ? "true" : "false") << ",\n";
        file << "  \"enable_string_obfuscation\": " << (config.enable_string_obfuscation ? "true" : "false") << ",\n";
        file << "  \"enable_bogus_control_flow\": " << (config.enable_bogus_control_flow ? "true" : "false") << ",\n";
        file << "  \"enable_anti_analysis\": " << (config.enable_anti_analysis ? "true" : "false") << ",\n";
        file << "  \"enable_ai_optimization\": " << (config.enable_ai_optimization ? "true" : "false") << ",\n";
        file << "  \"genetic_algorithm_generations\": " << config.genetic_algorithm_generations << ",\n";
        file << "  \"mutation_rate\": " << config.mutation_rate << ",\n";
        file << "  \"crossover_rate\": " << config.crossover_rate << ",\n";
        file << "  \"enable_blockchain_verification\": " << (config.enable_blockchain_verification ? "true" : "false") << ",\n";
        file << "  \"blockchain_network\": \"" << config.blockchain_network << "\",\n";
        file << "  \"verification_contract_address\": \"" << config.verification_contract_address << "\",\n";
        file << "  \"max_complexity_threshold\": " << config.max_complexity_threshold << ",\n";
        file << "  \"performance_weight\": " << config.performance_weight << ",\n";
        file << "  \"security_weight\": " << config.security_weight << ",\n";
        file << "  \"max_threads\": " << config.max_threads << ",\n";
        file << "  \"memory_limit_mb\": " << config.memory_limit_mb << ",\n";
        file << "  \"generate_detailed_report\": " << (config.generate_detailed_report ? "true" : "false") << ",\n";
        file << "  \"enable_debug_symbols\": " << (config.enable_debug_symbols ? "true" : "false") << ",\n";
        file << "  \"output_directory\": \"" << config.output_directory << "\"\n";
        file << "}\n";
        
        file.close();
        return true;
    } catch (const std::exception&) {
        return false;
    }
}

ObfuscationConfig ConfigParser::getDefaultConfig() {
    ObfuscationConfig config;
    // Default values are already set in the struct
    return config;
}

} // namespace h5x