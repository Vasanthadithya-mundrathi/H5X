#ifndef H5X_STRING_OBFUSCATION_HPP
#define H5X_STRING_OBFUSCATION_HPP

// Simplified header without LLVM includes to avoid compatibility issues
#include <cstdint>

namespace llvm {
class Module;
class GlobalVariable;
class Function;
class LLVMContext;
} // namespace llvm

namespace h5x {

class StringObfuscationPass {
public:
    // Simplified interface that works with LLVM 21.1.1
    bool run(llvm::Module &M);

private:
    bool obfuscateString(llvm::GlobalVariable &GV, llvm::Module &M);
    bool simpleXorObfuscate(llvm::GlobalVariable &GV, llvm::Module &M);
    llvm::Function* createDecryptFunction(llvm::Module &M, uint8_t xorKey);
};

} // namespace h5x

#endif // H5X_STRING_OBFUSCATION_HPP
