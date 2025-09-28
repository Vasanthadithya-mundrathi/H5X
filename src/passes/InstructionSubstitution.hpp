#ifndef H5X_INSTRUCTION_SUBSTITUTION_HPP
#define H5X_INSTRUCTION_SUBSTITUTION_HPP

#ifdef USE_MOCK_LLVM
// Mock implementation when LLVM is not available
namespace h5x {
class InstructionSubstitutionPass {
public:
    bool run();
};
} // namespace h5x
#else
// Real LLVM implementation when available
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"

namespace h5x {
class InstructionSubstitutionPass : public llvm::PassInfoMixin<InstructionSubstitutionPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);
};
} // namespace h5x
#endif

#endif // H5X_INSTRUCTION_SUBSTITUTION_HPP