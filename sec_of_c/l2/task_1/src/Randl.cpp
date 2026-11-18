#include "Randl.hpp"

#include <random>

std::uint32_t get_random_uint(std::uint32_t min, std::uint32_t max) {
    std::random_device random_device;
    std::mt19937 generator(random_device());
    std::uniform_int_distribution<std::uint32_t> distribution(min, max);
    return distribution(generator);
}
