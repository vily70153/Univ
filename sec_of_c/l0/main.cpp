#include <iostream>
#include <algorithm>
#include <numeric>
#include <span>
#include <string_view>
#include <vector>

template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <Numeric T>
T calculate_sum(std::span<const T> data) {
    return std::accumulate(data.begin(), data.end(), T{0});
} 

void print_banner(std::string_view title) {
 std::cout << "========================================\n";
 std::cout << " " << title << "\n";
 std::cout << "========================================\n";
}

int main() {
 print_banner("C++20 Environment Verification");
 std::vector<int> numbers = {10, 20, 30, 40, 50};
 int total = calculate_sum<int>(numbers);
 std::cout << "[OK] Compiler supports C++20 Concepts and std::span\n";
 std::cout << "[OK] Elements count: " << numbers.size() << "\n";
 std::cout << "[OK] Computed sum: " << total << "\n";
 std::cout << "[OK] Toolchain setup successful!\n";
 return 0;
}
