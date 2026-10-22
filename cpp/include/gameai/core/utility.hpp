#pragma once

// 显式包含（同 astar.hpp 的说明：MSVC 传递包含、GCC 不传递）。
#include <functional> // std::function
#include <string>
#include <utility>    // std::pair
#include <vector>

#include "vector2.hpp"

namespace gameai {

// Minimal view objects the utility considerations read from. They mirror the
// fields the Python input functions (_enemy_closeness, _in_attack_range,
// _retreat_score) consume, so the two languages score identically.
struct AgentView {
    double hp = 100.0;
    double max_hp = 100.0;
    double sight_range = 6.0;
    double attack_range = 1.6;
    Vector2 pos;
};

struct WorldView {
    bool enemy_exists = false;
    double enemy_distance = 0.0;
};

using InputFn = std::function<double(const AgentView&, const WorldView&)>;

enum class CurveType { Linear, Quadratic, Power, Sigmoid };

double normalize(double value, double min_val, double max_val);
double response_curve(CurveType curve, double x);

struct Consideration {
    InputFn input_fn;
    CurveType curve = CurveType::Linear;
    double min_val = 0.0;
    double max_val = 1.0;
    double weight = 1.0;
};

struct Option {
    std::string name;
    std::vector<Consideration> considerations;

    double score(const AgentView& agent, const WorldView& world) const;
};

// Returns the highest-scoring option and its score (mirrors Python utility.decide).
std::pair<Option, double> decide(const std::vector<Option>& options,
                                 const AgentView& agent, const WorldView& world);

// The three input functions used by the skirmish utility brain (mirror Python).
double input_enemy_closeness(const AgentView& a, const WorldView& w);
double input_in_attack_range(const AgentView& a, const WorldView& w);
double input_retreat_score(const AgentView& a, const WorldView& w);

}  // namespace gameai
