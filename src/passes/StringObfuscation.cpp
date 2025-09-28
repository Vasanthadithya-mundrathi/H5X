#include "StringObfuscation.hpp"

// Working LLVM includes for LLVM 21.1.1 on M1 Mac
#include "llvm/IR/Module.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/Type.h"
#include "llvm/IR/Value.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/Support/raw_ostream.h"
#include <vector>
#include <string>
#include <random>

using namespace llvm;

namespace h5x {

// Working LLVM 21.1.1 compatible pass implementation
bool StringObfuscationPass::run(Module &M) {
    bool modified = false;
    int transformCount = 0;

    errs() << "[DEBUG] StringObfuscation pass starting (M1 Mac compatible)...\n";

    try {
        // Proper string obfuscation with runtime decryption
        for (GlobalVariable &GV : M.globals()) {
            if (GV.hasInitializer() && GV.isConstant() && !GV.getName().starts_with("llvm.")) {
                if (auto *CDA = dyn_cast<ConstantDataArray>(GV.getInitializer())) {
                    if (CDA->isCString()) {
                        std::string originalStr = CDA->getAsCString().str();

                        errs() << "[DEBUG] Found string: \"" << originalStr << "\"\n";

                        // Only obfuscate reasonable length strings
                        if (!originalStr.empty() && originalStr.length() < 1000 && originalStr.length() > 2) {
                            if (obfuscateString(GV, M)) {
                                modified = true;
                                transformCount++;
                                errs() << "[DEBUG] Successfully obfuscated string #" << transformCount << "\n";
                            }
                        }
                    }
                }
            }
        }
    } catch (const std::exception& e) {
        errs() << "[ERROR] Exception in StringObfuscationPass: " << e.what() << "\n";
        return false;
    }

    errs() << "[DEBUG] StringObfuscation pass completed. Modified=" << modified
           << " Transforms=" << transformCount << "\n";

    return modified;
}

bool StringObfuscationPass::obfuscateString(GlobalVariable &GV, Module &M) {
    auto *CA = dyn_cast<ConstantDataArray>(GV.getInitializer());
    if (!CA || !CA->isCString()) return false;
    
    std::string originalStr = CA->getAsCString().str();
    if (originalStr.empty() || originalStr.size() < 2) return false;
    
    LLVMContext &Ctx = M.getContext();
    
    // Generate XOR key
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> keyDis(1, 255);
    uint8_t xorKey = keyDis(gen);
    
    // Create encrypted string (WITHOUT null terminator to hide it better)
    std::vector<uint8_t> encryptedData;
    for (size_t i = 0; i < originalStr.length(); i++) {
        encryptedData.push_back(static_cast<uint8_t>(originalStr[i]) ^ xorKey);
    }
    
    // Create new global for encrypted data  
    ArrayType *encryptedType = ArrayType::get(Type::getInt8Ty(Ctx), encryptedData.size());
    Constant *encryptedInit = ConstantDataArray::get(Ctx, encryptedData);
    
    GlobalVariable *encryptedGV = new GlobalVariable(
        M, encryptedType, true, GlobalValue::PrivateLinkage,
        encryptedInit, GV.getName() + "_enc"
    );
    
    // Store the original string length as a separate global
    GlobalVariable *lengthGV = new GlobalVariable(
        M, Type::getInt32Ty(Ctx), true, GlobalValue::PrivateLinkage,
        ConstantInt::get(Type::getInt32Ty(Ctx), originalStr.length()),
        GV.getName() + "_len"
    );
    
    // Replace ALL uses of the original global variable
    std::vector<Use*> usesToReplace;
    for (Use &U : GV.uses()) {
        usesToReplace.push_back(&U);
    }
    
    for (Use *U : usesToReplace) {
        User *user = U->getUser();
        
        // Find the function containing this use
        Function *containingFunc = nullptr;
        if (auto *I = dyn_cast<Instruction>(user)) {
            containingFunc = I->getFunction();
        } else if (auto *CE = dyn_cast<ConstantExpr>(user)) {
            // Find instruction that uses this constant expression
            for (Use &CEU : CE->uses()) {
                if (auto *I = dyn_cast<Instruction>(CEU.getUser())) {
                    containingFunc = I->getFunction();
                    break;
                }
            }
        }
        
        if (!containingFunc) continue;
        
        // Insert decryption after all phi nodes in the entry block
        BasicBlock &entryBB = containingFunc->getEntryBlock();
        Instruction *insertPoint = &entryBB.front();
        // Find first non-phi instruction
        for (Instruction &I : entryBB) {
            if (!isa<PHINode>(I)) {
                insertPoint = &I;
                break;
            }
        }
        IRBuilder<> Builder(insertPoint);
        
        // Create runtime string decryption
        Value *lengthVal = Builder.CreateLoad(Type::getInt32Ty(Ctx), lengthGV, "str_len");

        // Allocate memory for decrypted string (+1 for null terminator)
        Value *sizeWithNull = Builder.CreateAdd(lengthVal, ConstantInt::get(Type::getInt32Ty(Ctx), 1));

        Function *mallocFunc = M.getFunction("malloc");
        if (!mallocFunc) {
            Type* voidPtrTy = PointerType::getUnqual(Ctx);
            FunctionType *mallocType = FunctionType::get(voidPtrTy, {Type::getInt64Ty(Ctx)}, false);
            mallocFunc = Function::Create(mallocType, Function::ExternalLinkage, "malloc", M);
        }

        Value *sizeExt = Builder.CreateZExt(sizeWithNull, Type::getInt64Ty(Ctx));
        Value *decryptedPtr = Builder.CreateCall(mallocFunc, {sizeExt}, "decrypted_str");

        // Create a cleanup block to free the allocated memory
        BasicBlock *cleanupBB = BasicBlock::Create(Ctx, "cleanup", containingFunc);
        
        // Create decryption loop
        Value *indexVar = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "i");
        Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 0), indexVar);
        
        BasicBlock *loopBB = BasicBlock::Create(Ctx, "decrypt_loop", containingFunc);
        BasicBlock *exitBB = BasicBlock::Create(Ctx, "decrypt_exit", containingFunc);
        
        Builder.CreateBr(loopBB);
        
        // Loop body
        Builder.SetInsertPoint(loopBB);
        Value *i = Builder.CreateLoad(Type::getInt32Ty(Ctx), indexVar, "i_val");
        Value *cond = Builder.CreateICmpULT(i, lengthVal, "continue_loop");
        
        BasicBlock *bodyBB = BasicBlock::Create(Ctx, "loop_body", containingFunc);
        Builder.CreateCondBr(cond, bodyBB, exitBB);
        
        // Decrypt character
        Builder.SetInsertPoint(bodyBB);
        Value *encPtr = Builder.CreateInBoundsGEP(encryptedType, encryptedGV, {ConstantInt::get(Type::getInt32Ty(Ctx), 0), i});
        Value *encChar = Builder.CreateLoad(Type::getInt8Ty(Ctx), encPtr, "enc_char");
        Value *decChar = Builder.CreateXor(encChar, ConstantInt::get(Type::getInt8Ty(Ctx), xorKey), "dec_char");
        
        Value *decPtr = Builder.CreateInBoundsGEP(Type::getInt8Ty(Ctx), decryptedPtr, i);
        Builder.CreateStore(decChar, decPtr);
        
        // Increment and continue
        Value *nextI = Builder.CreateAdd(i, ConstantInt::get(Type::getInt32Ty(Ctx), 1));
        Builder.CreateStore(nextI, indexVar);
        Builder.CreateBr(loopBB);
        
        // Add null terminator
        Builder.SetInsertPoint(exitBB);
        Value *nullPtr = Builder.CreateInBoundsGEP(Type::getInt8Ty(Ctx), decryptedPtr, lengthVal);
        Builder.CreateStore(ConstantInt::get(Type::getInt8Ty(Ctx), 0), nullPtr);
        
        // Replace the use with decrypted pointer
        U->set(decryptedPtr);
    }
    
    // Remove the original global if no uses remain
    if (GV.use_empty()) {
        GV.eraseFromParent();
    }
    
    return true;
}

