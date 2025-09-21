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
        
        // Add bogus control flow to random blocks
        for (BasicBlock *BB : originalBlocks) {
            // 30% chance to add bogus control flow to each block
            if (dis(gen) < 0.3) {
                if (addBogusControlFlow(*BB)) {
                    modified = true;
                }
            }
        }
    }
    
    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}

bool BogusControlFlowPass::addBogusControlFlow(BasicBlock &BB) {
    // Don't modify blocks with PHI nodes or complex terminators
    if (!BB.phis().empty() || 
        isa<InvokeInst>(BB.getTerminator()) ||
        isa<SwitchInst>(BB.getTerminator())) {
        return false;
    }
    
    LLVMContext &Ctx = BB.getContext();
    Function *F = BB.getParent();
    
    // Find a good insertion point (not the terminator)
    Instruction *insertPoint = nullptr;
    for (Instruction &I : BB) {
        if (!I.isTerminator()) {
            insertPoint = &I;
        } else {
            break;
        }
    }
    
    if (!insertPoint) return false;
    
    // Create opaque predicates (always true or always false, but hard to analyze)
    IRBuilder<> Builder(insertPoint->getNextNode());
    
    // Create an opaque predicate: (x * (x + 1)) % 2 == 0 (always true for integers)
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> valueDis(1, 100);
    
    Value *x = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
    Value *xPlus1 = Builder.CreateAdd(x, ConstantInt::get(Type::getInt32Ty(Ctx), 1), "bogus_x_plus_1");
    Value *product = Builder.CreateMul(x, xPlus1, "bogus_product");
    Value *mod2 = Builder.CreateSRem(product, ConstantInt::get(Type::getInt32Ty(Ctx), 2), "bogus_mod");
    Value *isEven = Builder.CreateICmpEQ(mod2, ConstantInt::get(Type::getInt32Ty(Ctx), 0), "bogus_is_even");
    
    // Create bogus blocks
    BasicBlock *bogusTrue = BasicBlock::Create(Ctx, "bogus_true", F);
    BasicBlock *bogusFalse = BasicBlock::Create(Ctx, "bogus_false", F);
    BasicBlock *bogusJoin = BasicBlock::Create(Ctx, "bogus_join", F);
    
    // Create the bogus conditional branch
    Builder.CreateCondBr(isEven, bogusTrue, bogusFalse);
    
    // Fill bogus true block with meaningless operations
    Builder.SetInsertPoint(bogusTrue);
    Value *bogusVar1 = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "bogus_var1");
    Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 42), bogusVar1);
    Value *bogusLoad1 = Builder.CreateLoad(Type::getInt32Ty(Ctx), bogusVar1, "bogus_load1");
    Value *bogusAdd = Builder.CreateAdd(bogusLoad1, ConstantInt::get(Type::getInt32Ty(Ctx), 13), "bogus_add");
    Builder.CreateStore(bogusAdd, bogusVar1);
    Builder.CreateBr(bogusJoin);
    
    // Fill bogus false block with different meaningless operations
    Builder.SetInsertPoint(bogusFalse);
    Value *bogusVar2 = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "bogus_var2");
    Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 17), bogusVar2);
    Value *bogusLoad2 = Builder.CreateLoad(Type::getInt32Ty(Ctx), bogusVar2, "bogus_load2");
    Value *bogusMul = Builder.CreateMul(bogusLoad2, ConstantInt::get(Type::getInt32Ty(Ctx), 3), "bogus_mul");
    Builder.CreateStore(bogusMul, bogusVar2);
    Builder.CreateBr(bogusJoin);
    
    // Bogus join block - continue with original flow
    Builder.SetInsertPoint(bogusJoin);
    
    // Move the rest of the original block after our insertion point to the join block
    std::vector<Instruction*> instructionsToMove;
    Instruction *startFrom = insertPoint->getNextNode();
    
    while (startFrom && startFrom != BB.getTerminator()) {
        instructionsToMove.push_back(startFrom);
        startFrom = startFrom->getNextNode();
    }
    
    // Move instructions to bogus join block
    for (Instruction *I : instructionsToMove) {
        I->moveAfter(bogusJoin->getTerminator() ? 
                     bogusJoin->getTerminator()->getPrevNode() : 
                     &bogusJoin->back());
    }
    
    // Move the original terminator to bogus join block
    if (BB.getTerminator()) {
        Instruction *terminator = BB.getTerminator();
        terminator->moveAfter(&bogusJoin->back());
    }
    
    // Add branch from bogus join to continue normal execution
    Builder.SetInsertPoint(bogusJoin);
    if (!bogusJoin->getTerminator()) {
        Builder.CreateUnreachable(); // Fallback if no terminator was moved
    }
    
    return true;
}

} // namespace h5x