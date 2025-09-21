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

} // namespace h5x