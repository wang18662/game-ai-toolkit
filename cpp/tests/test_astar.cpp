#include <gtest/gtest.h>

#include <set>
#include <vector>

#include "gameai/core/astar.hpp"
#include "gameai/core/vector2.hpp"

using namespace gameai;

namespace {
bool walkable_grid(int w, int h, const std::set<std::pair<int, int>>& obs, int x, int y) {
    if (x < 0 || y < 0 || x >= w || y >= h) return false;
    return obs.find({x, y}) == obs.end();
}
}  // namespace

TEST(AStar, straight_line) {
    auto f = [](int x, int y) { return walkable_grid(10, 10, {}, x, y); };
    auto path = find_path({0, 0}, {5, 0}, f);
    ASSERT_EQ(path.size(), 6u);
    EXPECT_EQ(static_cast<int>(path.front().x), 0);
    EXPECT_EQ(static_cast<int>(path.back().x), 5);
}

TEST(AStar, detour_around_wall) {
    // vertical wall at x=2 for rows 0..3; gap at row 4 (must route through it)
    std::set<std::pair<int, int>> obs = {{2, 0}, {2, 1}, {2, 2}, {2, 3}};
    auto f = [&](int x, int y) { return walkable_grid(6, 6, obs, x, y); };
    auto path = find_path({0, 0}, {5, 0}, f);
    ASSERT_FALSE(path.empty());
    EXPECT_EQ(static_cast<int>(path.back().x), 5);
    EXPECT_EQ(static_cast<int>(path.back().y), 0);
}

TEST(AStar, unreachable_returns_empty) {
    std::set<std::pair<int, int>> obs = {{2, 0}, {2, 1}, {2, 2}, {2, 3}, {2, 4}};
    auto f = [&](int x, int y) { return walkable_grid(6, 6, obs, x, y); };
    auto path = find_path({0, 0}, {5, 0}, f);
    EXPECT_TRUE(path.empty());
}

TEST(AStar, diagonal_shorter) {
    auto f = [](int x, int y) { return walkable_grid(10, 10, {}, x, y); };
    auto ortho = find_path({0, 0}, {3, 3}, f, Octile{}, UniformCost{}, false);
    auto diag = find_path({0, 0}, {3, 3}, f, Octile{}, UniformCost{}, true);
    EXPECT_EQ(ortho.size(), 7u);
    EXPECT_EQ(diag.size(), 4u);
}
