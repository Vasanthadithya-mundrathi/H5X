#include <iostream>
#include <string>
#include <vector>
#include <cmath>

// Test strings for obfuscation
const std::string SECRET_API_KEY = "sk-1234567890abcdef";
const std::string DATABASE_URL = "https://db.example.com/secure";
const std::string PASSWORD_SALT = "mysecretSALT123!";

// Simple function for instruction substitution testing
int simple_math(int a, int b) {
    int sum = a + b;          // Should be obfuscated: a + b -> (a^b) + 2*(a&b)
    int diff = a - b;         // Should be obfuscated: a - b -> (a^b) - 2*(~a&b)
    int product = a * 4;      // Should be obfuscated: a * 4 -> a << 2
    return sum + diff + product;
}

// Function with control flow for flattening testing
int control_flow_test(int x) {
    if (x > 10) {
        if (x > 20) {
            return x * 2;
        } else {
            return x + 5;
        }
    } else {
        if (x < 0) {
            return 0;
        } else {
            return x - 1;
        }
    }
}

// Function with loops for bogus control flow
void loop_function() {
    for (int i = 0; i < 5; i++) {
        std::cout << "Processing item " << i << std::endl;
        
        if (i % 2 == 0) {
            std::cout << "Even number: " << i << std::endl;
        } else {
            std::cout << "Odd number: " << i << std::endl;
        }
    }
}

// Financial calculation function (sensitive algorithm)
double calculate_interest(double principal, double rate, int years) {
    std::cout << "Calculating interest for principal: $" << principal << std::endl;
    std::cout << "Annual rate: " << rate << "%" << std::endl;
    std::cout << "Years: " << years << std::endl;
    
    double compound_interest = principal * pow((1 + rate/100), years);
    return compound_interest - principal;
}

int main() {
    std::cout << "=== H5X Obfuscation Test Program ===" << std::endl;
    std::cout << "This program tests various obfuscation techniques." << std::endl;
    
    // Test string constants (should be obfuscated)
    std::cout << "API Key: " << SECRET_API_KEY << std::endl;
    std::cout << "Database: " << DATABASE_URL << std::endl;
    std::cout << "Salt: " << PASSWORD_SALT << std::endl;
    
    // Test arithmetic operations
    std::cout << "\n--- Testing Arithmetic Operations ---" << std::endl;
    int result1 = simple_math(15, 7);
    std::cout << "Math result: " << result1 << std::endl;
    
    // Test control flow
    std::cout << "\n--- Testing Control Flow ---" << std::endl;
    std::cout << "Control flow test(25): " << control_flow_test(25) << std::endl;
    std::cout << "Control flow test(5): " << control_flow_test(5) << std::endl;
    std::cout << "Control flow test(-3): " << control_flow_test(-3) << std::endl;
    
    // Test loops
    std::cout << "\n--- Testing Loop Structures ---" << std::endl;
    loop_function();
    
    // Test financial calculation
    std::cout << "\n--- Testing Financial Calculations ---" << std::endl;
    double interest = calculate_interest(1000.0, 5.0, 3);
    std::cout << "Interest earned: $" << interest << std::endl;
    
    // Test vector operations
    std::cout << "\n--- Testing Data Structures ---" << std::endl;
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = 0;
    for (int num : numbers) {
        sum += num;
    }
    std::cout << "Sum of numbers: " << sum << std::endl;
    
    std::cout << "\n=== Test Complete ===" << std::endl;
    return 0;
}
