
cmake_minimum_required(VERSION 3.10)
project(ipb_arithmetic)
set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_library(ipb_arithmetic STATIC src/sum.cpp src/subtract.cpp)

add_executable(main src/main.cpp)
target_link_libraries(main ipb_arithmetic)

install(TARGETS main ipb_arithmetic
        RUNTIME DESTINATION bin
        ARCHIVE DESTINATION lib)

install(DIRECTORY include/ DESTINATION include)