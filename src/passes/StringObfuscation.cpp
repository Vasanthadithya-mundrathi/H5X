#include "StringObfuscation.hpp"
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

PreservedAnalyses StringObfuscationPass::run(Module &M, ModuleAnalysisManager &AM) {
    bool modified = false;
    std::vector<GlobalVariable*> stringGlobals;
    
    // Collect all string constants
    for (GlobalVariable &GV : M.globals()) {
        if (GV.hasInitializer() && GV.isConstant()) {
            if (auto *CA = dyn_cast<ConstantDataArray>(GV.getInitializer())) {
                if (CA->isCString() && CA->getAsCString().size() > 1) {
                    stringGlobals.push_back(&GV);
                }
            }
        }
    }
    
    // Obfuscate each string
    for (GlobalVariable *GV : stringGlobals) {
        if (obfuscateString(*GV, M)) {
            modified = true;
        }
    }
    
    return modified ? PreservedAnalyses::none() : PreservedAnalyses::all();
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
    
    // Create encrypted string
    std::vector<uint8_t> encryptedData;
    for (char c : originalStr) {
        encryptedData.push_back(static_cast<uint8_t>(c) ^ xorKey);
    }
    encryptedData.push_back(0); // Null terminator
    
    // Create new global for encrypted data  
    ArrayType *encryptedType = ArrayType::get(Type::getInt8Ty(Ctx), encryptedData.size());
    Constant *encryptedInit = ConstantDataArray::get(Ctx, encryptedData);
    
    GlobalVariable *encryptedGV = new GlobalVariable(
        M, encryptedType, true, GlobalValue::PrivateLinkage,
        encryptedInit, GV.getName() + "_enc"
    );
    
    // Create decryption function
    Function *decryptFunc = createDecryptFunction(M, xorKey);
    
    // Replace all uses of the original string with calls to decrypt function
    std::vector<User*> users(GV.users().begin(), GV.users().end());
    
    for (User *U : users) {
        if (auto *I = dyn_cast<Instruction>(U)) {
            IRBuilder<> Builder(I);
            
            // Create GEP to encrypted string
            Value *indices[] = {
                ConstantInt::get(Type::getInt32Ty(Ctx), 0),
                ConstantInt::get(Type::getInt32Ty(Ctx), 0)
            };
            Value *encryptedPtr = Builder.CreateInBoundsGEP(
                encryptedType, encryptedGV, indices, "enc_ptr"
            );
            
            // Call decrypt function
            Value *decryptedStr = Builder.CreateCall(decryptFunc, {encryptedPtr}, "decrypted");
            
            // Replace the use
            I->replaceUsesOfWith(&GV, decryptedStr);
        }
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
    Type* charPtrTy = PointerType::get(Type::getInt8Ty(Ctx), 0);
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
    
    // Allocate buffer for decrypted string (simple approach: assume max 1024 chars)
    Value *bufferSize = ConstantInt::get(Type::getInt32Ty(Ctx), 1024);
    Value *decryptedBuffer = Builder.CreateAlloca(Type::getInt8Ty(Ctx), bufferSize, "buffer");
    
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
    
    // Check for null terminator
    Value *isNull = Builder.CreateICmpEQ(encChar, ConstantInt::get(Type::getInt8Ty(Ctx), 0), "is_null");
    
    // Decrypt character
    Value *decChar = Builder.CreateXor(encChar, ConstantInt::get(Type::getInt8Ty(Ctx), xorKey), "dec_char");
    
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