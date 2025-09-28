// Test program with known string characteristics for validation
// Contains exactly 8 string literals that should be obfuscated

#include <iostream>
#include <string>

int main() {
    std::string message1 = "Hello World!";
    std::string message2 = "This is a test string";
    std::string message3 = "String obfuscation test";
    std::string message4 = "H5X validation";
    std::string message5 = "Obfuscation system";
    std::string message6 = "Security analysis";
    std::string message7 = "Code protection";
    std::string message8 = "Validation complete";

    std::cout << message1 << std::endl;
    std::cout << message2 << std::endl;
    std::cout << message3 << std::endl;
    std::cout << message4 << std::endl;
    std::cout << message5 << std::endl;
    std::cout << message6 << std::endl;
    std::cout << message7 << std::endl;
    std::cout << message8 << std::endl;

    return 0;
}