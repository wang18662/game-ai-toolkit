#include "gameai/core/utility.hpp"

#include <algorithm>
#include <cmath>

namespace gameai {

double normalize(double value, double min_val, double max_val) {
    if (max_val == min_val) return 0.0;
    double v = (value - min_val) / (max_val - min_val);
    return std::max(0.0, std::min(1.0, v));
}

double response_curve(CurveType curve, double x) {
    x = std::max(0.0, std::min(1.0, x));
    switch (curve) {
        case CurveType::Linear:   return x;
        case CurveType::Quadratic: return x * x;
        case CurveType::Power:     return std::sqrt(x);
        case CurveType::Sigmoid:   return 1.0 / (1.0 + std::exp(-(x - 0.5) * 10.0));
    }
    return x;
}

double Option::score(const AgentView& agent, const WorldView& world) const {
    if (considerations.empty()) return 0.0;
    double total = 0.0;
    double weight_sum = 0.0;
    for (const auto& c : considerations) {
        double raw = c.input_fn(agent, world);
        double n = normalize(raw, c.min_val, c.max_val);
        total += c.weight * response_curve(c.curve, n);
        weight_sum += c.weight;
    }
    return weight_sum == 0.0 ? 0.0 : total / weight_sum;
}

std::pair<Option, double> decide(const std::vector<Option>& options,
                                 const AgentView& agent, const WorldView& world) {
    Option best = options.empty() ? Option{"none"} : options.front();
    double best_score = -1.0;
    for (const auto& o : options) {
        double s = o.score(agent, world);
        if (s > best_score) {
            best_score = s;
            best = o;
        }
    }
    return {best, best_score};
}

double input_enemy_closeness(const AgentView& a, const WorldView& w) {
    if (!w.enemy_exists) return 0.0;
    return std::max(0.0, a.sight_range - w.enemy_distance);
}

double input_in_attack_range(const AgentView& a, const WorldView& w) {
    if (!w.enemy_exists) return 0.0;
    return w.enemy_distance <= a.attack_range ? 1.0 : 0.0;
}

double input_retreat_score(const AgentView& a, const WorldView& w) {
    double low = 1.0 - a.hp / a.max_hp;
    double threat = 0.0;
    if (w.enemy_exists && w.enemy_distance <= a.sight_range) threat = 0.6;
    return std::max(low, threat);
}

}  // namespace gameai
