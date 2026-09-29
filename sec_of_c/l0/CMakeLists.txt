cmake_minimum_required(VERSION 3.20)
project(CppEnvCheck LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_compile_options(
 -Wall
 -Wextra
 -Wpedantic
 -Werror
 -Wshadow
 -Wconversion
)

add_executable(test_app main.cpp)
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
 target_compile_options(test_app PRIVATE -fsanitize=address,undefined -g)
 target_link_options(test_app PRIVATE -fsanitize=address,undefined)
endif()
