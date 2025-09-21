#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <cmath>
#include <map>
#include <memory>

// Complex algorithms to test comprehensive obfuscation
class AdvancedCalculator {
private:
    std::map<std::string, double> variables;
    
public:
    // Complex mathematical operations
    double fibonacci(int n) {
        if (n <= 1) return n;
        
        double a = 0, b = 1, temp;
        for (int i = 2; i <= n; i++) {
            temp = a + b;
            a = b;
            b = temp;
        }
        return b;
    }
    
    // Prime number generation with sieve
    std::vector<int> sieveOfEratosthenes(int limit) {
        std::vector<bool> isPrime(limit + 1, true);
        std::vector<int> primes;
        
        isPrime[0] = isPrime[1] = false;
        
        for (int i = 2; i * i <= limit; i++) {
            if (isPrime[i]) {
                for (int j = i * i; j <= limit; j += i) {
                    isPrime[j] = false;
                }
            }
        }
        
        for (int i = 2; i <= limit; i++) {
            if (isPrime[i]) {
                primes.push_back(i);
            }
        }
        
        return primes;
    }
    
    // Complex string processing
    std::string encryptString(const std::string& input, int shift = 3) {
        std::string result = input;
        
        for (char& c : result) {
            if (c >= 'a' && c <= 'z') {
                c = 'a' + (c - 'a' + shift) % 26;
            } else if (c >= 'A' && c <= 'Z') {
                c = 'A' + (c - 'A' + shift) % 26;
            }
        }
        
        return result;
    }
    
    // Variable management
    void setVariable(const std::string& name, double value) {
        variables[name] = value;
    }
    
    double getVariable(const std::string& name) {
        auto it = variables.find(name);
        return (it != variables.end()) ? it->second : 0.0;
    }
    
    // Complex calculation with multiple operations
    double complexCalculation(double x, double y) {
        double result = 0.0;
        
        // Multiple arithmetic operations for instruction substitution testing
        result += (x * y) + (x - y);
        result *= (x + y) / 2.0;
        result -= std::pow(x, 2) + std::pow(y, 2);
        result /= std::sqrt(x * x + y * y);
        
        // Conditional logic for control flow testing
        if (result > 0) {
            result = std::log(result + 1);
        } else if (result < 0) {
            result = -std::log(-result + 1);
        }
        
        return result;
    }
};

// Recursive algorithms for advanced obfuscation testing
class RecursiveAlgorithms {
public:
    // Tower of Hanoi
    void hanoi(int n, char from, char to, char aux) {
        if (n == 1) {
            std::cout << "Move disk from " << from << " to " << to << std::endl;
            return;
        }
        
        hanoi(n - 1, from, aux, to);
        std::cout << "Move disk from " << from << " to " << to << std::endl;
        hanoi(n - 1, aux, to, from);
    }
    
    // Binary tree operations
    struct TreeNode {
        int data;
        std::unique_ptr<TreeNode> left;
        std::unique_ptr<TreeNode> right;
        
        TreeNode(int val) : data(val), left(nullptr), right(nullptr) {}
    };
    
    void inorderTraversal(TreeNode* root) {
        if (root) {
            inorderTraversal(root->left.get());
            std::cout << root->data << " ";
            inorderTraversal(root->right.get());
        }
    }
    
    int treeHeight(TreeNode* root) {
        if (!root) return 0;
        
        int leftHeight = treeHeight(root->left.get());
        int rightHeight = treeHeight(root->right.get());
        
        return 1 + std::max(leftHeight, rightHeight);
    }
};

// Data structure operations
class DataStructureDemo {
private:
    std::vector<int> numbers;
    
public:
    void addNumbers(const std::vector<int>& nums) {
        numbers.insert(numbers.end(), nums.begin(), nums.end());
    }
    
    // Sorting algorithms
    void bubbleSort() {
        int n = numbers.size();
        for (int i = 0; i < n - 1; i++) {
            for (int j = 0; j < n - i - 1; j++) {
                if (numbers[j] > numbers[j + 1]) {
                    std::swap(numbers[j], numbers[j + 1]);
                }
            }
        }
    }
    
