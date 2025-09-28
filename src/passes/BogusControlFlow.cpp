#include "BogusControlFlow.hpp"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Constants.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include <vector>
#include <random>

using namespace llvm;

namespace h5x {

PreservedAnalyses BogusControlFlowPass::run(Module &M, ModuleAnalysisManager &AM) {
    bool modified = false;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 1.0);
    
    for (Function &F : M) {
        // Skip external functions, system functions, and small functions
        if (F.isDeclaration() || 
            F.getName().starts_with("__") || 
            F.size() < 2) {
            continue;
        }
        
        std::vector<BasicBlock*> originalBlocks;
        for (BasicBlock &BB : F) {
            originalBlocks.push_back(&BB);
        }
        
        // Add bogus control flow to ALL suitable blocks for maximum effect
        for (BasicBlock *BB : originalBlocks) {
            if (addBogusControlFlow(*BB)) {
                modified = true;
            }
        }
    }
    
    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}

bool BogusControlFlowPass::addBogusControlFlow(BasicBlock &BB) {
    // Don't modify blocks with PHI nodes, complex terminators, or single instructions
    if (!BB.phis().empty() || 
        isa<InvokeInst>(BB.getTerminator()) ||
        isa<SwitchInst>(BB.getTerminator()) ||
        BB.size() < 3) { // Need at least 2 non-terminator instructions
        return false;
    }
    
    LLVMContext &Ctx = BB.getContext();
    Function *F = BB.getParent();
    
    // Split the block at a safe point (middle of the block)
    Instruction *splitPoint = nullptr;
    int instCount = 0;
    for (Instruction &I : BB) {
        if (!I.isTerminator()) {
            instCount++;
            if (instCount == 2) { // Split after second instruction
                splitPoint = &I;
                break;
            }
        }
    }
    
    if (!splitPoint) return false;
    
    // Split the basic block
    BasicBlock *continuation = BB.splitBasicBlock(splitPoint->getNextNode(), "bogus_continuation");
    
    // Remove the unconditional branch created by splitBasicBlock
    BB.getTerminator()->eraseFromParent();
    
    // Create opaque predicate (always true: x*x >= 0)
    IRBuilder<> Builder(&BB);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> valueDis(1, 100);
    
    Value *x = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
    Value *square = Builder.CreateMul(x, x, "bogus_square");
    Value *isPositive = Builder.CreateICmpSGE(square, ConstantInt::get(Type::getInt32Ty(Ctx), 0), "bogus_predicate");
    
    // Create bogus blocks that do meaningless work but don't affect program state
    BasicBlock *bogusBlock = BasicBlock::Create(Ctx, "bogus_dead_code", F);
    
    // Create conditional branch: always go to continuation, never to bogus
    Builder.CreateCondBr(isPositive, continuation, bogusBlock);
    
    // Fill bogus block with dead code (unreachable)
    Builder.SetInsertPoint(bogusBlock);
    Value *deadVar = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "dead_var");
    Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 0xDEADBEEF), deadVar);
    Value *deadLoad = Builder.CreateLoad(Type::getInt32Ty(Ctx), deadVar, "dead_load");
    Value *deadMath = Builder.CreateAdd(deadLoad, ConstantInt::get(Type::getInt32Ty(Ctx), 42), "dead_math");
    Builder.CreateStore(deadMath, deadVar); // This code never executes
    Builder.CreateBr(continuation); // Dead branch
    
    return true;
}

} // namespace h5x
