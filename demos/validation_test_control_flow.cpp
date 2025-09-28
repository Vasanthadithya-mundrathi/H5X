// Test program with known control flow patterns for validation
// Contains loops, conditionals, and switch statements

#include <iostream>
#include <vector>

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // For loop pattern
    int sum = 0;
    for (size_t i = 0; i < numbers.size(); i++) {
        sum += numbers[i];
    }
    std::cout << "For loop sum: " << sum << std::endl;

    // While loop pattern
    sum = 0;
    size_t index = 0;
    while (index < numbers.size()) {
        sum += numbers[index];
        index++;
    }
    std::cout << "While loop sum: " << sum << std::endl;

    // Do-while loop pattern
    sum = 0;
    index = 0;
    do {
        sum += numbers[index];
        index++;
    } while (index < numbers.size());
    std::cout << "Do-while sum: " << sum << std::endl;

    // If-else chain pattern
    for (int num : numbers) {
        if (num < 3) {
            std::cout << num << " is small" << std::endl;
        } else if (num < 7) {
            std::cout << num << " is medium" << std::endl;
        } else {
            std::cout << num << " is large" << std::endl;
        }
    }

    // Switch statement pattern
    for (int num : numbers) {
        switch (num) {
            case 1:
            case 2:
                std::cout << num << " is one or two" << std::endl;
                break;
            case 3:
            case 4:
            case 5:
                std::cout << num << " is three to five" << std::endl;
                break;
            case 6:
            case 7:
            case 8:
            case 9:
            case 10:
                std::cout << num << " is six to ten" << std::endl;
                break;
            default:
                std::cout << num << " is out of range" << std::endl;
                break;
        }
    }

    // Nested loop pattern
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            std::cout << "Nested: " << i << "," << j << std::endl;
        }
    }

    return 0;
}