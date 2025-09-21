#include <gtest/gtest.h>
#include "passes/InstructionSubstitution.hpp"
#include "passes/StringObfuscation.hpp"
#include "passes/BogusControlFlow.hpp"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/LLVMContext.h"

using namespace llvm;

namespace h5x {
namespace test {

class LLVMPassTest : public ::testing::Test {
protected:
    void SetUp() override {
        context = std::make_unique<LLVMContext>();
        module = std::make_unique<Module>("test_module", *context);
        
        // Create a simple test function
        FunctionType *funcType = FunctionType::get(Type::getInt32Ty(*context), false);
        testFunction = Function::Create(funcType, Function::ExternalLinkage, "test_func", *module);
        
        BasicBlock *entryBB = BasicBlock::Create(*context, "entry", testFunction);
        IRBuilder<> builder(entryBB);
        
        // Add some basic instructions for testing
        Value *val1 = ConstantInt::get(Type::getInt32Ty(*context), 10);
        Value *val2 = ConstantInt::get(Type::getInt32Ty(*context), 20);
        Value *addResult = builder.CreateAdd(val1, val2, "add_result");
        Value *mulResult = builder.CreateMul(addResult, val1, "mul_result");
        
        builder.CreateRet(mulResult);
    }
    
    std::unique_ptr<LLVMContext> context;
    std::unique_ptr<Module> module;
    Function *testFunction;
};

TEST_F(LLVMPassTest, InstructionSubstitutionPass) {
    InstructionSubstitutionPass pass;
    ModuleAnalysisManager MAM;
    
    // Count original instructions
    size_t originalInstructions = 0;
    for (BasicBlock &BB : *testFunction) {
        originalInstructions += BB.size();
    }
    
    auto result = pass.run(*module, MAM);
    
    // Count instructions after transformation
    size_t transformedInstructions = 0;
    for (BasicBlock &BB : *testFunction) {
        transformedInstructions += BB.size();
    }
    
    // Instruction substitution should increase the number of instructions
    EXPECT_GE(transformedInstructions, originalInstructions);
}

TEST_F(LLVMPassTest, StringObfuscationPass) {
    // Add a string constant to the module
    Constant *stringConstant = ConstantDataArray::getString(*context, "Test String", true);
    GlobalVariable *stringGlobal = new GlobalVariable(
        *module, stringConstant->getType(), true, GlobalValue::PrivateLinkage,
        stringConstant, "test_string"
    );
    
    StringObfuscationPass pass;
    ModuleAnalysisManager MAM;
    
    auto result = pass.run(*module, MAM);
    
    // The pass should create additional globals (encrypted string + key)
    size_t globalCount = 0;
    for (GlobalVariable &GV : module->globals()) {
        globalCount++;
    }
    
    EXPECT_GT(globalCount, 1); // Should have more than just the original string
}

TEST_F(LLVMPassTest, BogusControlFlowPass) {
    BogusControlFlowPass pass;
    ModuleAnalysisManager MAM;
    
    // Count original basic blocks
    size_t originalBlocks = testFunction->size();
    
    auto result = pass.run(*module, MAM);
    
    // Count basic blocks after transformation
    size_t transformedBlocks = testFunction->size();
    
    // Bogus control flow should potentially add more basic blocks
    // (though it may not always modify every function)
    EXPECT_GE(transformedBlocks, originalBlocks);
}

} // namespace test
} // namespace h5x