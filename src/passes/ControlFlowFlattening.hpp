#ifndef H5X_CONTROL_FLOW_FLATTENING_HPP
#define H5X_CONTROL_FLOW_FLATTENING_HPP

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"

namespace h5x {

class ControlFlowFlatteningPass : public llvm::PassInfoMixin<ControlFlowFlatteningPass> {
public:
    llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);
    
private:
    bool flattenFunction(llvm::Function &F);
};

} // namespace h5x

#endif // H5X_CONTROL_FLOW_FLATTENING_HPP