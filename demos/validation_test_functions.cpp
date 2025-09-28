// Test program with known function call patterns for validation
// Contains various function definitions and calls

#include <iostream>
#include <string>
#include <cmath>

// Simple arithmetic functions
int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}

int divide(int a, int b) {
    if (b != 0) {
        return a / b;
    }
    return 0;
}

// String processing functions
std::string concatenate(const std::string& s1, const std::string& s2) {
    return s1 + s2;
}

int string_length(const std::string& s) {
    return s.length();
}

bool is_empty(const std::string& s) {
    return s.empty();
}

// Mathematical functions
double power(double base, int exponent) {
    return std::pow(base, exponent);
}

double square_root(double value) {
    return std::sqrt(value);
}

int absolute_value(int value) {
    return std::abs(value);
}

// Utility functions
void print_message(const std::string& message) {
    std::cout << message << std::endl;
}

void print_number(int number) {
    std::cout << "Number: " << number << std::endl;
}

void print_separator() {
    std::cout << "=================" << std::endl;
}

int main() {
    // Test arithmetic functions
    int x = 10;
    int y = 20;

    int sum = add(x, y);
    int diff = subtract(y, x);
    int prod = multiply(x, y);
    int quot = divide(y, x);

    print_number(sum);
    print_number(diff);
    print_number(prod);
    print_number(quot);

    print_separator();

    // Test string functions
    std::string first = "Hello";
    std::string second = " World";

    std::string combined = concatenate(first, second);
    int length = string_length(combined);
    bool empty = is_empty(combined);

    print_message(combined);
    print_number(length);
    print_number(empty ? 1 : 0);

    print_separator();

    // Test mathematical functions
    double base = 2.0;
    int exp = 8;

    double result = power(base, exp);
    double sqrt_result = square_root(result);
    int abs_result = absolute_value(-42);

    print_number(static_cast<int>(result));
    print_number(static_cast<int>(sqrt_result));
    print_number(abs_result);

    print_separator();

    // Complex function call chains
    std::string msg1 = "Function";
    std::string msg2 = " Testing";
    std::string msg3 = " Complete";

    std::string final_msg = concatenate(concatenate(msg1, msg2), msg3);
    print_message(final_msg);

    return 0;
}