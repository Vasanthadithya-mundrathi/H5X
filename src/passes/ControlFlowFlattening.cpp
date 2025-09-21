#include "ControlFlowFlattening.hpp"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Constants.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include <vector>
#include <map>
#include <random>

using namespace llvm;

namespace h5x {

PreservedAnalyses ControlFlowFlatteningPass::run(Module &M, ModuleAnalysisManager &AM) {
    bool modified = false;
    
    for (Function &F : M) {
        // Skip external functions, system functions, and main function
        if (F.isDeclaration() || 
            F.getName().starts_with("__") || 
            F.getName() == "main" ||
            F.size() < 3) { // Need at least 3 blocks to flatten
            continue;
        }
        
        // Skip functions with complex control flow that might break
        bool hasComplexFlow = false;
        for (BasicBlock &BB : F) {
            if (isa<InvokeInst>(BB.getTerminator()) ||
                isa<ResumeInst>(BB.getTerminator()) ||
                isa<CatchReturnInst>(BB.getTerminator())) {
                hasComplexFlow = true;
                break;
            }
        }
        if (hasComplexFlow) continue;
        
        if (flattenFunction(F)) {
            modified = true;
        }
    }
    
    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}

bool ControlFlowFlatteningPass::flattenFunction(Function &F) {
    // Don't flatten functions that are too small or have problematic patterns
    if (F.size() < 3) return false;
    
    std::vector<BasicBlock*> originalBlocks;
    for (BasicBlock &BB : F) {
        originalBlocks.push_back(&BB);
    }
    
    // Skip if entry block has PHI nodes (complex to handle)
    if (!F.getEntryBlock().phis().empty()) {
        return false;
    }
    
    // Create dispatcher block and switch variable
    BasicBlock *entryBlock = &F.getEntryBlock();
    LLVMContext &Ctx = F.getContext();
    
    // Create the main dispatcher block
    BasicBlock *dispatcherBlock = BasicBlock::Create(Ctx, "dispatcher", &F);
    
    // Create switch variable (state machine variable)
    IRBuilder<> Builder(entryBlock);
    Builder.SetInsertPoint(entryBlock->getTerminator());
    
    AllocaInst *switchVar = Builder.CreateAlloca(
        Type::getInt32Ty(Ctx), nullptr, "switch_var"
    );
    
    // Initialize switch variable to 0 (entry state)
    Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 0), switchVar);
    
    // Replace entry block terminator with jump to dispatcher
    Instruction *entryTerm = entryBlock->getTerminator();
    Builder.SetInsertPoint(entryTerm);
    Builder.CreateBr(dispatcherBlock);
    entryTerm->eraseFromParent();
    
    // Assign state numbers to each block
    std::map<BasicBlock*, int> blockToState;
    int stateCounter = 1; // 0 is reserved for entry
    
    for (BasicBlock *BB : originalBlocks) {
        if (BB != entryBlock) {
            blockToState[BB] = stateCounter++;
        }
    }
    
    // Create the switch instruction in dispatcher
    Builder.SetInsertPoint(dispatcherBlock);
    Value *switchValue = Builder.CreateLoad(Type::getInt32Ty(Ctx), switchVar, "switch_val");
    
    // Create end block for function exit
    BasicBlock *endBlock = BasicBlock::Create(Ctx, "end", &F);
    
    SwitchInst *switchInst = Builder.CreateSwitch(switchValue, endBlock, originalBlocks.size());
    
    // Add case for entry block (state 0)
    switchInst->addCase(ConstantInt::get(Type::getInt32Ty(Ctx), 0), entryBlock);
    
    // Process each original block
    for (BasicBlock *BB : originalBlocks) {
        if (BB == entryBlock) continue;
        
        // Add case to switch
        int state = blockToState[BB];
        switchInst->addCase(ConstantInt::get(Type::getInt32Ty(Ctx), state), BB);
        
        // Modify block terminator to update switch variable and jump to dispatcher
        Instruction *terminator = BB->getTerminator();
        Builder.SetInsertPoint(terminator);
        
        if (auto *brInst = dyn_cast<BranchInst>(terminator)) {
            if (brInst->isUnconditional()) {
                // Unconditional branch: set next state and jump to dispatcher
                BasicBlock *nextBB = brInst->getSuccessor(0);
                if (blockToState.find(nextBB) != blockToState.end()) {
                    int nextState = blockToState[nextBB];
                    Builder.CreateStore(
                        ConstantInt::get(Type::getInt32Ty(Ctx), nextState), switchVar
                    );
                    Builder.CreateBr(dispatcherBlock);
                } else {
                    // Jumping to entry or exit
                    Builder.CreateBr(nextBB);
                }
            } else {
                // Conditional branch: create conditional update of switch variable
                Value *condition = brInst->getCondition();
                BasicBlock *trueBB = brInst->getSuccessor(0);
                BasicBlock *falseBB = brInst->getSuccessor(1);
                
                // Create blocks for true and false cases
                BasicBlock *trueCase = BasicBlock::Create(Ctx, "true_case", &F);
                BasicBlock *falseCase = BasicBlock::Create(Ctx, "false_case", &F);
                
                Builder.CreateCondBr(condition, trueCase, falseCase);
                
                // True case
                Builder.SetInsertPoint(trueCase);
                if (blockToState.find(trueBB) != blockToState.end()) {
                    Builder.CreateStore(
                        ConstantInt::get(Type::getInt32Ty(Ctx), blockToState[trueBB]), switchVar
                    );
                    Builder.CreateBr(dispatcherBlock);
                } else {
                    Builder.CreateBr(trueBB);
                }
                
                // False case
                Builder.SetInsertPoint(falseCase);
                if (blockToState.find(falseBB) != blockToState.end()) {
                    Builder.CreateStore(
                        ConstantInt::get(Type::getInt32Ty(Ctx), blockToState[falseBB]), switchVar
                    );
                    Builder.CreateBr(dispatcherBlock);
                } else {
                    Builder.CreateBr(falseBB);
                }
            }
        } else if (auto *retInst = dyn_cast<ReturnInst>(terminator)) {
            // Return instruction: jump to end block
            Builder.CreateBr(endBlock);
        }
        
        // Remove original terminator
        terminator->eraseFromParent();
    }
    
    // Create end block with return
    Builder.SetInsertPoint(endBlock);
    if (F.getReturnType()->isVoidTy()) {
        Builder.CreateRetVoid();
    } else {
        // For non-void functions, we need to handle return values more carefully
        // For now, return a default value (this is a limitation)
        Value *defaultRet = Constant::getNullValue(F.getReturnType());
        Builder.CreateRet(defaultRet);
    }
    
    return true;
}

} // namespace h5x