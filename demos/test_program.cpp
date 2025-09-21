#include <iostream>
#include <string>

// Simple function to demonstrate obfuscation
int calculate_sum(int a, int b) {
    return a + b;
}

// Function with string literals
void print_message(const std::string& name) {
    std::cout << "Hello, " << name << "!" << std::endl;
    std::cout << "This is a test program for H5X obfuscation." << std::endl;
}

int main() {
    int x = 10;
    int y = 20;
    int result = calculate_sum(x, y);
    
    std::cout << "Sum of " << x << " and " << y << " is: " << result << std::endl;
    
    print_message("H5X User");
    
    // Conditional logic for control flow
    if (result > 25) {
        std::cout << "Result is greater than 25" << std::endl;
    } else {
        std::cout << "Result is 25 or less" << std::endl;
    }
    
    return 0;
}