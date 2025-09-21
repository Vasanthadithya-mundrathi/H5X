#ifndef H5X_BOGUS_CONTROL_FLOW_HPP
#define H5X_BOGUS_CONTROL_FLOW_HPP

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"

namespace h5x {

class BogusControlFlowPass : public llvm::PassInfoMixin<BogusControlFlowPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);
};

} // namespace h5x

#endif // H5X_BOGUS_CONTROL_FLOW_HPP