    void quickSort(int low, int high) {
        if (low < high) {
            int pi = partition(low, high);
            quickSort(low, pi - 1);
            quickSort(pi + 1, high);
        }
    }
    
    int partition(int low, int high) {
        int pivot = numbers[high];
        int i = low - 1;
        
        for (int j = low; j <= high - 1; j++) {
            if (numbers[j] < pivot) {
                i++;
                std::swap(numbers[i], numbers[j]);
            }
        }
        std::swap(numbers[i + 1], numbers[high]);
        return i + 1;
    }
    
    void printNumbers() {
        std::cout << "Numbers: ";
        for (int num : numbers) {
            std::cout << num << " ";
        }
        std::cout << std::endl;
    }
    
    // Statistical operations
    double mean() {
        if (numbers.empty()) return 0.0;
        
        double sum = 0.0;
        for (int num : numbers) {
            sum += num;
        }
        return sum / numbers.size();
    }
    
    double standardDeviation() {
        if (numbers.size() <= 1) return 0.0;
        
        double avg = mean();
        double sum = 0.0;
        
        for (int num : numbers) {
            sum += (num - avg) * (num - avg);
        }
        
        return std::sqrt(sum / (numbers.size() - 1));
    }
};

// String manipulation class with various algorithms
class StringProcessor {
public:
    // Pattern matching
    std::vector<int> naivePatternSearch(const std::string& text, const std::string& pattern) {
        std::vector<int> positions;
        int n = text.length();
        int m = pattern.length();
        
        for (int i = 0; i <= n - m; i++) {
            int j;
            for (j = 0; j < m; j++) {
                if (text[i + j] != pattern[j]) {
                    break;
                }
            }
            if (j == m) {
                positions.push_back(i);
            }
        }
        
        return positions;
    }
    
    // String compression
    std::string compressString(const std::string& input) {
        if (input.empty()) return "";
        
        std::string compressed;
        char currentChar = input[0];
        int count = 1;
        
        for (size_t i = 1; i < input.length(); i++) {
            if (input[i] == currentChar) {
                count++;
            } else {
                compressed += currentChar + std::to_string(count);
                currentChar = input[i];
                count = 1;
            }
        }
        compressed += currentChar + std::to_string(count);
        
        return compressed.length() < input.length() ? compressed : input;
    }
    
    // Palindrome checking
    bool isPalindrome(const std::string& str) {
        int left = 0;
        int right = str.length() - 1;
        
        while (left < right) {
            if (str[left] != str[right]) {
                return false;
            }
            left++;
            right--;
        }
        
        return true;
    }
};

