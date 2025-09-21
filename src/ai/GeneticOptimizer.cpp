#include "GeneticOptimizer.hpp"
#include "../utils/ConfigParser.hpp"
#include <algorithm>
#include <numeric>
#include <chrono>
#include <cmath>
#include <set>
#include <map>
#include <unordered_set>
#include "llvm/Transforms/Utils/Cloning.h"

namespace h5x {

GeneticOptimizer::GeneticOptimizer(Logger& logger)
    : logger_(logger)
    , initialized_(false)
    , rng_(std::chrono::steady_clock::now().time_since_epoch().count())
{
    // Initialize available obfuscation passes
    available_passes_ = {
        PassType::CONTROL_FLOW_FLATTENING,
        PassType::INSTRUCTION_SUBSTITUTION,
        PassType::STRING_OBFUSCATION,
        PassType::BOGUS_CONTROL_FLOW,
        PassType::ANTI_ANALYSIS,
        PassType::DEAD_CODE_ELIMINATION,
        PassType::CONSTANT_PROPAGATION
    };

    logger_.debug("GeneticOptimizer created");
}

bool GeneticOptimizer::initialize(const ObfuscationConfig& config) {
    logger_.info("Initializing GeneticOptimizer...");

    try {
        // Configure genetic algorithm parameters based on config
        params_.population_size = 30 + config.obfuscation_level * 10;
        params_.generations = config.genetic_algorithm_generations;
        params_.mutation_rate = config.mutation_rate;
        params_.crossover_rate = config.crossover_rate;

        initialized_ = true;
        logger_.info("GeneticOptimizer initialized successfully");
        logger_.info("Parameters: pop=" + std::to_string(params_.population_size) +
                    ", gen=" + std::to_string(params_.generations) +
                    ", mut=" + std::to_string(params_.mutation_rate) +
                    ", cross=" + std::to_string(params_.crossover_rate));

        return true;

    } catch (const std::exception& e) {
        logger_.error("Failed to initialize GeneticOptimizer: " + std::string(e.what()));
        return false;
    }
}

void GeneticOptimizer::update_configuration(const ObfuscationConfig& config) {
    params_.generations = config.genetic_algorithm_generations;
    params_.mutation_rate = config.mutation_rate;
    params_.crossover_rate = config.crossover_rate;

    logger_.info("GeneticOptimizer configuration updated");
}

std::vector<int> GeneticOptimizer::optimize_pass_sequence(llvm::Module& module) {
    if (!initialized_) {
        logger_.error("GeneticOptimizer not initialized");
        return generate_random_sequence();
    }

    logger_.info("Starting genetic algorithm optimization...");
    fitness_history_.clear();

    auto start_time = std::chrono::high_resolution_clock::now();

    try {
        // Initialize population
        auto population = initialize_population();
        logger_.info("Initialized population with " + std::to_string(population.size()) + " individuals");

        // Evaluate initial population
        for (auto& individual : population) {
            individual.fitness_score = evaluate_fitness(individual, module);
        }

        // Sort population by fitness (higher is better)
        std::sort(population.begin(), population.end(), 
                 [](const Individual& a, const Individual& b) {
                     return a.fitness_score > b.fitness_score;
                 });

        // Evolution loop
        for (int generation = 0; generation < params_.generations; ++generation) {
            std::vector<Individual> new_population;

            // Elitism - keep best individuals
            int elite_count = static_cast<int>(params_.elitism_ratio * params_.population_size);
            for (int i = 0; i < elite_count; ++i) {
                new_population.push_back(population[i]);
            }

            // Generate offspring through selection, crossover, and mutation
            while (new_population.size() < static_cast<size_t>(params_.population_size)) {
                // Selection
                auto selected = selection(population);

                // Crossover
                if (selected.size() >= 2 && 
                    std::uniform_real_distribution<>(0.0, 1.0)(rng_) < params_.crossover_rate) {

                    auto offspring = crossover(selected[0], selected[1]);

                    // Mutation
                    if (std::uniform_real_distribution<>(0.0, 1.0)(rng_) < params_.mutation_rate) {
                        offspring = mutate(offspring);
                    }

                    offspring.fitness_score = evaluate_fitness(offspring, module);
                    new_population.push_back(offspring);
                }
            }

            // Replace population
            population = new_population;

            // Sort by fitness
            std::sort(population.begin(), population.end(), 
                     [](const Individual& a, const Individual& b) {
                         return a.fitness_score > b.fitness_score;
                     });

            // Record best fitness
            fitness_history_.push_back(population[0].fitness_score);

            // Log progress
            if (generation % 10 == 0 || generation == params_.generations - 1) {
                log_generation_stats(generation, population);
            }
        }

        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

        logger_.info("Genetic algorithm optimization completed in " + 
                    std::to_string(duration.count()) + "ms");
        logger_.info("Best fitness achieved: " + std::to_string(population[0].fitness_score));

        return population[0].pass_sequence;

    } catch (const std::exception& e) {
        logger_.error("Genetic algorithm optimization failed: " + std::string(e.what()));
        return generate_random_sequence();
    }
}

std::vector<Individual> GeneticOptimizer::initialize_population() {
    std::vector<Individual> population;
    population.reserve(params_.population_size);

    for (int i = 0; i < params_.population_size; ++i) {
        Individual individual(generate_random_sequence());
        population.push_back(individual);
    }

    return population;
}

double GeneticOptimizer::evaluate_fitness(const Individual& individual, llvm::Module& module) {
    try {
        // For now, use simple heuristics based on the pass sequence
        // TODO: Apply actual obfuscation passes to create obfuscated module
        auto original_clone = llvm::CloneModule(module);
        
        // Calculate fitness based on pass sequence characteristics
        double security_score = calculate_security_score(module, *original_clone);
        double performance_impact = calculate_performance_impact(module, *original_clone);
        double complexity_score = calculate_complexity_score(module);

        // Weighted fitness function for Level 2 obfuscation
        double fitness = 0.0;
        fitness += security_score * 0.5;           // 50% weight on security
        fitness += (100.0 - performance_impact) * 0.3;  // 30% weight on performance (lower impact = higher score)
        fitness += complexity_score * 0.2;        // 20% weight on complexity

        // Penalty for overly long sequences (efficiency consideration)
        if (individual.pass_sequence.size() > 6) {
            fitness *= 0.9; 
        }

        // Bonus for using complementary techniques
        std::set<int> unique_passes(individual.pass_sequence.begin(), individual.pass_sequence.end());
        if (unique_passes.size() >= 3) {
            fitness *= 1.1; // 10% bonus for diversity
        }

        return std::max(0.0, std::min(100.0, fitness));

    } catch (const std::exception& e) {
        logger_.warning("Fitness evaluation failed: " + std::string(e.what()));
        return 0.0;
    }
}

std::vector<Individual> GeneticOptimizer::selection(const std::vector<Individual>& population) {
    std::vector<Individual> selected;

    // Tournament selection
    for (int i = 0; i < 2; ++i) {
        std::vector<Individual> tournament;

        for (int j = 0; j < params_.tournament_size; ++j) {
            std::uniform_int_distribution<> dist(0, population.size() - 1);
            int index = dist(rng_);
            tournament.push_back(population[index]);
        }

        // Select best from tournament
        auto best = std::max_element(tournament.begin(), tournament.end(),
                                   [](const Individual& a, const Individual& b) {
                                       return a.fitness_score < b.fitness_score;
                                   });

        selected.push_back(*best);
    }

    return selected;
}

Individual GeneticOptimizer::crossover(const Individual& parent1, const Individual& parent2) {
    Individual offspring;

    // Single-point crossover
    int min_length = std::min(parent1.pass_sequence.size(), parent2.pass_sequence.size());
    if (min_length <= 1) {
        // If sequences are too short, return one of the parents
        return std::uniform_int_distribution<>(0, 1)(rng_) ? parent1 : parent2;
    }

    std::uniform_int_distribution<> dist(1, min_length - 1);
    int crossover_point = dist(rng_);

    // Combine sequences
    offspring.pass_sequence.insert(offspring.pass_sequence.end(),
                                 parent1.pass_sequence.begin(),
                                 parent1.pass_sequence.begin() + crossover_point);

    offspring.pass_sequence.insert(offspring.pass_sequence.end(),
                                 parent2.pass_sequence.begin() + crossover_point,
                                 parent2.pass_sequence.end());

    return offspring;
}

Individual GeneticOptimizer::mutate(const Individual& individual) {
    Individual mutated = individual;

    if (mutated.pass_sequence.empty()) {
        return mutated;
    }

    std::uniform_real_distribution<> prob(0.0, 1.0);

    // Point mutation - change random passes
    for (size_t i = 0; i < mutated.pass_sequence.size(); ++i) {
        if (prob(rng_) < 0.1) {  // 10% chance to mutate each gene
            std::uniform_int_distribution<> pass_dist(0, available_passes_.size() - 1);
            mutated.pass_sequence[i] = static_cast<int>(available_passes_[pass_dist(rng_)]);
        }
    }

    // Insert mutation - add a random pass
    if (prob(rng_) < 0.1 && mutated.pass_sequence.size() < 10) {
        std::uniform_int_distribution<> pos_dist(0, mutated.pass_sequence.size());
        std::uniform_int_distribution<> pass_dist(0, available_passes_.size() - 1);

        int position = pos_dist(rng_);
        int new_pass = static_cast<int>(available_passes_[pass_dist(rng_)]);
        mutated.pass_sequence.insert(mutated.pass_sequence.begin() + position, new_pass);
    }

    // Delete mutation - remove a random pass
    if (prob(rng_) < 0.1 && mutated.pass_sequence.size() > 2) {
        std::uniform_int_distribution<> pos_dist(0, mutated.pass_sequence.size() - 1);
        int position = pos_dist(rng_);
        mutated.pass_sequence.erase(mutated.pass_sequence.begin() + position);
    }

    return mutated;
}

std::vector<int> GeneticOptimizer::generate_random_sequence() {
    std::uniform_int_distribution<> length_dist(3, 7);
    int sequence_length = length_dist(rng_);

    std::uniform_int_distribution<> pass_dist(0, available_passes_.size() - 1);

    std::vector<int> sequence;
    for (int i = 0; i < sequence_length; ++i) {
        sequence.push_back(static_cast<int>(available_passes_[pass_dist(rng_)]));
    }

    return sequence;
}

bool GeneticOptimizer::is_valid_sequence(const std::vector<int>& sequence) {
    // Check if all passes are valid
    for (int pass : sequence) {
        if (pass < 0 || pass >= static_cast<int>(available_passes_.size())) {
            return false;
        }
    }

    // Check sequence length
    return sequence.size() >= 1 && sequence.size() <= 15;
}

void GeneticOptimizer::log_generation_stats(int generation, const std::vector<Individual>& population) {
    if (population.empty()) return;

    double best_fitness = population[0].fitness_score;
    double avg_fitness = 0.0;

    for (const auto& individual : population) {
        avg_fitness += individual.fitness_score;
    }
    avg_fitness /= population.size();

    logger_.info("Generation " + std::to_string(generation) + 
                ": Best=" + std::to_string(best_fitness) +
                ", Avg=" + std::to_string(avg_fitness));
}

double GeneticOptimizer::get_best_fitness() const {
    if (fitness_history_.empty()) {
        return 0.0;
    }
    return *std::max_element(fitness_history_.begin(), fitness_history_.end());
}

double GeneticOptimizer::calculate_security_score(llvm::Module& original, llvm::Module& obfuscated) {
    // Calculate security score based on actual module differences
    double security_score = 0.0;
    
    // Count function complexity increase
    size_t original_functions = 0;
    size_t obfuscated_functions = 0;
    
    for (auto& func : original) {
        if (!func.isDeclaration()) {
            original_functions++;
        }
    }
    
    for (auto& func : obfuscated) {
        if (!func.isDeclaration()) {
            obfuscated_functions++;
        }
    }
    
    // Base security score based on module changes
    if (obfuscated_functions > original_functions) {
        security_score += (obfuscated_functions - original_functions) * 10.0;
    }
    
    // TODO: Add more sophisticated analysis
    // For now, return a base score
    security_score += 50.0;
    
    return std::min(100.0, security_score);
}

double GeneticOptimizer::calculate_performance_impact(llvm::Module& original, llvm::Module& obfuscated) {
    // Calculate performance impact based on module differences
    double performance_impact = 0.0;
    
    // Count instructions in both modules
    size_t original_instructions = 0;
    size_t obfuscated_instructions = 0;
    
    for (auto& func : original) {
        if (!func.isDeclaration()) {
            for (auto& bb : func) {
                original_instructions += bb.size();
            }
        }
    }
    
    for (auto& func : obfuscated) {
        if (!func.isDeclaration()) {
            for (auto& bb : func) {
                obfuscated_instructions += bb.size();
            }
        }
    }
    
    // Calculate instruction bloat as performance impact
    if (original_instructions > 0) {
        double bloat_factor = static_cast<double>(obfuscated_instructions) / original_instructions;
        performance_impact = (bloat_factor - 1.0) * 50.0; // Scale to percentage
    }
    
    return std::min(100.0, performance_impact);
}

double h5x::GeneticOptimizer::calculate_complexity_score(llvm::Module& module) {
    // Calculate complexity based on control flow and instruction diversity

    int total_basic_blocks = 0;
    int total_instructions = 0;
    int total_functions = 0;

    for (const auto& func : module) {
        if (!func.isDeclaration()) {
            total_functions++;
            for (const auto& bb : func) {
                total_basic_blocks++;
                total_instructions += bb.size();
            }
        }
    }

    // Simple complexity heuristic
    return total_instructions * 0.5 + total_basic_blocks * 2.0 + total_functions * 10.0;
}

} // namespace h5x