Function* StringObfuscationPass::createDecryptFunction(Module &M, uint8_t xorKey) {
    LLVMContext &Ctx = M.getContext();
    
    // Check if decrypt function already exists
    std::string funcName = "h5x_decrypt_" + std::to_string(xorKey);
    if (Function *existingFunc = M.getFunction(funcName)) {
        return existingFunc;
    }
    
    // Create function type: char* decrypt(char* encrypted)
    Type* charPtrTy = PointerType::get(Ctx, 0);
    FunctionType *funcType = FunctionType::get(
        charPtrTy,
        {charPtrTy},
        false
    );
    
    Function *decryptFunc = Function::Create(
        funcType, Function::InternalLinkage, funcName, M
    );
    
    // Create basic blocks
    BasicBlock *entryBB = BasicBlock::Create(Ctx, "entry", decryptFunc);
    BasicBlock *loopBB = BasicBlock::Create(Ctx, "loop", decryptFunc);
    BasicBlock *exitBB = BasicBlock::Create(Ctx, "exit", decryptFunc);
    
    IRBuilder<> Builder(entryBB);
    
    // Get function argument
    Value *encryptedPtr = decryptFunc->getArg(0);
    
    // Allocate buffer for decrypted string using malloc for heap allocation
    Type* sizeTy = Type::getInt64Ty(Ctx);
    Value *bufferSize = ConstantInt::get(sizeTy, 1024);
    
    // Create malloc declaration if it doesn't exist
    Function *mallocFunc = M.getFunction("malloc");
    if (!mallocFunc) {
        Type* voidPtrTy = PointerType::get(Ctx, 0);
        FunctionType *mallocType = FunctionType::get(voidPtrTy, {sizeTy}, false);
        mallocFunc = Function::Create(mallocType, Function::ExternalLinkage, "malloc", M);
    }
    
    Value *decryptedBuffer = Builder.CreateCall(mallocFunc, {bufferSize}, "buffer");
    
    // Initialize loop variables
    Value *index = Builder.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "index");
    Builder.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 0), index);
    
    Builder.CreateBr(loopBB);
    
    // Loop body
    Builder.SetInsertPoint(loopBB);
    Value *currentIndex = Builder.CreateLoad(Type::getInt32Ty(Ctx), index, "current_idx");
    
    // Load encrypted character
    Value *encCharPtr = Builder.CreateInBoundsGEP(Type::getInt8Ty(Ctx), encryptedPtr, currentIndex, "enc_char_ptr");
    Value *encChar = Builder.CreateLoad(Type::getInt8Ty(Ctx), encCharPtr, "enc_char");
    
    // Check for null terminator (decrypt first, then check)
    Value *decChar = Builder.CreateXor(encChar, ConstantInt::get(Type::getInt8Ty(Ctx), xorKey), "dec_char");
    Value *isNull = Builder.CreateICmpEQ(decChar, ConstantInt::get(Type::getInt8Ty(Ctx), 0), "is_null");
    
    // Store decrypted character
    Value *decCharPtr = Builder.CreateInBoundsGEP(Type::getInt8Ty(Ctx), decryptedBuffer, currentIndex, "dec_char_ptr");
    Builder.CreateStore(decChar, decCharPtr);
    
    // Increment index and continue or exit
    Value *nextIndex = Builder.CreateAdd(currentIndex, ConstantInt::get(Type::getInt32Ty(Ctx), 1), "next_idx");
    Builder.CreateStore(nextIndex, index);
    
    Builder.CreateCondBr(isNull, exitBB, loopBB);
    
    // Exit block
    Builder.SetInsertPoint(exitBB);
    Builder.CreateRet(decryptedBuffer);
    
    return decryptFunc;
}


} // namespace h5x
