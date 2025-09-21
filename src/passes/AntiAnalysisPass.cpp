#include "AntiAnalysisPass.hpp"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/Support/raw_ostream.h"
#include <vector>
#include <string>
#include <random>

using namespace llvm;

namespace h5x {

PreservedAnalyses AntiAnalysisPass::run(Module &M, ModuleAnalysisManager &AM) {
    bool modified = false;
    
    // Apply various anti-analysis techniques
    if (obfuscateFunctionNames(M)) modified = true;
    if (addJunkInstructions(M)) modified = true;
    if (addFakeJumps(M)) modified = true;
    if (removeDebugInfo(M)) modified = true;
    
    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}

bool AntiAnalysisPass::obfuscateFunctionNames(Module &M) {
    bool modified = false;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 35);
    
    auto generateRandomName = [&]() -> std::string {
        std::string chars = "abcdefghijklmnopqrstuvwxyz0123456789";
        std::string result = "h5x_";
        for (int i = 0; i < 8; ++i) {
            result += chars[dis(gen)];
        }
        return result;
    };
    
    for (Function &F : M) {
        // Don't rename main, system functions, or externally visible functions
        if (F.getName() == "main" || 
            F.getName().starts_with("__") ||
            F.getName().starts_with("llvm.") ||
            F.hasExternalLinkage()) {
            continue;
        }
        
        if (!F.isDeclaration()) {
            F.setName(generateRandomName());
            modified = true;
        }
    }
    
    return modified;
}

bool AntiAnalysisPass::addJunkInstructions(Module &M) {
    bool modified = false;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 1.0);
    
    for (Function &F : M) {
        if (F.isDeclaration()) continue;
        
        std::vector<Instruction*> insertionPoints;
        for (BasicBlock &BB : F) {
            for (Instruction &I : BB) {
                if (!I.isTerminator() && dis(gen) < 0.1) { // 10% chance
                    insertionPoints.push_back(&I);
                }
            }
        }
        
        for (Instruction *insertPoint : insertionPoints) {
            if (addJunkAfterInstruction(*insertPoint)) {
                modified = true;
            }
        }
    }
    
    return modified;
}

bool AntiAnalysisPass::addJunkAfterInstruction(Instruction &I) {
    LLVMContext &Ctx = I.getContext();
    IRBuilder<> Builder(I.getNextNode());
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> typeDis(0, 3);
    std::uniform_int_distribution<> valueDis(1, 1000);
    
    switch (typeDis(gen)) {
    case 0: {
        // Add meaningless arithmetic
        Value *val1 = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
        Value *val2 = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
        Value *temp = Builder.CreateAdd(val1, val2, "junk_add");
        Value *temp2 = Builder.CreateMul(temp, ConstantInt::get(Type::getInt32Ty(Ctx), 1), "junk_mul");
        // Result is not used, will be optimized away by dead code elimination
        (void)temp2; // Suppress unused variable warning
        break;
    }
    case 1: {
        // Add stack allocation and deallocation
        Value *junkVar = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "junk_var");
        Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen)), junkVar);
        Value *junkLoad = Builder.CreateLoad(Type::getInt32Ty(Ctx), junkVar, "junk_load");
        (void)junkLoad; // Suppress unused variable warning
        break;
    }
    case 2: {
        // Add bitwise operations
        Value *val = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
        Value *shifted = Builder.CreateShl(val, 1, "junk_shl");
        Value *result = Builder.CreateLShr(shifted, 1, "junk_lshr");
        (void)result; // Suppress unused variable warning
        break;
    }
    case 3: {
        // Add comparison operations
        Value *val1 = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
        Value *val2 = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
        Value *cmp = Builder.CreateICmpEQ(val1, val2, "junk_cmp");
        (void)cmp; // Suppress unused variable warning
        break;
    }
    }
    
    return true;
}

bool AntiAnalysisPass::addFakeJumps(Module &M) {
    bool modified = false;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 1.0);
    
    for (Function &F : M) {
        if (F.isDeclaration() || F.size() < 2) continue;
        
        std::vector<BasicBlock*> blocks;
        for (BasicBlock &BB : F) {
            blocks.push_back(&BB);
        }
        
        for (BasicBlock *BB : blocks) {
            if (dis(gen) < 0.15) { // 15% chance to add fake jump
                if (addFakeJumpToBlock(*BB)) {
                    modified = true;
                }
            }
        }
    }
    
    return modified;
}

bool AntiAnalysisPass::addFakeJumpToBlock(BasicBlock &BB) {
    // Don't modify blocks with complex terminators
    if (isa<InvokeInst>(BB.getTerminator()) ||
        isa<SwitchInst>(BB.getTerminator()) ||
        !BB.phis().empty()) {
        return false;
    }
    
    LLVMContext &Ctx = BB.getContext();
    Function *F = BB.getParent();
    
    // Find insertion point before terminator
    Instruction *terminator = BB.getTerminator();
    if (!terminator) return false;
    
    IRBuilder<> Builder(terminator);
    
    // Create an always-false condition using opaque predicates
    // (x & 1) == 2 is always false since x & 1 can only be 0 or 1
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> valueDis(2, 100);
    
    Value *x = ConstantInt::get(Type::getInt32Ty(Ctx), valueDis(gen));
    Value *masked = Builder.CreateAnd(x, ConstantInt::get(Type::getInt32Ty(Ctx), 1), "fake_mask");
    Value *alwaysFalse = Builder.CreateICmpEQ(masked, ConstantInt::get(Type::getInt32Ty(Ctx), 2), "fake_cond");
    
    // Create fake target block
    BasicBlock *fakeBlock = BasicBlock::Create(Ctx, "fake_block", F);
    BasicBlock *realContinue = BasicBlock::Create(Ctx, "real_continue", F);
    
    // Add fake conditional branch
    Builder.CreateCondBr(alwaysFalse, fakeBlock, realContinue);
    
    // Fill fake block with junk and unreachable
    Builder.SetInsertPoint(fakeBlock);
    Value *junkVar = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "fake_var");
    Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 0xDEADBEEF), junkVar);
    Value *junkLoad = Builder.CreateLoad(Type::getInt32Ty(Ctx), junkVar, "fake_load");
    Builder.CreateAdd(junkLoad, ConstantInt::get(Type::getInt32Ty(Ctx), 1), "fake_add");
    Builder.CreateUnreachable();
    
    // Move original terminator to real continue block
    Builder.SetInsertPoint(realContinue);
    terminator->moveAfter(&realContinue->back());
    
    return true;
}

bool AntiAnalysisPass::removeDebugInfo(Module &M) {
    bool modified = false;
    
    // Remove debug info from functions
    for (Function &F : M) {
        if (F.hasMetadata()) {
            F.setSubprogram(nullptr);
            modified = true;
        }
        
        for (BasicBlock &BB : F) {
            for (Instruction &I : BB) {
                if (I.hasMetadata()) {
                    I.setDebugLoc(DebugLoc());
                    modified = true;
                }
            }
        }
    }
    
    // Remove named metadata related to debug info
    std::vector<NamedMDNode*> toRemove;
    for (NamedMDNode &NMD : M.named_metadata()) {
        if (NMD.getName().starts_with("llvm.dbg") ||
            NMD.getName().starts_with("llvm.module.flags")) {
            toRemove.push_back(&NMD);
        }
    }
    
    for (NamedMDNode *NMD : toRemove) {
        NMD->eraseFromParent();
        modified = true;
    }
    
    return modified;
}

} // namespace h5x