int main() {
    std::cout << "🧮 H5X COMPREHENSIVE OBFUSCATION DEMO" << std::endl;
    std::cout << "=====================================" << std::endl;
    
    // Test advanced calculator
    std::cout << "\n📊 Testing Advanced Calculator:" << std::endl;
    AdvancedCalculator calc;
    
    // Test fibonacci
    int fibNum = 10;
    std::cout << "Fibonacci(" << fibNum << ") = " << calc.fibonacci(fibNum) << std::endl;
    
    // Test prime generation
    std::vector<int> primes = calc.sieveOfEratosthenes(30);
    std::cout << "Primes up to 30: ";
    for (int prime : primes) {
        std::cout << prime << " ";
    }
    std::cout << std::endl;
    
    // Test string encryption
    std::string original = "HelloWorld";
    std::string encrypted = calc.encryptString(original, 5);
    std::cout << "Encrypted '" << original << "' -> '" << encrypted << "'" << std::endl;
    
    // Test variable management
    calc.setVariable("pi", 3.14159);
    calc.setVariable("e", 2.71828);
    std::cout << "Stored variables: pi = " << calc.getVariable("pi") 
              << ", e = " << calc.getVariable("e") << std::endl;
    
    // Test complex calculation
    double complexResult = calc.complexCalculation(5.0, 3.0);
    std::cout << "Complex calculation result: " << complexResult << std::endl;
    
    // Test recursive algorithms
    std::cout << "\n🔄 Testing Recursive Algorithms:" << std::endl;
    RecursiveAlgorithms recursiveAlgo;
    
    std::cout << "Tower of Hanoi (3 disks):" << std::endl;
    recursiveAlgo.hanoi(3, 'A', 'C', 'B');
    
    // Test data structures
    std::cout << "\n📚 Testing Data Structures:" << std::endl;
    DataStructureDemo dataDemo;
    
    std::vector<int> testNumbers = {64, 34, 25, 12, 22, 11, 90, 5};
    dataDemo.addNumbers(testNumbers);
    
    std::cout << "Original ";
    dataDemo.printNumbers();
    
    std::cout << "Mean: " << dataDemo.mean() << std::endl;
    std::cout << "Standard Deviation: " << dataDemo.standardDeviation() << std::endl;
    
    dataDemo.bubbleSort();
    std::cout << "After bubble sort ";
    dataDemo.printNumbers();
    
    // Test string processing
    std::cout << "\n🔤 Testing String Processing:" << std::endl;
    StringProcessor strProcessor;
    
    std::string text = "ABABDABACDABABCABCABCABC";
    std::string pattern = "ABABCAB";
    
    std::vector<int> matches = strProcessor.naivePatternSearch(text, pattern);
    std::cout << "Pattern '" << pattern << "' found at positions: ";
    for (int pos : matches) {
        std::cout << pos << " ";
    }
    std::cout << std::endl;
    
    std::string testStr = "aabcccccaaa";
    std::string compressed = strProcessor.compressString(testStr);
    std::cout << "Compressed '" << testStr << "' -> '" << compressed << "'" << std::endl;
    
    std::string palindromeTest = "racecar";
    std::cout << "'" << palindromeTest << "' is " 
              << (strProcessor.isPalindrome(palindromeTest) ? "" : "not ") 
              << "a palindrome" << std::endl;
    
    // Final demonstration with multiple nested loops and conditions
    std::cout << "\n🎯 Final Complexity Test:" << std::endl;
    
    int matrix[5][5];
    int value = 1;
    
    // Create a spiral matrix (complex nested loops)
    for (int layer = 0; layer < 3; layer++) {
        // Fill top row
        for (int i = layer; i < 5 - layer; i++) {
            matrix[layer][i] = value++;
        }
        
        // Fill right column
        for (int i = layer + 1; i < 5 - layer; i++) {
            matrix[i][5 - 1 - layer] = value++;
        }
        
        // Fill bottom row (if exists)
        if (5 - 1 - layer > layer) {
            for (int i = 5 - 2 - layer; i >= layer; i--) {
                matrix[5 - 1 - layer][i] = value++;
            }
        }
        
        // Fill left column (if exists)
        if (layer < 5 - 1 - layer) {
            for (int i = 5 - 2 - layer; i > layer; i--) {
                matrix[i][layer] = value++;
            }
        }
    }
    
    std::cout << "Generated 5x5 spiral matrix:" << std::endl;
    for (int i = 0; i < 5; i++) {
        for (int j = 0; j < 5; j++) {
            std::cout << std::setw(3) << matrix[i][j] << " ";
        }
        std::cout << std::endl;
    }
    
    std::cout << "\n✅ Comprehensive obfuscation demo completed!" << std::endl;
    std::cout << "This program contains complex algorithms perfect for testing:" << std::endl;
    std::cout << "  • String obfuscation and encryption" << std::endl;
    std::cout << "  • Instruction substitution in arithmetic operations" << std::endl;
    std::cout << "  • Control flow flattening in recursive functions" << std::endl;
    std::cout << "  • Bogus control flow injection in loops" << std::endl;
    std::cout << "  • Anti-analysis techniques on function names" << std::endl;
    
    return 0;
}