#include "InstructionSubstitution.hpp"

#ifdef USE_MOCK_LLVM
// Mock implementation when LLVM is not available
#include <iostream>

namespace h5x {

bool InstructionSubstitutionPass::run() {
    std::cout << "[MOCK] InstructionSubstitution pass running (mock mode)" << std::endl;
    return true;
}

} // namespace h5x

#else
// Real LLVM implementation when available
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Constants.h"
#include "llvm/Support/raw_ostream.h"
#include <random>

using namespace llvm;

namespace h5x {

PreservedAnalyses InstructionSubstitutionPass::run(Module &M, ModuleAnalysisManager &AM) {
    bool modified = false;
    int totalInstructions = 0;
    int replacedInstructions = 0;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 3);

    llvm::errs() << "[DEBUG] InstructionSubstitution pass starting...\n";

    for (Function &F : M) {
        if (F.isDeclaration() || F.getName().starts_with("__")) {
            continue; // Skip external and system functions
        }

        llvm::errs() << "[DEBUG] Processing function: " << F.getName().str() << "\n";

        std::vector<Instruction*> toReplace;

        // Collect instructions to replace
        for (BasicBlock &BB : F) {
            for (Instruction &I : BB) {
                if (auto *BO = dyn_cast<BinaryOperator>(&I)) {
                    // Only substitute certain operations to avoid breaking the program
                    if (BO->getOpcode() == Instruction::Add ||
                        BO->getOpcode() == Instruction::Sub ||
                        BO->getOpcode() == Instruction::Mul) {
                        toReplace.push_back(&I);
                        totalInstructions++;
                    }
                }
            }
        }

        llvm::errs() << "[DEBUG] Found " << toReplace.size() << " instructions to replace in function " << F.getName().str() << "\n";

        // Apply substitutions
        IRBuilder<> Builder(M.getContext());
        for (Instruction *I : toReplace) {
            Builder.SetInsertPoint(I);
            Value *replacement = nullptr;

            if (auto *BO = dyn_cast<BinaryOperator>(I)) {
                Value *LHS = BO->getOperand(0);
                Value *RHS = BO->getOperand(1);

                switch (BO->getOpcode()) {
                case Instruction::Add:
                    // Replace: a + b with: (a ^ b) + 2 * (a & b)
                    // This is mathematically equivalent: a + b = (a XOR b) + 2 * (a AND b)
                    {
                        Value *XorVal = Builder.CreateXor(LHS, RHS, "sub_xor");
                        Value *AndVal = Builder.CreateAnd(LHS, RHS, "sub_and");
                        Value *TwoAndVal = Builder.CreateShl(AndVal, 1, "sub_2and"); // Multiply by 2
                        replacement = Builder.CreateAdd(XorVal, TwoAndVal, "sub_add");
                        llvm::errs() << "[DEBUG] Replaced Add instruction\n";
                    }
                    break;

                case Instruction::Sub:
                    // Replace: a - b with: (a ^ b) - 2 * (~a & b)
                    {
                        Value *XorVal = Builder.CreateXor(LHS, RHS, "sub_xor");
                        Value *NotA = Builder.CreateNot(LHS, "sub_not");
                        Value *AndVal = Builder.CreateAnd(NotA, RHS, "sub_and");
                        Value *TwoAndVal = Builder.CreateShl(AndVal, 1, "sub_2and");
                        replacement = Builder.CreateSub(XorVal, TwoAndVal, "sub_sub");
                        llvm::errs() << "[DEBUG] Replaced Sub instruction\n";
                    }
                    break;

                case Instruction::Mul:
                    // Replace simple multiplications with shifts when possible
                    if (auto *CI = dyn_cast<ConstantInt>(RHS)) {
                        uint64_t val = CI->getZExtValue();
                        if (val > 0 && (val & (val - 1)) == 0) { // Power of 2
                            uint64_t shiftAmount = 0;
                            uint64_t temp = val;
                            while (temp > 1) {
                                temp >>= 1;
                                shiftAmount++;
                            }
                            if (shiftAmount < 32) { // Reasonable shift amount
                                replacement = Builder.CreateShl(LHS, shiftAmount, "sub_shift");
                                llvm::errs() << "[DEBUG] Replaced Mul with shift (power of 2)\n";
                            }
                        }
                    }
                    // Skip non-power-of-2 multiplications to avoid incorrect transformations
                    break;

                default:
                    continue; // Skip unsupported operations
                }
            }

            if (replacement) {
                I->replaceAllUsesWith(replacement);
                modified = true;
                replacedInstructions++;
            }
        }

        // Clean up replaced instructions
        for (Instruction *I : toReplace) {
            if (I->use_empty()) {
                I->eraseFromParent();
            }
        }
    }

    llvm::errs() << "[DEBUG] InstructionSubstitution pass completed. Total instructions found: " << totalInstructions << ", replaced: " << replacedInstructions << ", modified: " << modified << "\n";

    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}

} // namespace h5x
#endif