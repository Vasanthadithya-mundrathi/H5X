#ifndef H5X_GENETIC_OPTIMIZER_HPP
#define H5X_GENETIC_OPTIMIZER_HPP

#include <vector>
#include <string>
#include <random>
#include <functional>
#include "llvm/IR/Module.h"
#include "../utils/Logger.hpp"

namespace h5x {

struct ObfuscationConfig;

struct Individual {
    std::vector<int> pass_sequence;
    double fitness_score;

    Individual() : fitness_score(0.0) {}
    Individual(const std::vector<int>& sequence) : pass_sequence(sequence), fitness_score(0.0) {}
};

struct GeneticAlgorithmParams {
    int population_size{50};
    int generations{100};
    double mutation_rate{0.1};
    double crossover_rate{0.8};
    int tournament_size{3};
    double elitism_ratio{0.1};
};

class GeneticOptimizer {
public:
    explicit GeneticOptimizer(Logger& logger);
    ~GeneticOptimizer() = default;

    bool initialize(const ObfuscationConfig& config);
    void update_configuration(const ObfuscationConfig& config);

    std::vector<int> optimize_pass_sequence(llvm::Module& module);

    // Genetic algorithm components
    std::vector<Individual> initialize_population();
    double evaluate_fitness(const Individual& individual, llvm::Module& module);
    std::vector<Individual> selection(const std::vector<Individual>& population);
    Individual crossover(const Individual& parent1, const Individual& parent2);
    Individual mutate(const Individual& individual);

    // Statistics and monitoring
    std::vector<double> get_fitness_history() const { return fitness_history_; }
    double get_best_fitness() const;

private:
    Logger& logger_;
    bool initialized_;

    GeneticAlgorithmParams params_;
    std::mt19937 rng_;

    // Obfuscation pass types
    enum class PassType {
        CONTROL_FLOW_FLATTENING = 0,
        INSTRUCTION_SUBSTITUTION = 1,
        STRING_OBFUSCATION = 2,
        BOGUS_CONTROL_FLOW = 3,
        ANTI_ANALYSIS = 4,
        DEAD_CODE_ELIMINATION = 5,
        CONSTANT_PROPAGATION = 6
    };

    std::vector<PassType> available_passes_;
    std::vector<double> fitness_history_;

    // Fitness evaluation components
    double calculate_security_score(llvm::Module& original, llvm::Module& obfuscated);
    double calculate_performance_impact(llvm::Module& original, llvm::Module& obfuscated);
    double calculate_complexity_score(llvm::Module& module);

    // Helper methods
    std::vector<int> generate_random_sequence();
    bool is_valid_sequence(const std::vector<int>& sequence);
    void log_generation_stats(int generation, const std::vector<Individual>& population);
};

} // namespace h5x

#endif // H5X_GENETIC_OPTIMIZER_HPP
