cmake_minimum_required(VERSION 3.20)
project(gameai_cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(FetchContent)

# ---------------------------------------------------------------------------
# 依赖一：nlohmann/json（只有 parity_runner 需要，核心库不需要）
#
# 策略：先找系统包；找不到再下载；**下载失败也只是跳过 parity_runner，不让整个构建挂**。
# 理由：核心库（astar / utility / fsm / bt）是纯标准库，本就不该被一个 JSON 库绑架。
# ---------------------------------------------------------------------------
find_package(nlohmann_json 3.11 QUIET)
if(NOT nlohmann_json_FOUND)
    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
        GIT_SHALLOW TRUE
        GIT_PROGRESS TRUE)
    # 只取头文件，不做 install / 不做测试，编译量小
    set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
    set(JSON_Install OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(nlohmann_json)
endif()

# ---------------------------------------------------------------------------
# 依赖二：GoogleTest
#
# 一律走 FetchContent。原因：
#   Ubuntu 的 libgtest-dev 只装源码/可能缺 gtest_main，find_package 稳不住；
#   而 googletest 的 shallow clone 只有几 MB，比版本差异带来的麻烦便宜得多。
# ---------------------------------------------------------------------------
set(BUILD_GMOCK OFF CACHE BOOL "" FORCE)
set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
    GIT_SHALLOW TRUE
    GIT_PROGRESS TRUE)
FetchContent_MakeAvailable(googletest)

enable_testing()

# ---------------------------------------------------------------------------
# 核心库：纯标准库，零外部依赖（这是「引擎无关」的一部分）
# ---------------------------------------------------------------------------
add_library(gameai_core
    src/astar.cpp
    src/utility.cpp
    src/fsm.cpp)
target_include_directories(gameai_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# ---------------------------------------------------------------------------
# 跨语言 parity 运行器：需要 JSON。拿不到就明确跳过，而不是让 CI 红一片。
# ---------------------------------------------------------------------------
if(TARGET nlohmann_json::nlohmann_json)
    add_executable(parity_runner src/parity_runner.cpp)
    target_link_libraries(parity_runner PRIVATE gameai_core nlohmann_json::nlohmann_json)
else()
    message(WARNING "nlohmann_json 不可用 —— 跳过 parity_runner（核心库与单测不受影响）")
endif()

# ---------------------------------------------------------------------------
# 单元测试
# ---------------------------------------------------------------------------
add_executable(cpp_tests
    tests/test_astar.cpp
    tests/test_utility.cpp
    tests/test_fsm.cpp
    tests/test_behavior_tree.cpp)
target_link_libraries(cpp_tests PRIVATE gameai_core GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(cpp_tests)
