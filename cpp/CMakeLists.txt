cmake_minimum_required(VERSION 3.20)
project(gameai_cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(FetchContent)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3)
FetchContent_MakeAvailable(nlohmann_json)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0)
FetchContent_MakeAvailable(googletest)

enable_testing()

# Core library (behavior_tree is header-only; no separate .cpp).
add_library(gameai_core
    src/astar.cpp
    src/utility.cpp
    src/fsm.cpp)
target_include_directories(gameai_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(gameai_core PUBLIC nlohmann_json::nlohmann_json)

# Parity runner (reads the shared JSON map, emits normalized output).
add_executable(parity_runner src/parity_runner.cpp)
target_link_libraries(parity_runner PRIVATE gameai_core)

# Unit tests (GoogleTest).
add_executable(cpp_tests
    tests/test_astar.cpp
    tests/test_utility.cpp
    tests/test_fsm.cpp
    tests/test_behavior_tree.cpp)
target_link_libraries(cpp_tests PRIVATE gameai_core GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(cpp_tests)
