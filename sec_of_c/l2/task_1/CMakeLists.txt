cmake_minimum_required(VERSION 3.16)
project(task_1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(task_1
    src/main.cpp
    src/Randl.cpp
)

target_include_directories(task_1 PRIVATE include)

set_target_properties(task_1 PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin"
)
