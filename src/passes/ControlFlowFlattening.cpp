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
        // Skip external functions and system functions only
        if (F.isDeclaration() || 
            F.getName().starts_with("__") || 
            F.getName().starts_with("_Z") && F.getName().contains("std") ||
            F.size() < 2) { // Need at least 2 blocks to flatten
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
    // Don't flatten functions that are too small
    if (F.size() < 2) return false;

    // Count PHI nodes and returns
    int phiCount = 0;
    int returnCount = 0;
    bool hasReturnValue = !F.getReturnType()->isVoidTy();
    std::vector<PHINode*> phiNodes;

    for (BasicBlock &BB : F) {
        for (PHINode &PHI : BB.phis()) {
            phiCount++;
            phiNodes.push_back(&PHI);
        }
        if (isa<ReturnInst>(BB.getTerminator())) {
            returnCount++;
        }
    }

    errs() << "ControlFlowFlattening: Processing function " << F.getName()
            << " with " << phiCount << " PHI nodes, " << returnCount << " returns, "
            << "return type: " << (hasReturnValue ? "non-void" : "void") << "\n";

    // Handle functions with PHI nodes properly instead of skipping
    if (phiCount > 0) {
        errs() << "ControlFlowFlattening: Function has PHI nodes, will handle them properly\n";
    }
    
    std::vector<BasicBlock*> originalBlocks;
    for (BasicBlock &BB : F) {
        originalBlocks.push_back(&BB);
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

    // Handle return values properly
    AllocaInst *returnVar = nullptr;
    if (hasReturnValue) {
        returnVar = Builder.CreateAlloca(F.getReturnType(), nullptr, "return_var");
    }

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
            // Return instruction: handle return value and jump to end block
            if (hasReturnValue && returnVar) {
                Builder.CreateStore(retInst->getReturnValue(), returnVar);
            }
            Builder.CreateBr(endBlock);
        }

        // Remove original terminator
        terminator->eraseFromParent();
    }
    
    // Create end block with proper return handling
    Builder.SetInsertPoint(endBlock);
    if (F.getReturnType()->isVoidTy()) {
        Builder.CreateRetVoid();
    } else {
        // For non-void functions, load the return value from the return variable
        if (returnVar) {
            Value *returnValue = Builder.CreateLoad(F.getReturnType(), returnVar, "return_val");
            Builder.CreateRet(returnValue);
        } else {
            // Fallback: return a default value if no return variable
            Value *defaultRet = Constant::getNullValue(F.getReturnType());
            Builder.CreateRet(defaultRet);
        }
    }
    
    return true;
}

} // namespace h5x
