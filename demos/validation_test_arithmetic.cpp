// Test program with known arithmetic operations for validation
// Contains various arithmetic operations that should be substituted

#include <iostream>

int main() {
    int a = 10;
    int b = 20;
    int c = 30;

    // Addition operations
    int sum1 = a + b;
    int sum2 = b + c;
    int sum3 = a + c;

    // Subtraction operations
    int diff1 = b - a;
    int diff2 = c - b;
    int diff3 = c - a;

    // Multiplication operations
    int prod1 = a * b;
    int prod2 = b * c;
    int prod3 = a * c;

    // Division operations
    int quot1 = b / a;
    int quot2 = c / b;
    int quot3 = c / a;

    // Modulo operations
    int mod1 = b % a;
    int mod2 = c % b;
    int mod3 = c % a;

    // Complex expressions
    int complex1 = (a + b) * c;
    int complex2 = a * (b - c);
    int complex3 = (a + b) * (c - a);
    int complex4 = a * b + c * a;
    int complex5 = (a + b + c) * 2;

    std::cout << "Sum1: " << sum1 << std::endl;
    std::cout << "Sum2: " << sum2 << std::endl;
    std::cout << "Sum3: " << sum3 << std::endl;
    std::cout << "Diff1: " << diff1 << std::endl;
    std::cout << "Diff2: " << diff2 << std::endl;
    std::cout << "Diff3: " << diff3 << std::endl;
    std::cout << "Prod1: " << prod1 << std::endl;
    std::cout << "Prod2: " << prod2 << std::endl;
    std::cout << "Prod3: " << prod3 << std::endl;
    std::cout << "Quot1: " << quot1 << std::endl;
    std::cout << "Quot2: " << quot2 << std::endl;
    std::cout << "Quot3: " << quot3 << std::endl;
    std::cout << "Mod1: " << mod1 << std::endl;
    std::cout << "Mod2: " << mod2 << std::endl;
    std::cout << "Mod3: " << mod3 << std::endl;
    std::cout << "Complex1: " << complex1 << std::endl;
    std::cout << "Complex2: " << complex2 << std::endl;
    std::cout << "Complex3: " << complex3 << std::endl;
    std::cout << "Complex4: " << complex4 << std::endl;
    std::cout << "Complex5: " << complex5 << std::endl;

    return 0;
}