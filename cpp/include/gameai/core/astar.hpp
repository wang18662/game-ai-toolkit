#pragma once

#include <functional>
#include <vector>

#include "vector2.hpp"

namespace gameai {

using GridCoord = std::pair<int, int>;

// GoF Strategy: pluggable heuristic (cost-to-goal estimate).
struct Heuristic {
    virtual ~Heuristic() = default;
    virtual double operator()(GridCoord a, GridCoord b) const = 0;
};

struct Manhattan : Heuristic {
    double operator()(GridCoord a, GridCoord b) const override {
        return std::abs(a.first - b.first) + std::abs(a.second - b.second);
    }
};

struct Octile : Heuristic {
    double operator()(GridCoord a, GridCoord b) const override {
        double dx = std::abs(a.first - b.first);
        double dy = std::abs(a.second - b.second);
        return (dx + dy) + (1.41421356 - 2.0) * std::min(dx, dy);
    }
};

// GoF Strategy: per-step traversal cost.
struct Cost {
    virtual ~Cost() = default;
    virtual double operator()(GridCoord /*node*/) const = 0;
};

struct UniformCost : Cost {
    double operator()(GridCoord /*node*/) const override { return 1.0; }
};

using WalkableFn = std::function<bool(int, int)>;

// Grid A* returning waypoints (start -> goal) as Vector2.
// Mirrors Python core.astar.find_path: deterministic tie-break by (f, x, y),
// no corner cutting, diagonal cost x1.41421356. Empty list when unreachable.
std::vector<Vector2> find_path(GridCoord start, GridCoord goal,
                               WalkableFn is_walkable,
                               const Heuristic& heuristic = Octile{},
                               const Cost& cost = UniformCost{},
                               bool allow_diagonal = true);

}  // namespace gameai
