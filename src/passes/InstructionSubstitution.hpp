#ifndef H5X_INSTRUCTION_SUBSTITUTION_HPP
#define H5X_INSTRUCTION_SUBSTITUTION_HPP

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"

namespace h5x {

class InstructionSubstitutionPass : public llvm::PassInfoMixin<InstructionSubstitutionPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);
};

} // namespace h5x

#endif // H5X_INSTRUCTION_SUBSTITUTION_HPP