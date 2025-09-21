#ifndef H5X_STRING_OBFUSCATION_HPP
#define H5X_STRING_OBFUSCATION_HPP

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"

namespace h5x {

class StringObfuscationPass : public llvm::PassInfoMixin<StringObfuscationPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);
};

} // namespace h5x

#endif // H5X_STRING_OBFUSCATION_HPP