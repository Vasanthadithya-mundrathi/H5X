#include <gtest/gtest.h>
#include "ai/GeneticOptimizer.hpp"
#include <fstream>

namespace h5x {
namespace test {

class AITest : public ::testing::Test {
protected:
    void SetUp() override {
        optimizer = std::make_unique<GeneticOptimizer>();
        
        // Create a simple test program
        testProgram = "test_ai_program.cpp";
        std::ofstream file(testProgram);
        file << R"(
#include <iostream>
int main() {
    int a = 10, b = 20;
    int result = a + b * 2;
    std::cout << result << std::endl;
    return 0;
}
)";
        file.close();
    }
    
    void TearDown() override {
        if (std::filesystem::exists(testProgram)) {
            std::filesystem::remove(testProgram);
        }
    }
    
    std::unique_ptr<GeneticOptimizer> optimizer;
    std::string testProgram;
};

TEST_F(AITest, GeneticOptimizerInitialization) {
    ASSERT_TRUE(optimizer != nullptr);
    
    // Test default parameters
    optimizer->setPopulationSize(30);
    optimizer->setGenerations(25);
    optimizer->setMutationRate(0.15);
    
    // These should not crash and should set the parameters
    EXPECT_NO_THROW(optimizer->setPopulationSize(50));
    EXPECT_NO_THROW(optimizer->setGenerations(50));
    EXPECT_NO_THROW(optimizer->setMutationRate(0.1));
}

TEST_F(AITest, GeneticOptimizerOptimization) {
    ObfuscationConfig baseConfig;
    baseConfig.level = 2;  
    baseConfig.enableStringObfuscation = true;
    baseConfig.enableInstructionSubstitution = true;
    baseConfig.enableAI = true;
    baseConfig.enableBlockchain = false; // Disable for testing
    
    // Use smaller parameters for faster testing
    optimizer->setPopulationSize(10);
    optimizer->setGenerations(5);
    optimizer->setMutationRate(0.2);
    
    auto result = optimizer->optimize(testProgram, baseConfig);
    
    EXPECT_GE(result.fitnessScore, 0.0);
    EXPECT_GT(result.generations, 0);
    EXPECT_EQ(result.optimizedConfig.level, baseConfig.level);
}

TEST_F(AITest, GeneticOptimizerParameterValidation) {
    // Test parameter bounds
    EXPECT_NO_THROW(optimizer->setPopulationSize(10));
    EXPECT_NO_THROW(optimizer->setPopulationSize(200));
    
    EXPECT_NO_THROW(optimizer->setGenerations(5));
    EXPECT_NO_THROW(optimizer->setGenerations(500));
    
    EXPECT_NO_THROW(optimizer->setMutationRate(0.01));
    EXPECT_NO_THROW(optimizer->setMutationRate(0.99));
}

} // namespace test
} // namespace h5x