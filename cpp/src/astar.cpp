#include "gameai/core/astar.hpp"

#include <queue>
#include <unordered_map>
#include <vector>

namespace gameai {

namespace {
// Min-heap ordered by (f, x, y) so tie-breaking matches the Python heapq
// (which compares (f, (x, y))). Deterministic given the same inputs.
struct PQItem {
    double f;
    int x;
    int y;
    GridCoord coord;
    bool operator>(const PQItem& o) const {
        if (f != o.f) return f > o.f;
        if (x != o.x) return x > o.x;
        return y > o.y;
    }
};

inline int key_of(int x, int y) { return x * 100000 + y; }
}  // namespace

std::vector<Vector2> find_path(GridCoord start, GridCoord goal, WalkableFn is_walkable,
                               const Heuristic& heuristic, const Cost& cost, bool allow_diagonal) {
    start = {static_cast<int>(std::round(start.first)), static_cast<int>(std::round(start.second))};
    goal = {static_cast<int>(std::round(goal.first)), static_cast<int>(std::round(goal.second))};

    if (!is_walkable(goal.first, goal.second)) return {};

    std::priority_queue<PQItem, std::vector<PQItem>, std::greater<PQItem>> open;
    std::unordered_map<int, double> g_score;
    std::unordered_map<int, GridCoord> came_from;
    std::unordered_map<int, int> parent_key;

    int skey = key_of(start.first, start.second);
    g_score[skey] = 0.0;
    came_from[skey] = start;
    parent_key[skey] = -1;
    open.push({heuristic(start, goal), start.first, start.second, start});

    static const std::vector<GridCoord> ortho = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    static const std::vector<GridCoord> diag = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};

    while (!open.empty()) {
        PQItem top = open.top();
        open.pop();
        GridCoord current = top.coord;
        int ckey = key_of(current.first, current.second);

        if (current == goal) {
            std::vector<Vector2> path;
            int cur = ckey;
            while (cur != -1) {
                GridCoord c = came_from.at(cur);
                path.push_back(Vector2(static_cast<double>(c.first), static_cast<double>(c.second)));
                cur = parent_key.at(cur);
            }
            std::reverse(path.begin(), path.end());
            return path;
        }

        std::vector<GridCoord> dirs = ortho;
        if (allow_diagonal) {
            dirs.insert(dirs.end(), diag.begin(), diag.end());
        }
        for (const auto& d : dirs) {
            int nx = current.first + d.first;
            int ny = current.second + d.second;
            if (!is_walkable(nx, ny)) continue;
            if (d.first != 0 && d.second != 0) {
                if (!(is_walkable(current.first + d.first, current.second) &&
                      is_walkable(current.first, current.second + d.second)))
                    continue;
            }
            double step = cost({nx, ny});
            if (d.first != 0 && d.second != 0) step *= 1.41421356;
            double tentative = g_score[ckey] + step;
            int nkey = key_of(nx, ny);
            if (g_score.find(nkey) == g_score.end() || tentative < g_score[nkey]) {
                g_score[nkey] = tentative;
                came_from[nkey] = current;
                parent_key[nkey] = ckey;
                double f = tentative + heuristic({nx, ny}, goal);
                open.push({f, nx, ny, {nx, ny}});
            }
        }
    }
    return {};
}

}  // namespace gameai
