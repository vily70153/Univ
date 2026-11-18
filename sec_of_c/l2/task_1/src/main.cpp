#include "Randl.hpp"

#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>

bool read_number(std::uint32_t& value) {
    long long input = 0;

    if (!(std::cin >> input)) {
        std::cerr << "Error encountered, exiting...\n";
        return false;
    }

    if (input < 0 || input > 99) {
        std::cerr << "[WARNING] : Number must be between 0 and 99\n";
        return false;
    }

    value = static_cast<std::uint32_t>(input);
    return true;
}

int main() {
    const std::uint32_t random_number = get_random_uint(0, 99);

    while (true) {
        std::cout << "Enter your guess: ";

        std::uint32_t user_input = 0;
        if (!read_number(user_input)) {
            std::cout << "Random number: " << random_number << '\n';
            return EXIT_FAILURE;
        }

        if (user_input < random_number) {
            std::cout << "The hidden number is greater.\n";
        } else if (user_input > random_number) {
            std::cout << "The hidden number is smaller.\n";
        } else {
            std::cout << "You won!\n";
            break;
        }
    }

    std::cout << "Random number: " << random_number << '\n';
    return EXIT_SUCCESS;
}
