#ifndef H5X_ANTI_ANALYSIS_PASS_HPP
#define H5X_ANTI_ANALYSIS_PASS_HPP

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"

namespace h5x {

class AntiAnalysisPass : public llvm::PassInfoMixin<AntiAnalysisPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);

private:
    bool obfuscateFunctionNames(llvm::Module &M);
    bool addJunkInstructions(llvm::Module &M);
    bool addJunkAfterInstruction(llvm::Instruction &I);
    bool addFakeJumps(llvm::Module &M);
    bool addFakeJumpToBlock(llvm::BasicBlock &BB);
    bool removeDebugInfo(llvm::Module &M);
};

} // namespace h5x

#endif // H5X_ANTI_ANALYSIS_PASS_HPP