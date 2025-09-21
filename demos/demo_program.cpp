#include <iostream>
#include <string>
#include <vector>
#include <cmath>
#include <algorithm>

// Global string constants for obfuscation demo
const std::string SECRET_KEY = "MySecretAPIKey123";
const std::string DATABASE_URL = "https://api.example.com/v1/secure";
const std::string PASSWORD_HASH = "sha256:abc123def456";

// Complex algorithm function
double calculate_fibonacci_golden_ratio(int n) {
    if (n <= 1) return n;
    
    std::vector<double> fib(n + 1);
    fib[0] = 0;
    fib[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
    
    // Calculate golden ratio approximation
    if (n > 1) {
        return fib[n] / fib[n-1];
    }
    return 1.0;
}

// Sensitive authentication function
bool authenticate_user(const std::string& username, const std::string& password) {
    // Simulate complex authentication logic
    std::string combined = username + ":" + password + ":" + SECRET_KEY;
    
    // Simple hash simulation (this would be more complex in real code)
    size_t hash = 0;
    for (char c : combined) {
        hash = hash * 31 + c;
    }
    
    // Check against known good hash
    bool authenticated = (hash % 1000 == 42);
    
    if (authenticated) {
        std::cout << "User authenticated successfully!" << std::endl;
        std::cout << "Welcome to the secure system, " << username << std::endl;
        std::cout << "Database connection: " << DATABASE_URL << std::endl;
    } else {
        std::cout << "Authentication failed for user: " << username << std::endl;
        std::cout << "Invalid credentials provided" << std::endl;
    }
    
    return authenticated;
}

// License validation function
bool validate_license(const std::string& license_key) {
    const std::string VALID_PREFIX = "H5X-PRO-";
    const std::string VALID_SUFFIX = "-2025";
    
    if (license_key.length() < 12) {
        std::cout << "License key too short" << std::endl;
        return false;
    }
    
    if (license_key.substr(0, 8) != VALID_PREFIX) {
        std::cout << "Invalid license prefix" << std::endl;
        return false;
    }
    
    if (license_key.substr(license_key.length() - 5) != VALID_SUFFIX) {
        std::cout << "Invalid license suffix" << std::endl;
        return false;
    }
    
    std::cout << "License validation successful!" << std::endl;
    std::cout << "Licensed to: Premium User" << std::endl;
    return true;
}

// Mathematical computation with multiple branches
double complex_calculation(double x, double y, int operation) {
    double result = 0.0;
    
    switch (operation) {
        case 1:
            result = sqrt(x * x + y * y);
            std::cout << "Calculated Euclidean distance: " << result << std::endl;
            break;
        case 2:
            result = pow(x, y);
            std::cout << "Calculated power: " << x << "^" << y << " = " << result << std::endl;
            break;
        case 3:
            if (y != 0) {
                result = x / y;
                std::cout << "Calculated division: " << x << "/" << y << " = " << result << std::endl;
            } else {
                std::cout << "Division by zero error!" << std::endl;
                result = -1;
            }
            break;
        case 4:
            result = log(abs(x)) + log(abs(y));
            std::cout << "Calculated logarithmic sum: " << result << std::endl;
            break;
        default:
            result = x + y;
            std::cout << "Default addition: " << x << " + " << y << " = " << result << std::endl;
    }
    
    return result;
}

// Main function with multiple code paths
int main() {
    std::cout << "=== H5X Obfuscation Demo Program ===" << std::endl;
    std::cout << "Testing advanced obfuscation techniques..." << std::endl;
    
    // Test authentication
    std::string username = "admin";
    std::string password = "secure123";
    
    if (authenticate_user(username, password)) {
        std::cout << "\n--- Access Granted ---" << std::endl;
        
        // Test license validation
        std::string license = "H5X-PRO-ABC-2025";
        if (validate_license(license)) {
            
            // Complex mathematical operations
            std::cout << "\n--- Mathematical Operations ---" << std::endl;
            
            double golden_ratio = calculate_fibonacci_golden_ratio(20);
            std::cout << "Fibonacci golden ratio approximation: " << golden_ratio << std::endl;
            
            // Multiple calculation paths
            for (int i = 1; i <= 4; i++) {
                double result = complex_calculation(10.5, 3.2, i);
                
                if (result > 100) {
                    std::cout << "Result is very large: " << result << std::endl;
                } else if (result > 10) {
                    std::cout << "Result is moderate: " << result << std::endl;
                } else if (result > 0) {
                    std::cout << "Result is small: " << result << std::endl;
                } else {
                    std::cout << "Result is negative or error: " << result << std::endl;
                }
            }
            
        } else {
            std::cout << "License validation failed - exiting" << std::endl;
            return 1;
        }
        
    } else {
        std::cout << "Authentication failed - access denied" << std::endl;
        return 2;
    }
    
    std::cout << "\n=== Demo Complete ===" << std::endl;
    std::cout << "All sensitive strings and logic have been obfuscated!" << std::endl;
    std::cout << "Password hash stored: " << PASSWORD_HASH << std::endl;
    
    return 0;
}