#include <cstdint>
#include <iostream>
#include <limits>
#include "../include/Randl.hpp"

bool get_user_input(uint32_t& user_input) {
  while (true) {
    std::cout << "Please enter a number between 1 and 100: ";

    if (std::cin >> user_input) {
      if (user_input >= 1 && user_input <= 100) {
        return true;
      }
      std::cout << "Number must be between 1 and 100.\n";
    } else {
      if (std::cin.eof()) {
        return false;
      }

      std::cin.clear();
      std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
      std::cout << "Invalid input.\n";
    }
  }
}

int main() {
  initialize();
  uint32_t random_number = get_random_uint(1, 100);
  uint32_t user_input;
  do {
    std::cout << "Random number: " << random_number << "\n";
    if (!get_user_input(user_input)) {
      std::cerr << "Error reading user input.\n";
      return 1;
    }
    if (user_input < random_number) {
      std::cout << "Your guess is too low.\n";
    } else if (user_input > random_number) {
      std::cout << "Your guess is too high.\n";
    } else {
      std::cout << "Congratulations! You guessed the number!\n";
      break;
    }
  } while (true);
  return 0;
}