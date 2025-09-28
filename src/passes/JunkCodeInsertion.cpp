#include "JunkCodeInsertion.hpp"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/raw_ostream.h"
#include <random>
#include <vector>

using namespace llvm;

namespace h5x {

PreservedAnalyses JunkCodeInsertionPass::run(Module &M, ModuleAnalysisManager &AM) {
    bool modified = false;

    errs() << "[JunkCodeInsertion] Starting junk code insertion pass\n";

    // Create or get the junk global variable
    GlobalVariable *junkGlobal = getOrCreateJunkGlobal(M);

    // Iterate over all functions
    for (Function &F : M) {
        // Skip external functions and system functions
        if (F.isDeclaration() ||
            F.getName().starts_with("__") ||
            F.getName().starts_with("_Z") ||
            F.size() < 2) {
            continue;
        }

        insertJunkCode(F, M);
        modified = true;
    }

    errs() << "[JunkCodeInsertion] Junk code insertion completed\n";
    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}

void JunkCodeInsertionPass::insertJunkCode(Function &F, Module &M) {
    LLVMContext &Ctx = M.getContext();
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 10); // Random chance to insert junk

    for (BasicBlock &BB : F) {
        // Skip blocks with phi nodes or complex terminators
        if (!BB.phis().empty() ||
            isa<InvokeInst>(BB.getTerminator()) ||
            isa<ResumeInst>(BB.getTerminator())) {
            continue;
        }

        std::vector<Instruction*> instructions;
        for (Instruction &I : BB) {
            instructions.push_back(&I);
        }

        // Insert junk code at random points
        for (size_t i = 0; i < instructions.size(); ++i) {
            if (dis(gen) < 3) { // 30% chance to insert junk before this instruction
                IRBuilder<> Builder(instructions[i]);
                insertRandomOperations(Builder, getOrCreateJunkGlobal(M));
            }
        }

        // Also insert at the end of the block (before terminator)
        if (!isa<ReturnInst>(BB.getTerminator()) && dis(gen) < 5) {
            IRBuilder<> Builder(BB.getTerminator());
            insertRandomOperations(Builder, getOrCreateJunkGlobal(M));
        }
    }
}

GlobalVariable* JunkCodeInsertionPass::getOrCreateJunkGlobal(Module &M) {
    LLVMContext &Ctx = M.getContext();
    const char* globalName = "h5x_junk_global";

    // Check if it already exists
    if (GlobalVariable *existing = M.getGlobalVariable(globalName)) {
        return existing;
    }

    // Create a new global variable
    Type *int32Ty = Type::getInt32Ty(Ctx);
    Constant *initVal = ConstantInt::get(int32Ty, 0);
    GlobalVariable *junkGlobal = new GlobalVariable(
        M, int32Ty, false, GlobalValue::PrivateLinkage,
        initVal, globalName
    );

    return junkGlobal;
}

void JunkCodeInsertionPass::insertRandomOperations(IRBuilder<> &Builder, Value *globalVar) {
    LLVMContext &Ctx = Builder.getContext();
    Type *int32Ty = Type::getInt32Ty(Ctx);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> opDis(0, 5);
    std::uniform_int_distribution<> valDis(1, 100);

    // Load the global value
    Value *loadedGlobal = Builder.CreateLoad(int32Ty, globalVar, "junk_load");

    // Create some random operations
    Value *result = loadedGlobal;
    int numOps = opDis(gen) + 1; // 1-6 operations

    for (int i = 0; i < numOps; ++i) {
        int opType = opDis(gen);
        Value *operand = ConstantInt::get(int32Ty, valDis(gen));

        switch (opType) {
            case 0: // Add
                result = Builder.CreateAdd(result, operand, "junk_add");
                break;
            case 1: // Sub
                result = Builder.CreateSub(result, operand, "junk_sub");
                break;
            case 2: // Mul
                result = Builder.CreateMul(result, operand, "junk_mul");
                break;
            case 3: // And
                result = Builder.CreateAnd(result, operand, "junk_and");
                break;
            case 4: // Or
                result = Builder.CreateOr(result, operand, "junk_or");
                break;
            case 5: // Xor
                result = Builder.CreateXor(result, operand, "junk_xor");
                break;
        }
    }

    // Store back to global to prevent optimization
    Builder.CreateStore(result, globalVar);
}

} // namespace h5x