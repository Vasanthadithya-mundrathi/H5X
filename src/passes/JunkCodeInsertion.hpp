#ifndef H5X_JUNK_CODE_INSERTION_H
#define H5X_JUNK_CODE_INSERTION_H

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/GlobalVariable.h"
#include <random>

namespace h5x {

class JunkCodeInsertionPass : public llvm::PassInfoMixin<JunkCodeInsertionPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);

private:
    void insertJunkCode(llvm::Function &F, llvm::Module &M);
    llvm::GlobalVariable* getOrCreateJunkGlobal(llvm::Module &M);
    void insertRandomOperations(llvm::IRBuilder<> &Builder, llvm::Value *globalVar);
};

} // namespace h5x

#endif // H5X_JUNK_CODE_INSERTION_H