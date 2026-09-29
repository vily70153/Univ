#include "../include/Randl.hpp"
#include <random>

uint32_t seed_val = 8345698;
std::uniform_int_distribution<uint32_t> uint_dist100(0,100);
MyRNG rng;   

void initialize() {
  static std::random_device rd;         // obtain a random number from hardware
  static MyRNG eng(rd());           // seed the generator
  rng.seed(seed_val);               // seed the generator
}

uint32_t get_random_uint(uint32_t min, uint32_t max) {
  std::uniform_int_distribution<uint32_t> uint_dist(min,max);
  return uint_dist(rng);
}