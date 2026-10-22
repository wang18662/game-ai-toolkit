cmake_minimum_required(VERSION 3.20)
project(gameai_cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(FetchContent)

# 依赖获取策略：**先用系统包，找不到才下载**。
#
# 原因：CI（ubuntu-latest）里 apt 已经装了 libgtest-dev，
# 若仍然无脑 FetchContent，等于在流水线里白下载一遍 googletest，
# 既慢又容易因网络抖动整 job 失败。
find_package(nlohmann_json 3.11 QUIET)
if(NOT nlohmann_json_FOUND)
    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
        GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(nlohmann_json)
endif()

find_package(GTest QUIET)
if(NOT GTest_FOUND)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.14.0
        GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(googletest)
endif()

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
