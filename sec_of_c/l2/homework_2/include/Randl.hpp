#ifndef RANDL_HPP_
#define RANDL_HPP_


#include <random>

typedef std::mt19937 MyRNG;  // the Mersenne Twister with a popular choice of parameters


void initialize();
uint32_t get_random_uint(uint32_t min, uint32_t max);





#endif  // RANDL_HPP_